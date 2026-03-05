"""Tests for CLI functionality."""

from pathlib import Path

from agent_tracking.cli import analyze_codebase


SAMPLE_CODE = """
class TestClass:
    def method_one(self):
        pass
    
    def method_two(self):
        pass


class AnotherClass:
    def run(self):
        pass
"""

EMPTY_CODE = """
# Just some comments
pass
"""


def test_analyze_codebase(tmp_path: Path) -> None:
    """Test codebase analysis and diagram generation."""
    # Create sample Python files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "sample.py").write_text(SAMPLE_CODE)

    output_dir = tmp_path / "diagrams"
    output_dir.mkdir()

    classes, output_path = analyze_codebase(src_dir, output_dir, verbose=False)

    # Verify analysis results
    assert "TestClass" in classes
    assert "AnotherClass" in classes
    assert len(classes["TestClass"].methods) == 2
    assert len(classes["AnotherClass"].methods) == 1

    # Verify diagram file was created
    assert output_path.exists()
    assert output_path.suffix == ".drawio"
    content = output_path.read_text()
    assert "TestClass" in content
    assert "AnotherClass" in content


def test_cli_visualize(tmp_path: Path, monkeypatch) -> None:
    """Test the CLI visualize subcommand writes output files."""
    dest = tmp_path / "figs"
    monkeypatch.chdir(tmp_path)
    # simulate arguments
    monkeypatch.setattr(
        "sys.argv",
        ["agent-tracking", "visualize", "--output-dir", str(dest), "--no-show"],
    )
    from agent_tracking import cli

    result = cli.main()
    assert result == 0
    assert (dest / "hotspots.png").exists()
    assert (dest / "quality.png").exists()
    assert (dest / "evolution.png").exists()


def test_analyze_codebase_empty_directory(tmp_path: Path) -> None:
    """Test analysis of directory with no classes."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "empty.py").write_text(EMPTY_CODE)

    output_dir = tmp_path / "diagrams"
    output_dir.mkdir()

    classes, output_path = analyze_codebase(src_dir, output_dir, verbose=False)

    # Should return empty dict for no classes
    assert len(classes) == 0
    assert output_path.exists()


def test_analyze_codebase_verbose(tmp_path: Path, capsys) -> None:
    """Test codebase analysis with verbose output."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "sample.py").write_text(SAMPLE_CODE)

    output_dir = tmp_path / "diagrams"
    output_dir.mkdir()

    classes, output_path = analyze_codebase(src_dir, output_dir, verbose=True)

    # Capture output
    captured = capsys.readouterr()
    assert "Analyzing" in captured.out
    assert "Found" in captured.out
    assert "Diagram saved" in captured.out
    assert len(classes) == 2


def test_analyze_codebase_nested_files(tmp_path: Path) -> None:
    """Test analysis of nested Python files."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text(SAMPLE_CODE)

    nested_dir = src_dir / "submodule"
    nested_dir.mkdir()
    (nested_dir / "module.py").write_text("class NestedClass:\n    pass")

    output_dir = tmp_path / "diagrams"
    output_dir.mkdir()

    classes, output_path = analyze_codebase(src_dir, output_dir, verbose=False)

    # Should find classes from both main and nested files
    assert "TestClass" in classes
    assert "AnotherClass" in classes
    assert "NestedClass" in classes
    assert output_path.exists()
