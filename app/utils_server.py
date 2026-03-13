import json
import logging
import os
import re
import sys
from pathlib import Path

# Make src/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# -----------------------------
# LOG CONFIG
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------
# PATH CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "visualizations"

logger.info(f"Base directory : {BASE_DIR}")
logger.info(f"Metrics folder : {DATA_DIR.resolve()}")


# -----------------------------
# ENV HELPERS
# -----------------------------

def read_env_repo_name() -> str:
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANALYZED_REPO_NAME="):
                return line.split("=", 1)[1].strip()
    return "Unknown Project"


def _load_dotenv():
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

REPO_NAME = read_env_repo_name()
ENV_IDE = os.getenv("ENV_IDE", "").lower()


def _resolve_conv_id() -> str | None:
    """Auto-detect AGENT_CONV_ID from the right interceptor if not set in env."""
    conv_id = os.getenv("AGENT_CONV_ID")
    if conv_id:
        logger.info(f"AGENT_CONV_ID from env: {conv_id}")
        return conv_id

    if ENV_IDE == "antigravity":
        try:
            from agent_tracking.antigravity_interceptor import get_current_session_id
            conv_id = get_current_session_id()
            if conv_id:
                logger.info(f"Auto-detected AGENT_CONV_ID (antigravity): {conv_id}")
                return conv_id
        except Exception as e:
            logger.warning(f"Could not auto-detect antigravity session: {e}")

    elif ENV_IDE == "claudecode":
        try:
            from agent_tracking.claude_interceptor import get_current_session_id
            result = get_current_session_id()
            if result:
                _, session_id = result
                logger.info(f"Auto-detected AGENT_CONV_ID (claudecode): {session_id}")
                return session_id
        except Exception as e:
            logger.warning(f"Could not auto-detect claudecode session: {e}")

    logger.warning("AGENT_CONV_ID could not be resolved. Set it in .env or via env var.")
    return None


def _resolve_current_conv_id() -> str | None:
    """Resolve conversation ID dynamically on each call."""
    explicit = os.getenv("AGENT_CONV_ID")
    if explicit:
        return explicit

    if ENV_IDE == "antigravity":
        try:
            from agent_tracking.antigravity_interceptor import get_current_session_id
            return get_current_session_id()
        except Exception as e:
            logger.warning(f"Could not auto-detect antigravity session: {e}")

    elif ENV_IDE == "claudecode":
        try:
            from agent_tracking.claude_interceptor import get_current_session_id
            result = get_current_session_id()
            if result:
                _, session_id = result
                return session_id
        except Exception as e:
            logger.warning(f"Could not auto-detect claudecode session: {e}")

    return None


def _tasks_file() -> Path | None:
    """Return the correct tasks JSON file based on ENV_IDE + current session ID."""
    conv_id = _resolve_current_conv_id()

    if ENV_IDE == "antigravity":
        if conv_id:
            f = DATA_DIR / f"tasks-agent-{conv_id}.json"
        else:
            candidates = sorted(
                DATA_DIR.glob("tasks-agent-*.json"),
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            f = candidates[0] if candidates else DATA_DIR / "tasks-agent.json"
        logger.info(f"Tasks file (antigravity): {f}")
        return f

    elif ENV_IDE == "claudecode":
        if conv_id:
            f = DATA_DIR / f"conversation-history-{conv_id}.json"
        else:
            candidates = sorted(
                DATA_DIR.glob("conversation-history-*.json"),
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            f = candidates[0] if candidates else DATA_DIR / "conversation-history.json"
        logger.info(f"Tasks file (claudecode): {f}")
        return f

    # Unknown ENV_IDE — try both
    for pattern in ("tasks-agent-*.json", "conversation-history-*.json"):
        candidates = sorted(
            DATA_DIR.glob(pattern),
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        if candidates:
            logger.info(f"Tasks file (fallback): {candidates[0]}")
            return candidates[0]
    return None


# -----------------------------
# DATA LOADERS
# -----------------------------

def get_latest_task_id_from_json() -> int | None:
    f = _tasks_file()
    if not f or not f.exists():
        return None
    try:
        tasks = json.loads(f.read_text())
        valid_ids = [t.get("id") for t in tasks if t.get("id") is not None]
        return max(valid_ids) if valid_ids else None
    except Exception as e:
        logger.error(f"Error reading agent tasks for latest ID: {e}")
        return None


def load_graph_data(task_id: int | None = None) -> dict:
    if task_id is None:
        task_id = get_latest_task_id_from_json()

    filename = (
        f"project_interaction_map-id-{task_id}.html"
        if task_id is not None
        else "project_interaction_map.html"
    )
    target_file = DATA_DIR / filename
    logger.info(f"Loading graph data (task_id={task_id}) from {target_file}...")

    if target_file.exists():
        content = target_file.read_text()
        nodes_match = re.search(r'nodes\s*=\s*new\s*vis\.DataSet\((.*?)\);', content, re.DOTALL)
        edges_match = re.search(r'edges\s*=\s*new\s*vis\.DataSet\((.*?)\);', content, re.DOTALL)
        nodes = json.loads(nodes_match.group(1)) if nodes_match else []
        edges = json.loads(edges_match.group(1)) if edges_match else []
        logger.info(f"Graph loaded: {len(nodes)} nodes, {len(edges)} edges")
        return {"nodes": nodes, "edges": edges}

    logger.warning(f"Graph file not found: {target_file}")
    return {"nodes": [], "edges": []}


def load_metrics(task_id: int | None = None) -> list:
    if task_id is None:
        task_id = get_latest_task_id_from_json()

    filename = f"metrics-id-{task_id}.json" if task_id is not None else "metrics.json"
    file = DATA_DIR / filename
    logger.info(f"Loading metrics (task_id={task_id}) from {file}")

    if not file.exists():
        logger.warning(f"Metrics file not found: {file}")
        return []

    try:
        data = json.loads(file.read_text())
        logger.info(f"{len(data)} metrics loaded")
        return data
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
        return []


def load_quality(task_id: int | None = None) -> dict:
    if task_id is None:
        task_id = get_latest_task_id_from_json()

    filename = f"quality-id-{task_id}.json" if task_id is not None else "quality.json"
    file = DATA_DIR / filename
    logger.info(f"Loading quality metrics (task_id={task_id}) from {file}")

    if not file.exists():
        logger.warning(f"Quality file not found: {file}")
        return {}

    try:
        return json.loads(file.read_text())
    except Exception as e:
        logger.error(f"Error reading quality metrics: {e}")
        return {}


def load_agent_tasks() -> list:
    f = _tasks_file()
    if not f:
        logger.warning("No tasks file resolved.")
        return []
    logger.info(f"Loading agent tasks from {f}")
    if not f.exists():
        logger.warning(f"Tasks file not found: {f}")
        return []
    try:
        data = json.loads(f.read_text())
        logger.info(f"{len(data)} tasks loaded")
        return data
    except Exception as e:
        logger.error(f"Error reading agent tasks: {e}")
        return []
