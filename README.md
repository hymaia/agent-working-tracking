# Agent Tracking

Visualize everything your AI coding assistant does — tasks, code complexity, and file interactions — in a live dashboard.

## Setup

```bash
git clone https://github.com/hymaia/agent-working-tracking.git
cd agent-tracking
pip install poetry
poetry install
```

Set your environment in `.env`:

```env
ENV_IDE=claudecode        # or: antigravity
ANALYZED_REPO_NAME=my-project
```

## Usage

**Sync history & generate diagrams:**

```bash
bash generate-diagrams.sh
```

This runs three steps automatically:
1. `agent-tracking visualize` — code complexity metrics
2. `agent-tracking map` — project interaction graph
3. `agent-tracking history` — sync agent task history

All outputs go to `visualizations/`.

**Run the dashboard:**

```bash
cd app && uvicorn server:app --reload
```

Then open `http://127.0.0.1:8000`.

## Auto-run on Claude stop

Add this to `~/.claude/settings.json` to run the script automatically after every Claude response:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/Desktop/agent-tracking/generate-diagrams.sh\""
          }
        ]
      }
    ]
  }
}
```

## ENV_IDE modes

| Value | Behavior |
|---|---|
| `claudecode` | Reads history from `~/.claude/projects/` |
| `antigravity` | Reads tasks from `~/.gemini/antigravity/brain/` |

The dashboard auto-detects the current session via `AGENT_CONV_ID` (set manually in `.env` to override).