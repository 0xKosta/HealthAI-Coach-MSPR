Jedael
jaedael
Invisible

Jedael
 a changé le nom du groupe : MSPR. Modifier le groupe — 28/04/2026 13:08
Jedael — 28/04/2026 13:12
à titre indicatif
Jedael — 28/04/2026 13:22
Type de fichier joint : acrobat
MSPR_Bloc1_Plan.pdf
13.64 KB
nouvelle version avec GitHub Actions pour le workflow
Jedael — Hier à 11:36
Les 3 dataset proposés :
https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset
https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset
https://github.com/ExerciseDB/exercisedb-api/tree/main
Daily Food & Nutrition Dataset
Track daily food intake and nutritional values for a health-related ML model.
Image
Gym Members Exercise Dataset
Analyzing Fitness Patterns and Performance Across Diverse Gym Experience Levels
Image
GitHub
GitHub - ExerciseDB/exercisedb-api: ExerciseDB API is an fitness ex...
ExerciseDB API is an fitness exercise database api that allows users to access high-quality exercises data which consists 11000+ exercises. This API offers extensive information on each exercise, i...
ExerciseDB API is an fitness exercise database api that allows users to access high-quality exercises data which consists 11000+ exercises. This API offers extensive information on each exercise, i...
Jedael — Hier à 13:02

Pourquoi du relationnel et pas du NoSQL ?
Les données sont fortement structurées et reliées entre elles. Le relationnel garantit l'intégrité référentielle (on ne peut pas créer un food_log avec un user_id qui n'existe pas). NoSQL serait pertinent pour les données biométriques en temps réel à haute fréquence
Jean-Charles — Hier à 13:11

Jean-Charles — Hier à 13:21
Image
Image
Jedael — Hier à 13:27
Image
Jedael
 a épinglé un message dans ce salon. Voir tous les messages épinglés. — Hier à 13:29
Jedael — Hier à 13:29
dbdiagram @ismail
pour initialiser la base supabase @ismail
-- =============================================================================
-- HealthAI Coach — Script d'initialisation de la base de données
-- MSPR Bloc 1 — Équipe de 4
-- Base : PostgreSQL (Supabase)
--
-- Usage :

init.sql
10 Ko
Jean-Charles — Hier à 13:38
Image
Image
Image
Image
Jedael — Hier à 15:40
@ismail
Image
Il va me falloir ça depuis la Supabase quand tu l'aura configuré
Jean-Charles — Hier à 16:14
tu as pu faire @ismail  j'en ai besoin pour commencer ma partie sinon je suis bloqué
ismail — Hier à 16:16
Je ne l’ai pas fini
Je le fais ce soir
Jean-Charles — Hier à 16:16
tié un tigre
Jedael — Hier à 16:25
Image
Image
Jedael — 09:28
Isma we need you
ismail — 09:28
Oui j’arrive
Jedael — 10:25
remplacez dans votre .env DATABASE_URL par :
postgresql+psycopg2://postgres:vmSUBxbPW9X5xQiu@db.tvfqosrefzpvekamitem.supabase.co:5432/postgres
Image
Jedael — 13:21
Reste à faire :
Rôle A (Kosta) : Finaliser ETL + Charger Données dans Supabase
Rôle B (Isma) : Rapport d'inventaire + Rapport Technique + queries.sql
Rôle D (JC) :  Configurer Metabase dès le chargement des données
kosta — 13:44
postgresql+psycopg2://postgres:vmSUBxbPW9X5xQiu@db.tvfqosrefzpvekamitem.supabase.co:5432/postgres
ismail — 14:06
postgresql://postgres.tvfqosrefzpvekamitem:[YOUR-PASSWORD]@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
password:vmSUBxbPW9X5xQiu
kosta — 14:07
postgresql://postgres.tvfqosrefzpvekamitem:vmSUBxbPW9X5xQiu@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
 
Jedael — 14:12
La différence
Ton URL (connexion directe) :
postgresql://postgres:[mdp]@db.tvfqosrefzpvekamitem.supabase.co:5432/postgres
Connexion directe à PostgreSQL. Chaque appel ouvre une vraie connexion réseau. Idéal pour des scripts qui tournent ponctuellement — comme un pipeline ETL.
Son URL (connection pooler) :
postgresql://postgres.tvfqosrefzpvekamitem:[mdp]@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
Passe par PgBouncer, un gestionnaire de pool de connexions de Supabase. Il mutualise les connexions pour éviter de saturer PostgreSQL. Recommandé pour les applications web avec beaucoup de requêtes simultanées.

Pourquoi ça marche pour lui et pas l'inverse
Le pipeline ETL du Rôle A fait des connexions longues et ponctuelles — le pooler peut parfois les couper. La connexion directe est plus stable pour ce cas.
Ton API FastAPI avec SQLAlchemy gère déjà son propre pool de connexions en interne — donc la connexion directe est aussi ce qu'il te faut.

