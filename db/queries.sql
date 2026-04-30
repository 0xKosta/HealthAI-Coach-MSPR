-- =============================================================================
-- HealthAI Coach — Requetes analytiques pour le dashboard Metabase
-- Role B : Data Modeler
-- Base : PostgreSQL (Supabase)
--
-- Ces requetes alimentent directement les visualisations Metabase (Role D).
-- Chaque requete est prete a etre copiee dans une "Question" Metabase.
--
-- BLOC 1 : Metriques utilisateurs  (Q1  a Q5)
-- BLOC 2 : Analyses nutritionnelles (Q6  a Q10)
-- BLOC 3 : Statistiques fitness     (Q11 a Q15)
-- BLOC 4 : KPIs business            (Q16 a Q19)
-- =============================================================================


-- =============================================================================
-- BLOC 1 - METRIQUES UTILISATEURS
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1 : Repartition des utilisateurs par tranche d'age
-- Graphique recommande : bar chart
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN age < 20              THEN 'Moins de 20 ans'
        WHEN age BETWEEN 20 AND 29 THEN '20-29 ans'
        WHEN age BETWEEN 30 AND 39 THEN '30-39 ans'
        WHEN age BETWEEN 40 AND 49 THEN '40-49 ans'
        WHEN age BETWEEN 50 AND 59 THEN '50-59 ans'
        ELSE '60 ans et plus'
    END                                                     AS tranche_age,
    COUNT(*)                                                AS nb_utilisateurs,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)     AS pourcentage
FROM users
WHERE age IS NOT NULL
GROUP BY tranche_age
ORDER BY MIN(age);


-- ----------------------------------------------------------------------------
-- Q2 : Repartition par genre
-- Graphique recommande : pie chart
-- ----------------------------------------------------------------------------
SELECT
    gender                                                  AS genre,
    COUNT(*)                                                AS nb_utilisateurs,
    ROUND(AVG(bmi), 1)                                      AS imc_moyen,
    ROUND(AVG(weight_kg), 1)                                AS poids_moyen_kg,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)     AS pourcentage
FROM users
WHERE gender IS NOT NULL
GROUP BY gender
ORDER BY nb_utilisateurs DESC;


-- ----------------------------------------------------------------------------
-- Q3 : Repartition par niveau d'experience
-- Graphique recommande : bar chart horizontal
-- ----------------------------------------------------------------------------
SELECT
    CASE experience_level
        WHEN 1 THEN '1 - Debutant'
        WHEN 2 THEN '2 - Intermediaire'
        WHEN 3 THEN '3 - Avance'
        ELSE 'Non renseigne'
    END                                                     AS niveau,
    COUNT(*)                                                AS nb_utilisateurs,
    ROUND(AVG(bmi), 1)                                      AS imc_moyen,
    ROUND(AVG(weight_kg), 1)                                AS poids_moyen_kg,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)     AS pourcentage
FROM users
GROUP BY experience_level
ORDER BY experience_level;


-- ----------------------------------------------------------------------------
-- Q4 : Profil moyen de l'utilisateur (scorecard)
-- Graphique recommande : metriques cles / scorecard
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*)                        AS total_utilisateurs,
    ROUND(AVG(age), 0)              AS age_moyen,
    ROUND(AVG(bmi), 1)              AS imc_moyen,
    ROUND(AVG(weight_kg), 1)        AS poids_moyen_kg,
    ROUND(AVG(height_cm) / 100, 2)  AS taille_moyenne_m
FROM users;


-- ----------------------------------------------------------------------------
-- Q5 : Distribution de l'IMC selon les categories OMS
-- Graphique recommande : bar chart
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN bmi < 18.5                THEN 'Insuffisance ponderale (< 18.5)'
        WHEN bmi BETWEEN 18.5 AND 24.9 THEN 'Poids normal (18.5 - 24.9)'
        WHEN bmi BETWEEN 25.0 AND 29.9 THEN 'Surpoids (25 - 29.9)'
        WHEN bmi >= 30                 THEN 'Obesite (30 et plus)'
        ELSE 'Non renseigne'
    END                                                     AS categorie_imc,
    COUNT(*)                                                AS nb_utilisateurs,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)     AS pourcentage
