# Troubleshooting Guide

**Project:** Multi-AI Creative Platform
**Last Updated:** 2025-10-22

---

## CSS Layout Issues

### Horizontal Scrollbar (Overflow)

**Quick Diagnosis:**
```javascript
// Run in Browser Console to find overflowing elements
document.querySelectorAll('*').forEach(el => {
    if (el.scrollWidth > el.clientWidth) {
        console.log('Overflow:', el.tagName, el.className, el);
    }
});
```

**Common Causes:**
1. **Tables without fixed layout:**
   ```scss
   table {
     table-layout: fixed;
     width: 100%;
   }
   ```

2. **Flex containers without min-width:**
   ```scss
   .flex-item {
     min-width: 0; // Allows flex items to shrink below content size
   }
   ```

3. **Fixed width elements in responsive layouts:**
   ```scss
   // ❌ BAD
   .sidebar {
     width: 300px;
   }

   // ✅ GOOD
   .sidebar {
     width: min(300px, 100%);
   }
   ```

4. **Browser cache:**
   - Hard Refresh: `Cmd+Shift+R` (macOS)
   - Clear cache and reload

### Vertical Layout Issues

**Sticky footer not working:**
```scss
// ❌ BAD
.container {
  min-height: 100vh;
}

// ✅ GOOD
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content {
  flex: 1;
}
```

---

## Backend Issues

### PostgreSQL

#### Container not starting
```bash
# From project root
docker compose ps postgres
docker compose logs postgres

# Check if port is already in use
lsof -i :5432

# Restart container
docker compose restart postgres

# Nuclear option: Remove and recreate
docker compose down postgres
docker volume rm mac_ki_service_postgres_data
docker compose up -d postgres
```

#### Cannot connect to database
```bash
# From project root
docker exec -it mac_ki_service-postgres-1 psql -U aiuser -d aiproxy

# Test connection from host
psql -h localhost -U aiuser -d aiproxy -W

# Check credentials in .env
cat aiproxysrv/.env_postgres
```

#### Database migration issues
```bash
# From aiproxysrv directory
# IMPORTANT: Run from aiproxysrv/ root (where alembic.ini is located)!

# Check current migration version
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Auto-generate migration (DANGEROUS - always review!)
alembic revision --autogenerate -m "description"
```

### Celery Worker

#### Worker not processing tasks
```bash
# From aiproxysrv directory

# Check if worker is running
celery -A src.worker inspect active

# Check worker status
celery -A src.worker inspect stats

# Monitor tasks in real-time (Flower)
celery -A src.worker flower
# Open: http://localhost:5555

# Restart worker
pkill -f "celery worker"
python src/worker.py
```

#### Tasks stuck in pending
```bash
# Check Redis connection
docker compose ps redis
docker compose logs redis

# Connect to Redis CLI
docker exec -it mac_ki_service-redis-1 redis-cli

# List all keys
> KEYS *

# Check queue length
> LLEN celery

# Clear all tasks (DANGEROUS!)
> FLUSHALL
```

### FastAPI Server

#### Server won't start
```bash
# From aiproxysrv directory

# Check if port is in use
lsof -i :5050

# Kill process using port
kill -9 <PID>

# Check Python environment
conda activate mac_ki_service_py312
which python
python --version

# Check for errors in config
python src/server.py

# Check logs
tail -f logs/app.log
```

#### API endpoints not responding
```bash
# Test health endpoint
curl http://localhost:5050/api/health

# Test with verbose output
curl -v http://localhost:5050/api/health

# Test with authentication
curl -H "Authorization: Bearer <token>" http://localhost:5050/api/users/profile

# Check API documentation
open http://localhost:5050/docs
```

---

## Frontend Issues

### Angular Development Server

#### Server won't start
```bash
# From aiwebui directory

# Check Node version
node --version  # Should be 18.x or 20.x

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
lsof -i :4200

# Start with verbose output
npm run dev -- --verbose
```

#### Build errors
```bash
# From aiwebui directory

# Clear Angular cache
rm -rf .angular/cache

# Run build with detailed errors
npm run build:prod -- --verbose

# Check TypeScript config
npx tsc --noEmit

# Check for linting errors
npm run lint
```

