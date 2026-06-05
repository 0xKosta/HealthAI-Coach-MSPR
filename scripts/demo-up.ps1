# Demarre l'environnement de demo MSPR3 (profil full)
# Usage : .\scripts\demo-up.ps1
#         .\scripts\demo-up.ps1 -Offline
#         .\scripts\demo-up.ps1 -Performance

param(
    [switch]$Offline,
    [switch]$Performance
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$files = @("docker-compose.yml")
$profile = "full"

if ($Offline) {
    $files += "docker-compose.offline.yml"
    $profile = "offline"
}
if ($Performance) {
    $files += "docker-compose.performance.yml"
    $profile = "performance"
}

$composeArgs = $files | ForEach-Object { "-f", $_ }
docker compose @composeArgs --profile $profile up -d --build

Write-Host ""
Write-Host "HealthAI Coach - demo demarree (profil $profile)"
Write-Host "  Web PWA    : http://localhost:8080"
Write-Host "  API        : http://localhost:8000/docs"
Write-Host "  Health     : http://localhost:8000/health"
if ($profile -ne "performance") {
    Write-Host "  Prometheus : http://localhost:9090"
    Write-Host "  Grafana    : http://localhost:3001 (admin / admin)"
    Write-Host ""
    Write-Host "Comptes demo (seed auto, mot de passe 1234) :"
    Write-Host "  Ex. tom.thomas.1@healthai-coach.demo"
    Write-Host "Compte admin app (Docker demo uniquement) :"
    Write-Host "  Email      : admin@admin.com"
    Write-Host "  Mot de passe : admin"
    Write-Host ""
    Write-Host "Reset BDD + re-seed : docker compose --profile full down -v"
}
Write-Host ""
Write-Host "Migration 007 sur Supabase existant (hors Docker) :"
Write-Host '  psql ... -f db/migrations/007_post_likes_comments.sql'
