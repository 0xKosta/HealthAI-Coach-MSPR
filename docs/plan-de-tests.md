# Plan de tests — MSPR3

## Objectifs

- Valider le réseau social (publications, likes, commentaires, médias)
- Garantir la non-régression API (coach, auth, biométrie)
- Vérifier la PWA (build + tests unitaires front)
- Préparer le déploiement Docker

## Types de tests

| Type | Outil | Périmètre |
|------|-------|-----------|
| Unitaires / intégration API | pytest + SQLite mémoire | Routes REST, permissions |
| Unitaires front | Vitest | Profil IA, statut API |
| Build | Vite `npm run build` | PWA compilable |
| Recette manuelle | Checklist ci-dessous | Parcours jury |
| E2E (optionnel) | Cypress — non automatisé | Login + feed |

## Tests automatisés API

```bash
pytest tests/ -v
pytest tests/ --cov=api --cov-report=term-missing
```

| Fichier | Scénarios |
|---------|-----------|
| `test_routes.py` | Health, users, nutrition, coach (mock OpenAI) |
| `test_biometrics.py` | Règles âge/IMC |
| `test_posts.py` | Feed, like, commentaire, suppression, image |
| `test_permissions.py` | Plans IA |
| `test_ai_requests.py` | Historique |
| `test_history_policy.py` | Fenêtres Premium |

## Tests automatisés front

```bash
cd front-end && npm test
```

- `useProfileCompletion.spec.js`
- `apiStatus.spec.js`

## Indicateurs de qualité

| Indicateur | Cible démo | Commande |
|------------|------------|----------|
| Tests API verts | 100 % pass (64 tests) | `pytest tests/` |
| Couverture API | ~70 %+ | `pytest --cov=api` |
| Build front | Succès | `npm run build` |
| CI GitHub | Vert | Actions → CI HealthAI Coach |

## Recette manuelle — feed PWA

1. Connexion utilisateur démo
2. Onglet **Communauté** → fil chargé
3. Publier texte seul → visible en tête de fil
4. Publier avec image JPEG → miniature affichée
5. Like → compteur + état actif
6. Commentaire → liste + compteur
7. Supprimer **sa** publication → disparaît
8. Installer PWA (Android ou iOS) → relancer app standalone

## Recette — Docker

1. `.\scripts\demo-up.ps1` → tous conteneurs `healthy`
2. http://localhost:8080 → login OK
3. http://localhost:9090 → cible `healthai-api` UP
4. `.\scripts\demo-up.ps1 -Offline` → coach advice sans clé OpenAI valide

## Tests de sécurité (manuel)

- Accès `/posts/` sans JWT → 401
- Suppression post autrui → 403
- JWT expiré → redirection login front

## Rapports

- Export couverture HTML : `htmlcov/index.html`
- Artefact CI : `coverage.xml`
