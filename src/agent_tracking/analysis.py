"""Utilities to analyze Python code structure."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List


class ClassInfo:
    """Representation of a Python class."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.bases: List[str] = []
        self.methods: List[str] = []

    def to_dict(self) -> Dict[str, List[str]]:
        return {"bases": self.bases, "methods": self.methods}


def analyze_file(path: Path) -> Dict[str, ClassInfo]:
    """Analyze a Python file and extract classes."""
    with open(path, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=str(path))

    classes: Dict[str, ClassInfo] = {}

    for item in node.body:
        if isinstance(item, ast.ClassDef):
            info = ClassInfo(item.name)

            for base in item.bases:
                if isinstance(base, ast.Name):
                    info.bases.append(base.id)

            for stmt in item.body:
                if isinstance(stmt, ast.FunctionDef):
                    info.methods.append(stmt.name)

            classes[item.name] = info

    return classes


def analyze_path(path: Path) -> Dict[str, ClassInfo]:
    """Recursively analyze all Python files in a directory."""
    result: Dict[str, ClassInfo] = {}

    for p in path.rglob("*.py"):
        result.update(analyze_file(p))

    return result
