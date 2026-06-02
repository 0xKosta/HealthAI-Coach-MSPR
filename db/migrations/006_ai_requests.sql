-- =============================================================================
-- HealthAI Coach — Migration 006 (additive)
-- Historique des requêtes / réponses IA par utilisateur
--
-- Usage : psql ... -f db/migrations/006_ai_requests.sql
--         ou SQL Editor Supabase (une seule fois)
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS ai_requests (
    id              BIGSERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type    VARCHAR(30) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'success',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    input_summary   TEXT,
    output_summary  TEXT,
    input_json      JSONB,
    output_json     JSONB,
    photo_path      VARCHAR(500),
    error_message   TEXT,
    from_cache      BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT ck_ai_requests_type CHECK (
        request_type IN (
            'advice',
            'analyze_photo',
            'workout_plan',
            'biometric_trend',
            'meal_plan'
        )
    ),
    CONSTRAINT ck_ai_requests_status CHECK (
        status IN ('success', 'error')
    )
);

CREATE INDEX IF NOT EXISTS idx_ai_requests_user_created
    ON ai_requests (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_requests_type
    ON ai_requests (request_type);

INSERT INTO schema_migrations (version)
VALUES ('006_ai_requests')
ON CONFLICT (version) DO NOTHING;

COMMIT;
