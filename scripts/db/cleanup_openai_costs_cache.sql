-- ============================================================
-- OpenAI Costs Cache Cleanup Script
-- ============================================================
-- Purpose: Remove cached entries with incorrect timezone timestamps
--
-- Background:
-- A bug in api_cost_service.py used datetime.now() without UTC,
-- causing cache timestamps to be stored in local timezone instead
-- of UTC. This caused incorrect TTL calculations.
--
-- This script removes non-finalized cache entries so they will be
-- regenerated with correct UTC timestamps on next API call.
--
-- SAFE TO RUN MULTIPLE TIMES (idempotent)
--
-- Usage (PyCharm SSH or local):
--   psql -h YOUR_HOST -U aiproxy -d aiproxysrv -f scripts/db/cleanup_openai_costs_cache.sql
--
-- ============================================================

BEGIN;

-- ============================================================
-- 1. Show current cache state (for documentation)
-- ============================================================
SELECT
    provider,
    year,
    month,
    total_cost,
    is_finalized,
    last_updated_at,
    NOW() - last_updated_at AS age,
    organization_id
FROM api_costs_monthly
WHERE provider = 'openai'
ORDER BY year DESC, month DESC;

-- ============================================================
-- 2. Delete non-finalized entries (current month)
-- ============================================================
-- These will be regenerated with correct UTC timestamps
-- on next API call (/api/v1/openai/costs/current)

DELETE FROM api_costs_monthly
WHERE provider = 'openai'
  AND is_finalized = false;

-- ============================================================
-- 3. Optional: Update finalized entries (if needed)
-- ============================================================
-- UNCOMMENT ONLY IF historical months also have wrong timestamps
-- (Usually not needed - finalized months are already correct)

-- UPDATE api_costs_monthly
-- SET last_updated_at = NOW()
-- WHERE provider = 'openai'
--   AND is_finalized = true;

COMMIT;

-- ============================================================
-- 4. Verification Query
-- ============================================================
-- Run this to verify cleanup was successful:
SELECT
    provider,
    year,
    month,
    total_cost,
    is_finalized,
    last_updated_at,
    organization_id
FROM api_costs_monthly
WHERE provider = 'openai'
ORDER BY year DESC, month DESC;

-- ============================================================
-- Expected Result:
-- ============================================================
-- - Finalized months (Aug/Sep): Still present with old timestamps
-- - Current month (Oct): DELETED (will be regenerated on next API call)
--
-- After running this script:
-- 1. Restart backend server (to reload ENV variables)
-- 2. Open User Profile in browser
-- 3. OpenAI costs will reload from API with correct UTC timestamp
-- 4. TTL should now show correct value (e.g., ttl_remaining=3599)
