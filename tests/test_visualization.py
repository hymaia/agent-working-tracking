"""Basic smoke tests for visualization functions."""

from pathlib import Path
from agent_tracking import (
    generate_hotspot_scatter,
    generate_quality_radar,
    generate_evolution_dual_axis,
)


def test_visualizations(tmp_path: Path) -> None:
    """Ensure each plotting function can be called and saves a file."""
    out1 = tmp_path / "hotspot.png"
    out2 = tmp_path / "radar.png"
    out3 = tmp_path / "evol.png"

    generate_hotspot_scatter(save_path=out1, show=False)
    assert out1.exists()

    generate_quality_radar(save_path=out2, show=False)
    assert out2.exists()

    generate_evolution_dual_axis(save_path=out3, show=False)
    assert out3.exists()
