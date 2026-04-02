from __future__ import annotations

import os
from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.session_skill_dao import SessionSkillDAO


class SkillService:
    def __init__(self) -> None:
        self.skill_roots = self._build_skill_roots()

    def _build_skill_roots(self) -> List[Path]:
        configured = os.getenv("MYCLAW_SKILLS_DIR")
        roots: List[Path] = []
        if configured:
            for item in configured.split(os.pathsep):
                if item.strip():
                    roots.append(Path(item.strip()))
        roots.append(Path.cwd() / "skills")
        return roots

    def discover_skills(self) -> list[dict]:
        discovered: list[dict] = []
        seen: set[str] = set()
        for root in self.skill_roots:
            if not root.exists():
                continue
            for skill_file in root.glob("**/SKILL.md"):
                name = skill_file.parent.name
                if name in seen:
                    continue
                seen.add(name)
                discovered.append(
                    {
                        "name": name,
                        "path": str(skill_file),
                        "description": self._read_description(skill_file),
                    }
                )
        discovered.sort(key=lambda item: item["name"].lower())
        return discovered

    async def list_session_skills(self, db: AsyncSession, session_id: int) -> list[dict]:
        records = await SessionSkillDAO.list_by_session(db, session_id)
        return [
            {
                "skill_name": record.skill_name,
                "skill_path": record.skill_path,
                "enabled": record.enabled,
            }
            for record in records
        ]

    async def update_session_skills(self, db: AsyncSession, session_id: int, skills: list[dict]) -> list[dict]:
        records = await SessionSkillDAO.replace_for_session(db, session_id, skills)
        return [
            {
                "skill_name": record.skill_name,
                "skill_path": record.skill_path,
                "enabled": record.enabled,
            }
            for record in records
        ]

    async def build_session_skill_context(self, db: AsyncSession, session_id: int) -> str:
        records = await SessionSkillDAO.list_by_session(db, session_id)
        enabled_records = [record for record in records if record.enabled]
        if not enabled_records:
            return ""
        snippets: list[str] = ["## Enabled Skills"]
        for record in enabled_records[:8]:
            snippets.append(f"- {record.skill_name}: {self._read_description(Path(record.skill_path))}")
        return "\n".join(snippets)

    def build_workspace_prompt_context(self, workspace_path: str | None) -> str:
        if not workspace_path:
            return ""
        workspace = Path(workspace_path)
        snippets = [f"## Workspace\n- Root: {workspace}"]
        for candidate in ("AGENTS.md", "TOOLS.md"):
            file_path = workspace / candidate
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if content:
                    snippets.append(f"### {candidate}\n{content[:1800]}")
        return "\n".join(snippets)

    def _read_description(self, skill_file: Path) -> str:
        try:
            text = skill_file.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            return ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped[:200]
        return ""
