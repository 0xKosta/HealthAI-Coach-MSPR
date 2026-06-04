-- =============================================================================
-- HealthAI Coach — Migration MSPR 3 (additive)
-- Tables : post_likes, post_comments
-- Usage : psql ... -f db/migrations/007_post_likes_comments.sql
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS post_likes (
    id          SERIAL PRIMARY KEY,
    post_id     INT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id     INT NOT NULL REFERENCES user_auth(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_post_likes_post_user UNIQUE (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_likes_post ON post_likes (post_id);

CREATE TABLE IF NOT EXISTS post_comments (
    id          SERIAL PRIMARY KEY,
    post_id     INT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id   INT NOT NULL REFERENCES user_auth(id) ON DELETE CASCADE,
    content     TEXT NOT NULL CHECK (char_length(trim(content)) > 0),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_comments_post_created ON post_comments (post_id, created_at ASC);

INSERT INTO schema_migrations (version)
VALUES ('007_post_likes_comments')
ON CONFLICT (version) DO NOTHING;

COMMIT;
