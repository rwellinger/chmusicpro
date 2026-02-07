# CI/CD Documentation

**Project:** Multi-AI Creative Platform
**Last Updated:** 2025-10-22

---

## GitHub Actions Setup

### Configuration

- **Platform:** GitHub Actions (hosted)
- **Trigger:** Git tag push (`v*.*.*`)
- **Workflow File:** `.github/workflows/release.yml`
- **Registry:** GitHub Container Registry (GHCR)
- **Architecture:** ARM64 only (linux/arm64)

### Build Triggers

#### Automatic
- **Tag Push:** `v*.*.*` → Full build & push to GHCR
- Triggered by: `./scripts/build/create_release.sh v2.2.6`

#### Manual
- GitHub UI: Actions → "Build & Release" → "Run workflow"
- Or: Re-run failed builds

---

## Pipeline Steps

1. **Checkout:** Clone repository
2. **QEMU Setup:** Enable ARM64 emulation
3. **Buildx:** Multi-platform Docker builds
4. **Login GHCR:** Automatic via `GITHUB_TOKEN`
5. **Build Images:** Parallel builds with layer caching
   - `aiproxysrv-app` (backend)
   - `celery-worker-app` (worker)
   - `aiwebui-app` (frontend)
6. **Lint:** ESLint on Angular code (parallel job)

---

## Build Performance

### Build Time
- **Expected:** ~10-12 minutes
- **First build:** ~15 minutes (no cache)
- **Subsequent:** ~8-10 minutes (with cache)

### Cost (GitHub Free Tier)
- **2000 minutes/month** for private repos
- Linux runners: 1x multiplier
- ~10-12 min/build = **~166 builds/month free**

---

## Secrets & Authentication

### Automatically Available
- `GITHUB_TOKEN` - Auto-generated for GHCR push access
- No manual configuration needed

---

## Monitoring

### Build Status

**Via GitHub UI:**
```
https://github.com/rwellinger/thwellys-ai-toolbox/actions
```

**Via gh CLI:**
```bash
gh run list --repo rwellinger/thwellys-ai-toolbox
gh run watch --repo rwellinger/thwellys-ai-toolbox
```

**Badge for README:**
```markdown
[![Build Status](https://github.com/rwellinger/thwellys-ai-toolbox/actions/workflows/release.yml/badge.svg)](https://github.com/rwellinger/thwellys-ai-toolbox/actions)
```

---

## Troubleshooting

### Build schlägt fehl

**Check logs:**
```bash
# Via GitHub UI
https://github.com/rwellinger/thwellys-ai-toolbox/actions

# Via CLI
gh run view --repo rwellinger/thwellys-ai-toolbox

# Re-run failed build
gh run rerun <RUN_ID> --repo rwellinger/thwellys-ai-toolbox
```

### Images nicht in GHCR

**Check GHCR packages:**
```bash
https://github.com/rwellinger?tab=packages
```

**Verify GITHUB_TOKEN permissions:**
1. Actions → Workflow → Settings → Permissions
2. Ensure "Read and write permissions" for packages

### Fallback: Manuelle Builds

**Falls GitHub Actions nicht verfügbar:**
```bash
./scripts/build/build-and-push-aiproxysrv.sh v2.2.6
./scripts/build/build-and-push-aiwebui.sh v2.2.6
```

---

## Release Workflow

### Creating a Release

1. **Local Testing:**
   ```bash
   # From aiwebui/
   npm run build:prod
   npm run lint

   # From aiproxysrv/
   ruff check . --fix && ruff format .
   pytest -v -s
   ```

2. **Create Release Tag:**
   ```bash
   # From project root
   ./scripts/build/create_release.sh v2.2.6
   ```

3. **Monitor Build:**
   - Check GitHub Actions for build status
   - Verify images in GHCR: `https://github.com/rwellinger?tab=packages`

4. **Deploy to Production:**
   ```bash
   # SSH to production server
   cd /path/to/mac_ki_service

   # Pull new images
   docker compose pull

   # Restart services
   docker compose up -d

   # Verify deployment
   docker compose logs -f
   ```

### Version Numbering

- **Format:** `vMAJOR.MINOR.PATCH`
- **Examples:**
  - `v2.0.0` - Major release (breaking changes)
  - `v2.1.0` - Minor release (new features)
  - `v2.1.1` - Patch release (bug fixes)

---

## Image Tags

### GHCR Registry Structure
```
ghcr.io/rwellinger/thwellys-ai-toolboxsrv-app:v2.2.6
ghcr.io/rwellinger/celery-worker-app:v2.2.6
ghcr.io/rwellinger/aiwebui-app:v2.2.6
```

### Tag Strategies
- **Versioned Tags:** `v2.2.6` (immutable)
- **Latest Tag:** `latest` (automatically updated)

---

## Local Build Scripts

### Backend (aiproxysrv)
```bash
# From project root
./scripts/build/build-and-push-aiproxysrv.sh v2.2.6
```

### Frontend (aiwebui)
```bash
# From project root
./scripts/build/build-and-push-aiwebui.sh v2.2.6
```

### Full Release
```bash
# From project root
./scripts/build/create_release.sh v2.2.6
```

---

## Best Practices

### Before Creating a Release
1. ✅ All tests pass locally (`pytest`, `npm run test`)
2. ✅ Linting passes (`ruff`, `npm run lint`)
3. ✅ Database migrations applied (`alembic upgrade head`)
4. ✅ No uncommitted changes (`git status`)
5. ✅ Version numbers updated in package files

### After Deployment
1. ✅ Verify services are running (`docker compose ps`)
2. ✅ Check logs for errors (`docker compose logs -f`)
3. ✅ Test critical workflows (login, image generation, song generation)
4. ✅ Verify database migrations applied on production
5. ✅ Monitor application for first 30 minutes

---

## Rollback Procedure

**If deployment fails:**

1. **Identify last working version:**
   ```bash
   gh run list --repo rwellinger/thwellys-ai-toolbox --limit 10
   ```

2. **Rollback Docker images:**
   ```bash
   # On production server
   docker compose down

   # Edit docker-compose.yml to use previous version tag
   vim docker-compose.yml

   # Restart with old version
   docker compose up -d
   ```

3. **Rollback database (if needed):**
   ```bash
   # From aiproxysrv/ directory
   alembic downgrade -1  # Downgrade one migration
   ```

4. **Verify rollback:**
   ```bash
   docker compose logs -f
   curl http://localhost:5050/api/health
   ```
