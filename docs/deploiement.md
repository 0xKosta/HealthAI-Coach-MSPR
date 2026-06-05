# Déploiement — environnement de démonstration MSPR3

## Prérequis

- Docker Desktop 4.x+ (Windows / macOS / Linux)
- 8 Go RAM recommandés (profil `full`)
- Ports libres : `5432`, `8000`, `8080`, `9090`, `3001`

## Démarrage en une commande

### Profil complet (défaut)

```powershell
.\scripts\demo-up.ps1
```

Équivalent :

```bash
docker compose --profile full up -d --build
```

| Service | URL |
|---------|-----|
| PWA (nginx) | http://localhost:8080 |
| API + Swagger | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (healthai / healthai) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin / admin) |

**Compte admin application** (seed automatique au démarrage de l’API Docker — **pas** sur Supabase) :

| Email | Mot de passe |
|-------|----------------|
| `admin@admin.com` | `admin` |

Rôle `admin` — utiliser l’interface admin pour attribuer `premium` / `premium_plus` aux comptes de test.

**Jeu de données démo** (seed automatique `SEED_DOCKER_DEMO_DATA=true`, source `db/seed/docker_demo_data.json`) :

| Contenu | Quantité |
|---------|----------|
| Profils `users` + comptes `user_auth` | 10 |
| `biometric_metrics` | ~300 (Trends) |
| `workout_sessions` | 10 |
| `exercises` | 20 |

Comptes `.demo` : mot de passe **`1234`** (hash ETL, ex. `tom.thomas.1@healthai-coach.demo`).  
**Feed social** : non seedé — publications/likes en démo live.

Premier remplissage ou reset complet :

```bash
docker compose --profile full down -v
.\scripts\demo-up.ps1
```

> Ordre au démarrage API : données démo → puis admin (`users.id` admin = 11).

### Profil offline

Pas d'appel OpenAI réel — réponses fallback coach.

```powershell
.\scripts\demo-up.ps1 -Offline
```

Fichiers : `docker-compose.yml` + `docker-compose.offline.yml`, variable `OPENAI_MOCK=true`.

### Profil performance

Stack sans Prometheus/Grafana, limites mémoire réduites.

```powershell
.\scripts\demo-up.ps1 -Performance
```

## Images Docker

| Image | Dockerfile | Rôle |
|-------|------------|------|
| `healthai-coach-api` | `Dockerfile.api` | FastAPI + uvicorn, volume `media/` |
| `healthai-coach-front` | `Dockerfile.front` | Build Vite → nginx:alpine |
| `postgres:16-alpine` | — | BDD locale |
| `prom/prometheus` | — | Scraping `/metrics` |
| `grafana/grafana` | — | Dashboards |

### Bonnes pratiques

- Utilisateur non-root dans images officielles de base
- Secrets via variables d'environnement (jamais dans l'image)
- `SECRET_KEY` et `OPENAI_API_KEY` à surcharger en production
- Healthcheck PostgreSQL avant démarrage API

## Initialisation base de données (Docker)

Au premier démarrage du volume `pgdata` :

1. `db/init.sql` — schéma MSPR 1/2
2. `db/migrations/*.sql` — extensions MSPR3 (auth, posts, likes, comments, IA…)

Sur **Supabase existant**, appliquer manuellement les migrations manquantes, notamment :

```bash
psql $DATABASE_URL -f db/migrations/007_post_likes_comments.sql
```

## Sauvegarde et restauration

```bash
python scripts/backup_db.py backup
python scripts/backup_db.py list
python scripts/backup_db.py restore --latest
```

Scripts PowerShell : `scripts/backup_db.ps1`, `scripts/restore_db.ps1`.

## Arrêt et remise à zéro

```bash
docker compose --profile full down
docker compose --profile full down -v   # supprime le volume PostgreSQL
```

## Variables d'environnement

Voir [`env.example`](../env.example) et surcharge Compose pour `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `OPENAI_API_KEY`, `OPENAI_MOCK`.
