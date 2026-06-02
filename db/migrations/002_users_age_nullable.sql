-- =============================================================================
-- HealthAI Coach — Migration MSPR 3 (additive)
-- Rend users.age optionnel.
--
-- Contexte : à l'inscription (/auth/register), on crée un profil santé `users`
-- VIDE lié au compte `user_auth`. Les champs santé (âge, poids, objectif...)
-- sont renseignés ensuite par l'utilisateur. `age` ne peut donc plus être
-- obligatoire à la création.
--
-- Usage : psql ... -f db/migrations/002_users_age_nullable.sql
--         ou SQL Editor Supabase (une seule fois)
-- =============================================================================

BEGIN;

ALTER TABLE users ALTER COLUMN age DROP NOT NULL;

INSERT INTO schema_migrations (version)
VALUES ('002_users_age_nullable')
ON CONFLICT (version) DO NOTHING;

COMMIT;
