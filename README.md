# HealthAI Coach — MSPR Bloc 1 & 2

Plateforme de coaching santé personnalisé alimentée par des données réelles (nutrition, fitness, exercices) et un moteur de recommandation IA via OpenAI GPT-4o.

| Rôle | Responsabilité | Statut |
|------|---------------|--------|
| A | Pipeline ETL (ingestion, transformation, chargement) | Terminé |
| B | Schéma BDD — PostgreSQL / Supabase | Terminé |
| C | API REST — FastAPI + endpoints IA Coach | Terminé |
| D | Frontend Vue 3 — interface utilisateur | Terminé |

---

## Architecture globale

```
Sources brutes (Kaggle CSV + GitHub JSON)
          │
          ▼
   Pipeline ETL (etl/)
   extract → transform → load
          │
          ▼
   PostgreSQL — Supabase
   7 tables relationnelles
          │
     ┌────┴────────────┐
     ▼                 ▼
 API REST           Frontend
 (FastAPI)          (Vue 3 + Vite)
     │
     ▼
 OpenAI GPT-4o
 (coach IA, vision, tendances)
```

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
- Un projet [Supabase](https://supabase.com) créé (fournit le PostgreSQL)
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
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname
OPENAI_API_KEY=sk-...
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

> L'URL Supabase : **Settings → Database → Connection string → URI** (mode `psycopg2`)  
> Sans clé OpenAI valide, les endpoints `/coach/*` retournent une erreur 502. Les autres endpoints fonctionnent normalement.

### 5. Initialiser la base de données

Exécuter `db/init.sql` une seule fois sur le projet Supabase :

```bash
psql -h <host> -U <user> -d <dbname> -f db/init.sql
```

Ou via le **SQL Editor** du dashboard Supabase (copier-coller le contenu de `db/init.sql`).

### 6. MSPR 3 — Réseau social (`user_auth` + `posts`)

> **Ne pas relancer `init.sql`** sur une base déjà peuplée (les `DROP` effacent toutes les données).

1. Migration additive (une fois) : `db/migrations/001_user_auth_posts.sql`
2. ETL + `db/seed.sql` si ce n’est pas déjà fait
3. Comptes démo (100) :

```bash
pip install -r requirements.txt
python db/seed_auth.py
```

| Comptes | Email dérivé du profil `users` (ex. `user-000001.42@healthai-coach.demo`) |
| Affichage | Reprend `users.name` (ex. `User_000042`) — le profil santé reste dans `users` via `user_id` |
| Mot de passe démo | `1234` |

Vérification Supabase : `SELECT COUNT(*) FROM user_auth;` → 100

Migrations : `002_user_auth_restrict_fk.sql`, `003_drop_user_auth_avatar.sql` (à exécuter sur Supabase si pas déjà fait)

**Important — ETL et `user_auth` :** si `user_auth` contient des lignes, le pipeline ETL **ne tronque plus** `users` (évite la suppression en cascade des comptes sociaux) et crée une **sauvegarde automatique** dans `backups/` avant chaque run. Relancez `python db/seed_auth.py` seulement si vous avez vidé `user_auth` ou changé de base.

### 7. MSPR 3 — Sauvegarde / restauration de la base

**Prérequis :** outils client PostgreSQL (`pg_dump`, `pg_restore`) dans le PATH.  
Sur Windows : [PostgreSQL](https://www.postgresql.org/download/windows/) ou `winget install PostgreSQL.PostgreSQL`.

Les dumps sont enregistrés dans `backups/` (non versionnés dans Git).

```bash
# Sauvegarde (fichier backups/healthai_YYYYMMDD_HHMMSS.dump)
python scripts/backup_db.py backup

# Lister les sauvegardes
python scripts/backup_db.py list

# Restaurer la dernière sauvegarde (--clean : remplace schéma + données du dump)
python scripts/backup_db.py restore --latest
```

**Windows (PowerShell) :**

```powershell
.\scripts\backup_db.ps1
.\scripts\restore_db.ps1
.\scripts\restore_db.ps1 backups\healthai_20260101_120000.dump
```

> **Supabase :** utilisez l’URI **directe** (port 5432, host `db.<ref>.supabase.co`) dans `.env` si `pg_dump` échoue avec le pooler. Ne commitez jamais `.env`.

---

## Installation — Frontend

```bash
cd front-end
npm install
npm run dev
```

Le frontend démarre sur `http://localhost:5173` et se connecte automatiquement à l'API sur `http://localhost:8000`.

---

## Lancer l'API

```bash
# Depuis la racine du projet, venv activé
uvicorn api.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — documentation interactive |
| `http://localhost:8000/redoc` | ReDoc — documentation alternative |
| `http://localhost:8000/health` | Health check |

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
| `/metrics/stats` | Agrégats globaux (âge moyen, BMI moyen, répartition des objectifs) |

### Coach IA — GPT-4o

| Endpoint | Modèle | Description |
|----------|--------|-------------|
| `POST /coach/advice` | GPT-4o-mini | Conseil personnalisé basé sur le profil et les dernières métriques |
| `POST /coach/analyze-photo` | GPT-4o Vision | Analyse photo de repas — aliments détectés, macros estimés, conseil |
| `POST /coach/workout-plan` | GPT-4o-mini | Programme d'entraînement hebdomadaire selon équipement et objectif |
| `POST /coach/biometric-trend` | GPT-4o-mini | Analyse des tendances biométriques sur 30 jours |

**Contrat d'interface — Coach IA :**

`POST /coach/advice` — Body : `{ "user_id": 1 }`
```json
{ "user_id": 1, "user_name": "string", "advice": "string (markdown supporté)" }
```

`POST /coach/analyze-photo` — Body : `{ "user_id": 1, "image_base64": "..." }`
```json
{
  "user_id": 1,
  "user_name": "string",
  "foods_detected": ["Poulet", "Riz", "Brocolis"],
  "macros": { "calories": 520, "protein_g": 38, "carbs_g": 45, "fat_g": 12 },
  "advice": "string (markdown supporté)"
}
```

`POST /coach/workout-plan` — Body : `{ "user_id": 1, "equipment": "dumbbell", "days_per_week": 3 }`
```json
{ "user_id": 1, "user_name": "string", "plan": "string (markdown supporté)" }
```
Valeurs `equipment` : `none` · `dumbbell` · `barbell` · `machine` · `resistance` · `full`

`POST /coach/biometric-trend` — Body : `{ "user_id": 1 }`
```json
{ "user_id": 1, "user_name": "string", "analysis": "string (markdown supporté)" }
```

---

## Lancer le pipeline ETL

```bash
python -m etl.pipeline
```

Le pipeline enchaîne : `extract` → `transform` → `load`.  
Il est **idempotent** : re-exécutable sans créer de doublons (TRUNCATE + reload). Les comptes **`user_auth`** et la table **`users`** sont **préservés** lorsque `user_auth` n'est pas vide (voir section MSPR 3).

**Prérequis ETL :**
```env
KAGGLE_USERNAME=ton_username
KAGGLE_KEY=ta_cle_api
```

Le pipeline est automatisé via GitHub Actions (`.github/workflows/etl.yml`) :
- Tous les jours à 3h00 UTC
- Sur chaque push touchant `etl/`
- Déclenchement manuel possible depuis GitHub

---

## Tests

```bash
# Lancer les tests
pytest tests/ -v

# Avec rapport de couverture
pytest tests/ --cov=api --cov-report=term-missing --cov-report=html
```

Les tests utilisent une base **SQLite en mémoire** — aucun fichier `.env` requis, aucune connexion Supabase nécessaire. Les appels OpenAI sont mockés.

Pour consulter le rapport HTML :
1. Lancer la commande avec `--cov-report=html`
2. Ouvrir `htmlcov/index.html` dans ton navigateur

> Si `pytest-cov` n'est pas installé : `pip install pytest-cov`

**Couverture actuelle : 73%** (20 tests — health, users, nutrition, exercises, metrics, coach)

| Fichier | Couverture |
|---------|-----------|
| `api/models.py` | 100% |
| `api/schemas.py` | 100% |
| `api/main.py` | 100% |
| `api/routers/coach.py` | 78% |
| `api/routers/users.py` | 67% |
| `api/routers/metrics.py` | 61% |
| `api/routers/nutrition.py` | 49% |
| `api/routers/exercises.py` | 41% |

Le rapport HTML détaillé est généré dans `htmlcov/index.html`.

---

## Documentation API

Le fichier `docs/openapi.json` contient le schéma OpenAPI complet, versionné dans le dépôt.

Pour le régénérer après modification des endpoints :

```bash
python export_openapi.py
```

---

## Structure du projet

```
api/
├── main.py              # Point d'entrée FastAPI + CORS + routers
├── database.py          # Connexion SQLAlchemy 2 + générateur get_db()
├── models.py            # 7 modèles ORM — syntaxe Mapped[] (SQLAlchemy 2)
├── schemas.py           # Schémas Pydantic v2
├── ai_client.py         # Client OpenAI centralisé
└── routers/
    ├── users.py         # CRUD /users
    ├── nutrition.py     # CRUD /nutrition/foods et /nutrition/logs
    ├── exercises.py     # CRUD /exercises, /sessions
    ├── metrics.py       # CRUD /metrics + stats
    └── coach.py         # IA /coach — advice, analyze-photo, workout-plan, biometric-trend

front-end/
├── src/
│   ├── views/           # DashboardView, NutritionView, WorkoutView, TrendsView
│   ├── components/      # Composants UI réutilisables
│   ├── services/        # api.js — appels HTTP vers le backend
│   └── stores/          # Pinia — état global (userStore)
└── vite.config.js

etl/
├── pipeline.py          # Orchestrateur principal
├── extract.py           # Lecture CSV + JSON
├── transform.py         # Nettoyage, normalisation, déduplication
├── load.py              # Chargement en base
└── config.py            # Configuration centralisée

db/
├── init.sql             # Création des 7 tables
├── seed.sql             # Données de test
└── queries.sql          # Requêtes analytiques utilitaires

docs/
├── openapi.json         # Schéma OpenAPI exporté (généré par export_openapi.py)
├── sources.md           # Inventaire des sources de données
└── modele-donnees.md    # Documentation du schéma relationnel

tests/
└── test_routes.py       # 20 tests d'intégration (pytest + SQLite + mock OpenAI)

export_openapi.py        # Script de génération de docs/openapi.json
env.example              # Template .env
requirements.txt         # Dépendances Python
mcd.png                  # Modèle Conceptuel de Données
```

---

## Schéma relationnel

![Modèle Conceptuel de Données](mcd.png)

7 tables : `users`, `foods`, `exercises`, `food_logs`, `workout_sessions`, `session_exercises`, `biometric_metrics`.  
Documentation complète dans [`docs/modele-donnees.md`](docs/modele-donnees.md).

---

## Conventions

- Ne jamais committer `.env` — utiliser les GitHub Actions Secrets pour la CI
- Toujours travailler sur une branche dédiée, jamais directement sur `main`
- Toute modification du schéma BDD doit mettre à jour `db/init.sql`
- Après modification des endpoints, régénérer `docs/openapi.json` via `python export_openapi.py`
