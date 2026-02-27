# Agent Tracking

A Python software project for agent tracking.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Poetry

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-tracking
```

2. Install dependencies using Poetry:
```bash
poetry install
```

### Running the Application

```bash
poetry run python -m agent_tracking
```

### Running Tests

```bash
poetry run pytest
```

### Code Quality

Format code with Black:
```bash
poetry run black .
```

Lint with Ruff:
```bash
poetry run ruff check .
```

Type checking with MyPy:
```bash
poetry run mypy src/
```

## Code Analysis & UML Generation

The library now includes utilities to analyze Python source and generate
UML diagrams compatible with draw.io.

### Quick Start with CLI

Generate a diagram for the entire codebase with a single command:

```bash
poetry run agent-tracking --source src --output diagrams -v
```

Options:
- `--source`: Source directory to analyze (default: `src`)
- `--output`: Output directory for diagrams (default: `diagrams`)
- `-v, --verbose`: Show detailed analysis output

### Programmatic Usage

```python
from pathlib import Path
from agent_tracking import analyze_codebase

classes, diagram_path = analyze_codebase(
    source_path=Path("src/agent_tracking"),
    output_dir=Path("diagrams"),
    verbose=True
)
```

### Hook Configuration for Auto-Analysis

Set up automatic diagram generation on code changes:

```python
from pathlib import Path
from agent_tracking import AnalysisHook, analyze_codebase

def on_code_change(results: dict) -> None:
    """Callback triggered when code changes are detected."""
    print(f"Diagram updated: {results}")

hook = AnalysisHook(
    root_path=Path("src"),
    output_dir=Path("diagrams")
)
hook.register_callback(on_code_change)

# When code changes, trigger analysis
classes, diagram_path = analyze_codebase(Path("src"), Path("diagrams"))
hook.trigger_analysis({"classes": len(classes), "diagram": str(diagram_path)})
```

The hook includes:
- **Automatic throttling** to prevent excessive re-analysis
- **Timestamped diagrams** for version tracking
- **Callback registration** for custom handling

### Viewing the Diagram

1. Open [draw.io](https://app.diagrams.net/).
2. Choose **File → Import From → Device** and select the `.drawio` file written to `diagrams/`.
3. Arrange or edit the boxes as needed. The exported XML is minimal, and you can add connectors manually if desired.

## Project Structure

```
agent-tracking/
├── src/
│   └── agent_tracking/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── docs/
├── README.md
├── pyproject.toml
└── .gitignore
```

## License

MIT
