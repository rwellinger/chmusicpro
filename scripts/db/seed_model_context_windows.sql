-- ============================================================
-- Model Context Windows - Complete Seed Script
-- ============================================================
-- Self-contained script that seeds ALL known AI model context
-- windows. Uses UPSERT (ON CONFLICT) to create or overwrite
-- existing entries.
--
-- Usage (local):
--   cat scripts/db/seed_model_context_windows.sql | docker exec -i postgres psql -U chmusicpro -d chmusicpro
--
-- Usage (VPS):
--   cat scripts/db/seed_model_context_windows.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
--
-- ============================================================

BEGIN;

-- ============================================================
-- OpenAI Models
-- ============================================================

INSERT INTO model_context_windows (model_name, context_window, provider, description) VALUES
-- GPT-5 Series
('gpt-5.1',              200000, 'openai', 'GPT-5.1'),
('gpt-5.1-codex-mini',   200000, 'openai', 'GPT-5.1 Codex Mini'),
('gpt-5',                200000, 'openai', 'GPT-5 base'),
('gpt-5-pro',            200000, 'openai', 'GPT-5 Pro'),
('gpt-5-mini',           200000, 'openai', 'GPT-5 Mini'),
('gpt-5-nano',           200000, 'openai', 'GPT-5 Nano'),
('gpt-5-codex',          200000, 'openai', 'GPT-5 Codex'),
('gpt-5-chat-latest',    200000, 'openai', 'GPT-5 Chat Latest'),
-- GPT-4.1 Series
('gpt-4.1',              128000, 'openai', 'GPT-4.1 base'),
('gpt-4.1-mini',         128000, 'openai', 'GPT-4.1 Mini'),
('gpt-4.1-nano',         128000, 'openai', 'GPT-4.1 Nano'),
-- GPT-4o Series
('gpt-4o',               128000, 'openai', 'GPT-4o'),
('gpt-4o-mini',          128000, 'openai', 'GPT-4o Mini'),
-- GPT-4 Series
('gpt-4-turbo',          128000, 'openai', 'GPT-4 Turbo'),
('gpt-4',                  8192, 'openai', 'GPT-4'),
-- GPT-3.5 Series
('gpt-3.5-turbo',         16385, 'openai', 'GPT-3.5 Turbo'),
('gpt-3.5-turbo-16k',     16385, 'openai', 'GPT-3.5 Turbo 16k')
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
-- Ollama Models
-- ============================================================

INSERT INTO model_context_windows (model_name, context_window, provider, description) VALUES
-- GPT-OSS
('gpt-oss:20b',                       8192, 'ollama', 'GPT-OSS 20B'),
-- DeepSeek
('deepseek-r1:8b',                  131072, 'ollama', 'DeepSeek R1 8B (128k)'),
-- Apertus
('MichelRosselli/apertus:latest',     65536, 'ollama', 'Apertus (64k)'),
-- LLaMA 2
('llama2:7b',                          4096, 'ollama', 'LLaMA 2 7B'),
('llama2:13b',                         4096, 'ollama', 'LLaMA 2 13B'),
('llama2:70b',                         4096, 'ollama', 'LLaMA 2 70B'),
-- LLaMA 3
('llama3:8b',                          8192, 'ollama', 'LLaMA 3 8B'),
('llama3:70b',                         8192, 'ollama', 'LLaMA 3 70B'),
('llama3.1:8b',                      131072, 'ollama', 'LLaMA 3.1 8B (128k)'),
('llama3.1:70b',                     131072, 'ollama', 'LLaMA 3.1 70B (128k)'),
('llama3.2:1b',                      131072, 'ollama', 'LLaMA 3.2 1B (128k)'),
('llama3.2:3b',                      131072, 'ollama', 'LLaMA 3.2 3B (128k)'),
-- Mistral
('mistral:7b',                         8192, 'ollama', 'Mistral 7B'),
('mistral:instruct',                   8192, 'ollama', 'Mistral Instruct'),
('mixtral:8x7b',                      32768, 'ollama', 'Mixtral 8x7B (32k)'),
-- Gemma
('gemma:2b',                           8192, 'ollama', 'Gemma 2B'),
('gemma:7b',                           8192, 'ollama', 'Gemma 7B'),
('gemma2:9b',                          8192, 'ollama', 'Gemma 2 9B'),
('gemma2:27b',                         8192, 'ollama', 'Gemma 2 27B'),
('gemma3:4b',                        131072, 'ollama', 'Gemma 3 4B (128k)'),
-- CodeLlama
('codellama:7b',                      16384, 'ollama', 'CodeLlama 7B (16k)'),
('codellama:13b',                     16384, 'ollama', 'CodeLlama 13B (16k)'),
('codellama:34b',                     16384, 'ollama', 'CodeLlama 34B (16k)'),
-- Phi
('phi3:mini',                          4096, 'ollama', 'Phi-3 Mini'),
('phi3:medium',                        4096, 'ollama', 'Phi-3 Medium'),
-- Qwen
('qwen:7b',                            8192, 'ollama', 'Qwen 7B'),
('qwen:14b',                           8192, 'ollama', 'Qwen 14B'),
('qwen2:7b',                          32768, 'ollama', 'Qwen 2 7B (32k)'),
('qwen3:8b',                          32768, 'ollama', 'Qwen 3 8B (32k)'),
('qwen3:30b',                         32768, 'ollama', 'Qwen 3 30B (32k)')
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
