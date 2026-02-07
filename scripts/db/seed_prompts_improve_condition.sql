-- ============================================================
-- Prompt Template: Improve PRE/POST-Conditions
-- ============================================================
-- This script adds a new prompt template for improving
-- prompt conditions using AI (Ollama/OpenAI).
--
-- Usage (PostgreSQL):
--   psql -h localhost -U aiproxy -d aiproxysrv -f seed_prompts_improve_condition.sql
--
-- Usage (Docker):
--   cat scripts/db/seed_prompts_improve_condition.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
--
-- ============================================================

BEGIN;

-- Helper function (reuse if exists)
CREATE OR REPLACE FUNCTION upsert_prompt_template(
    p_category VARCHAR,
    p_action VARCHAR,
    p_pre_condition TEXT,
    p_post_condition TEXT,
    p_description TEXT,
    p_version VARCHAR,
    p_model VARCHAR,
    p_temperature FLOAT,
    p_max_tokens INTEGER,
    p_active BOOLEAN
) RETURNS VOID AS $$
BEGIN
    INSERT INTO prompt_templates (
        category, action, pre_condition, post_condition, description,
        version, model, temperature, max_tokens, active,
        created_at, updated_at
    ) VALUES (
        p_category, p_action, p_pre_condition, p_post_condition, p_description,
        p_version, p_model, p_temperature, p_max_tokens, p_active,
        NOW(), NOW()
    )
    ON CONFLICT (category, action) DO UPDATE SET
        pre_condition = EXCLUDED.pre_condition,
        post_condition = EXCLUDED.post_condition,
        description = EXCLUDED.description,
        version = EXCLUDED.version,
        model = EXCLUDED.model,
        temperature = EXCLUDED.temperature,
        max_tokens = EXCLUDED.max_tokens,
        active = EXCLUDED.active,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PROMPT ENGINEERING: Improve Condition
-- ============================================================

SELECT upsert_prompt_template(
    'prompt_engineering',
    'improve_condition',
    'You are an expert in prompt engineering with deep knowledge of best practices for writing effective AI prompts.

Your task is to analyze and improve the given prompt condition. The improvement should focus on:

1. **Clarity**: Make instructions unambiguous and specific
2. **Structure**: Organize the prompt logically with clear sections
3. **Specificity**: Add concrete examples or constraints where helpful
4. **Completeness**: Ensure all necessary context is provided
5. **Actionability**: Make it clear what output is expected
6. **Conciseness**: Remove redundancy while maintaining clarity

Apply these prompt engineering best practices:
- Use clear, direct language
- Break complex instructions into numbered/bulleted lists
- Specify output format explicitly
- Add constraints and boundaries where appropriate
- Include examples if they clarify expectations
- Use markdown formatting for better readability (headers, lists, emphasis)

IMPORTANT:
- Preserve the original intent and core requirements
- Keep the same language as input (German → German, English → English)
- Do NOT change technical terms, variable names, or specific requirements
- Focus on improving structure and clarity, not changing functionality',
    'Return ONLY the improved prompt text.

RULES:
- Output the complete improved prompt as plain text with markdown formatting
- Use markdown for structure: ## headers, **bold**, `code`, bullet points
- Keep the same language as the input
- Do NOT add explanations about what you changed
- Do NOT add meta-commentary like "Here is the improved version:"
- Output ONLY the improved prompt itself',
    'AI-powered prompt condition improvement using prompt engineering best practices',
    '1.0',
    'llama3.2:3b',
    0.7,
    2048,
    true
);

COMMIT;

-- Verification
SELECT
    category,
    action,
    version,
    model,
    temperature,
    max_tokens,
    active,
    LENGTH(pre_condition) as pre_length,
    LENGTH(post_condition) as post_length
FROM prompt_templates
WHERE category = 'prompt_engineering' AND action = 'improve_condition';
