-- Schéma BDD HealthAI Coach
-- Doit rester aligné avec etl/transform.py et etl/config.py CONFLICT_KEYS.
-- Idempotent : peut être réexécuté à tout moment.

DROP TABLE IF EXISTS food_logs    CASCADE;
DROP TABLE IF EXISTS gym_sessions  CASCADE;
DROP TABLE IF EXISTS exercises     CASCADE;
DROP TABLE IF EXISTS users         CASCADE;


CREATE TABLE users (
    user_id           VARCHAR PRIMARY KEY,
    age               INTEGER,
    gender            VARCHAR,
    weight_kg         NUMERIC,
    height_m          NUMERIC,
    experience_level  INTEGER,
    bmi               NUMERIC
);


CREATE TABLE gym_sessions (
    user_id                       VARCHAR PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE,
    max_bpm                       INTEGER,
    avg_bpm                       INTEGER,
    resting_bpm                   INTEGER,
    session_duration_hours        NUMERIC,
    calories_burned               NUMERIC,
    workout_type                  VARCHAR,
    fat_percentage                NUMERIC,
    water_intake_liters           NUMERIC,
    workout_frequency_days_week   INTEGER
);


-- Pas de FK vers users : les user_id du dataset nutrition (FOOD_*) et ceux
-- du dataset gym (GYM_*) sont dans deux espaces de noms différents.
CREATE TABLE food_logs (
    user_id          VARCHAR NOT NULL,
    date             DATE    NOT NULL,
    meal_type        VARCHAR NOT NULL,
    food_item        VARCHAR NOT NULL,
    category         VARCHAR,
    calories_kcal    NUMERIC,
    protein_g        NUMERIC,
    carbohydrates_g  NUMERIC,
    fat_g            NUMERIC,
    fiber_g          NUMERIC,
    sugars_g         NUMERIC,
    sodium_mg        NUMERIC,
    cholesterol_mg   NUMERIC,
    water_intake_ml  NUMERIC,
    UNIQUE (user_id, date, meal_type, food_item)
);


CREATE TABLE exercises (
    id                 VARCHAR PRIMARY KEY,
    name               VARCHAR NOT NULL,
    force              VARCHAR,
    level              VARCHAR,
    mechanic           VARCHAR,
    equipment          VARCHAR,
    primary_muscles    TEXT,
    secondary_muscles  TEXT,
    instructions       TEXT,
    category           VARCHAR,
    images             TEXT
);


-- Index utiles pour les requêtes du dashboard
CREATE INDEX idx_food_logs_user_date  ON food_logs(user_id, date);
CREATE INDEX idx_food_logs_meal_type  ON food_logs(meal_type);
CREATE INDEX idx_gym_sessions_workout ON gym_sessions(workout_type);
CREATE INDEX idx_exercises_category   ON exercises(category);
CREATE INDEX idx_exercises_equipment  ON exercises(equipment);