Conclusion
QuiURL à utiliserPourquoiToi (Rôle C) — FastAPIConnexion directe (db.tvfq...)SQLAlchemy gère son propre poolRôle A — ETL PythonPooler (pooler.supabase.com)Plus stable pour ses scriptsRôle D — MetabaseL'une ou l'autreMetabase gère bien les deux
Chacun garde l'URL qui marche pour lui dans son .env local — c'est exactement pour ça que le .env est personnel et non committé sur GitHub.
Jedael — 14:18
utilisez celui ci dans votre .env comme DATABASE URL
jedael.dev@gmail.com
kosta — 14:19
konstantin.andjelkovic03@gmail.com
Jean-Charles — 14:19
jcrousseaupro@outlook.com
Jean-Charles — 14:28
jcrousseaupro@free.fr
﻿
-- =============================================================================
-- HealthAI Coach — Script d'initialisation de la base de données
-- MSPR Bloc 1 — Équipe de 4
-- Base : PostgreSQL (Supabase)
--
-- Usage :
--   Lancer ce script une seule fois pour créer toute la structure.
--   psql -h <host> -U <user> -d <dbname> -f init.sql
--
-- Ordre d'exécution :
--   1. Tables sans dépendances (users, foods, exercises)
--   2. Tables avec clés étrangères (food_logs, workout_sessions, biometric_metrics)
--   3. Table de liaison (session_exercises)
-- =============================================================================


-- Supprimer les tables dans l'ordre inverse si elles existent déjà
-- (utile pour relancer proprement le script en dev)
DROP TABLE IF EXISTS session_exercises   CASCADE;
DROP TABLE IF EXISTS food_logs           CASCADE;
DROP TABLE IF EXISTS biometric_metrics   CASCADE;
DROP TABLE IF EXISTS workout_sessions    CASCADE;
DROP TABLE IF EXISTS exercises           CASCADE;
DROP TABLE IF EXISTS foods               CASCADE;
DROP TABLE IF EXISTS users               CASCADE;


-- =============================================================================
-- TABLE : users
-- Source : Gym Members Exercise Dataset (Kaggle, CSV)
-- Contient les profils statiques des utilisateurs
-- =============================================================================
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    age             INT             NOT NULL CHECK (age >= 0 AND age <= 120),
    gender          VARCHAR(10)     CHECK (gender IN ('male', 'female', 'other')),
    weight_kg       FLOAT           CHECK (weight_kg > 0),
    height_cm       FLOAT           CHECK (height_cm > 0),
    bmi             FLOAT,          -- calculé à l'ingestion par le pipeline ETL
    body_fat_pct    FLOAT           CHECK (body_fat_pct >= 0 AND body_fat_pct <= 100),
    goal            VARCHAR(50)     CHECK (goal IN (
                                        'weight_loss',
                                        'muscle_gain',
                                        'sleep_improvement',
                                        'maintenance'
                                    )),
    created_at      DATE            NOT NULL DEFAULT CURRENT_DATE
);

COMMENT ON TABLE  users             IS 'Profils utilisateurs — source : Gym Members Exercise Dataset';
COMMENT ON COLUMN users.bmi         IS 'Indice de masse corporelle, calculé par le pipeline ETL : weight_kg / (height_m)^2';
COMMENT ON COLUMN users.goal        IS 'Objectif principal : weight_loss, muscle_gain, sleep_improvement, maintenance';


-- =============================================================================
-- TABLE : foods
-- Source : Daily Food & Nutrition Dataset (Kaggle, CSV)
-- Catalogue des aliments avec valeurs nutritionnelles pour 100g
-- =============================================================================
CREATE TABLE foods (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(200)    NOT NULL,
    category            VARCHAR(100),   -- ex : fruits, légumes, viandes, céréales...
    calories_per_100g   FLOAT           NOT NULL CHECK (calories_per_100g >= 0),
    proteins_g          FLOAT           CHECK (proteins_g >= 0),
    carbs_g             FLOAT           CHECK (carbs_g >= 0),
    fats_g              FLOAT           CHECK (fats_g >= 0),
    fiber_g             FLOAT           CHECK (fiber_g >= 0)
);

COMMENT ON TABLE  foods                   IS 'Catalogue nutritionnel — source : Daily Food & Nutrition Dataset';
COMMENT ON COLUMN foods.calories_per_100g IS 'Valeur calorique pour 100g de produit';


-- =============================================================================
-- TABLE : exercises
-- Source : ExerciseDB (GitHub, JSON)
-- Catalogue de 1300+ exercices sportifs
-- =============================================================================
CREATE TABLE exercises (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200)    NOT NULL,
    type            VARCHAR(100),   -- cardio, strength, flexibility, balance...
    muscle_group    VARCHAR(100),   -- chest, back, legs, shoulders, core...
    equipment       VARCHAR(100),   -- barbell, dumbbell, bodyweight, cable...
    level           VARCHAR(50)     CHECK (level IN ('beginner', 'intermediate', 'expert')),
    instructions    TEXT
);

