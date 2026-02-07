# Database Migration Process

**Version:** 1.0
**Last Updated:** 2025-10-21
**Author:** Rob Wellinger

---

## Overview

This document describes the reliable database migration process using Alembic with a dedicated init-container architecture.

### Key Principles

1. **Fail-Fast:** Migrations run BEFORE services start. Failed migrations prevent service startup.
2. **Idempotent:** Migrations can run multiple times safely (IF NOT EXISTS patterns).
3. **Verified:** Schema validation runs after every migration.
4. **Isolated:** Migrations run in dedicated container, not in application workers.

---

## Architecture

### Init-Container Pattern

```
docker-compose up -d
  ↓
postgres + redis start (with healthchecks)
  ↓
db-migration container starts:
  - Runs: alembic upgrade head
  - Runs: python scripts/verify_schema.py
  - Exit Code 0 ✅ → Container stops, services start
  - Exit Code ≠ 0 ❌ → Container stops, services DON'T start
  ↓
Only if db-migration succeeded:
  - celery-worker starts
  - aiproxysrv starts
```

**Benefits:**
- ✅ Clear separation: Migration ≠ Worker
- ✅ Visible logs: `docker logs db-migration`
- ✅ Production-safe: Failed migration keeps old services running
- ✅ No code duplication: Uses same image as backend

---

## Creating a New Migration

### Step 1: Create Migration File

```bash
# From aiproxysrv directory
cd src
alembic revision --autogenerate -m "add_feature_xyz"
```

**IMPORTANT:** `--autogenerate` is a starting point, NOT final code!

### Step 2: Review and Edit Migration

```bash
# Open generated file
vim src/alembic/versions/abc123_add_feature_xyz.py
```

**Use the template:**

```bash
# Copy template as reference
cp scripts/migration_template.py /tmp/template_reference.py
```

**Make it idempotent:**

```python
# ❌ BAD: Not idempotent
op.create_table("new_table", ...)

# ✅ GOOD: Idempotent
if not table_exists("new_table"):
    op.create_table("new_table", ...)
```

**Use helper functions from template:**
- `table_exists(table_name)`
- `column_exists(table_name, column_name)`
- `index_exists(index_name)`

### Step 3: Test on Development

```bash
# From aiproxysrv directory
docker-compose down
docker-compose up -d

# Check migration logs
docker logs db-migration

# Verify schema
docker exec -it aiproxysrv python scripts/verify_schema.py
```

**Expected output:**
```
✅ Schema verification PASSED!
   Tables verified: 10
   Critical columns checked: 42
```

### Step 4: Test Idempotency

Run migration again to verify it's idempotent:

```bash
docker-compose restart db-migration

# Should see:
# ℹ️  Table 'xyz' already exists, skipping creation
# ✅ Schema verification PASSED!
```

### Step 5: Test Rollback (Optional)

```bash
# Downgrade one version
docker exec -it db-migration alembic downgrade -1

# Check schema still valid
docker exec -it aiproxysrv python scripts/verify_schema.py

# Upgrade again
docker-compose restart db-migration
```

---

## Deploying to Production

### Pre-Deployment Checklist

- [ ] Migration tested on development
- [ ] Migration is idempotent (tested multiple runs)
- [ ] Rollback tested (or explicitly disabled with error message)
- [ ] Schema verification passes
- [ ] Breaking changes communicated (if any)
- [ ] Backup created

### Deployment Steps

**1. Create Database Backup**

```bash
# SSH to production
ssh rob@<production-server>

# Backup database
cd /path/to/mac_ki_service/aiproxysrv
./scripts/operation/dbbackup.sh

# Verify backup created
ls -lh ~/backup/*.sql.gz
```

**2. Pull Latest Code**

```bash
cd /path/to/mac_ki_service
git pull origin main

# Verify migration files are present
ls aiproxysrv/src/alembic/versions/
```

**3. Pull Latest Images**

```bash
cd aiproxysrv
docker-compose pull
```

**4. Run Migration**

```bash
# Stop services (but keep database running!)
docker-compose stop aiproxy-app celery-worker

# Run migration
docker-compose up -d db-migration

# Watch logs in real-time
docker logs -f db-migration
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add_feature_xyz
✅ Created table: new_table
✅ Added column: existing_table.new_column
🔍 Verifying database schema...
✅ Schema verification PASSED!
```

**5. Start Services**

```bash
# If migration succeeded
docker-compose up -d

# Check all services started
docker ps

# Check logs
docker logs aiproxysrv
docker logs celery-worker
```

**6. Verify Application**

- Open frontend: https://<production-server>
- Test affected features
- Check browser console for errors
- Monitor backend logs

---

## Troubleshooting

### Migration Failed

**Symptoms:**
```bash
$ docker logs db-migration
ERROR: column "xyz" already exists
```

**Resolution:**

1. **Check if partially applied:**
   ```bash
   docker exec -it postgres psql -U aiproxy -d aiproxysrv
   \d table_name  -- Check actual table structure
   ```

