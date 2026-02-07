# Claude Code Configuration

**Language:** English
**Last Updated:** 2025-11-10

---

# 🎯 Critical Rules (Guardrails)

## 1. 3-Layer Architecture (MANDATORY - Enforced by import-linter)

```
Controller → Orchestrator → Transformer/Normalizer + Repository
(HTTP)       (Coordinates)  (Pure Functions)      (DB CRUD)
```

**Naming Convention:**
- `*_orchestrator.py` - Coordinates services, NOT testable
- `*_transformer.py` - Pure functions, 100% testable
- `*_normalizer.py` - Pure functions, 100% testable
- `*_service.py` (in `db/`) - CRUD only, NOT testable

**Rules:**
- ✅ Business logic in transformers/normalizers (unit-testable)
- ❌ NO business logic in DB services (CRUD only)
- ❌ NO database queries in controllers (use orchestrator)

**Reference:** `sketch_controller.py` → `sketch_orchestrator.py` → `sketch_transformer.py` + `sketch_service.py`

---

## 2. API Routing & Security (PRODUCTION-CRITICAL!)

### All APIs MUST use ApiConfigService
```typescript
// ✅ CORRECT
private http = inject(HttpClient);
private apiConfig = inject(ApiConfigService);

getData() {
  return this.http.get(this.apiConfig.endpoints.category.action);
}

// ❌ WRONG
private baseUrl = 'http://localhost:5050/api';
```

