-- =============================================================================
-- HealthAI Coach — Script d'initialisation de la base de données
-- MSPR Bloc 1
-- Base : PostgreSQL (Supabase)
--
-- Usage :
--   Lancer ce script une seule fois pour créer toute la structure Supabase.
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