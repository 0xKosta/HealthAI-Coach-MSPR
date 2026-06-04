# Support de présentation — plan de slides (livrable MSPR3)

> Exportez vers PowerPoint / PDF pour la remise. Affinez pour l'oral du 11 juin.

1. **Titre** — HealthAI Coach MSPR3, mise en production, auteur, date
2. **Contexte** — Startup, freemium, besoin réseau social communauté
3. **Objectifs MSPR3** — Démo reproductible, PWA mobile, DevOps, supervision
4. **Choix PWA vs native** — Coûts stores, un codebase, validation formateur
5. **Architecture** — Schéma Docker + API + PWA (reprendre `architecture-mspr3.md`)
6. **Réseau social** — Tables posts / likes / comments, API, capture Feed
7. **Parcours démo** — Login → Feed → like → commentaire → install PWA
8. **Docker & 3 configs** — full, offline (`OPENAI_MOCK`), performance
9. **CI/CD** — pytest, Vitest, build, capture pipeline vert
10. **Monitoring** — Prometheus, Grafana, liste métriques `/metrics`
11. **Tests & qualité** — 64+ tests API, couverture, plan de tests
12. **Sécurité & RGPD** — JWT, OWASP, suppression compte
13. **Difficultés** — Délais, dépendances (OpenAI, Kaggle), contournements (PWA, mock IA)
14. **Perspectives** — SonarQube, K8s, push notifications PWA
15. **Questions**

Durée cible soutenance : **20 minutes** + démo live intégrée aux slides 6–7.