FROM users
WHERE bmi IS NOT NULL
GROUP BY categorie_imc
ORDER BY MIN(bmi);


-- =============================================================================
-- BLOC 2 - ANALYSES NUTRITIONNELLES
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q6 : Top 15 aliments les plus consommes
-- Graphique recommande : bar chart horizontal
-- ----------------------------------------------------------------------------
SELECT
    f.name                          AS aliment,
    f.category                      AS categorie,
    COUNT(fl.id)                    AS nb_occurrences,
    ROUND(AVG(f.calories_per_100g), 0) AS calories_moyennes_pour_100g,
    ROUND(AVG(f.proteins_g), 1)     AS proteines_g
FROM food_logs fl
JOIN foods f ON f.id = fl.food_id
GROUP BY f.name, f.category
ORDER BY nb_occurrences DESC
LIMIT 15;


-- ----------------------------------------------------------------------------
-- Q7 : Repartition des repas par type (meal_type)
-- Graphique recommande : pie chart
-- ----------------------------------------------------------------------------
SELECT
    meal_type                       AS type_repas,
    COUNT(*)                        AS nb_entrees,
    ROUND(AVG(calories_consumed), 0) AS calories_moyennes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
FROM food_logs
WHERE meal_type IS NOT NULL
GROUP BY meal_type
ORDER BY nb_entrees DESC;


-- ----------------------------------------------------------------------------
-- Q8 : Tendance calorique par categorie d'aliments
-- Graphique recommande : bar chart
-- ----------------------------------------------------------------------------
SELECT
    f.category                          AS categorie,
    COUNT(DISTINCT f.id)                AS nb_aliments_distincts,
    COUNT(fl.id)                        AS nb_consommations,
    ROUND(AVG(f.calories_per_100g), 0)  AS calories_moyennes_100g,
    ROUND(AVG(f.proteins_g), 1)         AS proteines_g,
    ROUND(AVG(f.carbs_g), 1)            AS glucides_g,
    ROUND(AVG(f.fats_g), 1)             AS lipides_g,
    ROUND(AVG(f.fiber_g), 1)            AS fibres_g
FROM food_logs fl
JOIN foods f ON f.id = fl.food_id
WHERE f.category IS NOT NULL
GROUP BY f.category
ORDER BY nb_consommations DESC;


-- ----------------------------------------------------------------------------
-- Q9 : Analyse des macronutriments - equilibre global
-- Graphique recommande : stacked bar ou pie chart
-- ----------------------------------------------------------------------------
SELECT
    ROUND(AVG(f.calories_per_100g), 0)  AS calories_moyennes_100g,
    ROUND(AVG(f.proteins_g), 1)         AS proteines_moyennes_g,
    ROUND(AVG(f.carbs_g), 1)            AS glucides_moyens_g,
    ROUND(AVG(f.fats_g), 1)             AS lipides_moyens_g,
    ROUND(AVG(f.fiber_g), 1)            AS fibres_moyennes_g,
    -- Part de chaque macronutriment dans les calories totales
    ROUND(AVG(f.proteins_g) * 4 * 100.0
          / NULLIF(AVG(f.calories_per_100g), 0), 1) AS pct_calories_proteines,
    ROUND(AVG(f.carbs_g) * 4 * 100.0
          / NULLIF(AVG(f.calories_per_100g), 0), 1) AS pct_calories_glucides,
    ROUND(AVG(f.fats_g) * 9 * 100.0
          / NULLIF(AVG(f.calories_per_100g), 0), 1) AS pct_calories_lipides
FROM food_logs fl
JOIN foods f ON f.id = fl.food_id
WHERE f.calories_per_100g > 0;


