"""Command-line interface for code analysis and UML generation."""

from __future__ import annotations

import sys
from pathlib import Path

from .analysis import analyze_path
from .uml import generate_drawio_xml
from .analysis import AnalysisHook


def analyze_codebase(
    source_path: Path, output_dir: Path, verbose: bool = False
) -> tuple[dict, Path]:
    """Analyze a codebase and generate a UML diagram.

    Args:
        source_path: Path to the source code directory.
        output_dir: Directory where to save the diagram.
        verbose: Print verbose output.

    Returns:
        Tuple of (classes_dict, output_path).
    """
    if verbose:
        print(f"Analyzing {source_path}...")

    classes = analyze_path(source_path)

    if verbose:
        print(f"Found {len(classes)} classes")

    xml = generate_drawio_xml(classes)

    # Generate timestamped filename
    hook = AnalysisHook(source_path, output_dir)
    output_path = hook.get_output_filename("diagram")

    output_path.write_text(xml, encoding="utf-8")

    if verbose:
        print(f"Diagram saved to {output_path}")

    return classes, output_path


def main() -> int:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze Python codebase and generate UML diagrams")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("src"),
        help="Source hhh directory to analyze (default: src)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diagrams"),
        help="Output directory for diagrams (default: diagrams)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    try:
        classes, output_path = analyze_codebase(
            args.source, args.output, verbose=args.verbose
        )
        if args.verbose:
            print(f"✓ Analysis complete. Diagram: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
