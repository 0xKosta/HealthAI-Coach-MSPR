#!/usr/bin/env bash
# HealthAI Coach — Restauration BDD (Linux / macOS)
# Usage :
#   ./scripts/restore_db.sh
#   ./scripts/restore_db.sh backups/healthai_YYYYMMDD_HHMMSS.dump
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -eq 0 ]]; then
  python scripts/backup_db.py restore --latest
else
  python scripts/backup_db.py restore "$1"
fi