-- ----------------------------------------------------------------------------
-- Q10 : Evolution des logs nutritionnels dans le temps (serie temporelle)
-- Graphique recommande : line chart
-- ----------------------------------------------------------------------------
SELECT
    log_date                        AS jour,
    COUNT(DISTINCT user_id)         AS utilisateurs_actifs,
    COUNT(*)                        AS nb_entrees_alimentaires,
    ROUND(AVG(calories_consumed), 0) AS calories_consommees_moyennes
FROM food_logs
GROUP BY log_date
ORDER BY log_date;


-- =============================================================================
-- BLOC 3 - STATISTIQUES FITNESS
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q11 : Repartition des types d'entrainement
-- Graphique recommande : bar chart ou pie chart
-- ----------------------------------------------------------------------------
SELECT
    ws.workout_type                 AS type_entrainement,
    COUNT(*)                        AS nb_sessions,
    ROUND(AVG(ws.calories_burned), 0)   AS calories_moyennes,
    ROUND(AVG(ws.duration_min), 0)      AS duree_moyenne_min,
    ROUND(AVG(ws.avg_bpm), 0)           AS bpm_moyen,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
FROM workout_sessions ws
WHERE ws.workout_type IS NOT NULL
GROUP BY ws.workout_type
ORDER BY nb_sessions DESC;


-- ----------------------------------------------------------------------------
-- Q12 : Intensite des seances par niveau d'experience
-- Graphique recommande : grouped bar chart
-- ----------------------------------------------------------------------------
SELECT
    CASE u.experience_level
        WHEN 1 THEN 'Debutant'
        WHEN 2 THEN 'Intermediaire'
        WHEN 3 THEN 'Avance'
    END                                     AS niveau,
    COUNT(ws.id)                            AS nb_sessions,
    ROUND(AVG(ws.avg_bpm), 0)              AS bpm_moyen,
    ROUND(AVG(ws.max_bpm), 0)              AS bpm_max_moyen,
    ROUND(AVG(ws.calories_burned), 0)      AS calories_moyennes,
    ROUND(AVG(ws.duration_min), 0)         AS duree_moyenne_min
FROM users u
JOIN workout_sessions ws ON ws.user_id = u.id
GROUP BY u.experience_level
ORDER BY u.experience_level;


-- ----------------------------------------------------------------------------
-- Q13 : Repartition des exercices du catalogue par categorie (type)
-- Graphique recommande : bar chart horizontal
-- ----------------------------------------------------------------------------
SELECT
    type                            AS categorie,
    COUNT(*)                        AS nb_exercices,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
FROM exercises
WHERE type IS NOT NULL
GROUP BY type
ORDER BY nb_exercices DESC;


-- ----------------------------------------------------------------------------
-- Q14 : Repartition des exercices par niveau de difficulte
-- Graphique recommande : bar chart
-- ----------------------------------------------------------------------------
SELECT
    level                           AS niveau_difficulte,
    COUNT(*)                        AS nb_exercices,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
FROM exercises
WHERE level IS NOT NULL
GROUP BY level
ORDER BY nb_exercices DESC;


-- ----------------------------------------------------------------------------
-- Q15 : Equipements les plus representes dans le catalogue
-- Graphique recommande : bar chart horizontal
-- ----------------------------------------------------------------------------
SELECT
    equipment                       AS equipement,
    COUNT(*)                        AS nb_exercices,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pourcentage
FROM exercises
WHERE equipment IS NOT NULL
GROUP BY equipment
ORDER BY nb_exercices DESC
LIMIT 15;


-- =============================================================================
-- BLOC 4 - KPIs BUSINESS
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q16 : Engagement global - activite nutritionnelle
-- Graphique recommande : scorecard
-- ----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT user_id)         AS utilisateurs_actifs_nutrition,
    COUNT(*)                        AS total_logs_alimentaires,
    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT user_id), 0), 1)
                                    AS logs_par_utilisateur,
    MIN(log_date)                   AS premiere_entree,
    MAX(log_date)                   AS derniere_entree,
    MAX(log_date) - MIN(log_date)   AS periode_couverte_jours
