-- =============================================================================
-- Migration: Fix NULL prompts in generated_images
-- =============================================================================
-- Purpose: Fill NULL prompt values before setting NOT NULL constraint
-- Date: 2025-11-10
--
-- Background:
--   Migration abe5d41256e3 tries to set prompt to NOT NULL, but Production DB
--   has NULL values (either from migrate_old_prompts.sql or from text overlay copies).
--
-- This script:
--   1. Fills prompt from user_prompt (primary fallback)
--   2. Fills prompt from enhanced_prompt (secondary fallback)
--   3. Sets default 'Legacy image (no prompt stored)' for remaining NULLs
--   4. Reports migration statistics
--
-- Idempotent: Can be run multiple times safely
-- =============================================================================

-- Step 1: Show current state BEFORE fix
SELECT
  'BEFORE FIX:' as status,
  COUNT(*) as total_images,
  COUNT(prompt) as with_prompt,
  COUNT(user_prompt) as with_user_prompt,
  COUNT(enhanced_prompt) as with_enhanced_prompt,
  SUM(CASE WHEN prompt IS NULL THEN 1 ELSE 0 END) as null_prompts
FROM generated_images;

-- Step 2: Fill NULL prompts from user_prompt (primary fallback)
UPDATE generated_images
SET prompt = user_prompt
WHERE prompt IS NULL
  AND user_prompt IS NOT NULL;

-- Step 3: Fill remaining NULL prompts from enhanced_prompt (secondary fallback)
UPDATE generated_images
SET prompt = enhanced_prompt
WHERE prompt IS NULL
  AND enhanced_prompt IS NOT NULL;

-- Step 4: Fill remaining NULL prompts with default text
UPDATE generated_images
SET prompt = 'Legacy image (no prompt stored)'
WHERE prompt IS NULL;

-- Step 5: Report final state AFTER fix
SELECT
  'AFTER FIX:' as status,
  COUNT(*) as total_images,
  COUNT(prompt) as with_prompt,
  COUNT(user_prompt) as with_user_prompt,
  COUNT(enhanced_prompt) as with_enhanced_prompt,
  SUM(CASE WHEN prompt IS NULL THEN 1 ELSE 0 END) as null_prompts_remaining
FROM generated_images;

-- Expected result after fix:
-- - null_prompts_remaining = 0 (ALL prompts filled)
-- - Migration abe5d41256e3 can now run successfully
