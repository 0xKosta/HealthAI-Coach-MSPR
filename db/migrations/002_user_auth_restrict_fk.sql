-- =============================================================================
-- MSPR 3 — Empêcher la suppression accidentelle de users liés à user_auth
-- (DELETE sur users ; le TRUNCATE users est déjà évité par l'ETL si user_auth > 0)
-- =============================================================================

BEGIN;

ALTER TABLE user_auth
    DROP CONSTRAINT IF EXISTS user_auth_user_id_fkey;

ALTER TABLE user_auth
    ADD CONSTRAINT user_auth_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;

INSERT INTO schema_migrations (version)
VALUES ('002_user_auth_restrict_fk')
ON CONFLICT (version) DO NOTHING;

COMMIT;
