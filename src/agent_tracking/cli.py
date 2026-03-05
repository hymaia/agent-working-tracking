"""
Command-line interface for code analysis, UML generation and Draw.io manipulation.
"""

from __future__ import annotations
import sys
from pathlib import Path
import argparse

# Imports locaux
from .analysis import analyze_path
from .uml import generate_drawio_xml, convert_drawio_to_png
from .visualization import analyze_local_codebase, generate_hotspot_scatter
from .network import GlobalProjectAnalyzer


DEFAULT_SOURCE = Path("/Users/houee/Desktop/papaga-ia/papaga-ia/papaga_ia")


def ensure_dir(path: Path) -> Path:
    """Crée un dossier si nécessaire."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def analyze_codebase(source: Path, output: Path, verbose: bool = False):
    """Analyze codebase and generate a Draw.io UML diagram."""

    if verbose:
        print(f"Analyzing {source}")

    classes = analyze_path(source)
    xml = generate_drawio_xml(classes)

    output_file = output / "diagram.drawio"
    output_file.write_text(xml, encoding="utf-8")

    print(f"Diagram generated: {output_file}")


def run_visualize(source: Path, output_dir: Path, show: bool):
    """Génère les graphiques de santé du code."""
    ensure_dir(output_dir)

    print(f"Extraction des métriques de {source.resolve()}")

    df_real = analyze_local_codebase(source)
    print("extraction terminée. Aperçu :")
    if df_real.empty:
        print("Aucun fichier Python trouvé.")
        return 1

    generate_hotspot_scatter(df_real, save_path=output_dir / "hotspots.png", show=show)

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


def run_inspect(file: Path, outdir: Path, export_png: bool, export_xml: bool):
    """Inspecte un fichier Draw.io."""
    if not file.exists():
        print(f"Erreur : {file} n'existe pas.")
        return 1

    ensure_dir(outdir)

    if not export_png and not export_xml:
        export_png = True

    if export_png:
        output_png = outdir / file.with_suffix(".png").name
        print(f"Conversion {file.name} -> {output_png.name}")

        success = convert_drawio_to_png(file, output_png)

        if success:
            print(f"Export PNG réussi : {output_png}")
        else:
            print("Échec conversion (Draw.io desktop requis).")

    if export_xml:
        print("Extraction XML (non implémentée).")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Outil d'analyse Agent-Tracking & Draw.io Toolset"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- analyze ---
    analyze = sub.add_parser("analyze", help="Générer UML Draw.io")
    analyze.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    analyze.add_argument("--output", type=Path, default=Path("diagrams"))
    analyze.add_argument("-v", "--verbose", action="store_true")

    # --- visualize ---
    viz = sub.add_parser("visualize", help="Graphiques santé code")
    viz.add_argument("--source", type=Path, default=Path("."))
    viz.add_argument("--output-dir", type=Path, default=Path("visualizations"))
    viz.add_argument("--no-show", action="store_true")

    # --- inspect ---
    inspect = sub.add_parser("inspect", help="Inspecter un Draw.io")
    inspect.add_argument(
        "file", type=Path, nargs="?", default=Path("diagrams/diagram.drawio")
    )
    inspect.add_argument("--png", action="store_true")
    inspect.add_argument("--xml", action="store_true")
    inspect.add_argument("--outdir", type=Path, default=Path("visualizations"))

    # --- map ---
    map_cmd = sub.add_parser("map", help="Carte interactions projet")
    map_cmd.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    map_cmd.add_argument("--output-dir", type=Path, default=Path("visualizations"))

    args = parser.parse_args()

    try:
        if args.command == "analyze":
            analyze_codebase(args.source, ensure_dir(args.output), args.verbose)

        elif args.command == "visualize":
            return run_visualize(args.source, args.output_dir, show=not args.no_show)

        elif args.command == "map":
            return run_map(args.source, args.output_dir)

        elif args.command == "inspect":
            return run_inspect(args.file, args.outdir, args.png, args.xml)

        return 0

    except Exception as e:
        print(f"Erreur fatale : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
