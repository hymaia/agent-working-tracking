"""Command-line interface for code analysis and UML generation."""

from __future__ import annotations
import sys
from pathlib import Path

# Imports locaux
from .analysis import analyze_path
from .uml import generate_drawio_xml
from .analysis import AnalysisHook
from .visualization import (
    analyze_local_codebase,
    generate_hotspot_scatter,
)


def analyze_codebase(
    source_path: Path, output_dir: Path, verbose: bool = False
) -> tuple[dict, Path]:
    """Analyse statique pour génération de diagramme UML."""
    if verbose:
        print(f"🔍 Analyse des classes dans {source_path}...")

    classes = analyze_path(source_path)
    xml = generate_drawio_xml(classes)

    hook = AnalysisHook(source_path, output_dir)
    output_path = hook.get_output_filename("diagram")
    output_path.write_text(xml, encoding="utf-8")

    return classes, output_path


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Outil d'analyse de santé de Codebase")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Commande 'analyze'
    analyze_parser = subparsers.add_parser(
        "analyze", help="Générer diagramme UML")
    analyze_parser.add_argument(
        "--source", type=Path, default=Path("."), help="Source (default: .)")
    analyze_parser.add_argument(
        "--output", type=Path, default=Path("diagrams"), help="Output dir")
    analyze_parser.add_argument("-v", "--verbose", action="store_true")

    # Commande 'visualize'
    viz_parser = subparsers.add_parser(
        "visualize", help="Générer graphiques de santé")
    viz_parser.add_argument("--source", type=Path,
                            default=Path("."), help="Dossier à analyser")
    viz_parser.add_argument("--output-dir", type=Path,
                            default=Path("visualizations"))
    viz_parser.add_argument("--no-show", action="store_true",
                            help="Ne pas ouvrir les fenêtres")

    args = parser.parse_args()

    try:
        if args.command == "analyze":
            _, out = analyze_codebase(args.source, args.output, args.verbose)
            print(f"Diagramme généré : {out}")

        elif args.command == "visualize":
            outdir = args.output_dir
            outdir.mkdir(parents=True, exist_ok=True)

            print(f"Extraction des métriques de {args.source.resolve()}...")
            df_real = analyze_local_codebase(args.source)

            if df_real.empty:
                print("Aucun fichier Python trouvé.")
                return 1

            # Génération des fichiers
            generate_hotspot_scatter(
                df_real, save_path=outdir / "hotspots.png", show=not args.no_show)

            print(f"Graphiques sauvegardés dans {outdir}/")

        return 0
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
