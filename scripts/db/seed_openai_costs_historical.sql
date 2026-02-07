-- ============================================================
-- OpenAI Costs Historical Data Seeding Script
-- ============================================================
-- This script seeds historical monthly cost data from OpenAI Admin API
--
-- IMPORTANT: You need to manually fetch data from OpenAI API first!
--
-- How to get the data:
-- 1. Calculate Unix timestamps for the month you want:
--    August 2025: start=1722470400 (2025-08-01 00:00), end=1725148800 (2025-09-01 00:00)
--    September 2025: start=1725148800 (2025-09-01 00:00), end=1727827200 (2025-10-01 00:00)
--
-- 2. Call OpenAI API (replace YOUR_ADMIN_KEY):
--    curl -X GET "https://api.openai.com/v1/organization/costs?start_time=1722470400&end_time=1725148800&group_by=line_item&limit=31" \
--      -H "Authorization: Bearer sk-proj-YOUR_ADMIN_KEY"
--
-- 3. Copy the JSON response and extract:
--    - organization_id (from response.data[0].results[0].organization_id)
--    - Aggregate all line_items across buckets
--    - Calculate total_cost, image_cost (dall-e*), chat_cost (gpt-*)
--
-- 4. Fill in the VALUES below with your data
--
-- Usage (PyCharm SSH or local):
--   psql -h YOUR_HOST -U aiproxy -d aiproxysrv -f seed_openai_costs_historical.sql
--
-- ============================================================

BEGIN;

-- ============================================================
-- Insert/Update August 2025 Costs
-- ============================================================
-- Data from OpenAI API (fetched 2025-10-25)
-- Result: No usage in August 2025 (all 31 buckets empty)
INSERT INTO api_costs_monthly (
    id,
    provider,
    organization_id,
    year,
    month,
    total_cost,
    image_cost,
    chat_cost,
    currency,
    line_items,
    bucket_count,
    is_finalized,
    last_updated_at
) VALUES (
    gen_random_uuid(),  -- Generate UUID
    'openai',
    NULL,  -- Optional: Can be updated later via UPDATE statement
    2025,
    8,
    0.00,  -- No usage in August
    0.00,  -- No DALL-E usage
    0.00,  -- No GPT usage
    'usd',
    '{}'::jsonb,  -- No line items (empty month)
    31,  -- Number of days in August
    true,  -- Historical month = finalized
    NOW()
)
ON CONFLICT (provider, organization_id, year, month)
DO UPDATE SET
    total_cost = EXCLUDED.total_cost,
    image_cost = EXCLUDED.image_cost,
    chat_cost = EXCLUDED.chat_cost,
    line_items = EXCLUDED.line_items,
    bucket_count = EXCLUDED.bucket_count,
    is_finalized = EXCLUDED.is_finalized,
    last_updated_at = NOW();

-- ============================================================
-- Insert/Update September 2025 Costs
-- ============================================================
-- Data from OpenAI API (fetched 2025-10-25)
-- Result: No usage in September 2025 (all 30 buckets empty)
INSERT INTO api_costs_monthly (
    id,
    provider,
    organization_id,
    year,
    month,
    total_cost,
    image_cost,
    chat_cost,
    currency,
    line_items,
    bucket_count,
    is_finalized,
    last_updated_at
) VALUES (
    gen_random_uuid(),  -- Generate UUID
    'openai',
    NULL,  -- Optional: Can be updated later via UPDATE statement
    2025,
    9,
    0.00,  -- No usage in September
    0.00,  -- No DALL-E usage
    0.00,  -- No GPT usage
    'usd',
    '{}'::jsonb,  -- No line items (empty month)
    30,  -- Number of days in September
    true,  -- Historical month = finalized
    NOW()
)
ON CONFLICT (provider, organization_id, year, month)
DO UPDATE SET
    total_cost = EXCLUDED.total_cost,
    image_cost = EXCLUDED.image_cost,
    chat_cost = EXCLUDED.chat_cost,
    line_items = EXCLUDED.line_items,
    bucket_count = EXCLUDED.bucket_count,
    is_finalized = EXCLUDED.is_finalized,
    last_updated_at = NOW();

COMMIT;

-- ============================================================
-- Optional: Update organization_id later
-- ============================================================
-- If you want to add organization_id later, run this UPDATE:
-- UPDATE api_costs_monthly
-- SET organization_id = 'org-YOUR_REAL_ORG_ID'
-- WHERE provider = 'openai'
--   AND year IN (2025)
--   AND month IN (8, 9)
--   AND organization_id IS NULL;

-- ============================================================
-- Verification Query
-- ============================================================
-- Run this after executing the script to verify data was inserted:
-- SELECT provider, organization_id, year, month, total_cost, image_cost, chat_cost, is_finalized
-- FROM api_costs_monthly
-- WHERE provider = 'openai'
-- ORDER BY year DESC, month DESC;
