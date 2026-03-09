"""Agent Tracking - A software project for agent tracking."""

from .analysis import analyze_path, analyze_file, ClassInfo
from .uml import generate_drawio_xml
from .cli import analyze_codebase
from .visualization import generate_hotspot_scatter
from .chat_interceptor import ChatStore

__version__ = "0.1.0"
__all__ = [
    "analyze_path",
    "analyze_file",
    "ClassInfo",
    "generate_drawio_xml",
    "analyze_codebase",
    "generate_hotspot_scatter",
    "ChatStore",
]
