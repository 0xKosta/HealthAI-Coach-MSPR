# CI/CD — HealthAI Coach

## Pipeline GitHub Actions

Fichier : [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Déclencheurs : push/PR sur `main`, `master`, `develop` ; `workflow_dispatch`.

### Jobs

| Job | Étapes | Objectif |
|-----|--------|----------|
| `api-tests` | `pip install` → `pytest` → couverture XML | Qualité backend |
| `frontend` | `npm ci` → `npm test` → `npm run build` | Qualité PWA |
| `docker-build` | Build `Dockerfile.api` + `Dockerfile.front` | Images reproductibles |

### Secrets (dépôt)

| Secret | Usage |
|--------|-------|
| — (CI tests) | `OPENAI_API_KEY` factice injectée dans le job |
| `DATABASE_URL` | Pipeline ETL ([`etl.yml`](../.github/workflows/etl.yml)) |
| `KAGGLE_*` | Téléchargement datasets ETL |

## Installation locale (reproduire la CI)

```bash
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ --cov=api --cov-report=term-missing

cd front-end
npm ci
npm test
npm run build
```

## Analyse de code (évolution)

SonarQube non configuré dans ce dépôt. Pistes :

- `sonar-scanner` sur job CI après tests
- Seuils : couverture > 60 %, 0 bug blocker

## Déploiement

La CI **build** les images Docker sans push registry (démo locale). Pour production :

1. Push images vers GHCR / Docker Hub
2. Déployer Compose ou Kubernetes sur VPS
3. Variables prod : `SECRET_KEY`, `DATABASE_URL`, `OPENAI_API_KEY`

## Maintenance

- Mettre à jour les actions `@v4` / `@v5` trimestriellement
- Vérifier compatibilité Python 3.11 et Node 20
- Conserver `workflow_dispatch` pour relancer manuellement avant soutenance