### Translation Issues

#### Missing translations
```bash
# From aiwebui directory

# Check translation files exist
ls -la src/assets/i18n/

# Verify JSON structure
cat src/assets/i18n/en.json | jq .
cat src/assets/i18n/de.json | jq .

# Check for duplicate keys
cat src/assets/i18n/en.json | jq 'paths(scalars) as $p | "\($p | join("."))"' | sort | uniq -d
```

---

## Docker Issues

### Container won't start

```bash
# From project root

# Check container logs
docker compose logs [service-name]

# Check all container statuses
docker compose ps

# Rebuild without cache
docker compose build --no-cache [service-name]

# Remove and recreate
docker compose down [service-name]
docker compose up -d [service-name]

# Nuclear option: Clean everything
docker compose down -v
docker system prune -af --volumes
docker compose up -d
```

### Port conflicts

```bash
# Check which process uses port
lsof -i :5050  # Backend
lsof -i :4200  # Frontend dev
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process using port
kill -9 <PID>

# Change port in docker-compose.yml if needed
vim docker-compose.yml
```

### Volume issues

```bash
# From project root

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mac_ki_service_postgres_data

# Remove volume (DANGEROUS - data loss!)
docker compose down
docker volume rm mac_ki_service_postgres_data

# Backup volume before removal
docker run --rm -v mac_ki_service_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Network issues

```bash
# From project root

# Check network
docker network ls
docker network inspect mac_ki_service_default

# Recreate network
docker compose down
docker network rm mac_ki_service_default
docker compose up -d
```

---

## External API Issues

### OpenAI API

#### Rate limit errors
```bash
# Check account limits
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Implement exponential backoff in code
# Wait 1s, 2s, 4s, 8s between retries
```

#### Authentication errors
```bash
# Verify API key in .env
cat aiproxysrv/.env | grep OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Mureka API

#### Job status not updating
```bash
# Check Celery worker is running
celery -A src.worker inspect active

# Check Redis for stuck jobs
docker exec -it mac_ki_service-redis-1 redis-cli
> KEYS celery-task-meta-*

# Manually check job status
curl https://api.mureka.ai/v1/jobs/<job_id> \
  -H "Authorization: Bearer $MUREKA_API_KEY"
```

### Ollama API

#### Model not found
```bash
# List available models
curl http://localhost:11434/api/tags

# Pull model
ollama pull llama2

# Check Ollama is running
ps aux | grep ollama
```

#### Connection refused
```bash
# Check Ollama service
brew services list | grep ollama

# Restart Ollama
brew services restart ollama

# Check Ollama logs
tail -f ~/.ollama/logs/server.log
```

---

## Performance Issues

### Slow API responses

**Diagnosis:**
```bash
# From aiproxysrv directory

# Check database query performance
# Add logging in SQLAlchemy models:
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Profile API endpoints with time decorator
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper
```

**Solutions:**
1. Add database indexes
2. Use Redis caching
3. Optimize SQLAlchemy queries (use `.joinedload()` for relationships)
4. Implement pagination for large datasets

### High memory usage

**Frontend:**
```typescript
// Check for memory leaks
// Always unsubscribe from observables
private destroy$ = new Subject<void>();

ngOnDestroy(): void {
  this.destroy$.next();
  this.destroy$.complete();
}

// Use takeUntil in subscriptions
this.service.getData()
  .pipe(takeUntil(this.destroy$))
  .subscribe(...);
```

**Backend:**
```python
# Check memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Close database sessions properly
try:
    # ... database operations
finally:
    db.close()
```

---

## Debugging Tips

### Enable Debug Logging

**Backend:**
```bash
# From aiproxysrv directory
# Edit .env
DEBUG=true
LOG_LEVEL=DEBUG
```

**Frontend:**
```typescript
// In environment.ts
export const environment = {
  production: false,
  debug: true
};
```

### Browser DevTools

**Network Tab:**
- Check API response times
- Inspect request/response headers
- View payload data

