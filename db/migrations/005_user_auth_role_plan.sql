-- =============================================================================
-- HealthAI Coach — Migration 005 (additive)
-- Colonnes role + plan sur user_auth (freemium / Premium / admin / démo)
--
-- Existants : role = user, plan = free (DEFAULT)
-- Usage : psql ... -f db/migrations/005_user_auth_role_plan.sql
--         ou SQL Editor Supabase (une seule fois)
-- =============================================================================

BEGIN;

ALTER TABLE user_auth
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user',
    ADD COLUMN IF NOT EXISTS plan VARCHAR(20) NOT NULL DEFAULT 'free';

ALTER TABLE user_auth DROP CONSTRAINT IF EXISTS ck_user_auth_role;
ALTER TABLE user_auth ADD CONSTRAINT ck_user_auth_role
    CHECK (role IN ('user', 'admin', 'demo'));

ALTER TABLE user_auth DROP CONSTRAINT IF EXISTS ck_user_auth_plan;
ALTER TABLE user_auth ADD CONSTRAINT ck_user_auth_plan
    CHECK (plan IN ('free', 'premium', 'premium_plus'));

INSERT INTO schema_migrations (version)
VALUES ('005_user_auth_role_plan')
ON CONFLICT (version) DO NOTHING;

COMMIT;
