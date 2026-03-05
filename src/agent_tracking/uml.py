"""Utilities for generating UML diagrams in draw.io format."""

from __future__ import annotations
import subprocess

from typing import Dict
from xml.sax.saxutils import escape

from .analysis import ClassInfo
import base64
import zlib
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from pathlib import Path


def generate_drawio_xml(classes: Dict[str, ClassInfo]) -> str:
    header = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1"
      tooltips="1" connect="1" arrows="1" fold="1" page="1"
      pageScale="1" pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
"""

    cells = []
    x_offset = 20
    y_offset = 20

    for i, (name, info) in enumerate(classes.items(), start=2):
        x = x_offset + ((i - 2) % 3) * 200
        y = y_offset + ((i - 2) // 3) * 140

        label = escape(name)
        if info.methods:
            label += "\n" + "\n".join(escape(m) for m in info.methods)

        cell = f"""
        <mxCell id="{i}" value="{label}"
          style="rounded=1;whiteSpace=wrap;html=1;"
          vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="160" height="100" as="geometry"/>
        </mxCell>
"""
        cells.append(cell)

    footer = """
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""

    return header + "".join(cells) + footer


def convert_drawio_to_png(input_file: Path, output_file: Path) -> bool:
    """Appelle l'exporteur draw.io pour transformer le XML en PNG."""
    try:
        # On s'assure que le dossier de destination existe
        output_file.parent.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [
                "drawio",
                "-x",
                "-f",
                "png",
                "-o",
                str(output_file),
                str(input_file),
            ],
            capture_output=True,
            text=True,
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("RETURN CODE:", result.returncode)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"❌ Erreur draw.io : {e}")
        return False
