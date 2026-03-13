"""
Command-line interface for Agent-Tracking & Draw.io Toolset.
Contains both code analysis tools and agent task logging.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
import argparse

# Imports locaux
from .visualization import analyze_local_codebase, generate_hotspot_scatter
from .network import GlobalProjectAnalyzer
from .quality_metrics import get_py_files, get_ruff_ratio, get_avg_function_length
from .antigravity_interceptor import ChatStore, get_current_session_id
from .claude_interceptor import ClaudeStore, get_current_session_id as get_claude_session_id
from .utils import get_last_task


DEFAULT_SOURCE = Path(os.getenv("ANALYZED_REPO_PATH", "."))
DEFAULT_SOURCE_SRC = Path(
    os.getenv("ANALYZED_REPO_PATH", ".")) / os.getenv("ANALYZED_REPO_SRC", "")


def ensure_dir(path: Path) -> Path:
    """Crée un dossier si nécessaire."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_latest_task_id(conv_id: str | None = None, output_dir: Path = Path("visualizations")) -> int:
    """Gets the latest task ID.

    When ENV_IDE=claude-code, reads the last id from conversation-history.json.
    Otherwise uses the appropriate store (auto-detected via ENV_IDE).
    """
    if os.getenv("ENV_IDE", "").lower() == "claudecode":
        # Try session-specific file first, then generic fallback
        candidates = sorted(
            output_dir.glob("conversation-history-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        history_file = candidates[0] if candidates else output_dir / \
            "conversation-history.json"
        if history_file.exists():
            try:
                tasks = json.loads(history_file.read_text())
                if tasks:
                    return tasks[-1]["id"]
            except Exception:
                pass
        return 0

    last_task = get_last_task(conv_id)
    return last_task.id if last_task and last_task.id is not None else 0


def run_visualize(source: Path, output_dir: Path, show: bool):
    """Génère les graphiques de santé du code."""
    ensure_dir(output_dir)

    print(f"Extraction des métriques de {source.resolve()}")

    df_real = analyze_local_codebase(source)
    print("extraction terminée. Aperçu :")
    if df_real.empty:
        print("Aucun fichier Python trouvé.")
        return 1

    # Task ID for versioning
    tid = get_latest_task_id(output_dir=output_dir)

    # Versioned filenames
    json_versioned = output_dir / f"metrics-id-{tid}.json"
    png_versioned = output_dir / f"hotspots-id-{tid}.png"

    # Save versioned
    df_real.to_json(json_versioned, orient="records")
    # generate_hotspot_scatter(df_real, save_path=png_versioned, show=show)

    print(f"Graphiques sauvegardés avec ID {tid} dans {output_dir}")
    return 0


def run_map(source: Path, output_dir: Path):
    """Génère la carte d'interaction du projet."""
    ensure_dir(output_dir)

    print(f"Génération de la carte d'interaction pour {source}")

    tid = get_latest_task_id(output_dir=output_dir)
    analyzer = GlobalProjectAnalyzer(root_dir=source, output_dir=output_dir)

    analyzer.scan_project()
    analyzer.analyze_interactions()

    # Versioned and main
    analyzer.generate_graph(filename=f"project_interaction_map-id-{tid}.html")

    return 0


def run_quality(source: Path, output_dir: Path) -> int:
    """Génère les métriques de qualité du code (ruff + longueur fonctions)."""
    ensure_dir(output_dir)

    code_dir = str(source.resolve())
    py_files = get_py_files(code_dir)
    if not py_files:
        print("Aucun fichier Python trouvé.")
        return 1

    tid = get_latest_task_id(output_dir=output_dir)

    quality = get_ruff_ratio(code_dir, py_files)
    avg_len = get_avg_function_length(py_files)

    result = {
        "task_id": tid,
        "files_analyzed": len(py_files),
        "clean_ratio": round(quality["clean_ratio"], 1),
        "total_violations": quality["total_violations"],
        "avg_function_length": round(avg_len, 1),
    }

    out_file = output_dir / f"quality-id-{tid}.json"
    out_file.write_text(json.dumps(result, indent=2))

    print(f"Fichiers analysés          : {len(py_files)}")
    print(f"Fichiers clean (ruff)      : {quality['clean_ratio']:.1f}%")
    print(f"Violations totales         : {quality['total_violations']}")
    print(f"Longueur moyenne fonctions : {avg_len:.1f} lignes")
    print(f"Résultats sauvegardés avec ID {tid} dans {out_file}")
    return 0


# ---------------------------------------------------------------------------
# Agent Tracking Sync
# ---------------------------------------------------------------------------

def run_track(conv_id: str | None) -> int:
    """Sync the latest task from task.md to the JSON record."""
    cid = conv_id or get_current_session_id()
    if not cid:
        print("Error: Could not determine conversation ID. Provide --conv-id.")
        return 1

    store = ChatStore()
    synced = store.sync_last_task(cid)
    if synced:
        print(f"✅ Synced {len(synced)} new task(s).")
        for t in synced:
            print(f"  - {t.asked}")
    else:
        print("Nothing new to sync.")
    return 0


def run_history(output_dir: Path) -> int:
    """Export Claude Code conversation history for the current session."""
    store = ClaudeStore()

    session_id = None
    current = get_claude_session_id()
    if current:
        _, session_id = current
    else:
        print("Could not detect current session, exporting all.")

    messages = store.get_messages(session_id=session_id)
    if not messages:
        print("No messages found.")
        return 0

    store.export(output_dir, session_id=session_id)
    print(f"{len(messages)} message(s) exported.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Outil d'analyse Agent-Tracking & Draw.io Toolset"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- visualize ---
    viz = sub.add_parser("visualize", help="Graphiques santé code")
    viz.add_argument("--source", type=Path, default=Path("."))
    viz.add_argument("--output-dir", type=Path, default=Path("visualizations"))
    viz.add_argument("--no-show", action="store_true")

    # --- map ---
    map_cmd = sub.add_parser("map", help="Carte interactions projet")
    map_cmd.add_argument("--source", type=Path, default=DEFAULT_SOURCE_SRC)
    map_cmd.add_argument("--output-dir", type=Path,
                         default=Path("visualizations"))

    # --- quality ---
    quality_cmd = sub.add_parser("quality", help="Métriques qualité code (ruff + longueur fonctions)")
    quality_cmd.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    quality_cmd.add_argument("--output-dir", type=Path, default=Path("visualizations"))

    # --- history (unified: antigravity=track, claudecode=history) ---
    history = sub.add_parser(
        "history", help="Sync agent tasks (antigravity) or export conversation history (claudecode)")
    history.add_argument("--conv-id", default=None,
                         help="Conversation ID (antigravity only, auto-detected if omitted)")
    history.add_argument("--output-dir", type=Path,
                         default=Path("visualizations"))

    args = parser.parse_args()

    try:

        if args.command == "quality":
            return run_quality(args.source, args.output_dir)

        elif args.command == "visualize":
            return run_visualize(args.source, args.output_dir, show=not args.no_show)

        elif args.command == "map":
            return run_map(args.source, args.output_dir)

        elif args.command == "history":
            env_ide = os.getenv("ENV_IDE", "").lower()
            if env_ide == "antigravity":
                return run_track(args.conv_id)
            else:
                return run_history(args.output_dir)

        return 0

    except Exception as e:
        print(f"Erreur fatale : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
