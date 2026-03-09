from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import logging
import re
import sys

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
GRAPH_FILE = ROOT_DIR / "visualizations" / "project_interaction_map.html"
TEMPLATE_DIR = BASE_DIR
logger.info(f"Server starting")
logger.info(f"Base directory : {BASE_DIR}")
logger.info(f"Metrics folder : {DATA_DIR.resolve()}")

def read_env_repo_name():
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANALYZED_REPO_NAME="):
                return line.split("=", 1)[1].strip()
    return "Unknown Project"

REPO_NAME = read_env_repo_name()


# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="Agent Dashboard Tracking")

templates = Jinja2Templates(directory=BASE_DIR)


# -----------------------------
# LOAD METRICS AND GRAPH
# -----------------------------


def get_latest_task_id_from_json() -> int | None:
    file = DATA_DIR / "tasks-agent.json"
    if not file.exists():
        return None
    try:
        tasks = json.loads(file.read_text())
        valid_ids = [t.get("id") for t in tasks if t.get("id") is not None]
        return max(valid_ids) if valid_ids else None
    except Exception as e:
        logger.error(f"Error reading agent tasks for latest ID: {e}")
        return None


def load_graph_data(task_id: int | None = None):
    if task_id is None:
        task_id = get_latest_task_id_from_json()

    filename = f"project_interaction_map-id-{task_id}.html" if task_id is not None else "project_interaction_map.html"
    
    target_file = DATA_DIR / filename
    logger.info(f"Loading graph data (task_id={task_id}) from {target_file}...")

    if target_file.exists():
        logger.info(f"Graph file found: {target_file}")
        content = target_file.read_text()
        
        nodes_match = re.search(r'nodes\s*=\s*new\s*vis\.DataSet\((.*?)\);', content, re.DOTALL)
        edges_match = re.search(r'edges\s*=\s*new\s*vis\.DataSet\((.*?)\);', content, re.DOTALL)
        
        nodes = json.loads(nodes_match.group(1)) if nodes_match else []
        edges = json.loads(edges_match.group(1)) if edges_match else []

        logger.info(f"Graph data loaded successfully: {len(nodes)} nodes, {len(edges)} edges")
        return {"nodes": nodes, "edges": edges}

    logger.warning(f"Graph file not found: {target_file}")
    return {"nodes": [], "edges": []}


def load_metrics(task_id: int | None = None):
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


@app.get("/api/metrics/{task_id}")
def get_metrics_version(task_id: int):
    return load_metrics(task_id)


@app.get("/api/graph/{task_id}")
def get_graph_version(task_id: int):
    return load_graph_data(task_id)

def load_agent_tasks():
    file = DATA_DIR / "tasks-agent.json"
    logger.info(f"Loading agent tasks from {file}")
    if not file.exists():
        return []
    try:
        data = json.loads(file.read_text())
        return data
    except Exception as e:
        logger.error(f"Error reading agent tasks: {e}")
        return []

# -----------------------------
# HOME PAGE
# -----------------------------


@app.get("/")
def home(request: Request):

    metrics = load_metrics()
    graph_data = load_graph_data()
    agent_tasks = load_agent_tasks()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "metrics": metrics,
            "graph_data": graph_data,
            "agent_tasks": agent_tasks,
            "repo_name": REPO_NAME
        }
    )


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR),
    name="static"
)
