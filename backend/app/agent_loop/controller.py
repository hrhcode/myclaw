from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent_loop.prompting import build_memory_message, build_system_prompt
from app.agent_loop.types import AgentRunState, LoopRuntimeConfig, ToolExecutionRecord
from app.common.config import get_config_value
from app.common.constants import API_KEY_KEY, LLM_MODEL_KEY
from app.dao.agent_event_dao import AgentEventDAO
from app.dao.agent_run_dao import AgentRunDAO
from app.dao.memory_dao import MemoryDAO
from app.dao.tool_call_dao import ToolCallDAO
from app.schemas.schemas import ChatRequest
from app.services.conversation_service import ConversationService
from app.services.llm_service import get_llm_service
from app.services.message_service import MessageService
from app.services.session_service import SessionService
from app.services.skill_service import SkillService
from app.services.vector_search_service import hybrid_memory_search
from app.tools import tool_executor, tool_registry, tools_to_zhipu_schemas
from app.tools import groups as tool_groups
from app.tools.profiles import create_profile_resolver
from app.tools.loop_detection import LoopSeverity, create_loop_detector

logger = logging.getLogger(__name__)

MAX_MODEL_TOOL_RESULT_CHARS = 4000
MAX_MODEL_TOOL_RESULT_ITEMS = 8
MAX_MODEL_TEXT_PREVIEW = 1200
MAX_CONTEXT_MESSAGES = 18
MAX_CONTEXT_CHARS = 22000
MAX_SUMMARY_LINES = 12


def build_memory_context(memory_results: List[Any]) -> str:
    if not memory_results:
        return ""

    lines = ["## Relevant Memory"]
    for result in memory_results:
        source_label = "message" if result.source == "message" else "long_term_memory"
        lines.append(f"- [{source_label}] {result.content} (score {result.score:.2f})")
    lines.append("")
    return "\n".join(lines)


