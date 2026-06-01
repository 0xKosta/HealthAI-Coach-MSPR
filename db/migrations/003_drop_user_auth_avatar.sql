-- =============================================================================
-- MSPR 3 — Retrait de avatar_url (profil affiché via users + prénom/nom dérivés)
-- =============================================================================

BEGIN;

ALTER TABLE user_auth DROP COLUMN IF EXISTS avatar_url;

INSERT INTO schema_migrations (version)
VALUES ('003_drop_user_auth_avatar')
ON CONFLICT (version) DO NOTHING;

COMMIT;
