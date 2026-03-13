from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils_server import (
    BASE_DIR,
    ENV_IDE,
    REPO_NAME,
    _resolve_conv_id,
    _resolve_current_conv_id,
    _tasks_file,
    load_agent_tasks,
    load_graph_data,
    load_metrics,
    logger,
)

# Resolved once at startup for the template default
AGENT_CONV_ID = _resolve_conv_id()

logger.info(f"Server starting")
logger.info(f"ENV_IDE       : {ENV_IDE or '(not set)'}")
logger.info(f"AGENT_CONV_ID : {AGENT_CONV_ID or '(not set)'}")

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="Agent Dashboard Tracking")

templates = Jinja2Templates(directory=BASE_DIR)


# -----------------------------
# API ROUTES
# -----------------------------

@app.get("/api/metrics/{task_id}")
def get_metrics_version(task_id: int):
    return load_metrics(task_id)


@app.get("/api/graph/{task_id}")
def get_graph_version(task_id: int):
    return load_graph_data(task_id)


@app.get("/api/tasks")
def get_tasks():
    return load_agent_tasks()


@app.get("/api/config")
def get_config():
    f = _tasks_file()
    return {
        "env_ide": ENV_IDE or None,
        "conv_id": _resolve_current_conv_id(),
        "tasks_file": str(f) if f else None,
        "tasks_file_exists": f.exists() if f else False,
    }


# -----------------------------
# HOME PAGE
# -----------------------------

@app.get("/")
def home(request: Request):
    metrics = load_metrics()
    graph_data = load_graph_data()
    agent_tasks = load_agent_tasks()
    conv_id = _resolve_current_conv_id() or AGENT_CONV_ID or "—"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "metrics": metrics,
            "graph_data": graph_data,
            "agent_tasks": agent_tasks,
            "repo_name": REPO_NAME,
            "env_ide": ENV_IDE or "unknown",
            "conv_id": conv_id,
        }
    )


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR),
    name="static"
)