#!/bin/bash

# 1. On récupère le dossier où se trouve ce script (la racine du projet)
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

echo "🚀 Lancement de agent-tracking dans : $PROJECT_ROOT"

# 2. On exécute poetry en forçant le répertoire de travail
poetry -C "$PROJECT_ROOT" run agent-tracking --source "$PROJECT_ROOT/src" --output "$PROJECT_ROOT/diagrams" -v