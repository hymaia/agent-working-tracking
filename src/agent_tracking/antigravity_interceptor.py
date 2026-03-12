from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()  

ENV_IDE = os.getenv("ENV_IDE", "").lower() 


if ENV_IDE == "antigravity":
    BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"
elif ENV_IDE == "vscode":
    BRAIN_DIR = Path.home() / "Library" / "Application" / "Support" / "Code" / "User" / "workspaceStorage"
else:
    BRAIN_DIR = None

print(f"Using brain directory: {BRAIN_DIR}")

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

    def _tasks_file(self, conversation_id: str) -> Path:
        BASE_DIR = Path(__file__).resolve().parent
        ROOT_DIR = BASE_DIR.parent.parent
        DATA_DIR = ROOT_DIR / "visualizations"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return DATA_DIR / f"tasks-agent-{conversation_id}.json"

    def _read_tasks(self, conversation_id: str) -> list[dict[str, Any]]:
        file = self._tasks_file(conversation_id)
        if not file.exists():
            return []
        try:
            return json.loads(file.read_text())
        except Exception:
            return []

    def _write_tasks(self, tasks: list[dict[str, Any]], conversation_id: str):
        file = self._tasks_file(conversation_id)
        file.write_text(json.dumps(tasks, indent=2))
        print(f"💾 JSON saved → {file.resolve()}")

    def log_task(self, conversation_id: str, asked: str, effectuated: str, files_modified: list[str], task_id: int | None = None) -> AgentTask:
        now = datetime.now(timezone.utc).isoformat()
        tasks = self._read_tasks(conversation_id)
        
        final_id = task_id if task_id is not None else (len(tasks) + 1)
        task = AgentTask(final_id, conversation_id, asked, effectuated, files_modified, now)
        
        tasks.append(task.to_dict())
        self._write_tasks(tasks, conversation_id)

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
        """Extracts each completed 'big block' from task.md as a separate entry,
        avoids duplicates based on ID and hash of the text."""
        task_file = self._brain_dir / conversation_id / "task.md"

        if not task_file.exists():
            print(f"No task.md found for {conversation_id}")
            return []

        lines = task_file.read_text().splitlines()
        if not lines:
            return []

        conv_name = lines[0].replace("# Task:", "").strip()
        
        blocks = []
        current_block = None
        
        # Parse markdown into blocks
        for line in lines[1:]:
            top_match = re.match(
                r"^- \[([xX])\] (.*?)(?:\s*<!--\s*id:\s*(\d+)\s*-->|$)", line
            )
            if top_match:
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
                current_block["lines"].append(line.strip())
            elif line.strip() == "":
                if current_block:
                    current_block["lines"].append("")
            else:
                if current_block:
                    blocks.append(current_block)
                    current_block = None
        
        if current_block:
            blocks.append(current_block)

        # Lecture des tâches existantes
        existing_tasks = self._read_tasks(conversation_id)
        existing_ids = {t["id"] for t in existing_tasks if t["id"] is not None}
        # On calcule aussi un set des hash des contenus déjà présents
        existing_hashes = {hashlib.sha256(t["effectuated"].encode()).hexdigest() for t in existing_tasks}

        def get_next_id(existing_ids):
            return max(existing_ids) + 1 if existing_ids else 1

        synced_tasks = []

        for b in blocks:
            # Contenu complet du bloc
            text_block = "\n".join(b["lines"]).strip()
            text_hash = hashlib.sha256(text_block.encode()).hexdigest()

            # Si déjà présent par hash ou par ID, on ignore
            if (b.get("id") in existing_ids) or (text_hash in existing_hashes):
                continue

            # Si l'ID est None, on attribue un nouvel ID unique
            if b.get("id") is None:
                b["id"] = get_next_id(existing_ids)

            asked_field = f"{conv_name} | {b['title']}"
            effectuated = text_block
            new_task = self.log_task(conversation_id, asked_field, effectuated, [], task_id=b["id"])

            # Ajoute ID et hash pour éviter doublons suivants
            existing_ids.add(b["id"])
            existing_hashes.add(text_hash)
            synced_tasks.append(new_task)

        return synced_tasks