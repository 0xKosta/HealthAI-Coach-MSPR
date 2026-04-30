-- =============================================================================
-- HealthAI Coach — Seed données dérivées
-- Role B : Data Modeler
--
-- Peuple les 2 tables sans source directe en utilisant les vraies données
-- déjà en base (users, workout_sessions, exercises).
--
-- Données de départ (réelles) :
--   - users.weight_kg       → utilisé dans biometric_metrics
--   - workout_sessions.avg_bpm / calories_burned → utilisé dans biometric_metrics
--   - workout_sessions.workout_type → utilisé pour choisir des exercices cohérents
--   - exercises.type        → filtré par workout_type de la session
--
-- Conformément au cahier des charges section III.1 :
-- "données biométriques simulées comme poids, sommeil, fréquence cardiaque"
--
-- A exécuter APRÈS le pipeline ETL (python -m etl.pipeline)
-- =============================================================================


-- =============================================================================
-- TABLE : session_exercises
-- Principe : pour chaque session, on sélectionne 3 exercices dont le type
-- correspond au workout_type de la session (cardio → cardio, strength → strength)
-- Source des workout_type : workout_sessions (vraies données Gym Members CSV)
-- Source des exercices    : exercises (vraies données ExerciseDB JSON)
-- =============================================================================
INSERT INTO session_exercises (session_id, exercise_id, sets, reps, duration_sec)
SELECT
    ws.id                                               AS session_id,
    e.id                                                AS exercise_id,
    -- Nombre de séries basé sur le type d'entrainement
    CASE
        WHEN ws.workout_type = 'cardio'     THEN 1
        WHEN ws.workout_type = 'strength'   THEN (FLOOR(RANDOM() * 3) + 3)::INT
        WHEN ws.workout_type = 'hiit'       THEN (FLOOR(RANDOM() * 2) + 4)::INT
        WHEN ws.workout_type = 'yoga'       THEN 1
        ELSE (FLOOR(RANDOM() * 3) + 2)::INT
    END                                                 AS sets,
    -- Répétitions basées sur le type
    CASE
        WHEN ws.workout_type IN ('cardio', 'yoga') THEN NULL
        ELSE (FLOOR(RANDOM() * 8) + 8)::INT
    END                                                 AS reps,
    -- Durée pour les exercices cardio et yoga
    CASE
        WHEN ws.workout_type IN ('cardio', 'yoga')
        THEN (FLOOR(ws.duration_min * 60.0 / 3))::INT  -- divise la durée totale par 3 exercices
        ELSE NULL
    END                                                 AS duration_sec
FROM workout_sessions ws
CROSS JOIN LATERAL (
    -- Sélectionne 3 exercices du même type que la session
    -- Si pas assez d'exercices du bon type, prend n'importe quel exercice
    (
        SELECT id FROM exercises
        WHERE LOWER(type) = LOWER(ws.workout_type)
        ORDER BY RANDOM()
        LIMIT 3
    )
    UNION ALL
    (
        SELECT id FROM exercises
        WHERE LOWER(type) != LOWER(ws.workout_type)
        ORDER BY RANDOM()
        LIMIT 3
    )
    LIMIT 3
) e
WHERE ws.duration_min IS NOT NULL;


-- =============================================================================
-- TABLE : biometric_metrics
-- Principe : utilise les vraies valeurs de weight_kg depuis users,
-- et dérive resting_bpm depuis les séances réelles de l'utilisateur.
-- Génère 1 enregistrement par semaine sur les 12 dernières semaines.
--
-- Source : users.weight_kg (vraie donnée Kaggle)
--          workout_sessions.avg_bpm (vraie donnée Kaggle, utilisée pour dériver FC repos)
-- =============================================================================
INSERT INTO biometric_metrics (user_id, record_date, weight_kg, sleep_hours, resting_bpm)
SELECT
    u.id                                                            AS user_id,
    CURRENT_DATE - (n * 7 || ' days')::INTERVAL                    AS record_date,
    -- Poids réel de l'utilisateur avec légère variation hebdomadaire (±0.5 kg)
    ROUND(
        (u.weight_kg + (RANDOM() * 1.0 - 0.5))::NUMERIC, 1
    )                                                               AS weight_kg,
    -- Sommeil entre 6h et 9h (données simulées, aucun dataset disponible)
    ROUND((6.0 + RANDOM() * 3.0)::NUMERIC, 1)                     AS sleep_hours,
    -- FC repos dérivée de la FC moyenne des séances : environ 60% de avg_bpm
    -- Si aucune séance, valeur par défaut selon expérience
    COALESCE(
        ROUND((avg_session.avg_bpm * 0.60)::NUMERIC, 0),
        CASE u.experience_level
            WHEN 3 THEN 50 + (RANDOM() * 10)::INT   -- Avancé : FC repos basse
            WHEN 2 THEN 58 + (RANDOM() * 10)::INT   -- Intermédiaire
            ELSE        65 + (RANDOM() * 15)::INT   -- Débutant : FC repos plus haute
        END
    )                                                               AS resting_bpm
FROM users u
CROSS JOIN generate_series(0, 11) AS n   -- 12 semaines
LEFT JOIN (
    -- FC moyenne réelle par utilisateur depuis les séances
    SELECT user_id, AVG(avg_bpm) AS avg_bpm
    FROM workout_sessions
    WHERE avg_bpm IS NOT NULL
    GROUP BY user_id
) avg_session ON avg_session.user_id = u.id
WHERE u.weight_kg IS NOT NULL;


-- =============================================================================
-- VERIFICATION FINALE
-- =============================================================================
SELECT
    'session_exercises'             AS table_name,
    COUNT(*)                        AS lignes_inserees,
    COUNT(DISTINCT session_id)      AS sessions_couvertes,
    COUNT(DISTINCT exercise_id)     AS exercices_distincts
FROM session_exercises
UNION ALL
SELECT
    'biometric_metrics',
    COUNT(*),
    COUNT(DISTINCT user_id),
    COUNT(DISTINCT record_date)
FROM biometric_metrics;
