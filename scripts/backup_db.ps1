# HealthAI Coach — Sauvegarde BDD (Windows PowerShell)
# Usage : .\scripts\backup_db.ps1

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python scripts/backup_db.py backup
