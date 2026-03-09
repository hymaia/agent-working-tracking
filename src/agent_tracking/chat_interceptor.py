from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone
from pathlib import Path
import json
import re


BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

def get_current_session_id() -> str | None:
    """Heuristic to find the current conversation ID."""
    if not BRAIN_DIR.exists():
        return None
    dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir()]
    if not dirs:
        return None
    dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return dirs[0].name

@dataclass
class AgentTask:
    id: int | None
    conversation_id: str
    asked: str
    effectuated: str
    files_modified: list[str]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "asked": self.asked,
            "effectuated": self.effectuated,
            "files_modified": self.files_modified,
            "created_at": self.created_at,
        }

class ChatStore:
    """Simplified store for Agent Tasks using JSON."""
    def __init__(self, brain_dir: Path | None = None) -> None:
        self._brain_dir = Path(brain_dir) if brain_dir else BRAIN_DIR

    def _tasks_file(self) -> Path:
        BASE_DIR = Path(__file__).resolve().parent
        ROOT_DIR = BASE_DIR.parent.parent
        DATA_DIR = ROOT_DIR / "visualizations"
        return DATA_DIR / "tasks-agent.json"

    def _read_tasks(self, conversation_id: str) -> list[dict[str, Any]]:
        file = self._tasks_file()
        if not file.exists():
            return []
        try:
            return json.loads(file.read_text())
        except Exception:
            return []

    def _write_tasks(self,tasks: list[dict[str, Any]]):
        file = self._tasks_file()
        file.write_text(json.dumps(tasks, indent=2))

    def log_task(self, conversation_id: str, asked: str, effectuated: str, files_modified: list[str], task_id: int | None = None) -> AgentTask:
        now = datetime.now(timezone.utc).isoformat()
        tasks = self._read_tasks(conversation_id)
        
        final_id = task_id if task_id is not None else (len(tasks) + 1)
        task = AgentTask(final_id, conversation_id, asked, effectuated, files_modified, now)
        
        tasks.append(task.to_dict())
        self._write_tasks(tasks)
        
        return task

    def get_last_task(self, conversation_id: str) -> AgentTask | None:
        tasks = self._read_tasks(conversation_id)
        if not tasks:
            return None
        t = tasks[-1]
        return AgentTask(**t)

    def list_tasks(self, conversation_id: str) -> list[AgentTask]:
        tasks = self._read_tasks(conversation_id)
        return [AgentTask(**t) for t in reversed(tasks)]

    def sync_last_task(self, conversation_id: str) -> list[AgentTask]:
        """Extracts each completed 'big block' from task.md as a separate entry."""
        task_file = self._brain_dir / conversation_id / "task.md"

        if not task_file.exists():
            print(f"No task.md found for {conversation_id}")
            return []

        lines = task_file.read_text().splitlines()
        if not lines:
            return []

        # First line is conversation name
        conv_name = lines[0].replace("# Task:", "").strip()
        
        blocks = []
        current_block = None
        
        for line in lines[1:]:
            # Match top-level completed bullet point: "- [x] Description <!-- id: 123 -->"
            # No leading whitespace allowed for top-level
            top_match = re.match(r"^- \[([xX])\] (.*?)(?:\s*<!--\s*id:\s*(\d+)\s*-->|$)", line)
            
            if top_match:
                # If we were building a block, save it if it was completed
                if current_block:
                    blocks.append(current_block)
                
                is_done = top_match.group(1).lower() == 'x'
                text = top_match.group(2).strip()
                t_id = int(top_match.group(3)) if top_match.group(3) else None
                
                if is_done:
                    current_block = {
                        "id": t_id,
                        "title": text,
                        "lines": [line.strip()]
                    }
                else:
                    current_block = None
            elif current_block and line.startswith("    "):
                # Indented line - add to current block
                current_block["lines"].append(line.strip())
            elif line.strip() == "":
                # Empty line - just ignore or keep if in block?
                if current_block:
                    current_block["lines"].append("")
            else:
                # Non-indented line that isn't a new top-level task
                if current_block:
                    blocks.append(current_block)
                    current_block = None
        
        if current_block:
            blocks.append(current_block)

        existing_tasks = self._read_tasks(conversation_id)
        existing_ids = {t["id"] for t in existing_tasks}
        
        synced_tasks = []
        for b in blocks:
            if b["id"] is None or b["id"] in existing_ids:
                continue

            # Log this individual block
            asked_field = f"{conv_name} | {b['title']}"
            effectuated = "\n".join(b["lines"]).strip()
            new_task = self.log_task(conversation_id, asked_field, effectuated, [], task_id=b["id"])
            synced_tasks.append(new_task)

        return synced_tasks
