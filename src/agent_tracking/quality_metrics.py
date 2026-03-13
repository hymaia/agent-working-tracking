import os
import subprocess
import ast
import json

PY_EXT = ".py"


def get_py_files(code_dir: str) -> list[str]:
    return [
        os.path.join(dp, f)
        for dp, _, filenames in os.walk(code_dir)
        for f in filenames
        if f.endswith(PY_EXT)
    ]


def get_ruff_ratio(code_dir: str, py_files: list[str]) -> dict:
    """Pourcentage de fichiers sans violation ruff (E, F, B)."""
    result = subprocess.run(
        ["ruff", "check", "--output-format=json", "--select=E,F,B", code_dir],
        capture_output=True, text=True,
    )
    try:
        violations = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        violations = []

    files_with_violations = {os.path.normpath(
        v["filename"]) for v in violations}
    clean = sum(1 for f in py_files if os.path.normpath(f)
                not in files_with_violations)

    return {
        "clean_ratio": clean / len(py_files) * 100,
        "total_violations": len(violations),
    }


def get_avg_function_length(py_files: list[str]) -> float:
    """Longueur moyenne des fonctions/méthodes via end_lineno (Python 3.8+)."""
    lengths = []

    def visit(node, parent=None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, "end_lineno"):
                lengths.append(node.end_lineno - node.lineno + 1)
        for child in ast.iter_child_nodes(node):
            visit(child, parent=node)

    for file in py_files:
        try:
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read(), filename=file)
            visit(tree)
        except SyntaxError:
            continue

    return sum(lengths) / len(lengths) if lengths else 0.0
