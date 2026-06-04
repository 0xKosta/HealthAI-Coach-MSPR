# Référence rapide — démo & ports

> **Fiche anti-perte** : quel URL ouvrir selon le mode (dev, preview, Docker), comptes, commandes, Grafana/Prometheus.

---

## Tableau des URLs (à garder sous les yeux)

| Port | URL | Mode | Qui / quoi |
|------|-----|------|------------|
| **3000** | http://localhost:3000 | **Dev front** | `npm run dev` — Vue + Vite, **API = :8000** (pas de PWA installable) |
| **4173** | http://localhost:4173 | **Preview front** | `npm run build` puis `npm run preview` — PWA testable (SW actif) |
| **5173** | http://localhost:5173 | *(optionnel)* | Port Vite par défaut si non configuré — **ce projet utilise 3000** en dev |
| **8000** | http://localhost:8000/docs | **API** | `uvicorn api.main:app` **ou** conteneur Docker `api` — Swagger, `/metrics`, auth, posts |
| **8001** | http://localhost:8001/docs | **Recommender ML** | MSPR2 seul — `uvicorn recommender.main:app --port 8001` |
| **8080** | http://localhost:8080 | **PWA Docker** | nginx + build front — **démo jury / install mobile** |
| **5432** | localhost:5432 | **PostgreSQL** | Docker `db` : user/pass/db = `healthai` / `healthai` / `healthai` |
| **9090** | http://localhost:9090 | **Prometheus** | Docker profil `full` ou `offline` — targets, requêtes PromQL |
| **3001** | http://localhost:3001 | **Grafana** | Docker profil `full` ou `offline` — login **admin / admin** |

> **Pas de port 9000** dans ce projet : métriques = **9090** (Prometheus).

---

## 3 modes — ne pas mélanger

### A) Développement local (2 terminaux, Supabase ou Postgres local)

| Terminal | Commande | URL |
|----------|----------|-----|
| 1 API | `uvicorn api.main:app --reload` | http://localhost:8000 |
| 2 Front | `cd front-end` → `npm run dev` | http://localhost:3000 |

- BDD : `.env` → `DATABASE_URL` (Supabase ou Postgres).
- Pas de Grafana/Prometheus sauf si Docker monitoring lancé à part.

### B) Preview PWA (sans Docker)

```bash
cd front-end
npm run build
npm run preview
```

| Élément | Détail |
|---------|--------|
| Front | http://localhost:4173 |
| API | Toujours http://localhost:8000 (lancer uvicorn à part) |
| PWA | Installable (Chrome / Safari) — **pas** en `npm run dev` |

### C) Démo Docker MSPR3 (tout-en-un)

```powershell
.\scripts\demo-up.ps1              # complet + monitoring
.\scripts\demo-up.ps1 -Offline     # mock OpenAI
.\scripts\demo-up.ps1 -Performance # sans Prometheus/Grafana
```

| Service | URL | Rôle |
|---------|-----|------|
| **PWA** | http://localhost:8080 | Interface utilisateur (point d’entrée démo) |
| **API** | http://localhost:8000/docs | Backend + feed + coach |
| **Prometheus** | http://localhost:9090 | Métriques |
| **Grafana** | http://localhost:3001 | Graphiques |
| **Postgres** | port 5432 | Données démo (volume Docker) |

Arrêt / reset :

```bash
docker compose --profile full down
docker compose --profile full down -v   # remise à zéro BDD
```

---

## Comptes utiles (démo)

| Contexte | Email | Mot de passe | Rôle / plan |
|----------|-------|--------------|-------------|
| **Docker seed** | `admin@admin.com` | `admin` | admin, premium_plus — **uniquement** stack Docker |
| **Supabase / ETL** | `*.@healthai-coach.demo` | `1234` | comptes Kaggle (si seed_auth) |
| **Inscription PWA** | tes comptes test | — | créés via `/register` |

---

## Monitoring — pas à refaire à chaque fois

### Vérifier Prometheus (30 s)

1. Ouvrir http://localhost:9090/targets  
2. Job `healthai-api` → état **UP**  
3. Métriques brutes : http://localhost:8000/metrics  

### Connecter Prometheus dans Grafana (première fois sur une machine)

1. http://localhost:3001 — login **admin** / **admin**  
2. Menu **Connections** → **Data sources** → **Add data source** → **Prometheus**  
3. URL : `http://prometheus:9090`  
   - *(depuis le conteneur Grafana, le hostname Docker est `prometheus`, pas `localhost`)*  
4. **Save & test** → doit afficher succès  

### Requêtes PromQL pour la démo (Explore → Prometheus)

| Requête | Effet |
|---------|--------|
| `http_requests_total` | Compteur de requêtes (naviguer sur le feed avant) |
| `rate(http_requests_total[1m])` | Débit sur 1 minute |
| `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | Latence p95 |

**Astuce démo :** ouvrir le feed sur :8080, liker/commenter, recharger Grafana → les courbes bougent.

### Profil performance

Pas de Grafana/Prometheus — seulement :8080, :8000, :5432.

---

## CI / prod cloud (hors démo locale)

| Où | Quoi |
|----|------|
| GitHub Actions | Workflow **CI HealthAI Coach** — pytest, Vitest, build Docker |
| GitHub Actions | Workflow **ETL** — pipeline Kaggle → Supabase |
| Supabase | BDD distante — pas un port localhost |

---

## Liens doc associés

| Sujet | Fichier |
|-------|---------|
| Déploiement Docker | [`deploiement.md`](deploiement.md) |
| Liste métriques | [`monitoring.md`](monitoring.md) |
| Checklist oral 11 juin | [`demo-oral-checklist.md`](demo-oral-checklist.md) |
| PWA mobile | [`application-mobile-pwa.md`](application-mobile-pwa.md) |

---

## Schéma mental (1 image)

```
DEV          PREVIEW           DOCKER DÉMO
:3000  →     :4173      →      :8080 (PWA)
  ↓            ↓                  ↓
:8000 API ← :8000 API ←────── :8000 API
                                  ↓
                            :9090 Prometheus → :3001 Grafana
```