2. **Fix migration to be idempotent:**
   ```python
   # Add IF NOT EXISTS check
   if not column_exists("table_name", "xyz"):
       op.add_column(...)
   ```

3. **Reset Alembic version if needed:**
   ```sql
   -- Only if migration state is inconsistent!
   UPDATE alembic_version SET version_num = 'previous_revision_id';
   ```

4. **Re-run migration:**
   ```bash
   docker-compose restart db-migration
   docker logs -f db-migration
   ```

### Schema Verification Failed

**Symptoms:**
```bash
❌ Schema verification FAILED!
  ❌ Table 'songs' missing column: sketch_id
```

**Resolution:**

1. **Check what actually exists:**
   ```bash
   docker exec -it postgres psql -U aiproxy -d aiproxysrv -c "\d songs"
   ```

2. **If column missing, apply manually:**
   ```sql
   ALTER TABLE songs ADD COLUMN sketch_id UUID;
   CREATE INDEX ix_songs_sketch_id ON songs(sketch_id);
   ```

3. **Re-verify:**
   ```bash
   docker exec -it aiproxysrv python scripts/verify_schema.py
   ```

### Services Won't Start

**Symptoms:**
```bash
$ docker ps
# db-migration shows "Exited (1)"
# Other services not starting
```

**Resolution:**

1. **Check migration logs:**
   ```bash
   docker logs db-migration
   ```

2. **If blocking issue, rollback:**
   ```bash
   # Restore from backup
   gunzip ~/backup/20251021_120000_aiproxy_full.sql.gz
   docker exec -i postgres psql -U aiproxy -d aiproxysrv < ~/backup/20251021_120000_aiproxy_full.sql
   ```

3. **Fix migration and retry:**
   - Edit migration file
   - Commit fix
   - Re-deploy

### Old Containers Still Running

**Expected behavior!** If migration fails, old containers keep running.

**To force update anyway (DANGEROUS):**

```bash
# Only if you're SURE migration is safe to skip
docker-compose down
docker-compose up -d --force-recreate
```

---

## Rollback Procedure

### Automatic Rollback (via Alembic)

```bash
# Downgrade one version
docker exec -it db-migration alembic downgrade -1

# Verify
docker exec -it aiproxysrv python scripts/verify_schema.py

# Restart services
docker-compose restart aiproxy-app celery-worker
```

### Manual Rollback (from Backup)

```bash
# 1. Stop all services
docker-compose down

# 2. Start only database
docker-compose up -d postgres

# 3. Restore backup
gunzip ~/backup/BACKUP_FILE.sql.gz
docker exec -i postgres psql -U aiproxy -d aiproxysrv < ~/backup/BACKUP_FILE.sql

# 4. Reset Alembic version
docker exec -it postgres psql -U aiproxy -d aiproxysrv \
  -c "UPDATE alembic_version SET version_num = 'PREVIOUS_REVISION_ID';"

# 5. Restart all services
docker-compose up -d
```

---

## Best Practices

### ✅ DO

- **Always test on development first**
- **Make migrations idempotent** (IF NOT EXISTS, IF EXISTS)
- **Add pre-flight checks** for destructive operations
- **Create backups** before production migration
- **Use template** from `scripts/migration_template.py`
- **Verify schema** after migration
- **Keep migrations small** (one logical change per migration)
- **Document breaking changes** in migration docstring

### ❌ DON'T

- **Never skip testing** on development
- **Never deploy untested migrations** to production
- **Never assume autogenerate is correct** (always review!)
- **Never drop columns with data** without backup
- **Never commit** without running `alembic upgrade head` locally
- **Never use** `--autogenerate` output without review
- **Never ignore** schema verification failures

---

## Reference

### Alembic Commands

```bash
# Current version
alembic current

# Migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade abc123

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade abc123

# Create migration (manual)
alembic revision -m "description"

# Create migration (autogenerate)
alembic revision --autogenerate -m "description"
```

### Helper Scripts

```bash
# Verify schema matches models
python scripts/verify_schema.py

# Create database backup
./scripts/operation/dbbackup.sh

# Export schema only (no data)
./scripts/operation/dbschema_export.sh

# Export schema to stdout
./scripts/operation/dbschema_export.sh -s
```

### Docker Commands

```bash
# View migration logs
docker logs db-migration

# Re-run migration
docker-compose restart db-migration

# Force recreate migration container
docker-compose up -d --force-recreate db-migration

# Interactive shell in migration container
docker run --rm -it \
  --network thwelly-net \
  -v $(pwd):/app \
  -v $(pwd)/alembic.ini:/app/alembic.ini:ro \
  --env-file .env \
  ghcr.io/rwellinger/aiproxysrv-app:v2.4.0 \
  /bin/bash
```

---

## Emergency Contacts

**Issues?**
- GitHub Issues: https://github.com/rwellinger/thwellys-ai-toolbox/issues

**Documentation:**
- ARC42 Docs: `docs/arch42/README.md`
- Migration Template: `scripts/migration_template.py`
- Schema Verification: `scripts/verify_schema.py`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-21 | Initial version with init-container architecture |
