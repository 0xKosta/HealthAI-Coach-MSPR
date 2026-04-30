# HealthAI Coach — MSPR Bloc 1

Plateforme de coaching santé personnalisé. Monorepo partagé entre 4 rôles.

| Rôle | Responsabilité |
|------|---------------|
| A | ETL (ingestion et transformation des données) |
| B | Schéma BDD (Supabase / PostgreSQL) |
| C | API REST (FastAPI) |
| D | Frontend / Interface utilisateur |

---

## Prérequis

- Python 3.11+
- Un compte [Supabase](https://supabase.com) avec un projet créé (Rôle B)
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
cp env.example .env
```

Ouvrir `.env` et renseigner les valeurs :

```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

> L'URL de connexion Supabase se trouve dans le dashboard du projet :
> **Settings → Database → Connection string → URI**

---

## Lancer l'API (Rôle C)

```bash
uvicorn api.main:app --reload
```

- Swagger UI : http://localhost:8000/docs
- Health check : http://localhost:8000/health

---

## Tester la connexion à la base de données

```bash
python test_connection.py
```

Ce fichier est temporaire et sera supprimé après validation de la connexion.

---

## Lancer les tests

```bash
pytest tests/
```

---

## Structure du projet

```
api/
├── main.py          # Point d'entrée FastAPI
├── database.py      # Connexion SQLAlchemy + session
├── models.py        # Modèles ORM (en cours)
├── schemas.py       # Schémas Pydantic (en cours)
└── routers/         # Endpoints par domaine (en cours)
    ├── users.py
    ├── nutrition.py
    ├── exercises.py
    └── metrics.py
tests/
└── test_routes.py   # Tests pytest (en cours)
requirements.txt     # Dépendances Python
.env.example         # Template de configuration
```

---

## Conventions

- Ne jamais committer le fichier `.env` (déjà dans `.gitignore`)
- Toujours travailler sur une branche dédiée, jamais directement sur `main`
- Les routers ne seront activés qu'après validation du schéma BDD par le Rôle B
