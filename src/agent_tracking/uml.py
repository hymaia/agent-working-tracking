"""Utilities for generating UML diagrams in draw.io format."""

from __future__ import annotations

from typing import Dict
from xml.sax.saxutils import escape

from .analysis import ClassInfo


def generate_drawio_xml(classes: Dict[str, ClassInfo]) -> str:
    """Return a minimal draw.io XML document representing the classes.

    The output contains a rectangle for each class named with the class name and
    a simple list of methods inside. Inheritance relationships are not drawn.

    Args:
        classes: Mapping from class name to :class:`ClassInfo`.

    Returns:
        XML string that can be imported into draw.io.
    """
    # draw.io uses a custom XML schema; we'll build a simple graph with cells.
    header = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<mxfile host=\"app.diagrams.net\" modified=\"2026-02-27T00:00:00.000Z\" "
        "agent=\"python\">\n"
        "  <diagram id=\"diagram\" name=\"Page-1\">\n"
    )
    cells = []
    x_offset = 20
    y_offset = 20
    for i, (name, info) in enumerate(classes.items()):
        x = x_offset + (i % 3) * 160
        y = y_offset + (i // 3) * 120
        label = escape(name)
        if info.methods:
            label += "\n" + "\n".join(escape(m) for m in info.methods)
        cell = (
            f"    <mxCell id=\"{i}\" value=\"{label}\" style=\"rounded=1;whiteSpace=wrap;html=1;\" "
            f"vertex=\"1\"><mxGeometry x=\"{x}\" y=\"{y}\" width=\"140\" height=\"80\" as=\"geometry\" /></mxCell>\n"
        )
        cells.append(cell)
    footer = "  </diagram>\n</mxfile>\n"
    return header + "".join(cells) + footer
