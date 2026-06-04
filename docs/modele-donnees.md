# Modele de donnees — HealthAI Coach

**MSPR Bloc 1 — Role B : Data Modeler**
**Outil de modelisation :** dbdiagram.io
**Base de donnees :** PostgreSQL 15 via Supabase

---

## 1. MCD — Modele Conceptuel de Donnees (Merise)

### Entites

| Entite | Description | Source |
|--------|-------------|--------|
| **UTILISATEUR** | Profil demographique et physique d'un membre | Gym Members Exercise Dataset (Kaggle, CSV) |
| **SEANCE_SPORT** | Session d'entrainement effectuee par un utilisateur | Gym Members Exercise Dataset (Kaggle, CSV) |
| **ALIMENT** | Fiche nutritionnelle d'un aliment (pour 100g) | Daily Food & Nutrition Dataset (Kaggle, CSV) |
| **JOURNAL_NUTRITION** | Ligne de consommation alimentaire quotidienne | Daily Food & Nutrition Dataset (Kaggle, CSV) |
| **EXERCICE** | Description d'un exercice sportif (catalogue) | ExerciseDB (GitHub, JSON) |
| **EXERCICE_SEANCE** | Liaison entre une seance et les exercices pratiques | Derive |
| **METRIQUE_BIOMETRIQUE** | Suivi biometrique temporel (poids, sommeil, FC repos) | Derive / futur wearable |

### Associations et cardinalites

```
UTILISATEUR ──(1,n)──────────────── SEANCE_SPORT
            Un utilisateur effectue une ou plusieurs seances.
            Une seance appartient a un seul utilisateur.

UTILISATEUR ──(1,n)──────────────── JOURNAL_NUTRITION
            Un utilisateur possede un ou plusieurs journaux.
            Un journal appartient a un seul utilisateur.

ALIMENT ────(1,n)──────────────── JOURNAL_NUTRITION
            Un aliment peut apparaitre dans plusieurs journaux.
            Un journal reference un seul aliment.

SEANCE_SPORT ──(1,n)────────────── EXERCICE_SEANCE
             Une seance inclut un ou plusieurs exercices.
             Un exercice_seance appartient a une seule seance.

EXERCICE ────(1,n)──────────────── EXERCICE_SEANCE
             Un exercice peut etre pratique dans plusieurs seances.
             Un exercice_seance reference un seul exercice.

UTILISATEUR ──(1,n)──────────────── METRIQUE_BIOMETRIQUE
            Un utilisateur possede un ou plusieurs enregistrements.
            Un enregistrement appartient a un seul utilisateur.
```

---

## 2. MLD — Modele Logique de Donnees

Notation : PK = cle primaire, FK = cle etrangere, * = obligatoire

```
users(
    id*           INTEGER     PK auto-incremente,
    name*         VARCHAR(100),
    age           INTEGER,      -- nullable a l'inscription ; 18-100 si renseigne
    gender        VARCHAR(10),
    weight_kg     FLOAT,        -- 20-300 kg si renseigne
    height_cm     FLOAT,        -- 90-230 cm si renseigne
    bmi           FLOAT,        -- 10-80 ; calcule serveur : poids / taille(m)^2
    body_fat_pct  FLOAT,
    goal          VARCHAR(50),
    created_at    DATE
)
-- Contraintes CHECK (init.sql + migration 004) — voir docs/validation-biometrique.md

foods(
    id*                INTEGER  PK auto-incremente,
    name*              VARCHAR(200),
    category           VARCHAR(100),
    calories_per_100g* FLOAT,
    proteins_g         FLOAT,
    carbs_g            FLOAT,
    fats_g             FLOAT,
    fiber_g            FLOAT
)

exercises(
    id*              INTEGER    PK auto-incremente,
    name*            VARCHAR(200),
    name_fr          VARCHAR(200),
    type             VARCHAR(100),
    type_fr          VARCHAR(100),
    muscle_group     VARCHAR(100),
    muscle_group_fr  VARCHAR(100),
    equipment        VARCHAR(100),
    equipment_fr     VARCHAR(100),
    level            VARCHAR(50),
    level_fr         VARCHAR(50),
    instructions     TEXT,
    instructions_fr  TEXT,
    gif_url          TEXT,
    video_url        TEXT,
    image_url        TEXT
)

food_logs(
    id*                INTEGER  PK auto-incremente,
    user_id*           INTEGER  FK -> users(id),
    food_id*           INTEGER  FK -> foods(id),
    log_date*          DATE,
    meal_type          VARCHAR(20),
    quantity_g*        FLOAT,
    calories_consumed  FLOAT
)

workout_sessions(
    id*              INTEGER  PK auto-incremente,
    user_id*         INTEGER  FK -> users(id),
    session_date*    DATE,
    duration_min     INTEGER,
    calories_burned  FLOAT,
    avg_bpm          FLOAT,
    max_bpm          FLOAT
)

session_exercises(
    id*           INTEGER  PK auto-incremente,
    session_id*   INTEGER  FK -> workout_sessions(id),
    exercise_id*  INTEGER  FK -> exercises(id),
    sets          INTEGER,
    reps          INTEGER,
    duration_sec  INTEGER
)

biometric_metrics(
    id*           INTEGER  PK auto-incremente,
    user_id*      INTEGER  FK -> users(id),
    record_date*  DATE,
    weight_kg     FLOAT,
    sleep_hours   FLOAT,
    resting_bpm   FLOAT,
    notes         TEXT
)
```

