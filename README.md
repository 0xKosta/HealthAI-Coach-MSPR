# HealthAI Coach — MSPR Blocs 1, 2 & 3

Plateforme de coaching santé personnalisé alimentée par des données réelles (nutrition, fitness, exercices), un moteur de recommandation IA via OpenAI GPT-4o, et un réseau social santé avec authentification JWT.

| Rôle | Responsabilité | Statut |
|------|---------------|--------|
| A | Pipeline ETL (ingestion, transformation, chargement) | Terminé |
| B | Schéma BDD — PostgreSQL / Supabase | Terminé |
| C | API REST — FastAPI + endpoints IA Coach + Auth + Feed social | Terminé |
| D | Frontend Vue 3 — interface utilisateur + PWA | Terminé |

---

## Architecture globale

```
Sources brutes (Kaggle CSV + GitHub JSON)
          │
          ▼
   Pipeline ETL (etl/) — GitHub Actions planifié
   extract → transform → load
          │
          ▼
   PostgreSQL 16
   (Supabase cloud · conteneur Docker en démo)
   12 tables métier (+ schema_migrations)
          │
     ┌────┴────────────┬──────────────┬─────────────┐
     ▼                 ▼              ▼             ▼
 API REST           PWA Vue 3    Recommender ML   OpenAI
 FastAPI :8000      :3000 dev    :8001 (MSPR2)    GPT-4o / mini
 JWT · coach · feed :8080 Docker Random Forest   (mock offline)
     │                 │
     │            nginx (Docker)
     └─────────────────┴──► Prometheus :9090 → Grafana :3001
```

| Mode | BDD | Front | Monitoring |
|------|-----|-------|------------|
| **Dev local** | Supabase ou Postgres | `npm run dev` → `:3000` | — |
| **Preview PWA** | idem | `npm run preview` → `:4173` | — |
| **Docker MSPR3** | Postgres conteneur `:5432` | PWA `:8080` | profils `full` / `offline` |

Schéma détaillé : [`docs/architecture-mspr3.md`](docs/architecture-mspr3.md) · ports et comptes : [`docs/reference-demo.md`](docs/reference-demo.md).

**Sources de données :**

| Dataset | Format | Licence | Tables alimentées |
|---------|--------|---------|-------------------|
| Daily Food & Nutrition (Kaggle) | CSV | CC0 | `foods`, `food_logs` |
| Gym Members Exercise (Kaggle) | CSV | CC BY 4.0 | `users`, `workout_sessions` |
| ExerciseDB (GitHub) | JSON | MIT | `exercises` |

---

## Prérequis