class AgentLoopController:
    def __init__(
        self,
        conversation_service: Optional[ConversationService] = None,
        message_service: Optional[MessageService] = None,
    ) -> None:
        self.conversation_service = conversation_service or ConversationService()
        self.message_service = message_service or MessageService()
        self.session_service = SessionService()
        self.skill_service = SkillService()

    async def run_stream(
        self,
        request: ChatRequest,
        db: AsyncSession,
    ) -> AsyncIterator[Dict[str, Any]]:
        session = await self.session_service.resolve_session(db, request.session_id)

        command_response = await self._handle_command(db, session.id, request)
        if command_response is not None:
            yield command_response
            yield {"type": "done", "conversation_id": command_response["conversation_id"], "run_id": command_response["run_id"], "session_id": session.id}
            return

        api_key = await get_config_value(db, API_KEY_KEY)
        if not api_key:
            raise RuntimeError("Zhipu API key is not configured")

        model = session.model or await get_config_value(db, LLM_MODEL_KEY)
        runtime_config = await self._load_runtime_config(db, session)
        tool_executor.timeout_seconds = runtime_config.timeout_seconds

        conversation_id, _conversation = await self.conversation_service.get_or_create(
            db, request.message, request.conversation_id, session_id=session.id
        )
        await self.message_service.save(db, session.id, conversation_id, "user", request.message)

        message_history = await self.message_service.get_model_history(db, conversation_id)
        memory_context = await self._load_memory_context(db, conversation_id, request.message)
        skill_context = await self.skill_service.build_session_skill_context(db, session.id)
        workspace_context = self.skill_service.build_workspace_prompt_context(session.workspace_path)

        state = AgentRunState(
            run_id=str(uuid4()),
            conversation_id=conversation_id,
            session_id=session.id,
            user_message=request.message,
            messages=self._build_initial_messages(
                message_history,
                memory_context,
                runtime_config,
                workspace_dir=session.workspace_path or os.getcwd(),
                skill_context=skill_context,
                workspace_context=workspace_context,
                context_summary=session.context_summary or "",
            ),
            memory_context=memory_context,
        )
        await AgentRunDAO.create(
            db,
            run_id=state.run_id,
            session_id=session.id,
            conversation_id=conversation_id,
            user_message=request.message,
            stop_reason=None,
            compacted_summary="",
        )

        yield await self._emit_event(
            db,
            state,
            {
                "type": "conversation",
                "conversation_id": conversation_id,
                "run_id": state.run_id,
                "session_id": session.id,
            },
            persist=False,
        )

        llm = get_llm_service(api_key)
        loop_detector = create_loop_detector()

        while state.iteration < runtime_config.max_iterations:
            state.iteration += 1
            self._maybe_compact_context(state)
            tools = self._resolve_tools(runtime_config, state)

            current_tool_calls: List[Dict[str, Any]] = []
            current_content = ""
            current_reasoning = ""
            reasoning_for_assistant_turn = ""
            reasoning_emitted = False
            saw_tool_calls = False

            if tools is None:
                async for content in llm.chat_stream(
                    messages=state.messages,
                    model=model,
                    thinking=True,
                ):
                    current_content += content
                    state.final_answer += content
                    yield await self._emit_event(
                        db,
                        state,
                        {
                            "type": "content",
                            "content": content,
                            "conversation_id": conversation_id,
                            "run_id": state.run_id,
                            "session_id": session.id,
                        },
                        persist=False,
                    )
                if current_reasoning.strip():
                    await self._persist_trace_event(
                        db,
                        state,
                        "reasoning",
                        {
                            "content": current_reasoning.strip(),
                            "iteration": state.iteration,
                        },
                    )
                state.stop_reason = "final_answer"
                break

            async for chunk in llm.chat_stream_with_tools(
                messages=state.messages,
                tools=tools,
                model=model,
                thinking=True,
            ):
                chunk_type = chunk.get("type")
                if chunk_type == "content":
                    content = chunk.get("content", "")
                    if content:
                        current_content += content
                        state.final_answer += content
                        yield await self._emit_event(
                            db,
                            state,
                            {
                                "type": "content",
                                "content": content,
                                "conversation_id": conversation_id,
                                "run_id": state.run_id,
                                "session_id": session.id,
                            },
                            persist=False,
                        )
                elif chunk_type == "reasoning":
                    reasoning = chunk.get("content", "")
                    if reasoning:
                        reasoning_emitted = True
                        current_reasoning += reasoning
                        yield await self._emit_event(
                            db,
                            state,
                            {
                                "type": "reasoning",
                                "content": reasoning,
                                "conversation_id": conversation_id,
                                "run_id": state.run_id,
                                "iteration": state.iteration,
                                "session_id": session.id,
                            },
                            persist=False,
                        )
                elif chunk_type == "tool_calls":
                    current_tool_calls = chunk.get("tool_calls", [])
                    if current_tool_calls:
                        saw_tool_calls = True
                        state.tool_calls_info.extend(current_tool_calls)
                        if current_reasoning.strip():
                            reasoning_for_assistant_turn = current_reasoning.strip()
                            await self._persist_trace_event(
                                db,
                                state,
                                "reasoning",
                                {
                                    "content": current_reasoning.strip(),
                                    "iteration": state.iteration,
                                },
                            )
                            current_reasoning = ""

                        for tool_call in current_tool_calls:
                            yield await self._emit_event(
                                db,
                                state,
                                {
                                    "type": "tool_call",
                                    "tool_name": tool_call.get("name"),
                                    "tool_call_id": tool_call.get("id"),
                                    "arguments": tool_call.get("arguments"),
                                    "conversation_id": conversation_id,
                                    "run_id": state.run_id,
                                    "iteration": state.iteration,
                                    "session_id": session.id,
                                },
                                persist=True,
                                event_type="tool_call",
                            )

            if current_reasoning.strip():
                if not reasoning_for_assistant_turn:
                    reasoning_for_assistant_turn = current_reasoning.strip()
                await self._persist_trace_event(
                    db,
                    state,
                    "reasoning",
                    {
                        "content": current_reasoning.strip(),
                        "iteration": state.iteration,
                    },
                )

            if not saw_tool_calls or not current_tool_calls:
                state.stop_reason = "final_answer"
                break

            state.messages.append(
                self._build_assistant_tool_message(
                    current_content,
                    current_tool_calls,
                    reasoning_for_assistant_turn,
                )
            )
            state.final_answer = ""

            tool_results = await self.message_service.process_tool_calls(
                db=db,
                session_id=session.id,
                conversation_id=conversation_id,
                message_id=None,
                tool_calls=current_tool_calls,
                tool_executor=tool_executor,
            )

            for tool_call, tool_result in zip(current_tool_calls, tool_results):
                normalized_args = self._safe_parse_json(tool_call.get("arguments", "{}"))
                normalized_result = self._safe_parse_json(tool_result.get("content", "{}"))
                sanitized_content = self._build_tool_result_for_model(
                    tool_name=tool_call.get("name", ""),
                    result_payload=normalized_result,
                )
                record = ToolExecutionRecord(
                    tool_name=tool_call.get("name", ""),
                    tool_call_id=tool_call.get("id", ""),
                    arguments=normalized_args,
                    success=bool(normalized_result.get("success")),
                    result=normalized_result,
                    error=normalized_result.get("error"),
                    sanitized_content=sanitized_content,
                )
                record.novelty_key = self._make_novelty_key(record)
                state.tool_history.append(record)

                loop_detector.record_call(
                    tool_name=record.tool_name,
                    params=record.arguments,
                    result=record.result,
                )

                yield await self._emit_event(
                    db,
                    state,
                    {
                        "type": "tool_result",
                        "tool_call_id": tool_result.get("tool_call_id"),
                        "content": tool_result.get("content"),
                        "conversation_id": conversation_id,
                        "run_id": state.run_id,
                        "iteration": state.iteration,
                        "session_id": session.id,
                    },
                    persist=True,
                    event_type="tool_result",
                )

                state.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_result.get("tool_call_id"),
                        "content": sanitized_content,
                    }
                )

            if not reasoning_emitted:
                post_tool_reasoning = await self._generate_post_tool_reasoning(
                    llm=llm,
                    state=state,
                    model=model,
                )
                if post_tool_reasoning:
                    yield await self._emit_event(
                        db,
                        state,
                        {
                            "type": "reasoning",
                            "content": post_tool_reasoning,
                            "conversation_id": conversation_id,
                            "run_id": state.run_id,
                            "iteration": state.iteration,
                            "phase": "post_tool_reflection",
                            "session_id": session.id,
                        },
                        persist=True,
                        event_type="reasoning",
                    )

            progress_hint = self._assess_progress(state)
            if progress_hint:
                yield await self._emit_event(
                    db,
                    state,
                    {
                        **progress_hint,
                        "conversation_id": conversation_id,
                        "run_id": state.run_id,
                        "session_id": session.id,
                    },
                    persist=True,
                    event_type="progress_warning",
                )

            detection = loop_detector.detect()
            if detection.severity != LoopSeverity.NONE:
                yield await self._emit_event(
                    db,
                    state,
                    {
                        "type": "loop_warning",
                        "severity": detection.severity.value,
                        "message": detection.message,
                        "pattern": detection.pattern,
                        "count": detection.count,
                        "conversation_id": conversation_id,
                        "run_id": state.run_id,
                        "session_id": session.id,
                    },
                    persist=True,
                    event_type="loop_warning",
                )
                state.messages.append(
                    {
                        "role": "system",
                        "content": self._build_loop_guidance(detection.message, detection.should_block),
                    }
                )
                if detection.should_block:
                    state.force_answer_next = True

        final_text = state.final_answer.strip()
        if not final_text and state.stop_reason != "final_answer":
            final_text = self._build_fallback_answer(state)
        if not final_text:
            final_text = "I do not have enough new information to continue safely."

        assistant_message = await self.message_service.save(
            db, session.id, conversation_id, "assistant", final_text
        )
        await self._maybe_extract_memory(db, session, request.message, final_text)
        if state.tool_calls_info:
            for tool_call in state.tool_calls_info:
                tool_call_id = tool_call.get("id", "")
                await ToolCallDAO.update_message_id(db, tool_call_id, assistant_message.id)

        await AgentEventDAO.update_message_id_by_run_id(db, state.run_id, assistant_message.id)

        run_record = await AgentRunDAO.get_by_run_id(db, state.run_id)
        if run_record:
            await AgentRunDAO.update(
                db,
                run_record,
                stop_reason=state.stop_reason,
                compacted_summary=state.compacted_summary,
                completed_at=datetime.utcnow(),
            )

        yield await self._emit_event(
            db,
            state,
            {
                "type": "done",
                "conversation_id": conversation_id,
                "run_id": state.run_id,
                "session_id": session.id,
            },
            persist=False,
        )

    async def _maybe_extract_memory(self, db: AsyncSession, session: Any, user_message: str, final_text: str) -> None:
        if not session.memory_auto_extract:
            return
        combined = f"User: {user_message}\nAssistant: {final_text}".strip()
        if len(combined) < max(session.memory_threshold, 1) * 20:
            return
        try:
            await MemoryDAO.create(
                db,
                session_id=session.id,
                content=self._truncate_text(combined, 2000),
                importance=0.6,
                source=f"session:{session.name}:auto_extract",
            )
        except Exception:
            logger.exception("[agent_loop] automatic memory extraction failed")

    async def dispatch_message(
        self,
        db: AsyncSession,
        session_id: int,
        message: str,
    ) -> Dict[str, Any]:
        stream = self.run_stream(ChatRequest(session_id=session_id, message=message), db)
        final_event: Dict[str, Any] = {"session_id": session_id}
        async for event in stream:
            final_event = event
        return final_event

    async def dispatch_message_for_automation(self, session_id: int, message: str, automation_id: Optional[int] = None) -> str:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await self.dispatch_message(db, session_id, message)
            return str(result.get("run_id") or "")

    async def _handle_command(
        self,
        db: AsyncSession,
        session_id: int,
        request: ChatRequest,
    ) -> Optional[Dict[str, Any]]:
        if not request.message.startswith("/"):
            return None
        command = request.message.strip().split()[0].lower()
        conversation_id, _conversation = await self.conversation_service.get_or_create(
            db, request.message, request.conversation_id, session_id=session_id
        )
        run_id = str(uuid4())

        if command in {"/new", "/reset"}:
            if command == "/new":
                new_conversation, _ = await self.conversation_service.get_or_create(
                    db, "New Chat", None, session_id=session_id
                )
                content = f"Created a new conversation in session {session_id}."
                conversation_id = new_conversation
            else:
                session = await self.session_service.get_by_id(db, session_id)
                if session:
                    await self.session_service.update(db, session_id, context_summary="")
                content = "Session context summary has been reset."
        elif command == "/compact":
            messages = await self.message_service.get_recent_messages(db, conversation_id, limit=8)
            summary_lines = ["## Manual Compact"]
            for message in messages:
                summary_lines.append(f"- [{message.role}] {self._truncate_text(message.content, 180)}")
            compact_summary = "\n".join(summary_lines[:10])
            await self.session_service.update(db, session_id, context_summary=compact_summary)
            content = compact_summary
        elif command == "/status":
            status = await self.session_service.get_status(db, session_id)
            content = json.dumps(status, ensure_ascii=False, indent=2)
        else:
            return None

        assistant_message = await self.message_service.save(db, session_id, conversation_id, "assistant", content, generate_embedding=False)
        await AgentRunDAO.create(
            db,
            run_id=run_id,
            session_id=session_id,
            conversation_id=conversation_id,
            user_message=request.message,
            stop_reason="command",
            compacted_summary=content[:1000],
            completed_at=datetime.utcnow(),
        )
        await AgentEventDAO.create(
            db=db,
            session_id=session_id,
            conversation_id=conversation_id,
            run_id=run_id,
            event_type="reasoning",
            payload=json.dumps({"content": f"Handled chat command {command}"}, ensure_ascii=False),
            sequence=1,
            message_id=assistant_message.id,
        )
        return {
            "type": "content",
            "content": content,
            "conversation_id": conversation_id,
            "run_id": run_id,
            "session_id": session_id,
        }

    async def _load_runtime_config(self, db: AsyncSession, session: Any) -> LoopRuntimeConfig:
        tool_enabled = await get_config_value(db, "tool_enabled")
        tool_max_iterations = await get_config_value(db, "tool_max_iterations")
        tool_timeout = await get_config_value(db, "tool_timeout_seconds")
        tool_profile = await get_config_value(db, "tool_profile")
        tool_allow = await get_config_value(db, "tool_allow")
        tool_deny = await get_config_value(db, "tool_deny")

        allow_list = [item.strip() for item in (tool_allow or "").split(",") if item.strip()]
        deny_list = [item.strip() for item in (tool_deny or "").split(",") if item.strip()]

        return LoopRuntimeConfig(
            use_tools=tool_enabled == "true" if tool_enabled else True,
            max_iterations=session.max_iterations or (int(tool_max_iterations) if tool_max_iterations else 5),
            timeout_seconds=int(tool_timeout) if tool_timeout else 30,
            profile=session.tool_profile or tool_profile or "full",
            allow=[item.strip() for item in (session.tool_allow or "").split(",") if item.strip()] or allow_list,
            deny=[item.strip() for item in (session.tool_deny or "").split(",") if item.strip()] or deny_list,
        )

    async def _load_memory_context(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_message: str,
    ) -> str:
        memory_top_k = await get_config_value(db, "memory_top_k")
        memory_min_score = await get_config_value(db, "memory_min_score")
        memory_use_hybrid = await get_config_value(db, "memory_use_hybrid")
        memory_vector_weight = await get_config_value(db, "memory_vector_weight")
        memory_text_weight = await get_config_value(db, "memory_text_weight")
        memory_enable_mmr = await get_config_value(db, "memory_enable_mmr")
        memory_mmr_lambda = await get_config_value(db, "memory_mmr_lambda")
        memory_enable_temporal_decay = await get_config_value(db, "memory_enable_temporal_decay")
        memory_half_life_days = await get_config_value(db, "memory_half_life_days")

        memory_results = await hybrid_memory_search(
            db=db,
            query=user_message,
            conversation_id=conversation_id,
            top_k=int(memory_top_k) if memory_top_k else 5,
            min_score=float(memory_min_score) if memory_min_score else 0.5,
            include_messages=True,
            include_long_term=True,
            use_hybrid=(memory_use_hybrid == "true") if memory_use_hybrid else True,
            vector_weight=float(memory_vector_weight) if memory_vector_weight else 0.7,
            text_weight=float(memory_text_weight) if memory_text_weight else 0.3,
            enable_mmr=(memory_enable_mmr == "true") if memory_enable_mmr else True,
            mmr_lambda=float(memory_mmr_lambda) if memory_mmr_lambda else 0.7,
            enable_temporal_decay=(memory_enable_temporal_decay == "true") if memory_enable_temporal_decay else True,
            half_life_days=int(memory_half_life_days) if memory_half_life_days else 30,
        )
        return build_memory_context(memory_results)

    def _build_initial_messages(
        self,
        message_history: List[Dict[str, Any]],
        memory_context: str,
        runtime_config: LoopRuntimeConfig,
        *,
        workspace_dir: str,
        skill_context: str = "",
        workspace_context: str = "",
        context_summary: str = "",
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": build_system_prompt(
                    tool_enabled=runtime_config.use_tools,
                    max_iterations=runtime_config.max_iterations,
                    profile=runtime_config.profile,
                    workspace_dir=workspace_dir,
                    available_tool_names=self._get_prompt_tool_names(runtime_config),
                ),
            }
        ]
        if context_summary:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "## Session Context Summary\n"
                        f"{context_summary}\n\n"
                        "Use this as prior working context for the current session."
                    ),
                }
            )
        if workspace_context:
            messages.append({"role": "system", "content": workspace_context})
        if skill_context:
            messages.append({"role": "system", "content": skill_context})
        if memory_context:
            messages.append(
                {
                    "role": "system",
                    "content": build_memory_message(memory_context),
                }
            )
        messages.extend(message_history)
        return messages

    def _resolve_tools(
        self, runtime_config: LoopRuntimeConfig, state: AgentRunState
    ) -> Optional[List[Dict[str, Any]]]:
        if not runtime_config.use_tools or state.force_answer_next:
            return None

        enabled_tools = tool_registry.list_enabled_tools()
        resolver = create_profile_resolver(tool_groups)
        policy = resolver.resolve(
            profile_id=runtime_config.profile,
            custom_allow=runtime_config.allow,
            custom_deny=runtime_config.deny,
        )
        allowed = policy.get("allow", set())
        denied = policy.get("deny", set())

        filtered_tools = []
        for tool in enabled_tools:
            if tool.name in denied:
                continue
            if allowed and tool.name not in allowed:
                continue
            filtered_tools.append(tool)

        if not filtered_tools:
            logger.warning(
                "[agent_loop] 褰撳墠绛栫暐涓嬫棤鍙敤宸ュ叿: profile=%s allow=%s deny=%s",
                runtime_config.profile,
                runtime_config.allow,
                runtime_config.deny,
            )
            return None

        return tools_to_zhipu_schemas(filtered_tools)

    def _get_prompt_tool_names(self, runtime_config: LoopRuntimeConfig) -> List[str]:
        if not runtime_config.use_tools:
            return []

        enabled_tools = tool_registry.list_enabled_tools()
        resolver = create_profile_resolver(tool_groups)
        policy = resolver.resolve(
            profile_id=runtime_config.profile,
            custom_allow=runtime_config.allow,
            custom_deny=runtime_config.deny,
        )
        allowed = policy.get("allow", set())
        denied = policy.get("deny", set())

        tool_names: List[str] = []
        for tool in enabled_tools:
            if tool.name in denied:
                continue
            if allowed and tool.name not in allowed:
                continue
            tool_names.append(tool.name)
        return tool_names

    def _build_assistant_tool_message(
        self,
        content: str,
        tool_calls: List[Dict[str, Any]],
        reasoning_content: str = "",
    ) -> Dict[str, Any]:
        message = {
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": tool_call.get("id"),
                    "type": "function",
                    "function": {
                        "name": tool_call.get("name"),
                        "arguments": tool_call.get("arguments"),
                    },
                }
                for tool_call in tool_calls
            ],
        }
        if reasoning_content:
            message["reasoning_content"] = reasoning_content
        return message

    def _assess_progress(self, state: AgentRunState) -> Optional[Dict[str, Any]]:
        if not state.tool_history:
            return None

        last_record = state.tool_history[-1]
        previous_record = state.tool_history[-2] if len(state.tool_history) >= 2 else None
        signature = self._make_progress_signature(last_record)
        made_progress = self._tool_result_shows_progress(state, last_record)

        if state.progress.last_signature == signature:
            state.progress.repeated_tool_call_count += 1
        else:
            state.progress.repeated_tool_call_count = 0

        if made_progress:
            state.progress.stalled_iterations = 0
            if last_record.success:
                state.progress.last_success_signature = signature
        else:
            state.progress.stalled_iterations += 1

        state.progress.last_signature = signature

        if (
            previous_record is not None
            and not previous_record.success
            and not last_record.success
            and previous_record.tool_name == last_record.tool_name
            and previous_record.arguments == last_record.arguments
        ):
            state.messages.append(
                {
                    "role": "system",
                    "content": (
                        "The same tool call has failed repeatedly with the same inputs. "
                        "Do not retry it again. Explain the failure and provide the best possible answer."
                    ),
                }
            )
            state.force_answer_next = True
            return {
                "type": "progress_warning",
                "stalled_iterations": state.progress.stalled_iterations,
                "message": f"Repeated failure detected for tool `{last_record.tool_name}`.",
            }

        if state.progress.stalled_iterations < 2:
            return None

        state.messages.append(
            {
                "role": "system",
                "content": (
                    "You have not made progress in recent iterations. Stop repeating the same tool call. "
                    "Try a different strategy, summarize the blocker, or tell the user what is missing."
                ),
            }
        )
        return {
            "type": "progress_warning",
            "stalled_iterations": state.progress.stalled_iterations,
            "message": "Recent iterations did not show clear progress.",
        }

    def _make_progress_signature(self, record: ToolExecutionRecord) -> str:
        payload = {
            "tool_name": record.tool_name,
            "arguments": record.arguments,
            "success": record.success,
            "error": record.error,
            "result": record.sanitized_content,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _make_novelty_key(self, record: ToolExecutionRecord) -> str:
        payload = {
            "tool_name": record.tool_name,
            "success": record.success,
            "error": record.error,
            "sanitized_content": record.sanitized_content,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _tool_result_shows_progress(
        self, state: AgentRunState, record: ToolExecutionRecord
    ) -> bool:
        if not record.success:
            return False
        if not record.sanitized_content.strip():
            return False
        if record.novelty_key is None:
            return False

        previous_keys = {
            item.novelty_key
            for item in state.tool_history[:-1]
            if item.success and item.novelty_key
        }
        return record.novelty_key not in previous_keys

    def _build_tool_result_for_model(
        self,
        tool_name: str,
        result_payload: Dict[str, Any],
    ) -> str:
        success = bool(result_payload.get("success"))
        error = result_payload.get("error")
        execution_time_ms = result_payload.get("execution_time_ms")
        content = result_payload.get("content")

        summary = {
            "tool": tool_name,
            "success": success,
            "error": error,
            "execution_time_ms": execution_time_ms,
            "content": self._sanitize_tool_content(content),
        }
        text = json.dumps(summary, ensure_ascii=False, sort_keys=True, default=str)
        if len(text) <= MAX_MODEL_TOOL_RESULT_CHARS:
            return text
        return text[: MAX_MODEL_TOOL_RESULT_CHARS - 24] + "...[truncated for model]"

    def _sanitize_tool_content(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return self._truncate_text(value, MAX_MODEL_TEXT_PREVIEW)
        if isinstance(value, list):
            sanitized_items = [
                self._sanitize_tool_content(item)
                for item in value[:MAX_MODEL_TOOL_RESULT_ITEMS]
            ]
            if len(value) > MAX_MODEL_TOOL_RESULT_ITEMS:
                sanitized_items.append(
                    f"... ({len(value) - MAX_MODEL_TOOL_RESULT_ITEMS} more items omitted)"
                )
            return sanitized_items
        if isinstance(value, dict):
            preferred_keys = [
                "title",
                "text",
                "content",
                "snapshot",
                "format",
                "summary",
                "answer",
                "url",
                "results",
                "status",
                "message",
                "stdout",
                "stderr",
                "exit_code",
            ]
            sanitized: Dict[str, Any] = {}
            for key in preferred_keys:
                if key in value:
                    if key == "snapshot" and isinstance(value[key], str):
                        # Keep more browser snapshot text because it often contains critical page state.
                        sanitized[key] = self._truncate_text(
                            value[key],
                            MAX_MODEL_TOOL_RESULT_CHARS,
                        )
                    else:
                        sanitized[key] = self._sanitize_tool_content(value[key])

            if not sanitized:
                for index, (key, item) in enumerate(value.items()):
                    if index >= MAX_MODEL_TOOL_RESULT_ITEMS:
                        sanitized["omitted_keys"] = len(value) - MAX_MODEL_TOOL_RESULT_ITEMS
                        break
                    sanitized[key] = self._sanitize_tool_content(item)
            return sanitized
        return self._truncate_text(str(value), MAX_MODEL_TEXT_PREVIEW)

    def _truncate_text(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 16] + "...[truncated]"

    def _build_loop_guidance(self, message: str, should_block: bool) -> str:
        if should_block:
            return (
                f"{message}\n"
                "Do not repeat the same tool call again. Based on current evidence, provide an answer "
                "or explain what information is still missing."
            )
        return (
            f"{message}\n"
            "Avoid repeating the same action. The next step must use a different strategy."
        )

    def _build_fallback_answer(self, state: AgentRunState) -> str:
        if not state.tool_history:
            return "I do not have enough tool output to continue. Please try again."

        last_record = state.tool_history[-1]
        if last_record.error:
            return (
                "I hit a blocker during tool execution and stopped the loop to avoid blind retries. "
                f"Last failure: tool `{last_record.tool_name}` -> {last_record.error}"
            )
        return (
            "I stopped the current tool loop to avoid ineffective repetition. "
            "I can continue by summarizing the current findings and the next best step."
        )

    def _safe_parse_json(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return {"raw": value}
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except json.JSONDecodeError:
            return {"raw": value}

    def _maybe_compact_context(self, state: AgentRunState) -> None:
        total_chars = sum(len(str(message.get("content") or "")) for message in state.messages)
        if len(state.messages) <= MAX_CONTEXT_MESSAGES and total_chars <= MAX_CONTEXT_CHARS:
            return

        recent_messages = state.messages[-8:]
        summary_lines: List[str] = [
            "## Task Summary",
            f"- User goal: {self._truncate_text(state.user_message, 300)}",
        ]

        successful_tools = [record for record in state.tool_history if record.success]
        failed_tools = [record for record in state.tool_history if not record.success]

        for record in successful_tools[-4:]:
            summary_lines.append(
                f"- Successful tool: {record.tool_name} -> {self._truncate_text(record.sanitized_content, 240)}"
            )
        for record in failed_tools[-2:]:
            summary_lines.append(
                f"- Failed tool: {record.tool_name} -> {self._truncate_text(record.error or 'unknown error', 160)}"
            )
        if state.progress.stalled_iterations:
            summary_lines.append(
                f"- Current blocker: stalled for {state.progress.stalled_iterations} iteration(s)"
            )

        summary_lines = summary_lines[:MAX_SUMMARY_LINES]
        state.compacted_summary = "\n".join(summary_lines)

        compacted_messages: List[Dict[str, Any]] = []
        if state.messages and state.messages[0].get("role") == "system":
            compacted_messages.append(state.messages[0])
        if state.memory_context:
            compacted_messages.append(
                {
                    "role": "system",
                    "content": build_memory_message(state.memory_context),
                }
            )
        compacted_messages.append({"role": "system", "content": state.compacted_summary})
        compacted_messages.extend(recent_messages)
        state.messages = compacted_messages

    async def _emit_event(
        self,
        db: AsyncSession,
        state: AgentRunState,
        event: Dict[str, Any],
        *,
        persist: bool,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if persist:
            await self._persist_trace_event(db, state, event_type or event["type"], event)
        return event

    async def _persist_trace_event(
        self,
        db: AsyncSession,
        state: AgentRunState,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        state.event_sequence += 1
        await AgentEventDAO.create(
            db=db,
            session_id=state.session_id,
            conversation_id=state.conversation_id,
            run_id=state.run_id,
            event_type=event_type,
            payload=json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
            sequence=state.event_sequence,
            message_id=None,
        )

    async def _generate_post_tool_reasoning(
        self,
        llm: Any,
        state: AgentRunState,
        model: Optional[str],
    ) -> str:
        if not state.tool_history:
            return ""

        latest = state.tool_history[-1]
        tool_result_preview = self._truncate_text(latest.sanitized_content, 420)
        prompt = (
            f"User goal: {self._truncate_text(state.user_message, 180)}\\n"
            f"Latest tool: {latest.tool_name}\\n"
            f"Success: {'yes' if latest.success else 'no'}\\n"
            f"Tool output: {tool_result_preview}\\n"
            "Write a short internal reflection with: "
            "1) the key signal learned from this tool call, and "
            "2) the next best step. "
            "Do not give the final answer. Do not use markdown. Keep it under 120 words."
        )
        messages = [
            {
                "role": "system",
                "content": "You are an internal reasoning assistant for a multi-step agent. Output brief plain text only.",
            },
            {"role": "user", "content": prompt},
        ]

        chunks: List[str] = []
        try:
            async for content in llm.chat_stream(
                messages=messages,
                model=model,
                thinking=False,
            ):
                if content:
                    chunks.append(content)
            return self._truncate_text("".join(chunks).strip(), 300)
        except Exception:
            logger.exception("[agent_loop] failed to generate post-tool reasoning")
            return ""
