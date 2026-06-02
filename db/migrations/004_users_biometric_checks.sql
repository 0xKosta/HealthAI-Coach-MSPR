-- =============================================================================
-- HealthAI Coach — Migration 004 (additive)
-- Contraintes CHECK biométriques sur users (âge, taille, poids, IMC)
--
-- Usage : psql ... -f db/migrations/004_users_biometric_checks.sql
--         ou SQL Editor Supabase (une seule fois)
-- =============================================================================

BEGIN;

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_age;
ALTER TABLE users ADD CONSTRAINT ck_users_age
    CHECK (age IS NULL OR (age >= 18 AND age <= 100));

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_weight_kg;
ALTER TABLE users ADD CONSTRAINT ck_users_weight_kg
    CHECK (weight_kg IS NULL OR (weight_kg >= 20 AND weight_kg <= 300));

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_height_cm;
ALTER TABLE users ADD CONSTRAINT ck_users_height_cm
    CHECK (height_cm IS NULL OR (height_cm >= 90 AND height_cm <= 230));

ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_bmi;
ALTER TABLE users ADD CONSTRAINT ck_users_bmi
    CHECK (bmi IS NULL OR (bmi >= 10 AND bmi <= 80));

INSERT INTO schema_migrations (version)
VALUES ('004_users_biometric_checks')
ON CONFLICT (version) DO NOTHING;

COMMIT;
