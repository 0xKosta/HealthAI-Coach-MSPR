# Rapport d'inventaire des sources de donnees — HealthAI Coach

**MSPR Bloc 1 — Role B : Data Modeler**
**Date de redaction :** Avril 2026

---

## 1. Tableau recapitulatif des sources

| # | Nom du dataset | Origine | Format | Licence | Table(s) cible(s) |
|---|----------------|---------|--------|---------|-------------------|
| 1 | Daily Food & Nutrition Dataset | Kaggle (adilshamim8) | CSV | CC0 Public Domain | `foods`, `food_logs` |
| 2 | Gym Members Exercise Dataset | Kaggle (valakhorasani) | CSV | CC BY 4.0 | `users`, `workout_sessions` |
| 3 | ExerciseDB | GitHub (yuhonas/free-exercise-db) | JSON | MIT | `exercises` |

**Justification du choix des sources :**
Ces trois datasets couvrent les trois domaines metier de HealthAI Coach (nutrition, fitness, catalogue d'exercices). Ils sont issus de deux formats distincts (CSV et JSON), ce qui demontre la competence "collecte de sources heterogenes" exigee par le cahier des charges. Tous sont sous licence ouverte, conformes a une utilisation pedagogique et reproductible.

---

## 2. Description detaillee de chaque source

### Source 1 — Daily Food & Nutrition Dataset

| Attribut | Valeur |
|----------|--------|
| **URL** | https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset |
| **Format** | CSV |
| **Separateur** | virgule |
| **Encodage** | UTF-8 |
| **Frequence de mise a jour** | Statique (snapshot ponctuel) |
| **Volume estime** | Plusieurs milliers de lignes |
| **Licence** | CC0 Public Domain (libre de droits) |

**Colonnes principales exploitees :**

| Colonne source | Colonne cible (BDD) | Type | Description |
|----------------|---------------------|------|-------------|
| food_item | foods.name / food_logs.food_name | VARCHAR | Nom de l'aliment |
| category | foods.category | VARCHAR | Categorie alimentaire |
| calories_kcal | foods.calories_per_100g | FLOAT | Apport calorique pour 100g |
| protein_g | foods.proteins_g | FLOAT | Proteines en grammes |
| carbohydrates_g | foods.carbs_g | FLOAT | Glucides en grammes |
| fat_g | foods.fats_g | FLOAT | Lipides en grammes |
| fiber_g | foods.fiber_g | FLOAT | Fibres en grammes |
| meal_type | food_logs.meal_type | VARCHAR | Type de repas |

**Colonnes generees par le pipeline ETL (absentes du dataset) :**
- `user_id` : genere au format `User_000001` (index de ligne)
- `log_date` : genere en remontant depuis aujourd'hui (1 jour par ligne)
- `quantity_g` : fixee a 100g par convention (pas de donnee de quantite dans le dataset)

**Anomalies connues et regles de qualite appliquees :**
- Valeurs manquantes sur certains micronutriments → lignes conservees avec NULL
- Doublons sur `food_item` → deduplication globale avant chargement dans `foods`
- `calories_kcal` hors bornes (> 5000 kcal) → lignes supprimees par l'ETL
- Macronutriments negatifs → filtres par validation hors-borne (>= 0)
- Normalisation : noms en minuscules, espaces en debut/fin supprimes

---

### Source 2 — Gym Members Exercise Dataset

| Attribut | Valeur |
|----------|--------|
| **URL** | https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset |
| **Format** | CSV |
| **Separateur** | virgule |
| **Encodage** | UTF-8 |
| **Frequence de mise a jour** | Statique (snapshot ponctuel) |
| **Volume** | 973 lignes |
| **Licence** | CC BY 4.0 (attribution requise) |

**Colonnes principales exploitees :**

| Colonne source | Colonne cible (BDD) | Type | Description |
|----------------|---------------------|------|-------------|
| Age | users.age | INTEGER | Age en annees |
| Gender | users.gender | VARCHAR | Genre (normalise en minuscules) |
| Weight (kg) | users.weight_kg | FLOAT | Poids en kilogrammes |
| Height (m) | users.height_cm | FLOAT | Taille convertie en cm |
| BMI | users.bmi | FLOAT | Indice de masse corporelle |
| Fat_Percentage | users.body_fat_pct | FLOAT | Pourcentage de masse grasse |
| Experience_Level | users.experience_level | INTEGER | Niveau 1/2/3 |
| Session_Duration (hours) | workout_sessions.duration_min | INTEGER | Converti en minutes |
| Calories_Burned | workout_sessions.calories_burned | FLOAT | Calories brulees |
| Avg_BPM | workout_sessions.avg_bpm | FLOAT | Frequence cardiaque moyenne |
| Max_BPM | workout_sessions.max_bpm | FLOAT | Frequence cardiaque maximale |
| Workout_Type | workout_sessions.workout_type | VARCHAR | Type d'entrainement |

**Colonnes generees par le pipeline ETL (absentes du dataset) :**
- `name` : genere au format `User_000001` (clef de liaison interne)
- `session_date` : generee en remontant depuis aujourd'hui (1 jour par ligne)

**Anomalies connues et regles de qualite appliquees :**
- Age hors bornes (< 10 ou > 100 ans) → lignes supprimees
- Poids hors bornes (< 30 ou > 250 kg) → lignes supprimees
- Taille hors bornes (< 1.0 ou > 2.5 m) → lignes supprimees
- Calories_Burned > 3000 → lignes supprimees
- BPM hors bornes (< 30 ou > 250) → lignes supprimees
- Gender normalise en minuscules ('Male' → 'male')
- Taille convertie de metres en centimetres (x100)

---

### Source 3 — ExerciseDB (GitHub)

| Attribut | Valeur |
|----------|--------|
| **URL** | https://github.com/yuhonas/free-exercise-db |
| **Format** | JSON (tableau d'objets) |
| **Encodage** | UTF-8 |
| **Frequence de mise a jour** | Mise a jour communautaire (open source) |
| **Volume** | 1300+ exercices |
| **Licence** | MIT (libre de droits) |

**Structure JSON d'un exercice :**
```json
{
  "name": "barbell bench press",
  "category": "strength",
  "equipment": ["barbell"],
  "level": "intermediate",
  "primaryMuscles": ["chest"],
  "secondaryMuscles": ["shoulders", "triceps"],
  "instructions": ["Lie on bench...", "Lower the bar..."],
  "images": ["barbell-bench-press/0.jpg"]
}
```

**Colonnes exploitees :**

| Champ JSON source | Colonne cible (BDD) | Type | Description |
|-------------------|---------------------|------|-------------|
| name | exercises.name | VARCHAR | Nom de l'exercice |
| category | exercises.type | VARCHAR | Categorie (strength, cardio...) |
| equipment[0] | exercises.equipment | VARCHAR | Equipement principal |
| level | exercises.level | VARCHAR | Difficulte (beginner/intermediate/expert) |
| primaryMuscles[0] | exercises.muscle_group | VARCHAR | Muscle principal cible |
| instructions | exercises.instructions | TEXT | Etapes aplaties par " \| " |

**Anomalies connues et regles de qualite appliquees :**
- Champs optionnels absents (mechanic, force) → NULL en base
- Listes JSON (primaryMuscles, instructions) → aplaties en TEXT separe par " \| "
- Level 'advanced' → mappe vers 'expert' pour coherence avec la contrainte CHECK
- Doublons sur `name` → deduplication avant chargement
- Noms et types normalises en minuscules

**Pourquoi cette source est strategique :**
ExerciseDB est en format JSON, contrairement aux deux autres sources en CSV. Ce contraste demontre la competence "sources heterogenes" exigee par le cahier des charges (section III.1) : le pipeline ETL doit gerer deux formats distincts avec des structures differentes.

---

## 3. Diagramme de flux de donnees

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           SOURCES BRUTES                                    ║
║                                                                              ║
║  [Kaggle CSV #1]            [Kaggle CSV #2]         [GitHub JSON]           ║
║  Daily Food & Nutrition     Gym Members Exercise    ExerciseDB              ║
║  Dataset                    Dataset                 (1300+ exercices)       ║
╚══════════╤══════════════════════════╤═══════════════════╤════════════════════╝
           │                          │                   │
           ▼                          ▼                   ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                      PIPELINE ETL (etl/)                                    ║
║                                                                              ║
║  extract.py    ──▶  Lecture des fichiers bruts (CSV + JSON)                 ║
║                     Validation de la structure et des types                 ║
║                                                                              ║
║  transform.py  ──▶  Nettoyage des valeurs aberrantes                        ║
║                     Normalisation (minuscules, encodage)                    ║
║                     Generation des cles (name, log_date)                    ║
║                     Validation hors-bornes                                  ║
║                     Deduplication                                            ║
║                     Rapport qualite (QualityReport)                         ║
║                                                                              ║
║  load.py       ──▶  TRUNCATE des tables (idempotence)                       ║
║                     Resolution des FK (name → id)                           ║
║                     Insertion via COPY PostgreSQL                            ║
║                     Logs de chaque execution                                 ║
║                                                                              ║
║  pipeline.py   ──▶  Orchestration complete dans l'ordre des dependances     ║
╚══════════════════════════════╤═══════════════════════════════════════════════╝
                               │
                               ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║          BASE DE DONNEES RELATIONNELLE (PostgreSQL via Supabase)            ║
║                                                                              ║
║   users ──────────< workout_sessions                                        ║
║   users ──────────< food_logs >────────── foods                            ║
║   users ──────────< biometric_metrics                                       ║
║   workout_sessions < session_exercises >── exercises                        ║
╚══════════════════════════════╤═══════════════════════════════════════════════╝
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
╔══════════════════════╗         ╔═══════════════════════════╗
║   API REST (FastAPI) ║         ║  Dashboard (Metabase)     ║
║   /users             ║         ║  Metriques utilisateurs   ║
║   /nutrition         ║         ║  Analyses nutritionnelles ║
║   /exercises         ║         ║  Statistiques fitness     ║
║   /metrics           ║         ║  KPIs business            ║
╚══════════════════════╝         ╚═══════════════════════════╝
```

---

## 4. Automatisation et securite

### Planification (GitHub Actions)

Le pipeline ETL est automatise via `.github/workflows/etl.yml` :
- **Declenchement automatique** : tous les jours a 3h00 UTC (cron `0 3 * * *`)
- **Declenchement manuel** : via `workflow_dispatch` depuis l'interface GitHub
- **Declenchement sur push** : a chaque modification des fichiers `etl/`

### Securite des credentials

Les informations sensibles ne sont jamais committees dans le depot :
- `DATABASE_URL` → stocke dans les **GitHub Actions Secrets**
- `KAGGLE_USERNAME` et `KAGGLE_KEY` → stockes dans les **GitHub Actions Secrets**
- Le fichier `.env` est dans `.gitignore` — seul `env.example` est versionne
- Supabase impose SSL (`require`) sur toutes les connexions

### Idempotence du pipeline

A chaque execution, le pipeline :
1. Tronque toutes les tables dans l'ordre inverse des dependances FK
2. Recharge integrallement les donnees depuis les sources
3. Garantit un etat coherent meme en cas de re-execution multiple
