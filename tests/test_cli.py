"""Tests for CLI functionality."""

from pathlib import Path
import json
import pytest

from agent_tracking import cli


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


def test_cli_visualize(tmp_path: Path, monkeypatch) -> None:
    """Test the CLI visualize subcommand writes output files."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "sample.py").write_text(SAMPLE_CODE)
    
    dest = tmp_path / "figs"
    monkeypatch.chdir(tmp_path)
    # Mock get_latest_task_id to return 0 for consistent filenames
    monkeypatch.setattr(cli, "get_latest_task_id", lambda: 0)
    # simulate arguments
    monkeypatch.setattr(
        "sys.argv",
        ["agent-tracking", "visualize", "--source", str(source), "--output-dir", str(dest), "--no-show"],
    )

    result = cli.main()
    assert result == 0
    # The output filename includes the task ID, which is 0 by default
    assert (dest / "metrics-id-0.json").exists()


def test_cli_map(tmp_path: Path, monkeypatch) -> None:
    """Test the CLI map subcommand."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("class MyApp: pass")
    
    dest = tmp_path / "visuals"
    monkeypatch.chdir(tmp_path)
    # Mock get_latest_task_id to return 0 for consistent filenames
    monkeypatch.setattr(cli, "get_latest_task_id", lambda: 0)
    
    monkeypatch.setattr(
        "sys.argv",
        ["agent-tracking", "map", "--source", str(source), "--output-dir", str(dest)],
    )
    
    result = cli.main()
    assert result == 0
    # GlobalProjectAnalyzer generates project_interaction_map-id-0.html by default if no tasks
    assert (dest / "project_interaction_map-id-0.html").exists()


def test_cli_track(tmp_path: Path, monkeypatch) -> None:
    """Test the CLI track subcommand."""
    # Setup mock brain dir
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()
    conv_id = "test-conv-id"
    conv_dir = brain_dir / conv_id
    conv_dir.mkdir()
    
    # Create a dummy task.md with one task with ID and one without
    task_md = conv_dir / "task.md"
    task_md.write_text("# Task: Test Conversation\n\n- [x] Task With ID <!-- id: 1 -->\n    details 1\n- [x] Task Without ID\n    details 2\n")
    
    # Mock BRAIN_DIR in chat_interceptor
    from agent_tracking import chat_interceptor
    monkeypatch.setattr(chat_interceptor, "BRAIN_DIR", brain_dir)
    
    # Mock the tasks file path to avoid writing to the real visualizations dir
    tasks_file = tmp_path / "tasks-agent.json"
    monkeypatch.setattr(chat_interceptor.ChatStore, "_tasks_file", lambda self: tasks_file)
    
    monkeypatch.setattr(
        "sys.argv",
        ["agent-tracking", "track", "--conv-id", conv_id],
    )
    
    result = cli.main()
    assert result == 0
    
    # Verify tasks-agent.json was created/updated
    assert tasks_file.exists()
    content = json.loads(tasks_file.read_text())
    assert any(t["asked"] == "Test Conversation | Task With ID" for t in content)
    assert any(t["asked"] == "Test Conversation | Task Without ID" for t in content)
    assert len(content) == 2

    # Run again to ensure no duplicates
    result = cli.main()
    assert result == 0
    content_after = json.loads(tasks_file.read_text())
    assert len(content_after) == 2
