-- URAP Sprint 2 — consent ledger service-role SELECT policy
-- The service_role key bypasses RLS, but this policy documents intent and
-- enables a future switch to a dedicated server key with restricted privileges.

-- Allow authenticated reads for the service role (outreach TCPA gate checks).
-- Public (anon) cannot SELECT — INSERT-only constraint from Sprint 1 remains.
CREATE POLICY IF NOT EXISTS "urap_consent_service_select"
  ON urap_consent_ledger FOR SELECT
  USING (auth.role() = 'service_role');
