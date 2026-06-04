# Gestion de projet agile — MSPR3

## Méthode

Approche **Scrum** (sprints de 2 semaines, backlog priorisé par valeur métier).

| Cérémonie | Fréquence | Objectif |
|-----------|-----------|----------|
| Daily | Quotidien (15 min) | Avancement, blocages |
| Sprint Planning | Début sprint | Backlog priorisé |
| Review | Fin sprint | Démo incrément |
| Rétrospective | Fin sprint | Amélioration process |

## Outil de suivi

Kanban (Trello / GitHub Projects / tableau physique) avec colonnes :

- **À faire** — Docker, feed PWA, likes/comments, docs
- **En cours** — tâche active
- **Terminé** — validé + testé

Captures à joindre au dossier de remise (export PNG du tableau).

## Sprints (synthèse)

### Sprint 1 — Fondations MSPR3

- Auth JWT, plans, migrations `user_auth` / `posts`
- API publications + médias

### Sprint 2 — Réseau social & PWA

- Likes et commentaires (migration 007)
- `FeedView` + navigation Communauté
- Bannière installation PWA

### Sprint 3 — Mise en production démo

- Docker Compose (3 profils)
- CI pytest + build front
- Prometheus / Grafana
- Documentation livrables IV

## Backlog restant (oral 11 juin)

- Répétition démo 20 min
- Affinage slides
- Tests Lighthouse PWA (capture)

## Risques suivis

| Risque | Mitigation |
|--------|------------|
| Délai remise | Priorisation PWA + Docker minimal |
| OpenAI indisponible | `OPENAI_MOCK` + fallbacks |
| iOS install PWA | Doc + démo Safari |

## Communication

- Dépôt Git partagé (historique commits par feature)
- Documentation `docs/` versionnée avec le code
