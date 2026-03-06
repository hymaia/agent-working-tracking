# Agent Tracking

A Python software project for agent tracking. The goal is to display all changements done by agent code assistant.

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/hymaia/agent-working-tracking.git
cd agent-tracking
pip install poetry
```

2. Install dependencies using Poetry:
```bash
poetry install
```

### Running the Application

```bash
bash generate-diagrams.sh
```


## Code Analysis & UML Generation

The library now includes utilities to analyze Python source and generate UML diagrams compatible with draw.io. We are also able to evaluate the complexity of your project and
all links between fonction/class.

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


### Explication complexité cyclomatique

La complexité cyclomatique (en anglais cyclomatic complexity) est une mesure utilisée en génie logiciel pour évaluer la complexité d’un programme en fonction du nombre de chemins logiques indépendants dans son code.

```M=E−N+2P```
où :
    ** M = complexité cyclomatique
    **E = nombre d’arêtes (edges) dans le graphe
    **N = nombre de nœuds (nodes)
    **P = nombre de composants connectés (souvent 1 pour une fonction)

