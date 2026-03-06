#!/bin/bash

set -e

# dossier où se trouve ce script
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# projet analysé (niveau au dessus)
TARGET_PROJECT=$(cd "$PROJECT_ROOT/.." && pwd)

SRC="$(cd "$PROJECT_ROOT/../papaga-ia/papaga-ia/papaga_ia" && pwd)"
SRC_GIT="$(cd "$PROJECT_ROOT/../papaga-ia/papaga-ia" && pwd)"
DIAGRAMS="$PROJECT_ROOT/diagrams"
VISUALS="$PROJECT_ROOT/visualizations"

echo "Lancement de agent-tracking"
echo "Tool root : $PROJECT_ROOT"
echo "Projet analysé : $TARGET_PROJECT"
echo "Source analysée : $SRC"
echo "Folder de destination : $VISUALS"
echo

# -----------------------------
# UML ANALYSIS
# -----------------------------
echo "Analyse UML..."
poetry -C "$PROJECT_ROOT" run agent-tracking analyze \
    --source "$SRC" \
    --output "$DIAGRAMS" \
    -v

echo

# récupérer le dernier diagramme généré
LATEST_DIAGRAM=$(ls -t "$DIAGRAMS"/*.drawio | head -n 1)

echo "Conversion du diagramme UML en PNG..."
poetry -C "$PROJECT_ROOT" run agent-tracking inspect \
    "$LATEST_DIAGRAM" \
    --png \
    --outdir "$VISUALS"

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
echo "🕸 Génération de la carte d'interactions..."
poetry -C "$PROJECT_ROOT" run agent-tracking map \
    --source "$SRC" \
    --output-dir "$VISUALS"

echo
echo "Analyse terminée"