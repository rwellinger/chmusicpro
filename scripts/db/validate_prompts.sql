-- ============================================================
-- Prompt Templates Validation Script
-- ============================================================
-- Validates that templates have sufficient max_tokens for their
-- pre_condition + post_condition content.
--
-- Usage (PostgreSQL Docker):
--   cat validate_prompts.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
--
-- Usage (SSH Tunnel to PROD):
--   psql -h localhost -p 5432 -U aiproxy -d aiproxysrv -f validate_prompts.sql
--
-- This script is READ-ONLY - it makes no changes to the database.
-- ============================================================

\echo ''
\echo '============================================================'
\echo 'Prompt Template Token Budget Validation'
\echo '============================================================'
\echo ''

-- Create temporary view for validation
CREATE TEMP VIEW template_token_analysis AS
SELECT
    category,
    action,
    model,
    max_tokens,
    version,
    LENGTH(COALESCE(pre_condition, '')) + LENGTH(COALESCE(post_condition, '')) as total_chars,
    (LENGTH(COALESCE(pre_condition, '')) + LENGTH(COALESCE(post_condition, ''))) / 4 as estimated_tokens,
    CASE
        WHEN max_tokens IS NULL OR max_tokens = 0 THEN NULL
        ELSE ROUND(
            ((LENGTH(COALESCE(pre_condition, '')) + LENGTH(COALESCE(post_condition, ''))) / 4.0 / max_tokens * 100)::numeric,
            1
        )
    END as percent_used,
    -- Model-specific thresholds (different models have different token overhead)
    CASE
        WHEN model IN ('gpt-oss:20b', 'deepseek-r1:8b') THEN 60.0  -- Large models with Chain-of-Thought need more room
        WHEN model IN ('llama3.2:3b', 'gemma3:4b') THEN 75.0        -- Small models without thinking can use more
        ELSE 70.0                                                    -- Default threshold
    END as threshold,
    CASE
        WHEN model IN ('gpt-oss:20b', 'deepseek-r1:8b') THEN 'CoT'
        WHEN model IN ('llama3.2:3b', 'gemma3:4b') THEN 'Direct'
        ELSE 'Unknown'
    END as model_type,
    active
FROM prompt_templates
WHERE max_tokens IS NOT NULL AND max_tokens > 0
ORDER BY percent_used DESC NULLS LAST;

-- Show warnings for templates exceeding model-specific thresholds
DO $$
DECLARE
    rec RECORD;
    warning_count INTEGER := 0;
BEGIN
    FOR rec IN
        SELECT category, action, model, model_type, max_tokens, estimated_tokens, percent_used, threshold
        FROM template_token_analysis
        WHERE percent_used > threshold
        ORDER BY percent_used DESC
    LOOP
        warning_count := warning_count + 1;
        RAISE WARNING 'Template %.%/% [%] uses %.1f%% of max_tokens (%/%), exceeds %.0f%% threshold',
            rec.category, rec.action, rec.model, rec.model_type, rec.percent_used,
            rec.estimated_tokens, rec.max_tokens, rec.threshold;
    END LOOP;

    IF warning_count > 0 THEN
        RAISE NOTICE '';
        RAISE NOTICE '⚠️  Found % template(s) exceeding model-specific thresholds', warning_count;
        RAISE NOTICE 'Model-specific thresholds:';
        RAISE NOTICE '  • Large models (gpt-oss:20b, deepseek-r1:8b): 60%% (need room for Chain-of-Thought)';
        RAISE NOTICE '  • Small models (llama3.2:3b, gemma3:4b): 75%% (direct response, no thinking overhead)';
        RAISE NOTICE 'Consider increasing max_tokens in seed_prompts.sql';
    ELSE
        RAISE NOTICE '✅ All templates meet model-specific token budget thresholds';
    END IF;
    RAISE NOTICE '';
END $$;

-- Show detailed table
\echo 'Detailed Token Budget Analysis:'
\echo '(Sorted by percent_used DESC - most critical first)'
\echo ''

SELECT
    category || '/' || action as template,
    model,
    model_type as type,
    version,
    max_tokens as max_tok,
    estimated_tokens as est_tok,
    percent_used as "used_%",
    threshold as "limit_%",
    CASE
        WHEN percent_used > threshold THEN '⚠️'
        ELSE '✓'
    END as status,
    total_chars as chars,
    CASE WHEN active THEN '✓' ELSE '✗' END as active
FROM template_token_analysis;

\echo ''
\echo 'Token Estimation Formula: (pre_condition + post_condition) chars / 4'
\echo 'Model-Specific Thresholds:'
\echo '  • CoT Models (gpt-oss:20b, deepseek-r1:8b): 60% limit (need room for thinking)'
\echo '  • Direct Models (llama3.2:3b, gemma3:4b): 75% limit (no thinking overhead)'
\echo ''
\echo '============================================================'
\echo 'Validation Complete'
\echo '============================================================'
\echo ''

-- Cleanup
DROP VIEW template_token_analysis;
