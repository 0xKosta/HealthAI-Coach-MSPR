# HealthAI Coach — Restauration BDD (Windows PowerShell)
# Usage :
#   .\scripts\restore_db.ps1                          # dernière sauvegarde
#   .\scripts\restore_db.ps1 backups\healthai_xxx.dump

param(
    [string]$File = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if ($File -eq "") {
    python scripts/backup_db.py restore --latest
} else {
    python scripts/backup_db.py restore $File
}