### External APIs ONLY via aiproxysrv Proxy
- **ALL** external calls (OpenAI, Ollama, S3/MinIO) **MUST** go through backend
- **NEVER** call external APIs directly from Angular
- **NEVER** use S3 presigned URLs in Angular (Browser can't access internal MinIO!)

**Why?** HTTPS/CORS, API Keys in Backend, Internal services not accessible from Browser

### S3 Resources: Backend Proxy Pattern (MANDATORY!)
```
✅ CORRECT:
Frontend → /api/v1/resource/{id} → Backend loads from S3 → Binary Response

❌ WRONG:
Frontend ← MinIO presigned URL (https://minio:9000/...) ← Backend
          └─ Browser CAN'T access internal MinIO!
```

**Reference:** `song_release_routes.py` → `serve_cover()` → `s3_proxy_service.py`

### JWT Authentication REQUIRED
```python
# ✅ CORRECT
@api_user_v1.route("/profile", methods=["GET"])
@jwt_required
def get_user_profile():
    user_id = get_current_user_id()  # From JWT, NOT URL params!
```

---

## 3. Template-Driven Ollama Integration (MANDATORY)

**This is NOT a direct Ollama proxy - it's a Template-Driven Generation System!**

**Workflow:**
```
User Input → Load Template from DB → Validate → Unified Endpoint → Response
```

**Rules:**
- **ALL** Ollama+Template calls **MUST** use `/api/v1/ollama/chat/generate-unified`
- **ALL** operations **MUST** go through `ChatService` in frontend
- **NEVER** implement direct Ollama API calls
- **NEVER** use templates before they exist in DB

```typescript
// ✅ CORRECT
async myNewFeature(input: string): Promise<string> {
  return this.chatService.validateAndCallUnified('category', 'action', input);
}

// ❌ WRONG: Direct Ollama call
this.http.post('http://localhost:11434/api/generate', {...});
```

**Reference:** `chat.service.ts` → `validateAndCallUnified()`

---

## 4. Pre-Implementation Checklist (MANDATORY for External Resources!)

**Before implementing ANY feature that returns external resources (files, images, URLs):**

### Step 1: Pattern Search
```bash
# Does a similar feature exist?
grep -r "serve.*s3\|proxy.*resource" src/

# Found existing pattern? → COPY it 1:1
```

### Step 2: Use Backend Proxy Pattern
```
✅ Image S3 Proxy:
   Route: api/routes/image_routes.py → serve_s3_image()
   Service: adapters/s3/s3_proxy_service.py → serve_resource()

✅ Song Release Cover Proxy:
   Route: api/routes/song_release_routes.py → serve_cover()
   Service: adapters/s3/s3_proxy_service.py → serve_resource()
```

---

# 📚 Reference Implementations (Copy These!)

## Backend Patterns

| Pattern | Reference File | Purpose |
|---------|---------------|---------|
| **S3 Proxy** | `song_release_routes.py:123` → `s3_proxy_service.py` | Serve S3 resources via backend |
| **3-Layer** | `sketch_controller.py` → `sketch_orchestrator.py` → `sketch_transformer.py` | Testable business logic |
| **AI Integration** | Backend: `chat_controller.py`, Frontend: `chat.service.ts` | Template-driven Ollama |
| **DB Migration** | `aiproxysrv/src/alembic/versions/` | Schema changes |

## Frontend Patterns

| Pattern | Reference Component | Purpose |
|---------|-------------------|---------|
| **Master-Detail** | `equipment-gallery/` | List/Detail layout, buttons, icons |
| **AI Buttons** | `song-sketch-creator/` | Progress overlay, error handling |
| **Forms** | `song-release-editor/` | Validation, reactive forms |
| **i18n** | All components | `{{ 'key' | translate }}` |

**CRITICAL:** Read `docs/UI_PATTERNS.md` before creating new UI pages!

---

# 🛠️ Quick Commands

## Frontend (aiwebui)

```bash
# Code Quality & Build (ALWAYS run before commit!)
make build-prod                # Production build (linters + tests + compilation)
make lint-all                  # TypeScript + SCSS + Architecture only
make lint-fix                  # Auto-fix issues

# Build
make build-dev                 # Development build

# Development
make dev                       # Dev server
make test                      # Unit tests
make test-watch               # Tests in watch mode
```

## Backend (aiproxysrv)

```bash
# Activate conda environment first!
conda activate mac_ki_service_py312

# Development
python src/server.py           # Dev server

# Database
make db-current                # Show current version
make db-upgrade                # Apply migrations
make db-revision               # Create new migration

# Code Quality
make lint-all                  # Ruff + import-linter
make format                    # Auto-fix and format
make test                      # pytest
```

## Database Seeding

```bash
# From project root (mac_ki_service/)
cat scripts/db/seed_prompts.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
cat scripts/db/seed_lyric_parsing_rules.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
```

**DB Credentials:** See `.env` file (not committed to repository)

---

# ❌ Critical DON'Ts

## Backend
- ❌ NO business logic in DB layer (`src/db/*_service.py` = CRUD only)
- ❌ NO database queries in controllers (use orchestrator)
- ❌ NO `import logging` (use `from utils.logger import logger` - Loguru!)
- ❌ NO commits without `make lint-all`

## Frontend
- ❌ NO hardcoded URLs in services (use `ApiConfigService`)
- ❌ NO external API calls from Angular (go through backend)
- ❌ NO S3 presigned URLs in Angular (use backend proxy)
- ❌ NO constructor DI (use `inject()`)
- ❌ NO hardcoded text (use `{{ 'key' | translate }}`)
- ❌ NO deep SCSS nesting (max 2-3 levels)
- ❌ NO commits without `make build-prod` (runs linters + tests + production build)

## General
- ❌ NO `.env` files in commits
- ❌ NO emojis in code/docs (unless requested)
- ❌ NO unnecessary documentation files

---

# 📖 Full Documentation

**When you need details:**
- **Project Overview:** `README.md` (803 lines - Build, Features, Commands)
- **Architecture Deep-Dive:** `docs/arch42/README.md` (2000+ lines - arc42, ADRs, Workflows)
- **UI Patterns:** `docs/UI_PATTERNS.md` (CRITICAL - Read before new UI!)
- **Code Patterns:** `docs/CODE_PATTERNS.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **CI/CD:** `docs/CI_CD.md`

**External API Docs:**
- **Ollama:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **OpenAI:** https://platform.openai.com/docs/api-reference/introduction

---

# 🤖 How I (Claude) Use This File

**When you give me a task:**

1. **Check:** Does pattern exist? → Look at reference implementations
2. **Check:** S3 involved? → Use backend proxy pattern
3. **Check:** New UI page? → Read `docs/UI_PATTERNS.md` first
4. **Implement** → Code changes
5. **Validate:**
   - Frontend: `make build-prod` (linters + tests + compilation)
   - Backend: `make lint-all` (Ruff + import-linter)
6. **Done** → Ready for manual testing & commit

**When I need business context:**
→ I'll ask you! (Just-in-time explanation)

**What I DON'T need in this file:**
- Business logic details (you explain when needed)
- Complete feature specs (README.md has that)
- Detailed workflows (arc42/ has that)

---

# 🎯 Tech Stack Summary

**Frontend:** Angular 20, Material, SCSS, TypeScript, RxJS, ngx-translate
**Backend:** FastAPI, Python 3.12.12, SQLAlchemy, Alembic
**Database:** PostgreSQL
**Deployment:** Docker (Colima), Nginx
**Hardware:** Apple Silicon (M-Series), Python 3.12 via Conda

---

# 💬 Communication Style

- Code/Comments/Docs: English only
- Be factual and direct
- Present analysis, plan & effort estimation first

---

**Last Review:** 2025-11-10
