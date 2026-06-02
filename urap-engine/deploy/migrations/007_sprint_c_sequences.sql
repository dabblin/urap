-- URAP Sprint C — Drip Sequences
-- Sequence templates + per-contact enrollments with step scheduling.

-- ── urap_sequences — reusable sequence templates ──────────────────────────────
CREATE TABLE IF NOT EXISTS urap_sequences (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  TEXT        NOT NULL,
  name       TEXT        NOT NULL,
  from_email TEXT        NOT NULL DEFAULT '',
  from_name  TEXT        NOT NULL DEFAULT '',
  steps      JSONB       NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- steps JSON shape: [{"step":0,"delay_days":0,"subject":"...","body_html":"..."}, ...]

CREATE INDEX IF NOT EXISTS idx_urap_sequences_tenant
  ON urap_sequences (tenant_id, created_at DESC);

-- ── urap_sequence_enrollments — one row per contact per sequence ──────────────
CREATE TABLE IF NOT EXISTS urap_sequence_enrollments (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  sequence_id   UUID        NOT NULL REFERENCES urap_sequences(id) ON DELETE CASCADE,
  tenant_id     TEXT        NOT NULL,
  to_email      TEXT        NOT NULL,
  to_name       TEXT        NOT NULL DEFAULT '',
  company       TEXT        NOT NULL DEFAULT '',
  current_step  INT         NOT NULL DEFAULT 0,
  status        TEXT        NOT NULL DEFAULT 'active',
  next_send_at  TIMESTAMPTZ,
  enrolled_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- status: active | paused | completed | replied | bounced | unsubscribed

CREATE INDEX IF NOT EXISTS idx_urap_seq_enroll_tenant
  ON urap_sequence_enrollments (tenant_id, status);

CREATE INDEX IF NOT EXISTS idx_urap_seq_enroll_due
  ON urap_sequence_enrollments (next_send_at)
  WHERE status = 'active';
