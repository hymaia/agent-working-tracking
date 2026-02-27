"""Code analysis utilities for agent_tracking library.

Includes analysis functionality and hook management for automatic analysis
on file changes with git hooks for version control integration.
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional


class ClassInfo:
    """Simple representation of a Python class."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.bases: List[str] = []
        self.methods: List[str] = []

    def to_dict(self) -> Dict[str, List[str]]:
        return {"bases": self.bases, "methods": self.methods}


def analyze_file(path: Path) -> Dict[str, ClassInfo]:
    """Analyze a single Python file and return information about classes.

    Args:
        path: Path to Python source file.

    Returns:
        Mapping from class name to :class:`ClassInfo`.
    """
    with open(path, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=str(path))

    classes: Dict[str, ClassInfo] = {}
    for item in node.body:
        if isinstance(item, ast.ClassDef):
            info = ClassInfo(item.name)
            for base in item.bases:
                if isinstance(base, ast.Name):
                    info.bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    info.bases.append(base.attr)
            # methods
            for stmt in item.body:
                if isinstance(stmt, ast.FunctionDef):
                    info.methods.append(stmt.name)
            classes[item.name] = info
    return classes


def analyze_path(path: Path) -> Dict[str, ClassInfo]:
    """Recursively analyze all .py files under a directory."""
    result: Dict[str, ClassInfo] = {}
    for p in path.rglob("*.py"):
        result.update(analyze_file(p))
    return result


class AnalysisHook:
    """Manages automatic analysis triggers on code changes.

    Monitors Python files and runs analysis callbacks when changes are detected.
    """

    def __init__(self, root_path: Path, output_dir: Path):
        """Initialize the hook configuration.

        Args:
            root_path: Root directory to analyze.
            output_dir: Directory where to store generated diagrams.
        """
        self.root_path = root_path
        self.output_dir = output_dir
        self.callbacks: list[Callable[[dict], None]] = []
        self._last_analysis_time: Optional[datetime] = None

    def register_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a callback to be called on code changes.

        Args:
            callback: Function to call with analysis results dict.
        """
        self.callbacks.append(callback)

    def should_analyze(self) -> bool:
        """Check if analysis should run (simple time-based throttle)."""
        now = datetime.now()
        if self._last_analysis_time is None:
            self._last_analysis_time = now
            return True
        # Only run if at least 1 second has passed
        delta = (now - self._last_analysis_time).total_seconds()
        if delta >= 1.0:
            self._last_analysis_time = now
            return True
        return False

    def trigger_analysis(self, results: dict) -> None:
        """Trigger registered callbacks with analysis results.

        Args:
            results: Dictionary containing analysis data (classes, diagram XML, etc).
        """
        if not self.should_analyze():
            return
        for callback in self.callbacks:
            callback(results)

    def get_output_filename(self, prefix: str = "diagram") -> Path:
        """Generate an output filename with timestamp.

        Args:
            prefix: Filename prefix.

        Returns:
            Path object pointing to the output file in output_dir.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.drawio"
        return self.output_dir / filename
