from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import logging

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

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI()

templates = Jinja2Templates(directory=BASE_DIR)


# -----------------------------
# LOAD METRICS AND GRAPH
# -----------------------------


def load_graph_html():
    logger.info("Loading graph HTML...")

    if GRAPH_FILE.exists():
        logger.info(f"Graph file found: {GRAPH_FILE}")

        content = GRAPH_FILE.read_text()

        logger.info("Graph HTML loaded successfully")
        return content

    logger.warning(f"Graph file not found: {GRAPH_FILE}")
    return "<p>No graph found</p>"


def load_metrics():

    file = DATA_DIR / "metrics.json"

    logger.info(f"Loading metrics from {file}")

    if not file.exists():
        logger.warning("metrics.json not found")
        return []

    try:
        data = json.loads(file.read_text())
        logger.info(f"{len(data)} metrics loaded")
        return data
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
        return []

# -----------------------------
# HOME PAGE
# -----------------------------


@app.get("/")
def home(request: Request):

    metrics = load_metrics()
    graph_html = load_graph_html()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "metrics": metrics,
            "graph_html": graph_html
        }
    )


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR),
    name="static"
)