FROM food_logs;


-- ----------------------------------------------------------------------------
-- Q17 : Engagement fitness - calories brulees par type d'entrainement
-- Graphique recommande : bar chart
-- ----------------------------------------------------------------------------
SELECT
    ws.workout_type                 AS type_entrainement,
    COUNT(DISTINCT ws.user_id)      AS utilisateurs_uniques,
    ROUND(AVG(ws.calories_burned), 0)  AS calories_moyennes,
    ROUND(SUM(ws.calories_burned), 0)  AS calories_totales,
    ROUND(AVG(ws.duration_min), 0)     AS duree_moyenne_min
FROM workout_sessions ws
WHERE ws.workout_type IS NOT NULL
GROUP BY ws.workout_type
ORDER BY calories_totales DESC;


-- ----------------------------------------------------------------------------
-- Q18 : Vue consolidee utilisateur - export pour modules IA
-- Usage : export CSV depuis Metabase, base de travail pour la prediction IA
-- ----------------------------------------------------------------------------
SELECT
    u.id,
    u.name,
    u.age,
    u.gender,
    u.weight_kg,
    u.height_cm,
    u.bmi,
    u.body_fat_pct,
    u.experience_level,
    ws.workout_type,
    ws.duration_min,
    ws.calories_burned,
    ws.avg_bpm,
    ws.max_bpm,
    COUNT(fl.id)                    AS nb_repas_enregistres,
    ROUND(AVG(fl.calories_consumed), 0) AS calories_alimentaires_moyennes
FROM users u
LEFT JOIN workout_sessions ws ON ws.user_id = u.id
LEFT JOIN food_logs fl        ON fl.user_id = u.id
GROUP BY u.id, u.name, u.age, u.gender, u.weight_kg, u.height_cm,
         u.bmi, u.body_fat_pct, u.experience_level,
         ws.workout_type, ws.duration_min, ws.calories_burned,
         ws.avg_bpm, ws.max_bpm
ORDER BY u.id;


-- ----------------------------------------------------------------------------
-- Q19 : Qualite des donnees - taux de completude par table
-- Usage : monitoring pipeline ETL, dashboard qualite
-- ----------------------------------------------------------------------------
SELECT
    'users'     AS table_name,
    COUNT(*)    AS total_lignes,
    ROUND(COUNT(age)              * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_age,
    ROUND(COUNT(gender)           * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_gender,
    ROUND(COUNT(bmi)              * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_bmi,
    ROUND(COUNT(experience_level) * 100.0 / NULLIF(COUNT(*), 0), 1) AS pct_experience_level
FROM users
UNION ALL
SELECT
    'workout_sessions',
    COUNT(*),
    ROUND(COUNT(avg_bpm)          * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(calories_burned)  * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(workout_type)     * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(duration_min)     * 100.0 / NULLIF(COUNT(*), 0), 1)
FROM workout_sessions
UNION ALL
SELECT
    'foods',
    COUNT(*),
    ROUND(COUNT(calories_per_100g) * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(proteins_g)        * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(carbs_g)           * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(category)          * 100.0 / NULLIF(COUNT(*), 0), 1)
FROM foods
UNION ALL
SELECT
    'food_logs',
    COUNT(*),
    ROUND(COUNT(user_id)           * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(food_id)           * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(meal_type)         * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(calories_consumed) * 100.0 / NULLIF(COUNT(*), 0), 1)
FROM food_logs
UNION ALL
SELECT
    'exercises',
    COUNT(*),
    ROUND(COUNT(level)             * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(equipment)         * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(type)              * 100.0 / NULLIF(COUNT(*), 0), 1),
    ROUND(COUNT(muscle_group)      * 100.0 / NULLIF(COUNT(*), 0), 1)
FROM exercises;