---

## 3. MPD — Modele Physique de Donnees (DBML pour dbdiagram.io)

Coller ce code sur [dbdiagram.io](https://dbdiagram.io) pour regenerer le diagramme :

```
Table users {
  id           integer   [pk, increment]
  name         varchar   [not null]
  age          integer
  gender       varchar
  weight_kg    decimal
  height_cm    decimal
  bmi          decimal
  body_fat_pct decimal
  goal         varchar
  created_at   date
}

Table foods {
  id                integer  [pk, increment]
  name              varchar  [not null]
  category          varchar
  calories_per_100g decimal  [not null]
  proteins_g        decimal
  carbs_g           decimal
  fats_g            decimal
  fiber_g           decimal
}

Table exercises {
  id              integer  [pk, increment]
  name            varchar  [not null, note: "EN"]
  name_fr         varchar  [note: "FR - traduction automatique"]
  type            varchar  [note: "EN"]
  type_fr         varchar  [note: "FR"]
  muscle_group    varchar  [note: "EN"]
  muscle_group_fr varchar  [note: "FR"]
  equipment       varchar  [note: "EN"]
  equipment_fr    varchar  [note: "FR"]
  level           varchar  [note: "EN - beginner / intermediate / expert"]
  level_fr        varchar  [note: "FR - debutant / intermediaire / expert"]
  instructions    text     [note: "EN"]
  instructions_fr text     [note: "FR - traduction automatique"]
  gif_url         text
  video_url       text
  image_url       text
}

Table food_logs {
  id                integer  [pk, increment]
  user_id           integer  [ref: > users.id]
  food_id           integer  [ref: > foods.id]
  log_date          date
  meal_type         varchar
  quantity_g        decimal
  calories_consumed decimal
}

Table workout_sessions {
  id              integer  [pk, increment]
  user_id         integer  [ref: > users.id]
  session_date    date
  duration_min    integer
  calories_burned decimal
  avg_bpm         decimal
  max_bpm         decimal
}

Table session_exercises {
  id           integer  [pk, increment]
  session_id   integer  [ref: > workout_sessions.id]
  exercise_id  integer  [ref: > exercises.id]
  sets         integer
  reps         integer
  duration_sec integer
}

Table biometric_metrics {
  id          integer  [pk, increment]
  user_id     integer  [ref: > users.id]
  record_date date
  weight_kg   decimal
  sleep_hours decimal
  resting_bpm decimal
  notes       text
}
```

---

## 4. Diagramme MCD

> Exporter le diagramme depuis dbdiagram.io en PNG et le placer ici :
> `docs/mcd.png`

![MCD HealthAI Coach](./mcd.png)

---

## 5. Justifications des choix de conception

### Internationalisation EN / FR de la table exercises

La table `exercises` embarque deux versions linguistiques pour chaque champ textuel :
les colonnes anglaises issues de la source ExerciseDB (`name`, `type`, `muscle_group`,
`equipment`, `level`, `instructions`) et leurs equivalents francais
(`name_fr`, `type_fr`, `muscle_group_fr`, `equipment_fr`, `level_fr`, `instructions_fr`)
generes par traduction automatique (bibliotheque `deep-translator`, moteur Google Translate).

L'API expose un parametre `?lang=en` (defaut) ou `?lang=fr` sur les endpoints
`GET /exercises` et `GET /exercises/{id}`. Le front-end n'a qu'a passer ce parametre
selon le choix de l'utilisateur dans la liste deroulante de langue.

Cette approche de **colonnes paralleles** a ete preferee a une table de traductions
separee pour sa simplicite d'interrogation (pas de JOIN supplementaire) et ses
performances en lecture.

---

### Pourquoi du relationnel (SQL) et pas du NoSQL ?

Le modele de donnees est fortement structure et relationnel :
- Les utilisateurs ont des profils fixes avec des types de donnees bien definis
- Les relations entre entites (utilisateur -> seance, aliment -> journal) sont claires et stables
- Les requetes analytiques du dashboard (GROUP BY, JOIN, agregations) sont nativement optimisees en SQL
- Les contraintes d'integrite (FK, CHECK) garantissent la qualite des donnees des l'insertion

Le NoSQL serait justifie uniquement pour les champs semi-structures : c'est pourquoi `exercises.instructions` est stocke en TEXT (liste aplatie) plutot qu'en JSONB, ce qui simplifie les requetes Metabase.

### Pourquoi separer `users` de `workout_sessions` ?

Un utilisateur peut avoir plusieurs seances dans le temps. Fusionner les deux en une seule table imposerait une ligne par seance avec les informations du profil repetees — violation de la 2NF. La separation garantit :
- Un profil unique par utilisateur (pas de duplication)
- Un historique illimite de seances
- Des mises a jour du profil sans impacter l'historique

### Pourquoi separer `foods` de `food_logs` ?

- `foods` est un **referentiel** : chaque aliment est unique, ses valeurs nutritionnelles sont fixes
- `food_logs` est un **fait** : une ligne par consommation (utilisateur x date x aliment x quantite)
- Cette separation evite de dupliquer les valeurs nutritionnelles a chaque log et permet une mise a jour centralisee du referentiel

### Pourquoi `biometric_metrics` est une table separee de `users` ?

Le poids, le sommeil et la frequence cardiaque au repos sont des donnees **temporelles** : elles evoluent dans le temps et doivent etre trackees sous forme d'historique. Les stocker dans `users` permettrait uniquement la valeur actuelle. La table separee permet de tracer la progression sur le temps — indispensable pour les modules IA de prediction.

L'ETL (`run_biometric_metrics`) ne simule l'historique que pour les utilisateurs ayant des `workout_sessions` (dataset Gym). Les comptes inscrits via l'app n'ont pas de courbe fictive injectee automatiquement.

### Pourquoi `session_exercises` comme table de liaison ?

La relation entre `workout_sessions` et `exercises` est **N-N** : une seance contient plusieurs exercices, et un exercice peut apparaitre dans plusieurs seances. Une table de liaison est la seule facon correcte de modeliser une relation N-N en relationnel, tout en portant les attributs specifiques a chaque occurrence (sets, reps, duree).

---

## 6. Validation biométrique du profil (API)

Le profil `users` est soumis a des **regles metier** a l'ecriture (POST/PUT, `PUT /auth/me/profile`) :

| Champ | Plage |
|-------|--------|
| age | 18 – 100 (null autorise tant que le profil n'est pas complete) |
| height_cm | 90 – 230 |
| weight_kg | 20 – 300 |
| bmi | 10 – 80, recalcule automatiquement |

En lecture (`GET /users/{id}`, `GET /auth/me/profile`), l'API renvoie les valeurs stockees et un champ **`profile_issues`** (liste de messages en francais) si des donnees legacy ou aberrantes sont presentes — sans erreur HTTP 500.

Les endpoints **`/coach/*`** refusent les appels si le profil est incomplet ou invalide (HTTP 400).

Documentation complete : [`validation-biometrique.md`](./validation-biometrique.md).
