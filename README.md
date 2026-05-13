# HealthAI Coach — MSPR Bloc 1

Plateforme de coaching santé personnalisé alimentée par des données réelles (nutrition, fitness, exercices).

Monorepo partagé entre 4 rôles :

| Rôle | Responsabilité | Statut |
|------|---------------|--------|
| A | Pipeline ETL (ingestion, transformation, chargement) | Implémenté |
| B | Schéma BDD — PostgreSQL / Supabase | Implémenté |
| C | API REST — FastAPI | Implémenté |
| D | Frontend / Interface utilisateur | En cours |

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
     ┌────┴────┐
     ▼         ▼
 API REST    Dashboard
 (FastAPI)  (Metabase)
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
- Un projet [Supabase](https://supabase.com) créé (fournit le PostgreSQL)
- Git

---

## Installation

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
# Windows
cp env.example .env

# macOS / Linux
cp env.example .env
```

Ouvrir `.env` et renseigner :

```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

> L'URL de connexion Supabase se trouve dans le dashboard du projet :
> **Settings → Database → Connection string → URI** (mode `psycopg2`)

### 5. Initialiser la base de données

Exécuter `db/init.sql` une seule fois sur le projet Supabase pour créer les 7 tables :

```bash
psql -h <host> -U <user> -d <dbname> -f db/init.sql
```

Ou via le **SQL Editor** du dashboard Supabase (copier-coller le contenu de `db/init.sql`).

Pour charger les données de test :

```bash
psql -h <host> -U <user> -d <dbname> -f db/seed.sql
```

---

## Lancer l'API (Rôle C)

```bash
uvicorn api.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — documentation interactive |
| `http://localhost:8000/redoc` | ReDoc — documentation alternative |
| `http://localhost:8000/health` | Health check |

**Endpoints disponibles :**

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

---

## Lancer le pipeline ETL (Rôle A)

```bash
python -m etl.pipeline
```

Le pipeline enchaîne dans l'ordre : `extract` → `transform` → `load`.
Il est **idempotent** : re-exécutable sans créer de doublons (TRUNCATE + reload complet).

**Prérequis ETL :** credentials Kaggle dans `.env` ou variables d'environnement :
```env
KAGGLE_USERNAME=ton_username
KAGGLE_KEY=ta_cle_api
```

Le pipeline est aussi automatisé via GitHub Actions (`.github/workflows/etl.yml`) :
- Déclenchement automatique tous les jours à 3h00 UTC
- Déclenchement sur chaque push touchant `etl/`
- Déclenchement manuel possible depuis l'interface GitHub

---

## Lancer les tests

```bash
pytest tests/ -v
```

Les tests utilisent une base SQLite en mémoire — aucun fichier `.env` requis, aucune connexion Supabase nécessaire.

---

## Vérifier la connexion Supabase

```bash
python test_connection.py
```

> Ce fichier est temporaire et sera supprimé une fois la connexion validée.

---

## Structure du projet

```
api/
├── main.py              # Point d'entrée FastAPI + CORS + inclusion des routers
├── database.py          # Connexion SQLAlchemy + générateur de session get_db()
├── models.py            # 7 modèles ORM (Users, Foods, Exercises, FoodLogs...)
├── schemas.py           # Schémas Pydantic v2 — XxxCreate + XxxResponse par ressource
└── routers/
    ├── users.py         # CRUD /users
    ├── nutrition.py     # CRUD /nutrition/foods et /nutrition/logs
    ├── exercises.py     # CRUD /exercises, /sessions, /sessions/{id}/exercises
    └── metrics.py       # CRUD /metrics + GET /metrics/stats

db/
├── init.sql             # Création des 7 tables (à exécuter une fois sur Supabase)
├── seed.sql             # Données de test
└── queries.sql          # Requêtes analytiques utilitaires

etl/
├── pipeline.py          # Orchestrateur principal
├── extract.py           # Lecture des fichiers bruts (CSV + JSON)
├── transform.py         # Nettoyage, normalisation, déduplication
├── load.py              # Chargement en base (TRUNCATE + INSERT)
└── config.py            # Configuration centralisée

docs/
├── sources.md           # Inventaire et documentation des sources de données
└── modele-donnees.md    # Documentation du schéma relationnel

tests/
└── test_routes.py       # Tests d'intégration (pytest + TestClient + SQLite)

.github/workflows/
└── etl.yml              # Pipeline CI/CD — exécution ETL automatisée

env.example              # Template de configuration (copier en .env)
requirements.txt         # Dépendances Python (ETL + API)
mcd.png                  # Modèle Conceptuel de Données
```

---

## Schéma relationnel

![Modèle Conceptuel de Données](mcd.png)

7 tables : `users`, `foods`, `exercises`, `food_logs`, `workout_sessions`, `session_exercises`, `biometric_metrics`.
Documentation complète dans [`docs/modele-donnees.md`](docs/modele-donnees.md) et [`docs/sources.md`](docs/sources.md).

---

## Conventions

- Ne jamais committer `.env` (déjà dans `.gitignore`) — utiliser les GitHub Actions Secrets pour la CI
- Toujours travailler sur une branche dédiée, jamais directement sur `main`
- Toute modification du schéma BDD doit passer par le Rôle B et mettre à jour `db/init.sql`
