-- =============================================================================
-- HealthAI Coach — Migration MSPR 3 (additive)
-- Tables : user_auth, posts, schema_migrations
--
-- NE PAS exécuter init.sql sur une base déjà peuplée.
-- Usage : psql ... -f db/migrations/001_user_auth_posts.sql
--         ou SQL Editor Supabase (une seule fois)
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS user_auth (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_auth_email ON user_auth (email);

CREATE TABLE IF NOT EXISTS posts (
    id              SERIAL PRIMARY KEY,
    author_id       INT NOT NULL REFERENCES user_auth(id) ON DELETE CASCADE,
    content         TEXT,
    media_url       TEXT,
    media_type      VARCHAR(20) CHECK (media_type IN ('image', 'video')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT posts_content_or_media CHECK (
        content IS NOT NULL OR media_url IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_posts_author_created ON posts (author_id, created_at DESC);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(50) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version)
VALUES ('001_user_auth_posts')
ON CONFLICT (version) DO NOTHING;

COMMIT;
