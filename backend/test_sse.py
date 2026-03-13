"""
测试 SSE 流式输出
"""
import asyncio
import json
import time
import uuid

from app.agent import get_agent

async def test_sse_stream():
    """测试 SSE 格式的流式输出"""
    agent = get_agent()
    
    print("=== 开始测试 SSE 流式输出 ===")
    print()
    
    chunk_count = 0
    thoughts_chunks = 0
    content_chunks = 0
    
    async for chunk in agent.process_message_stream(
        session_id="test-sse",
        user_message="你好",
        enable_thinking=True,
        model="glm-4.1v-thinking-flash"
    ):
        chunk_count += 1
        
        if isinstance(chunk, dict):
            if "thoughts" in chunk:
                thoughts_chunks += 1
                data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "glm-4.1v-thinking-flash",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "thoughts": chunk["thoughts"]
                            },
                            "finish_reason": None,
                        }
                    ],
                }
                print(f"data: {json.dumps(data, ensure_ascii=False)}\n")
        else:
            content_chunks += 1
            data = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "glm-4.1v-thinking-flash",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None,
                    }
                ],
            }
            print(f"data: {json.dumps(data, ensure_ascii=False)}\n")
    
    print("data: [DONE]\n")
    print()
    print(f"=== 测试完成 ===")
    print(f"总 chunk 数: {chunk_count}")
    print(f"思考 chunk 数: {thoughts_chunks}")
    print(f"内容 chunk 数: {content_chunks}")

if __name__ == "__main__":
    asyncio.run(test_sse_stream())