COMMENT ON TABLE  exercises              IS 'Catalogue d''exercices — source : ExerciseDB (GitHub, format JSON)';
COMMENT ON COLUMN exercises.muscle_group IS 'Groupe musculaire principal ciblé';
COMMENT ON COLUMN exercises.level        IS 'Niveau de difficulté : beginner, intermediate, expert';


-- =============================================================================
-- TABLE : food_logs
-- Historique des repas journaliers par utilisateur
-- Relation N-N résolue : un utilisateur -> plusieurs entrées par jour
-- =============================================================================
CREATE TABLE food_logs (
    id                  SERIAL PRIMARY KEY,
    user_id             INT             NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    food_id             INT             NOT NULL REFERENCES foods(id)  ON DELETE RESTRICT,
    log_date            DATE            NOT NULL DEFAULT CURRENT_DATE,
    meal_type           VARCHAR(20)     CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    quantity_g          FLOAT           NOT NULL CHECK (quantity_g > 0),
    -- calories_consumed est calculé à l'ingestion pour éviter les incohérences
    calories_consumed   FLOAT           CHECK (calories_consumed >= 0)
);

COMMENT ON TABLE  food_logs                  IS 'Journal alimentaire journalier par utilisateur';
COMMENT ON COLUMN food_logs.calories_consumed IS 'Calculé par ETL : (foods.calories_per_100g / 100) * quantity_g';

-- Index pour accélérer les requêtes analytics du dashboard (filtres par user + date)
CREATE INDEX idx_food_logs_user_date ON food_logs (user_id, log_date);


-- =============================================================================
-- TABLE : workout_sessions
-- Sessions d'entraînement d'un utilisateur
-- Source : Gym Members Exercise Dataset (Kaggle, CSV)
-- =============================================================================
CREATE TABLE workout_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_date    DATE            NOT NULL DEFAULT CURRENT_DATE,
    duration_min    INT             CHECK (duration_min > 0),
    calories_burned FLOAT           CHECK (calories_burned >= 0),
    avg_bpm         FLOAT           CHECK (avg_bpm > 0),
    max_bpm         FLOAT           CHECK (max_bpm > 0)
);

COMMENT ON TABLE  workout_sessions          IS 'Sessions d''entraînement — source : Gym Members Exercise Dataset';
COMMENT ON COLUMN workout_sessions.avg_bpm  IS 'Fréquence cardiaque moyenne durant la session';
COMMENT ON COLUMN workout_sessions.max_bpm  IS 'Fréquence cardiaque maximale atteinte';

CREATE INDEX idx_workout_sessions_user_date ON workout_sessions (user_id, session_date);


-- =============================================================================
-- TABLE : session_exercises
-- Table de liaison N-N entre workout_sessions et exercises
-- Porte les données propres à chaque occurrence (sets, reps, durée)
-- =============================================================================
CREATE TABLE session_exercises (
    id              SERIAL PRIMARY KEY,
    session_id      INT     NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id     INT     NOT NULL REFERENCES exercises(id)        ON DELETE RESTRICT,
    sets            INT     CHECK (sets > 0),
    reps            INT     CHECK (reps > 0),
    -- duration_sec pour les exercices à durée (planche, cardio continu...)
    duration_sec    INT     CHECK (duration_sec > 0)
);

COMMENT ON TABLE  session_exercises             IS 'Liaison N-N : exercices pratiqués par session';
COMMENT ON COLUMN session_exercises.duration_sec IS 'Durée en secondes, pour les exercices chronométrés (planche, cardio...)';


-- =============================================================================
-- TABLE : biometric_metrics
-- Suivi biométrique dans le temps, séparé du profil statique users
-- Les données évoluent dans le temps → table dédiée pour l'historique
-- =============================================================================
CREATE TABLE biometric_metrics (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    record_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    weight_kg       FLOAT           CHECK (weight_kg > 0),
    sleep_hours     FLOAT           CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    resting_bpm     FLOAT           CHECK (resting_bpm > 0),
    notes           TEXT
);

COMMENT ON TABLE  biometric_metrics         IS 'Suivi biométrique temporel — données évolutives séparées du profil statique';
COMMENT ON COLUMN biometric_metrics.notes   IS 'Observations libres : fatigue, maladie, conditions particulières';

CREATE INDEX idx_biometric_user_date ON biometric_metrics (user_id, record_date);


-- =============================================================================
-- VÉRIFICATION FINALE
-- Liste les tables créées pour confirmer que tout s'est bien passé
-- =============================================================================
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = t.table_name
     AND table_schema = 'public') AS nb_colonnes
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
init.sql
10 Ko