- Python 3.11+
- Node.js 18+ (pour le frontend)
- Un projet [Supabase](https://supabase.com) **ou** Docker Desktop (démo MSPR3 sans Supabase)
- Une clé API OpenAI (pour les endpoints `/coach/*`)
- Git

---

## Installation — Backend

### 1. Cloner le repo

```bash
git clone <url-du-repo>
cd HealthAI-Coach-MSPR1
```

### 2. Créer et activer l'environnement virtuel

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp env.example .env
```

Ouvrir `.env` et renseigner :

```env
# Base de données
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname

# OpenAI (endpoints /coach/*)
OPENAI_API_KEY=sk-...

# JWT Auth (MSPR 3)
SECRET_KEY=une-chaine-aleatoire-longue-et-secrete-changez-moi
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:4173,http://localhost:8080,http://localhost:8000
```

> **URL Supabase :** Settings → Database → Connection string → URI (mode `psycopg2`)
> **Sans clé OpenAI valide**, les endpoints `/coach/*` retournent une erreur 502 — les autres endpoints fonctionnent normalement.
> **Sans `SECRET_KEY`**, l'auth JWT utilise une valeur par défaut non sécurisée — à changer en production.

### 5. Initialiser la base de données (première fois)

Exécuter `db/init.sql` **une seule fois** sur le projet Supabase :

```bash
psql -h <host> -U <user> -d <dbname> -f db/init.sql
```

Ou via le **SQL Editor** du dashboard Supabase.

> **Ne pas relancer `init.sql`** sur une base déjà peuplée — les `DROP` effacent toutes les données.

### 6. MSPR 3 — Migrations réseau social, auth et IA

Appliquer les migrations **additives** dans l'ordre (SQL Editor Supabase ou `psql`) :

```bash
psql ... -f db/migrations/001_user_auth_posts.sql
psql ... -f db/migrations/005_user_auth_role_plan.sql
psql ... -f db/migrations/006_ai_requests.sql
psql ... -f db/migrations/007_post_likes_comments.sql
```

| Migration | Effet |
|-----------|--------|
| `001` | `user_auth`, `posts` |
| `005` | `role`, `plan` sur `user_auth` |
| `006` | Historique `ai_requests` |
| `007` | `post_likes`, `post_comments` |

Puis charger les 100 comptes démo Supabase :

```bash
python db/seed_auth.py
```

| Comptes | 100 comptes liés aux profils `users` existants |
|---------|------------------------------------------------|
| Email | Dérivé du profil (ex. `tom.thomas.1@healthai-coach.demo`) |
| Mot de passe démo | `1234` |
| Avatar | `null` par défaut |

Vérification : `SELECT COUNT(*) FROM user_auth;` → 100

### 7. Migrations profil santé (âge nullable + validation biométrique)

Sur une base **déjà initialisée**, appliquer les migrations additives dans l'ordre :

```bash
psql -h <host> -U <user> -d <dbname> -f db/migrations/002_users_age_nullable.sql
psql -h <host> -U <user> -d <dbname> -f db/migrations/004_users_biometric_checks.sql
```

| Migration | Effet |
|-----------|--------|
| `002_users_age_nullable.sql` | `users.age` nullable à l'inscription |
| `004_users_biometric_checks.sql` | Contraintes CHECK âge, taille, poids, IMC |

Documentation détaillée : [`docs/validation-biometrique.md`](docs/validation-biometrique.md).

### 8. Sauvegarde / restauration de la base

```bash
# Sauvegarde
python scripts/backup_db.py backup

# Lister les sauvegardes
python scripts/backup_db.py list

# Restaurer la dernière sauvegarde
python scripts/backup_db.py restore --latest
```

**Windows (PowerShell) :**

```powershell
.\scripts\backup_db.ps1
.\scripts\restore_db.ps1
```

---

## Installation — Frontend

```bash
cd front-end
npm install
npm run dev
```

Le frontend démarre sur `http://localhost:3000` et se connecte à l'API sur `http://localhost:8000`.  
Preview PWA installable : `npm run build` puis `npm run preview` → `http://localhost:4173`.

---

## Lancer l'API

```bash
uvicorn api.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — documentation interactive |
| `http://localhost:8000/redoc` | ReDoc — documentation alternative |
| `http://localhost:8000/health` | Health check |

---

## Démarrage rapide MSPR2

Pour tester l'application complète (API + front + micro-service ML), ouvrir **trois terminaux** (venv activé sur les terminaux Python) :

| Terminal | Commande | URL |
|----------|----------|-----|
| 1 — API principale | `uvicorn api.main:app --reload` | http://localhost:8000/docs |
| 2 — Frontend | `cd front-end` puis `npm run dev` | http://localhost:3000 |
| 3 — Recommandation ML | `uvicorn recommender.main:app --port 8001 --reload` | http://localhost:8001/docs |

**Prérequis recommender :** `pip install -r recommender/requirements.txt` et présence de `recommender/model.pkl` (sinon `python -m recommender.train`).

---

## Moteur de recommandation (MSPR2)

Micro-service FastAPI **séparé** de l'API principale — prédit le type d'entraînement (`Cardio`, `HIIT`, `Strength`, `Yoga`) via une **forêt aléatoire** (scikit-learn).

| Élément | Détail |
|---------|--------|
| Port | **8001** (l'API coach OpenAI reste sur **8000**) |
| Endpoint principal | `POST /recommend` |
| Historique optionnel | MongoDB (`MONGO_URI` dans `.env`) — l'API fonctionne sans Mongo |
| Documentation | [`recommender/README.md`](recommender/README.md) — entraînement, évaluation, correspondance grille Bloc 2 |
| Notebook | [`notebooks/ml_recommendation.ipynb`](notebooks/ml_recommendation.ipynb) |

**Métriques indicatives (modèle `rf_200`, 438 lignes) :**

| Indicateur | Valeur |
|------------|--------|
| Cross-validation (5 folds) | ~80 % |
| Accuracy test | ~75 % |
| F1-score pondéré | ~0,75 |

---

## Endpoints disponibles

### Données métier

| Préfixe | Ressources |
|---------|------------|
| `/users` | Profils utilisateurs (CRUD) |
| `/nutrition/foods` | Catalogue nutritionnel (CRUD) |
| `/nutrition/logs` | Journal alimentaire (CRUD) |
| `/exercises` | Catalogue d'exercices (CRUD) |
| `/exercises/sessions` | Sessions d'entraînement (CRUD) |
| `/exercises/sessions/{id}/exercises` | Exercices d'une session |
| `/metrics` | Mesures biométriques (CRUD) |
| `/metrics/stats` | Agrégats globaux |

### Coach IA — GPT-4o

| Endpoint | Modèle | Description |
|----------|--------|-------------|
| `POST /coach/advice` | GPT-4o-mini | Conseil personnalisé basé sur le profil |
| `POST /coach/analyze-photo` | GPT-4o Vision | Analyse photo de repas — aliments, macros, conseil |
| `POST /coach/workout-plan` | GPT-4o-mini | Programme d'entraînement hebdomadaire |
| `POST /coach/biometric-trend` | GPT-4o-mini | Analyse des tendances biométriques 30 jours |
| `POST /coach/meal-plan` | GPT-4o-mini | Plan repas hebdomadaire avec budget et allergies |

> Tous les endpoints `/coach/*` intègrent un **cache TTL** (1h), un **rate limiting** (10 appels/h/utilisateur) et un **fallback** si OpenAI est indisponible.
>
> **Prérequis profil :** âge, poids, taille et objectif renseignés, biométrie dans les plages autorisées — sinon réponse **400**. Voir [`docs/validation-biometrique.md`](docs/validation-biometrique.md).

### Authentification — JWT (MSPR 3)

| Endpoint | Description |
|----------|-------------|
| `POST /auth/register` | Créer un compte (retourne un token JWT) |
| `POST /auth/login` | Se connecter (email + mot de passe) |
| `GET /auth/me` | Profil du compte connecté 🔒 |
| `GET /auth/me/profile` | Profil santé lié (`users`) + `profile_issues` 🔒 |
| `PUT /auth/me/profile` | Mettre à jour le profil santé (validation biométrique) 🔒 |
| `DELETE /auth/me` | Suppression du compte (RGPD) 🔒 |

### Feed Social (MSPR 3)

| Endpoint | Description |
|----------|-------------|
| `GET /posts/` | Feed — liste des publications (anti-chronologique) 🔒 |
| `POST /posts/` | Créer une publication (texte + média optionnel) 🔒 |
| `POST /posts/{id}/like` | Aimer / retirer son like 🔒 |
| `GET /posts/{id}/comments` | Liste des commentaires 🔒 |
| `POST /posts/{id}/comments` | Ajouter un commentaire 🔒 |
| `DELETE /posts/{id}` | Supprimer une publication (auteur uniquement) 🔒 |

**Front PWA :** route `/dashboard/:userId/feed` (onglet **Communauté**). Voir [`docs/application-mobile-pwa.md`](docs/application-mobile-pwa.md).

**Migration likes/commentaires** — incluse dans la liste ci-dessus (`007`).

> 🔒 = endpoint protégé, nécessite un token JWT dans le header `Authorization: Bearer <token>`

**Formats média acceptés :** JPEG, PNG, WebP, MP4 (max 50 Mo). Fichiers stockés **localement** dans `media/posts/` (dossier ignoré par Git, comme `media/ai-photos/`). En production : stockage objet / serveur de fichiers à prévoir.

---

## MSPR3 — Démo Docker (une commande)

```powershell
.\scripts\demo-up.ps1              # profil full — stack complète + monitoring
.\scripts\demo-up.ps1 -Offline     # mock OpenAI (pas d'appel réel)
.\scripts\demo-up.ps1 -Performance # sans Prometheus/Grafana, limites mémoire
```

Équivalent : `docker compose --profile full|offline|performance up -d --build`.

| Service | URL | Détail |
|---------|-----|--------|
| PWA (nginx) | http://localhost:8080 | Point d'entrée démo jury |
| API + Swagger | http://localhost:8000/docs | JWT, feed, coach, `/metrics` |
| PostgreSQL | localhost:5432 | `healthai` / `healthai` / `healthai` |
| Prometheus | http://localhost:9090 | Profils `full` et `offline` |
| Grafana | http://localhost:3001 | admin / admin |

**Seed automatique au démarrage Docker** (`SEED_DOCKER_DEMO_DATA=true`) : 10 profils + comptes `.demo` (mdp `1234`), biométrie, exercices, séances. Feed social non seedé (démo live). Reset : `docker compose --profile full down -v` puis `demo-up.ps1`.

**Compte admin application (seed Docker uniquement, pas Supabase) :**

| Champ | Valeur |
|-------|--------|
| Email | `admin@admin.com` |
| Mot de passe | `admin` |

Permet de passer d’autres comptes en `premium` / `premium_plus` via l’interface admin.

Documentation : [`docs/deploiement.md`](docs/deploiement.md), [`docs/monitoring.md`](docs/monitoring.md), [`docs/ci-cd.md`](docs/ci-cd.md), [`docs/reference-demo.md`](docs/reference-demo.md).

---

## Lancer le pipeline ETL

```bash
python -m etl.pipeline
```

Le pipeline enchaîne : `extract` → `transform` → `load`. Il est **idempotent**.
Si `user_auth` contient des lignes, le pipeline **préserve** la table `users`.

Les métriques biométriques simulées (`biometric_metrics`) ne sont générées que pour les profils ayant au moins une séance Gym (`workout_sessions`) — pas pour les comptes créés via l'inscription.

**Prérequis ETL :**
```env
KAGGLE_USERNAME=ton_username
KAGGLE_KEY=ta_cle_api
```

Automatisé via GitHub Actions (`.github/workflows/etl.yml`) : quotidien à 3h UTC, sur push dans `etl/`, ou déclenchement manuel.

---

## Tests

### API — pytest (services critiques)

```bash
# Lancer les tests
pytest tests/ -v

# Avec rapport de couverture terminal
pytest tests/ --cov=api --cov-report=term-missing

# Avec rapport HTML
pytest tests/ --cov=api --cov-report=term-missing --cov-report=html
```

Les tests utilisent une base **SQLite en mémoire** — aucun `.env` requis, aucune connexion Supabase. Les appels OpenAI sont mockés.

Rapport HTML : ouvrir `htmlcov/index.html` dans le navigateur.

> Si `pytest-cov` n'est pas installé : `pip install pytest-cov`

**~66 tests** (auth, posts, permissions, biométrie, coach, routes) — SQLite en mémoire, OpenAI mocké. CI : [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Détail : [`docs/plan-de-tests.md`](docs/plan-de-tests.md).

### Frontend — Vitest (logique UI)

```bash
cd front-end
npm test
```

**7 tests unitaires** sur la logique métier critique : accès IA selon le profil (`useProfileCompletion`), détection panne réseau (`apiStatusStore`). Les parcours complets (login, nutrition, PWA) sont validés en recette manuelle ; E2E Cypress prévu en MSPR3.

Détail : [`front-end/README.md`](front-end/README.md).

---

## Documentation API

```bash
python export_openapi.py
```

Le fichier `docs/openapi.json` est versionné dans le dépôt.

---

## Structure du projet

```
api/
├── main.py              # Point d'entrée FastAPI + CORS + routers + handler 400 biométrie
├── database.py          # Connexion SQLAlchemy 2 + générateur get_db()
├── models.py            # 12 modèles ORM — syntaxe Mapped[] (SQLAlchemy 2)
├── schemas.py           # Schémas Pydantic v2 (input strict / response + profile_issues)
├── biometrics.py        # Règles métier âge, taille, poids, IMC
├── ai_client.py         # Client OpenAI centralisé
├── coach_utils.py       # Cache TTL, rate limiter, fallbacks IA
└── routers/
    ├── users.py         # CRUD /users
    ├── nutrition.py     # CRUD /nutrition/foods et /nutrition/logs
    ├── exercises.py     # CRUD /exercises, /sessions
    ├── metrics.py       # CRUD /metrics + stats
    ├── coach.py         # IA /coach — advice, analyze-photo, workout-plan, biometric-trend, meal-plan
    ├── auth.py          # JWT /auth — register, login, me
    └── posts.py         # Feed /posts — publications, likes, commentaires, médias

front-end/
├── src/
│   ├── views/           # Vues (Dashboard, Nutrition, Workout, Trends, Feed, Login...)
│   ├── components/      # Composants UI réutilisables
│   ├── composables/     # useBiometricValidation, useProfileCompletion…
│   ├── services/        # api.js — appels HTTP
│   └── stores/          # Pinia — état global (userStore, authStore)
└── vite.config.js

recommender/            # Micro-service ML MSPR2 (port 8001)
├── main.py             # FastAPI — POST /recommend
├── train.py            # Entraînement Random Forest
├── evaluate.py         # Métriques F1, matrice de confusion
├── model.pkl           # Modèle entraîné (rf_200)
└── README.md           # Lancement, grille Bloc 2, MongoDB

etl/
├── pipeline.py          # Orchestrateur principal
├── extract.py           # Lecture CSV + JSON
├── transform.py         # Nettoyage, normalisation
├── load.py              # Chargement en base
└── config.py            # Configuration centralisée

db/
├── init.sql             # Tables MSPR 1/2 (nutrition, fitness, biométrie)
├── seed.sql             # Données de test MSPR 1/2
├── queries.sql          # Requêtes analytiques
├── seed_auth.py         # 100 comptes démo user_auth (Supabase)
├── seed/                # Jeu Docker (docker_demo_data.json)
└── migrations/          # Migrations additives 001 → 007
    ├── 001_user_auth_posts.sql
    ├── 002_users_age_nullable.sql
    ├── 004_users_biometric_checks.sql
    ├── 005_user_auth_role_plan.sql
    ├── 006_ai_requests.sql
    └── 007_post_likes_comments.sql

docker-compose.yml       # Profils full / offline / performance
docker-compose.offline.yml
docker-compose.performance.yml
scripts/
├── demo-up.ps1          # Démarrage démo Docker
├── seed_docker_demo_data.py
├── backup_db.py         # Sauvegarde / restauration PostgreSQL
└── backup_db.ps1        # Version PowerShell (Windows)

docs/
├── architecture-mspr3.md    # Vue système MSPR3
├── modele-donnees.md        # MCD / MLD / MPD (Merise + dbdiagram)
├── deploiement.md           # Docker, profils, seed
├── reference-demo.md        # Ports, comptes, modes dev/preview/Docker
├── monitoring.md            # Prometheus + Grafana
├── ci-cd.md                 # Pipeline GitHub Actions
├── application-mobile-pwa.md  # PWA, feed, install mobile
├── plan-de-tests.md         # Stratégie de tests
├── demo-oral-checklist.md   # Préparation soutenance
├── openapi.json             # Schéma OpenAPI exporté
├── sources.md               # Inventaire des sources de données
└── validation-biometrique.md

media/posts/             # Médias uploadés (non versionnés — dans .gitignore)
backups/                 # Dumps PostgreSQL (non versionnés — dans .gitignore)

tests/
├── conftest.py          # Fixtures pytest (SQLite mémoire)
├── test_routes.py       # CRUD métier
├── test_biometrics.py   # Validation biométrique
├── test_posts.py        # Feed, likes, commentaires
├── test_auth_delete.py  # Suppression compte RGPD
├── test_permissions.py  # Rôles et plans
└── test_ai_requests.py  # Historique coach IA

export_openapi.py        # Script export openapi.json
env.example              # Template .env
requirements.txt         # Dépendances Python
mcd.png                  # Modèle Conceptuel de Données
```

---

## Modèle de données

| Niveau | Contenu | Fichier |
|--------|---------|---------|
| **MCD Merise** | Entités + cardinalités (MSPR1-2 + extension MSPR3) | [`docs/modele-donnees.md`](docs/modele-donnees.md) §1 |
| **MLD** | Schéma relationnel (PK/FK) | [`docs/modele-donnees.md`](docs/modele-donnees.md) §2 |
| **MPD** | DBML dbdiagram.io + migrations SQL | [`docs/modele-donnees.md`](docs/modele-donnees.md) §3 · `db/migrations/` |

**12 tables métier :** `users`, `foods`, `exercises`, `food_logs`, `workout_sessions`, `session_exercises`, `biometric_metrics`, `user_auth`, `posts`, `post_likes`, `post_comments`, `ai_requests`.

![Schéma historique MSPR1-2](mcd.png) — *figure MSPR2 ; régénérer depuis dbdiagram pour la version MSPR3 complète.*

---

## Documentation complémentaire

| Document | Sujet |
|----------|--------|
| [`docs/architecture-mspr3.md`](docs/architecture-mspr3.md) | Composants, déploiement, sécurité |
| [`docs/deploiement.md`](docs/deploiement.md) | Docker Compose, seed, reset |
| [`docs/reference-demo.md`](docs/reference-demo.md) | Ports, comptes, 3 modes (dev / preview / Docker) |
| [`docs/monitoring.md`](docs/monitoring.md) | Prometheus, Grafana, métriques API |
| [`docs/ci-cd.md`](docs/ci-cd.md) | GitHub Actions (tests, build, ETL) |
| [`docs/application-mobile-pwa.md`](docs/application-mobile-pwa.md) | PWA, feed social, mobile |
| [`docs/plan-de-tests.md`](docs/plan-de-tests.md) | Pytest, Vitest, recette |
| [`docs/demo-oral-checklist.md`](docs/demo-oral-checklist.md) | Checklist soutenance |
| [`docs/gestion-projet.md`](docs/gestion-projet.md) | Kanban, sprints |

---

## Conventions

- Ne jamais committer `.env` — utiliser les GitHub Actions Secrets pour la CI
- Toujours travailler sur une branche dédiée, jamais directement sur `main`
- Toute modification du schéma BDD doit passer par une migration dans `db/migrations/`
- Après modification des endpoints, régénérer `docs/openapi.json` via `python export_openapi.py`
- Les uploads **`media/posts/`** et **`media/ai-photos/`** ne doivent **jamais** être commités (`.gitkeep` seulement) — stockage serveur prévu plus tard
- Le dossier `backups/` est dans `.gitignore`