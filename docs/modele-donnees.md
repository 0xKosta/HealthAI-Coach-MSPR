# Modele de donnees — HealthAI Coach

**MSPR Blocs 1, 2 & 3 — Role B : Data Modeler**
**Outil de modelisation :** dbdiagram.io
**Base de donnees :** PostgreSQL 15+ (Supabase / Docker)

> **MSPR3 :** le MCD/MLD MSPR1-2 (nutrition, fitness, biométrie) est inchangé. S’ajoutent
> `user_auth`, `posts`, `post_likes`, `post_comments` et `ai_requests` (migrations 001, 005, 006, 007).

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
| **COMPTE_AUTH** | Compte de connexion (email, JWT, plan, role) | MSPR3 |
| **PUBLICATION** | Post du feed social (texte et/ou media) | MSPR3 |
| **LIKE_PUBLICATION** | Like d’un utilisateur sur une publication | MSPR3 |
| **COMMENTAIRE** | Commentaire sur une publication | MSPR3 |
| **REQUETE_IA** | Historique des appels coach IA (OpenAI) | MSPR3 |

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

UTILISATEUR ──(0,1)──────────────── COMPTE_AUTH
            Un profil santé peut avoir au plus un compte de connexion.
            Un compte est lie a un seul profil users.

COMPTE_AUTH ──(1,n)──────────────── PUBLICATION
            Un compte publie zero ou plusieurs posts.

PUBLICATION ──(1,n)──────────────── LIKE_PUBLICATION
            Une publication recoit zero ou plusieurs likes.

COMPTE_AUTH ──(1,n)──────────────── LIKE_PUBLICATION
            Un compte peut liker plusieurs publications.

PUBLICATION ──(1,n)──────────────── COMMENTAIRE
            Une publication a zero ou plusieurs commentaires.

COMPTE_AUTH ──(1,n)──────────────── COMMENTAIRE
            Un compte redige zero ou plusieurs commentaires.

UTILISATEUR ──(1,n)──────────────── REQUETE_IA
            Historique des requetes coach IA par profil santé.
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

-- MSPR3 — authentification et reseau social

user_auth(
    id*             INTEGER  PK auto-incremente,
    user_id*        INTEGER  FK UNIQUE -> users(id),
    email*          VARCHAR(255) UNIQUE,
    password_hash*  TEXT,
    first_name*     VARCHAR(100),
    last_name*      VARCHAR(100),
    avatar_url      TEXT,
    role*           VARCHAR(20),   -- user | admin | demo
    plan*           VARCHAR(20),   -- free | premium | premium_plus
    created_at*     TIMESTAMPTZ,
    updated_at*     TIMESTAMPTZ
)

posts(
    id*           INTEGER  PK auto-incremente,
    author_id*    INTEGER  FK -> user_auth(id),
    content       TEXT,
    media_url     TEXT,
    media_type    VARCHAR(20),     -- image | video
    created_at*   TIMESTAMPTZ,
    updated_at*   TIMESTAMPTZ
)

post_likes(
    id*           INTEGER  PK auto-incremente,
    post_id*      INTEGER  FK -> posts(id),
    user_id*      INTEGER  FK -> user_auth(id),
    created_at*   TIMESTAMPTZ,
    UNIQUE(post_id, user_id)
)

post_comments(
    id*           INTEGER  PK auto-incremente,
    post_id*      INTEGER  FK -> posts(id),
    author_id*    INTEGER  FK -> user_auth(id),
    content*      TEXT,
    created_at*   TIMESTAMPTZ
)

ai_requests(
    id*             BIGINT   PK auto-incremente,
    user_id*        INTEGER  FK -> users(id),
    request_type*   VARCHAR(30),
    status*         VARCHAR(20),
    created_at*     TIMESTAMPTZ,
    input_summary   TEXT,
    output_summary  TEXT,
    input_json      JSONB,
    output_json     JSONB,
    photo_path      VARCHAR(500),
    error_message   TEXT,
    from_cache      BOOLEAN
)
```

---

## 3. MPD — Modele Physique de Donnees (DBML pour dbdiagram.io)

Coller ce code sur [dbdiagram.io](https://dbdiagram.io) pour regenerer le diagramme (MSPR1-2 + extension MSPR3) :

```
// --- MSPR 1/2 : nutrition, fitness, biométrie ---

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
  name_fr         varchar  [note: "FR"]
  type            varchar  [note: "EN"]
  type_fr         varchar  [note: "FR"]
  muscle_group    varchar  [note: "EN"]
  muscle_group_fr varchar  [note: "FR"]
  equipment       varchar  [note: "EN"]
  equipment_fr    varchar  [note: "FR"]
  level           varchar  [note: "EN"]
  level_fr        varchar  [note: "FR"]
  instructions    text     [note: "EN"]
  instructions_fr text     [note: "FR"]
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

// --- MSPR 3 : auth, feed social, historique IA ---

Table user_auth {
  id            integer   [pk, increment]
  user_id       integer   [ref: - users.id, unique, not null]
  email         varchar   [unique, not null]
  password_hash varchar   [not null]
  first_name    varchar   [not null]
  last_name     varchar   [not null]
  avatar_url    text
  role          varchar   [not null, default: 'user', note: 'user | admin | demo']
  plan          varchar   [not null, default: 'free', note: 'free | premium | premium_plus']
  created_at    timestamp [not null]
  updated_at    timestamp [not null]
}

Table posts {
  id          integer   [pk, increment]
  author_id   integer   [ref: > user_auth.id, not null]
  content     text
  media_url   text      [note: 'fichier local /media/posts/']
  media_type  varchar   [note: 'image | video']
  created_at  timestamp [not null]
  updated_at  timestamp [not null]
}

Table post_likes {
  id         integer   [pk, increment]
  post_id    integer   [ref: > posts.id, not null]
  user_id    integer   [ref: > user_auth.id, not null]
  created_at timestamp [not null]

  indexes {
    (post_id, user_id) [unique]
  }
}

Table post_comments {
  id         integer   [pk, increment]
  post_id    integer   [ref: > posts.id, not null]
  author_id  integer   [ref: > user_auth.id, not null]
  content    text      [not null]
  created_at timestamp [not null]
}

Table ai_requests {
  id             bigint    [pk, increment]
  user_id        integer   [ref: > users.id, not null]
  request_type   varchar   [not null, note: 'advice | analyze_photo | workout_plan | biometric_trend | meal_plan']
  status         varchar   [not null, default: 'success', note: 'success | error']
  created_at     timestamp [not null]
  input_summary  text
  output_summary text
  input_json     json
  output_json    json
  photo_path     varchar
  error_message  text
  from_cache     boolean   [not null, default: false]
}
```

---

## 4. Diagramme MCD

> Exporter le diagramme depuis dbdiagram.io en PNG et le placer ici :
> `docs/mcd.png` (ou `mcd.png` a la racine du repo)

Apres MSPR3 : regenerer le PNG pour inclure `user_auth`, `posts`, `post_likes`, `post_comments`, `ai_requests`.

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
