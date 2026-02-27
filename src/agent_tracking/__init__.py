"""Agent Tracking - A software project for agent tracking."""

from .analysis import analyze_path, analyze_file, ClassInfo
from .uml import generate_drawio_xml
from .analysis import AnalysisHook
from .cli import analyze_codebase

__version__ = "0.1.0"
__all__ = [
    "analyze_path",
    "analyze_file",
    "ClassInfo",
    "generate_drawio_xml",
    "AnalysisHook",
    "analyze_codebase",
]
