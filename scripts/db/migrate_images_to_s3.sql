-- =====================================================================
-- Migration: Filesystem Images → MinIO S3
-- =====================================================================
-- Purpose: Migrate existing filesystem images to S3-compatible storage
-- Date: 2025-11-02
--
-- Prerequisites:
--   1. All images with storage_backend='filesystem' must be manually uploaded to MinIO
--   2. MinIO bucket: ai-generated-images
--   3. Upload path: ai-generated-images/shared/<filename>
--   4. IMPORTANT: Use original filename from 'filename' column (NOT UUID!)
--
-- Execution:
--   cat scripts/db/migrate_images_to_s3.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
--
-- Rollback (if needed):
--   UPDATE generated_images
--   SET storage_backend = 'filesystem', s3_key = NULL
--   WHERE storage_backend = 's3' AND s3_key LIKE 'shared/%' AND s3_key NOT LIKE 'shared/%-%-%-%-%';
-- =====================================================================

-- Start transaction
BEGIN;

-- Show current state BEFORE migration
SELECT
    storage_backend,
    COUNT(*) AS image_count
FROM generated_images
GROUP BY storage_backend
ORDER BY storage_backend;

-- Migrate filesystem images to S3
UPDATE generated_images
SET
    storage_backend = 's3',
    s3_key = 'shared/' || filename
WHERE
    storage_backend = 'filesystem';

-- Show affected rows
SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'Migration successful: ' || COUNT(*) || ' images migrated'
        ELSE 'No images to migrate'
    END AS migration_result
FROM generated_images
WHERE storage_backend = 's3' AND s3_key LIKE 'shared/%' AND s3_key NOT LIKE 'shared/%-%-%-%-%';

-- Show current state AFTER migration
SELECT
    storage_backend,
    COUNT(*) AS image_count
FROM generated_images
GROUP BY storage_backend
ORDER BY storage_backend;

-- Commit transaction
COMMIT;

-- Display sample migrated images (for verification)
SELECT
    id,
    filename,
    s3_key,
    storage_backend,
    created_at
FROM generated_images
WHERE storage_backend = 's3' AND s3_key LIKE 'shared/%' AND s3_key NOT LIKE 'shared/%-%-%-%-%'
ORDER BY created_at DESC
LIMIT 5;
