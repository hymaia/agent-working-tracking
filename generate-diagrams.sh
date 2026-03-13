#!/bin/bash

set -e

# dossier où se trouve ce script
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Load .env
set -a
source "$PROJECT_ROOT/.env"
set +a

# projet analysé
TARGET_PROJECT="${ANALYZED_REPO_PATH}"
SRC_GIT="${ANALYZED_REPO_PATH}"
SRC="${ANALYZED_REPO_PATH}/${ANALYZED_REPO_SRC}"
DIAGRAMS="$PROJECT_ROOT/diagrams"
VISUALS="$PROJECT_ROOT/visualizations"

echo "Lancement de agent-tracking"
echo "Tool root : $PROJECT_ROOT"
echo "Projet analysé : $TARGET_PROJECT"
echo "Source analysée : $SRC"
echo "Folder de destination : $VISUALS"
echo


# -----------------------------
# AGENT INTERACTION (first — sets the task ID for subsequent steps)
# -----------------------------
echo "Génération des interactions avec l'agent..."
poetry -C "$PROJECT_ROOT" run agent-tracking history --output-dir "$VISUALS"
echo

# -----------------------------
# CODE HEALTH VISUALIZATION
# -----------------------------
echo "Génération des hotspots..."
poetry -C "$PROJECT_ROOT" run agent-tracking visualize \
    --source "$SRC_GIT" \
    --output-dir "$VISUALS"

echo

# -----------------------------
# PROJECT INTERACTION MAP
# -----------------------------
echo "Génération de la carte d'interactions..."
poetry -C "$PROJECT_ROOT" run agent-tracking map \
    --source "$SRC" \
    --output-dir "$VISUALS"

echo

# -----------------------------
# PROJECT METRICS ANALYSE
# -----------------------------
echo "Génération de la carte d'interactions..."
poetry -C "$PROJECT_ROOT" run agent-tracking quality \
    --source "$SRC" \
    --output-dir "$VISUALS"

echo
echo "Analyse terminée"