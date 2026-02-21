-- ============================================================
-- Model Context Windows - VPS Seed Script
-- ============================================================
-- Lightweight version with only VPS-relevant Ollama models.
-- Uses UPSERT (ON CONFLICT) to create or overwrite existing
-- entries.
--
-- Usage (local):
--   cat scripts/db/seed_model_vps_windows.sql | docker exec -i postgres psql -U chmusicpro -d chmusicpro
--
-- Usage (VPS):
--   cat scripts/db/seed_model_vps_windows.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
--
-- ============================================================

BEGIN;

-- ============================================================
-- OpenAI Models
-- ============================================================

INSERT INTO model_context_windows (model_name, context_window, provider, description) VALUES
('gpt-5.2',              400000, 'openai', 'GPT-5.2 (400k)'),
('gpt-5.1',              200000, 'openai', 'GPT-5.1 (200k)'),
('gpt-4o',               128000, 'openai', 'GPT-4o (128k)'),
('gpt-4o-mini',          128000, 'openai', 'GPT-4o Mini (128k)'),
('gpt-4.1',              128000, 'openai', 'GPT-4.1 (128k)'),
('gpt-4.1-mini',         128000, 'openai', 'GPT-4.1 Mini (128k)')
ON CONFLICT (model_name) DO UPDATE SET
    context_window = EXCLUDED.context_window,
    provider = EXCLUDED.provider,
    description = EXCLUDED.description,
    updated_at = NOW();

-- ============================================================
-- Claude / Anthropic Models
-- ============================================================

INSERT INTO model_context_windows (model_name, context_window, provider, description) VALUES
-- Claude 4 Series
('claude-opus-4-6',              200000, 'claude', 'Claude Opus 4.6'),
('claude-sonnet-4-6',            200000, 'claude', 'Claude Sonnet 4.6'),
-- Claude 4.5 Series
('claude-haiku-4-5-20251001',    200000, 'claude', 'Claude Haiku 4.5'),
-- Claude 3.5 Series
('claude-3-5-sonnet-20241022',   200000, 'claude', 'Claude 3.5 Sonnet'),
('claude-3-5-haiku-20241022',    200000, 'claude', 'Claude 3.5 Haiku'),
-- Claude 3 Series
('claude-3-opus-20240229',       200000, 'claude', 'Claude 3 Opus'),
('claude-3-sonnet-20240229',     200000, 'claude', 'Claude 3 Sonnet'),
('claude-3-haiku-20240307',      200000, 'claude', 'Claude 3 Haiku')
ON CONFLICT (model_name) DO UPDATE SET
    context_window = EXCLUDED.context_window,
    provider = EXCLUDED.provider,
    description = EXCLUDED.description,
    updated_at = NOW();

-- ============================================================
-- Ollama Models (VPS subset)
-- ============================================================

INSERT INTO model_context_windows (model_name, context_window, provider, description) VALUES
('llama3.2:3b',       131072, 'ollama', 'LLaMA 3.2 3B (128k)'),
('gemma3:4b',         131072, 'ollama', 'Gemma 3 4B (128k)'),
('phi4-mini',         131072, 'ollama', 'Phi-4 Mini (128k)'),
('qwen2.5:7b',         32768, 'ollama', 'Qwen 2.5 7B (32k)'),
('mistral:7b',          8192, 'ollama', 'Mistral 7B')
ON CONFLICT (model_name) DO UPDATE SET
    context_window = EXCLUDED.context_window,
    provider = EXCLUDED.provider,
    description = EXCLUDED.description,
    updated_at = NOW();

-- ============================================================
-- Statistics
-- ============================================================

DO $$
DECLARE
    total_count INTEGER;
    openai_count INTEGER;
    claude_count INTEGER;
    ollama_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM model_context_windows;
    SELECT COUNT(*) INTO openai_count FROM model_context_windows WHERE provider = 'openai';
    SELECT COUNT(*) INTO claude_count FROM model_context_windows WHERE provider = 'claude';
    SELECT COUNT(*) INTO ollama_count FROM model_context_windows WHERE provider = 'ollama';

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Model Context Windows seeding completed!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total models:   %', total_count;
    RAISE NOTICE '  OpenAI:       %', openai_count;
    RAISE NOTICE '  Claude:       %', claude_count;
    RAISE NOTICE '  Ollama:       %', ollama_count;
    RAISE NOTICE '';
END $$;

SELECT provider, COUNT(*) as count,
       string_agg(model_name, ', ' ORDER BY model_name) as models
FROM model_context_windows
GROUP BY provider
ORDER BY provider;

COMMIT;
