#!/usr/bin/env bash
# HealthAI Coach — Sauvegarde BDD (Linux / macOS)
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/backup_db.py backup