**Console Tab:**
- Check for JavaScript errors
- View console.log outputs
- Test API calls manually

**Application Tab:**
- Inspect localStorage/sessionStorage
- View JWT token contents (jwt.io)
- Check service worker status

### VS Code Debugging

**Backend (Python):**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.server:app", "--reload"],
      "cwd": "${workspaceFolder}/aiproxysrv",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/aiproxysrv"
      }
    }
  ]
}
```

**Frontend (Angular):**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "ng serve",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:4200",
      "webRoot": "${workspaceFolder}/aiwebui",
      "sourceMapPathOverrides": {
        "webpack:/*": "${webRoot}/*"
      }
    }
  ]
}
```

---

## Emergency Recovery

### Database Corruption

```bash
# From project root

# 1. Stop all services
docker compose down

# 2. Backup current database (if possible)
docker run --rm -v mac_ki_service_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_emergency_backup.tar.gz /data

# 3. Remove corrupted volume
docker volume rm mac_ki_service_postgres_data

# 4. Recreate database
docker compose up -d postgres

# 5. Restore from backup (if available)
# ... restore commands ...

# 6. Apply migrations
cd aiproxysrv
alembic upgrade head

# 7. Run seed scripts
cd ..
cat scripts/db/seed_prompts.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
```

### Complete System Reset

```bash
# ⚠️ DANGER: This will delete ALL data!

# From project root
docker compose down -v
docker system prune -af --volumes
rm -rf aiproxysrv/.angular/cache
rm -rf aiwebui/node_modules
rm -rf aiwebui/dist

# Rebuild everything
docker compose up -d postgres redis
cd aiproxysrv && alembic upgrade head && cd ..
cd aiwebui && npm install && npm run build:prod && cd ..
docker compose up -d
```

---

## Angular Material Styling Issues

### Problem: SCSS Styles werden nicht angewendet (Component-Level)

**Symptom:** SCSS-Änderungen in Component-Dateien greifen nicht, selbst mit `ViewEncapsulation.None` und `!important`.

**Root Cause:**
- Angular Material Custom Elements (wie `mat-panel-title`, `mat-expansion-panel-header`) werden in separate Lazy-Loaded Chunks kompiliert
- Component-SCSS wird später geladen als Angular Material Styles
- Selektoren mit CSS-Klassen (`.mat-panel-title`) funktionieren oft nicht, weil es Custom Elements sind

**Debugging-Prozess:**

1. **Test mit extremen Styles** (in `styles.scss`):
   ```scss
   // Try multiple selector variations with extreme colors
   mat-panel-title {
     background-color: pink !important;  // Custom element selector
   }

   .mat-panel-title {
     background-color: red !important;   // Class selector
   }

   mat-expansion-panel-header {
     background-color: orange !important;
   }
   ```

2. **Build und Hard-Refresh** (Cmd+Shift+R / Strg+Shift+R)

3. **Welche Farbe siehst Du?**
   - Das zeigt, welcher Selector tatsächlich greift
   - Beispiel: Pink (#ffc0cb) → `mat-panel-title` funktioniert!

4. **Finalen Style anwenden**:
   ```scss
   // In styles.scss (global!)
   mat-panel-title {
     display: flex !important;
     align-items: center !important;
     gap: $spacing-xs !important;

     i {
       font-size: $font-sm !important;
       color: $primary-color !important;
     }
   }
   ```

**Wichtig:**
- ✅ **Immer in `src/styles.scss`** (global), nicht in Component-SCSS
- ✅ **Custom Element Selektoren** (`mat-panel-title`) statt Klassen (`.mat-panel-title`)
- ✅ **!important verwenden** um Angular Material zu überschreiben
- ✅ **Extreme Test-Styles** zum Debuggen (dann sieht man sofort, ob es greift)

**Beispiel-Fall:**
- Problem: Icons in `mat-expansion-panel` Titeln wurden nicht angezeigt
- Lösung: `mat-panel-title` (ohne Punkt!) in `styles.scss` mit `!important`
- Commit: "feat(text-overlay): Add icons to accordion panel titles"
