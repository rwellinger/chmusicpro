-- =============================================================================
-- Migration: Old Image Prompts → user_prompt
-- =============================================================================
-- Purpose: Migrate legacy prompt data to new user_prompt/enhanced_prompt structure
-- Date: 2025-10-22
--
-- Background:
--   Before Enhancement feature, all prompts were stored in `prompt` column.
--   After Enhancement, we use:
--     - user_prompt: Original user input
--     - enhanced_prompt: AI-enhanced version (if enhancement was used)
--     - prompt: Legacy column (deprecated, to be removed)
--
-- This script:
--   1. Copies old `prompt` values → `user_prompt` (where user_prompt is NULL)
--   2. Clears old `prompt` values (SET NULL) for clean DB structure
--   3. Reports migration statistics
--
-- Idempotent: Can be run multiple times safely
-- =============================================================================

-- Step 1: Show current state BEFORE migration
SELECT
  'BEFORE MIGRATION:' as status,
  COUNT(*) as total_images,
  COUNT(user_prompt) as with_user_prompt,
  COUNT(enhanced_prompt) as with_enhanced_prompt,
  COUNT(prompt) as with_old_prompt
FROM generated_images;

-- Step 2: Migrate prompt → user_prompt
-- Only for records where user_prompt is still NULL (old images)
UPDATE generated_images
SET user_prompt = prompt
WHERE user_prompt IS NULL
  AND prompt IS NOT NULL;

-- Step 3: Clear ALL old prompt values
-- Now that we have user_prompt + enhanced_prompt, we don't need prompt anymore
UPDATE generated_images
SET prompt = NULL
WHERE prompt IS NOT NULL;

-- Step 4: Report final state AFTER migration
SELECT
  'AFTER MIGRATION:' as status,
  COUNT(*) as total_images,
  COUNT(user_prompt) as with_user_prompt,
  COUNT(enhanced_prompt) as with_enhanced_prompt,
  COUNT(prompt) as with_old_prompt_remaining
FROM generated_images;

-- Expected result after migration:
-- - Old images: user_prompt=filled, prompt=NULL, enhanced_prompt=NULL
-- - Enhanced images: user_prompt=filled, enhanced_prompt=filled, prompt=NULL
-- - All images should have user_prompt filled
