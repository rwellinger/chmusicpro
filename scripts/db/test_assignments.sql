-- Test Script: Check Project Assignments
-- Run after manual UI testing with:
-- cat scripts/test_assignments.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv

-- 1. Check Song Assignment (1:1 relationship)
SELECT
    'SONG ASSIGNMENT' as type,
    s.id::text as entity_id,
    s.title,
    s.project_id::text,
    s.project_folder_id::text,
    sp.project_name,
    pf.folder_name
FROM songs s
LEFT JOIN song_projects sp ON s.project_id = sp.id
LEFT JOIN project_folders pf ON s.project_folder_id = pf.id
WHERE s.project_id IS NOT NULL
ORDER BY s.created_at DESC
LIMIT 5;

-- 2. Check Sketch Assignment (1:1 relationship)
SELECT
    'SKETCH ASSIGNMENT' as type,
    sk.id::text as entity_id,
    sk.title,
    sk.project_id::text,
    sk.project_folder_id::text,
    sp.project_name,
    pf.folder_name
FROM song_sketches sk
LEFT JOIN song_projects sp ON sk.project_id = sp.id
LEFT JOIN project_folders pf ON sk.project_folder_id = pf.id
WHERE sk.project_id IS NOT NULL
ORDER BY sk.created_at DESC
LIMIT 5;

-- 3. Check Image Assignment (N:M relationship via project_image_references)
SELECT
    'IMAGE ASSIGNMENT' as type,
    pir.id::text as reference_id,
    gi.id::text as image_id,
    gi.title,
    pir.project_id::text,
    pir.folder_id::text,
    sp.project_name,
    pf.folder_name
FROM project_image_references pir
LEFT JOIN generated_images gi ON pir.image_id = gi.id
LEFT JOIN song_projects sp ON pir.project_id = sp.id
LEFT JOIN project_folders pf ON pir.folder_id = pf.id
ORDER BY pir.created_at DESC
LIMIT 5;
