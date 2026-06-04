# Checklist démo orale — 11 juin

## Avant le jour J

- [ ] `docker compose --profile full up -d --build` testé sur la machine de présentation
- [ ] Migration `007` appliquée sur la BDD utilisée
- [ ] Compte démo fonctionnel (email / mot de passe connus)
- [ ] Téléphone chargé — PWA installée une fois en conditions réelles
- [ ] Slides exportées PDF + repo à jour sur la branche de remise
- [ ] Capture Grafana + capture GitHub Actions CI

## Scénario 15 min

1. (2 min) Contexte + architecture slide
2. (3 min) `demo-up.ps1` ou stack déjà up — montrer `docker ps`
3. (4 min) PWA : login → Communauté → publication → like → commentaire
4. (2 min) Installer PWA sur mobile ou expliquer iOS Partager
5. (2 min) Grafana métriques + Prometheus targets UP
6. (1 min) Mode offline : coach advice avec mock
7. (1 min) Backup `scripts/backup_db.py backup`

## Réponses jury rapides

- **Pourquoi PWA ?** — Un codebase, pas de store, installable Android/iOS 2026
- **Métriques ?** — `http_requests_total`, latence, `/health` — voir `monitoring.md`
- **Tests ?** — pytest + Vitest, CI automatique
- **RGPD ?** — `DELETE /auth/me` cascade documentée

## Plan B

- API locale sans Docker : uvicorn + `npm run dev`
- Pas de réseau jury : profil `offline` + feed local
