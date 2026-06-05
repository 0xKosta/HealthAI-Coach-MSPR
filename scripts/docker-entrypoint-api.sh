#!/bin/sh
set -e
echo "HealthAI API — démarrage (OPENAI_MOCK=${OPENAI_MOCK:-false})"
if [ "${SEED_DOCKER_DEMO_DATA:-false}" = "true" ]; then
  echo "Seed jeu de données démo Docker (10 users, biométrie, exercices)..."
  python scripts/seed_docker_demo_data.py
fi
if [ "${SEED_DOCKER_DEMO_ADMIN:-false}" = "true" ]; then
  echo "Seed compte admin démo Docker..."
  python scripts/seed_docker_demo_admin.py
fi
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
