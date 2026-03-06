# Agent Tracking

A Python software project for agent tracking. The goal is to display all changements done by agent code assistant.

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
bash generate-diagrams.sh
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



### Hook Configuration for Auto-Analysis

Set up automatic diagram generation on code changes.

## Repository Hook Configuration (recommended)

Add the following JSON file to the repository at `.github/hooks/tracking-flow-code.json` to enable automated diagram generation when repository code structure changes. Place the file in the `.github/hooks` folder and ensure hooks are installed (copying into `.git/hooks/` or using your project's hook manager).

Example `tracking-flow-code.json`:

```jsonc
{
    "hooks": {
        "Stop": [
            {
                "type": "command",
                "command": "cd \"$(git rev-parse --show-toplevel)\" && poetry run agent-tracking analyze --source src --output diagrams -v",
                "description": "Generate UML diagram when code structure changes",
                "enabled": true
            },
            {
                "type": "command",
                "command": "echo 'HOOK TEST' > test_hook.txt",
                "description": "Simple test",
                "enabled": true
            }

        ]
    }
}
```

Instructions for new developers:

- Add the file to `.github/hooks/tracking-flow-code.json` in the project.
- Install repository hooks (for example, copy or symlink the JSON into `.git/hooks/` or run a provided installer) so your local Git invokes the hook scripts on commit.
- To test the hook locally, make a small change, commit it, and verify the command runs and generates/updates files in `diagrams/`.

### Visualization Utilities

Beyond generating UML diagrams, the library can produce a set of
plots that give a high-level health overview of a codebase. These
charts currently use simulated data but are designed so that a real
backend (SonarQube, Git analytics, etc.) can populate a DataFrame later.

Example usage from Python:

```python
from agent_tracking import (
    generate_hotspot_scatter,
    generate_quality_radar,
    generate_evolution_dual_axis,
)

# each function accepts an optional DataFrame and/or save path
# and returns nothing; they display and/or save a figure.

generate_hotspot_scatter(save_path="hotspots.png")
generate_quality_radar(save_path="quality.png")
generate_evolution_dual_axis(save_path="evolution.png")
```

You can also use the same CLI with a `visualize` subcommand to produce all three images at once:

```bash
# after installing dependencies via poetry
poetry run agent-tracking visualize --output-dir diagrams/figs
```

The `--no-show` flag suppresses interactive display (useful in CI).

The first chart is a **hotspot scatter** (churn vs complexity), the
second a **radar chart** comparing maintenability, coverage, security,
reliability and documentation, and the third shows the **evolution over
12 months** of test coverage and technical debt.

### Viewing the Diagram

1. Open [draw.io](https://app.diagrams.net/).
2. Choose **File → Import From → Device** and select the `.drawio` file written to `diagrams/`.
3. Arrange or edit the boxes as needed. The exported XML is minimal, and you can add connectors manually if desired.

### Explication complexité cyclomatique

La complexité cyclomatique (en anglais cyclomatic complexity) est une mesure utilisée en génie logiciel pour évaluer la complexité d’un programme en fonction du nombre de chemins logiques indépendants dans son code.

```M=E−N+2P```
où :
    ** M = complexité cyclomatique
    **E = nombre d’arêtes (edges) dans le graphe
    **N = nombre de nœuds (nodes)
    **P = nombre de composants connectés (souvent 1 pour une fonction)
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
