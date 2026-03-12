"""Claude Code conversation storage reader."""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

CLAUDE_DIR = Path.home() / ".claude" / "projects"


def get_current_session_id(cwd: Path | None = None) -> tuple[str, str] | None:
    """Return (project_folder_name, session_id) for the most recent session in cwd."""
    cwd = cwd or Path.cwd()
    # Claude stores projects as the cwd path with '/' replaced by '-'
    project_name = str(cwd).replace("/", "-")
    project_dir = CLAUDE_DIR / project_name
    if not project_dir.exists():
        return None
    sessions = list(project_dir.glob("*.jsonl"))
    if not sessions:
        return None
    latest = max(sessions, key=lambda f: f.stat().st_mtime)
    return project_name, latest.stem


def _load_session(path: Path) -> list[dict]:
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _extract_text(content) -> str:
    if isinstance(content, list):
        return " ".join(
            c.get("text", "") for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        ).strip()
    return str(content).strip()


def _extract_paired_messages(entries: list[dict]) -> list[dict]:
    """Extract user messages paired with the first assistant text response."""
    children: dict[str, list[dict]] = {}
    for e in entries:
        parent = e.get("parentUuid")
        if parent:
            children.setdefault(parent, []).append(e)

    def first_assistant_text(uuid: str) -> str:
        for child in children.get(uuid, []):
            if child.get("type") == "assistant":
                text = _extract_text(child.get("message", {}).get("content", ""))
                if text:
                    return text
                deeper = first_assistant_text(child.get("uuid", ""))
                if deeper:
                    return deeper
        return ""

    messages = []
    for e in entries:
        if e.get("type") != "user":
            continue
        msg = e.get("message", {})
        if msg.get("role") != "user":
            continue
        text = _extract_text(msg.get("content", ""))
        if not text or text.startswith("/"):
            continue
        messages.append({
            "session_id": e.get("sessionId", ""),
            "timestamp": e.get("timestamp", ""),
            "project": "",
            "text": text,
            "effectuated": first_assistant_text(e.get("uuid", "")),
        })
    return messages


class ClaudeStore:
    """Read conversation history from Claude Code local storage."""

    def __init__(self, claude_dir: Path | None = None) -> None:
        self._dir = Path(claude_dir) if claude_dir else CLAUDE_DIR

    def list_projects(self) -> list[str]:
        if not self._dir.exists():
            return []
        return sorted(p.name for p in self._dir.iterdir() if p.is_dir())

    def get_messages(
        self,
        project: str | None = None,
        session_id: str | None = None,
        search: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        if not self._dir.exists():
            return []

        projects = sorted(self._dir.iterdir())
        if project:
            projects = [p for p in projects if project.lower() in p.name.lower()]

        all_messages = []
        for proj in projects:
            for session_file in sorted(proj.glob("*.jsonl")):
                if session_id and session_file.stem != session_id:
                    continue
                msgs = _extract_paired_messages(_load_session(session_file))
                for m in msgs:
                    m["project"] = proj.name
                all_messages.extend(msgs)

        all_messages.sort(key=lambda m: m["timestamp"])

        if search:
            kw = search.lower()
            all_messages = [m for m in all_messages if kw in m["text"].lower()]

        if limit:
            all_messages = all_messages[-limit:]

        return all_messages

    def export(self, output_dir: Path, **kwargs) -> Path:
        """Export messages as tasks-agent.json schema to output_dir."""
        session_id = kwargs.get("session_id")
        messages = self.get_messages(**kwargs)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"conversation-history-{session_id}.json" if session_id else "conversation-history.json"
        out = output_dir / filename
        formatted = [
            {
                "id": i,
                "conversation_id": m["session_id"],
                "asked": m["text"],
                "effectuated": m["effectuated"],
                "files_modified": [],
                "created_at": m["timestamp"],
            }
            for i, m in enumerate(messages)
        ]
        out.write_text(json.dumps(formatted, indent=2, ensure_ascii=False))
        print(f"💾 JSON saved → {out.resolve()}")
        return out
