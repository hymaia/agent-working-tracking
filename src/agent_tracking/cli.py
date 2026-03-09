"""
Command-line interface for Agent-Tracking & Draw.io Toolset.
Contains both code analysis tools and agent task logging.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
import argparse

# Imports locaux
from .visualization import analyze_local_codebase, generate_hotspot_scatter
from .network import GlobalProjectAnalyzer
from .chat_interceptor import ChatStore, get_current_session_id


DEFAULT_SOURCE = Path("/Users/houee/Desktop/papaga-ia/papaga-ia/papaga_ia")


def ensure_dir(path: Path) -> Path:
    """Crée un dossier si nécessaire."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_visualize(source: Path, output_dir: Path, show: bool):
    """Génère les graphiques de santé du code."""
    ensure_dir(output_dir)

    print(f"Extraction des métriques de {source.resolve()}")

    df_real = analyze_local_codebase(source)
    print("extraction terminée. Aperçu :")
    if df_real.empty:
        print("Aucun fichier Python trouvé.")
        return 1

    # sauver dataset
    json_file = output_dir / "metrics.json"
    df_real.to_json(json_file, orient="records")

    generate_hotspot_scatter(
        df_real, save_path=output_dir / "hotspots.png", show=show)

    print(f"Graphiques sauvegardés dans {output_dir}")
    return 0


def run_map(source: Path, output_dir: Path):
    """Génère la carte d'interaction du projet."""
    ensure_dir(output_dir)

    print(f"Génération de la carte d'interaction pour {source}")

    analyzer = GlobalProjectAnalyzer(root_dir=source, output_dir=output_dir)

    analyzer.scan_project()
    analyzer.analyze_interactions()
    analyzer.generate_graph()

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
    map_cmd.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    map_cmd.add_argument("--output-dir", type=Path,
                         default=Path("visualizations"))

    # --- track (Agent Tracking) ---
    track = sub.add_parser("track", help="Sync agent task progress")
    track.add_argument("--conv-id", default=None)

    args = parser.parse_args()

    try:
        
        if args.command == "visualize":
            return run_visualize(args.source, args.output_dir, show=not args.no_show)

        elif args.command == "map":
            return run_map(args.source, args.output_dir)

        elif args.command == "track":
            return run_track(args.conv_id)

        return 0

    except Exception as e:
        print(f"Erreur fatale : {e}", file=sys.stderr)
        return 1



if __name__ == "__main__":
    sys.exit(main())
