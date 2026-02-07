-- ============================================================
-- Lyric Parsing Rules Seeding Script
-- ============================================================
-- Exported from Dev-DB on 2025-10-17
-- This script seeds/updates regex-based lyric cleanup and section detection rules
--
-- Usage (PostgreSQL):
--   psql -h localhost -U aiuser -d aiproxy -f seed_lyric_parsing_rules.sql
--
-- Usage (Docker):
--   cat seed_lyric_parsing_rules.sql | docker exec -i mac_ki_service-postgres-1 psql -U aiuser -d aiproxy
--
-- NOTE: All replacement values are Base64-encoded for safe storage
-- ============================================================

BEGIN;

-- ============================================================
-- Ensure UNIQUE constraint exists (idempotent)
-- ============================================================
DO $$
BEGIN
    -- Check if constraint exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_lyric_parsing_rule_name'
    ) THEN
        -- Create constraint if missing
        ALTER TABLE lyric_parsing_rules
        ADD CONSTRAINT uq_lyric_parsing_rule_name UNIQUE (name);
        RAISE NOTICE 'Created UNIQUE constraint uq_lyric_parsing_rule_name';
    ELSE
        RAISE NOTICE 'UNIQUE constraint uq_lyric_parsing_rule_name already exists';
    END IF;
END $$;

-- Helper function for Base64 encoding
CREATE OR REPLACE FUNCTION encode_base64(input_text TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN encode(input_text::bytea, 'base64');
END;
$$ LANGUAGE plpgsql;

-- Helper function for upsert operations
CREATE OR REPLACE FUNCTION upsert_lyric_parsing_rule(
    p_name VARCHAR,
    p_description TEXT,
    p_pattern TEXT,
    p_replacement TEXT,
    p_rule_type VARCHAR,
    p_active BOOLEAN,
    p_order INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO lyric_parsing_rules (
        name, description, pattern, replacement, rule_type, active, "order",
        created_at, updated_at
    ) VALUES (
        p_name, p_description, p_pattern, p_replacement, p_rule_type, p_active, p_order,
        NOW(), NOW()
    )
    ON CONFLICT (name) DO UPDATE SET
        description = EXCLUDED.description,
        pattern = EXCLUDED.pattern,
        replacement = EXCLUDED.replacement,
        rule_type = EXCLUDED.rule_type,
        active = EXCLUDED.active,
        "order" = EXCLUDED."order",
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- CLEANUP RULES
-- ============================================================

-- Comma Line Breaks (Order: 0)
SELECT upsert_lyric_parsing_rule(
    'Comma Line Breaks',
    'Add line break after comma if followed by 5+ words',
    ',\s+(?=(?:[^\s,]+\s*){5,})',
    encode_base64(',
'),
    'cleanup',
    true,
    0
);

-- Line Break After Comma + Capital (Order: 1)
SELECT upsert_lyric_parsing_rule(
    'Line Break After Comma + Capital',
    'Add line break after comma when followed by capital letter',
    ',\s+(?=[A-Z])',
    encode_base64(',
'),
    'cleanup',
    true,
    1
);

-- Remove Trailing Spaces (Order: 3)
SELECT upsert_lyric_parsing_rule(
    'Remove Trailing Spaces',
    'Remove whitespace at the end of each line',
    '\s+$',
    encode_base64(''),
    'cleanup',
    true,
    3
);

-- Normalize Smart Quotes (Double) (Order: 4)
SELECT upsert_lyric_parsing_rule(
    'Normalize Smart Quotes (Double)',
    'Convert curly double quotes to straight quotes',
    '[\u201C\u201D]',
    encode_base64('"'),
    'cleanup',
    true,
    4
);

-- Normalize Smart Quotes (Single) (Order: 5)
SELECT upsert_lyric_parsing_rule(
    'Normalize Smart Quotes (Single)',
    'Convert curly single quotes to straight quotes',
    '[\u2018\u2019]',
    encode_base64(''''),
    'cleanup',
    true,
    5
);

-- Line Break After Period + Capital (Order: 6)
SELECT upsert_lyric_parsing_rule(
    'Line Break After Period + Capital',
    'Add line break after period when followed by capital letter',
    '\.\s+(?=[A-Z])',
    encode_base64('.
'),
    'cleanup',
    true,
    6
);

-- Normalize Em Dash (Order: 7)
SELECT upsert_lyric_parsing_rule(
    'Normalize Em Dash',
    'Convert em dash to regular dash with spaces',
    '\u2014',
    encode_base64(' - '),
    'cleanup',
    true,
    7
);

-- Normalize Ellipsis (Order: 8)
SELECT upsert_lyric_parsing_rule(
    'Normalize Ellipsis',
    'Convert ellipsis character to three periods',
    '\u2026',
    encode_base64('...'),
    'cleanup',
    true,
    8
);

-- Normalize En Dash (Order: 9)
SELECT upsert_lyric_parsing_rule(
    'Normalize En Dash',
    'Convert en dash to regular dash with spaces',
    '\u2013',
    encode_base64(' - '),
    'cleanup',
    true,
    9
);

-- Reduce Blank Lines (Order: 10)
SELECT upsert_lyric_parsing_rule(
    'Reduce Blank Lines',
    'Remove excessive blank lines (max 1 blank line)',
    '\n{3,}',
    encode_base64('

'),
    'cleanup',
    true,
    10
);

-- ============================================================
-- SECTION DETECTION RULES
-- ============================================================

-- Section Label Detection (Order: 2)
-- Supports both Markdown bold (**Label**) and Suno bracket ([Label]) formats
SELECT upsert_lyric_parsing_rule(
    'Section Label Detection',
    'Detect section labels in Markdown bold or Suno bracket format (Intro, Verse, Chorus, etc.)',
    '^(\*\*\s*(Intro|Verse\s*\d+|Chorus|Bridge|Outro|Pre[-_\s]?chorus|Post[-_\s]?chorus)\s*\*\*|\[\s*(Intro|Verse\s*\d+|Chorus|Bridge|Outro|Pre[-_\s]?chorus|Post[-_\s]?chorus)\s*\])\s*$',
    encode_base64(''),
    'section',
    true,
    2
);

-- ============================================================
-- Cleanup and Statistics
-- ============================================================

-- Drop helper functions
DROP FUNCTION IF EXISTS encode_base64;
DROP FUNCTION IF EXISTS upsert_lyric_parsing_rule;

-- Show results
DO $$
DECLARE
    total_count INTEGER;
    active_count INTEGER;
    cleanup_count INTEGER;
    section_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM lyric_parsing_rules;
    SELECT COUNT(*) INTO active_count FROM lyric_parsing_rules WHERE active = true;
    SELECT COUNT(*) INTO cleanup_count FROM lyric_parsing_rules WHERE rule_type = 'cleanup' AND active = true;
    SELECT COUNT(*) INTO section_count FROM lyric_parsing_rules WHERE rule_type = 'section' AND active = true;

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Seeding completed successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total rules in DB:    %', total_count;
    RAISE NOTICE 'Active rules:         %', active_count;
    RAISE NOTICE '  - Cleanup rules:    %', cleanup_count;
    RAISE NOTICE '  - Section rules:    %', section_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Rules by type (ordered):';
    RAISE NOTICE '';
END $$;

-- Show rules by type and order
SELECT
    rule_type,
    "order",
    name,
    CASE WHEN active THEN '✓' ELSE '✗' END as active
FROM lyric_parsing_rules
ORDER BY rule_type, "order";

COMMIT;
