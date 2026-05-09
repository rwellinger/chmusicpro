# Claude Code Configuration

**Last Updated:** 2026-05-09

---

# Critical Rules (Guardrails)

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

**Reference:** `sketch_controller.py` → `sketch_orchestrator.py` → `sketch_normalizer.py` + `sketch_service.py`

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

### External APIs ONLY via chmusicprosrv Proxy
- **ALL** external calls (OpenAI, Claude, S3) **MUST** go through backend
- **NEVER** call external APIs directly from Angular
- **NEVER** use S3 presigned URLs in Angular (browser can't access internal endpoints reliably)

**Why?** HTTPS/CORS, API keys in backend, internal services not accessible from browser

### S3 Resources: Backend Proxy Pattern (MANDATORY!)
```
✅ CORRECT:
Frontend → /api/v1/resource/{id} → Backend loads from S3 → Binary Response

❌ WRONG:
Frontend ← S3 presigned URL ← Backend
```

**Storage backend (Production):** Hetzner Object Storage (`hel1.your-objectstorage.com`), buckets prefixed `chmusicpro-*`. **Local dev:** MinIO via `develop-env/docker-compose.yml`.

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

## 3. Template-Driven AI Integration (MANDATORY)

**This is a Template-Driven Generation System using OpenAI/Claude — not a direct provider proxy.**

**Workflow:**
```
User Input → Load Template from DB → Validate → Unified Endpoint → Response
```

**Supported providers:** `openai`, `claude` (Ollama was removed; legacy `provider="ollama"` templates fall back to the configured external provider).

**Rules:**
- **ALL** template chat calls **MUST** use `/api/v1/ollama/chat/generate-unified` (URL kept for backwards compat)
- **ALL** operations **MUST** go through `ChatService` in frontend
- **NEVER** implement direct provider API calls from Angular
- **NEVER** use templates before they exist in DB

```typescript
// ✅ CORRECT
async myNewFeature(input: string): Promise<string> {
  return this.chatService.validateAndCallUnified('category', 'action', input);
}

// ❌ WRONG: Direct provider call from Angular
this.http.post('https://api.openai.com/v1/...', {...});
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

# Reference Implementations (Copy These!)

## Backend Patterns

| Pattern | Reference File | Purpose |
|---------|---------------|---------|
| **S3 Proxy** | `song_release_routes.py` → `serve_cover()` → `s3_proxy_service.py` | Serve S3 resources via backend |
| **3-Layer** | `sketch_controller.py` → `sketch_orchestrator.py` → `sketch_normalizer.py` | Testable business logic |
| **AI Integration** | Backend: `chat_controller.py`, Frontend: `chat.service.ts` | Template-driven OpenAI/Claude |
| **DB Migration** | `chmusicprosrv/src/alembic/versions/` | Schema changes |

## Frontend Patterns

| Pattern | Reference Component | Purpose |
|---------|-------------------|---------|
| **Master-Detail** | `equipment-gallery/` | List/Detail layout, buttons, icons |
| **AI Buttons** | `song-sketch-creator/` | Progress overlay, error handling |
| **Forms** | `song-release-editor/` | Validation, reactive forms |
| **i18n** | All components | `{{ 'key' | translate }}` |

**CRITICAL:** Read `docs/UI_PATTERNS.md` before creating new UI pages!

---

# Critical DON'Ts

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

# Terminology Mapping (Code vs. UI)

Internal code names (filenames, routes, DB tables) differ from what the user sees in the UI:

| Code / Filenames | UI Label | Notes |
|---|---|---|
| `sketch_*`, `song-sketch-*`, `songSketch.*` | **Composition** | Backend files + i18n keys still use "sketch" |
| `image_*`, `image-view`, `image-generator` | **Picture** | Backend files + routes still use "image" |
| `sketchLibrary` (menu key) | **Compositions** | Menu entry |
| `imageView` (page) | **Picture Gallery** | Page title |
| `imageGenerator` (page) | **Create Picture** | Page title |
| `coverArt` (pipeline step) | **Cover Art** | Pipeline + menu |
| `workshop`, `text-workshop` | **Text Workshop** / **Lyric Creation** | Pipeline step 1 |

**Important:** There is NO song generation feature (Mureka/Celery were removed). The app generates **text** (lyrics, descriptions, prompts) and **images** (gpt-image-1), not audio. Local Ollama support was also removed; only OpenAI and Claude are supported as AI providers.

---

**Last Review:** 2026-05-09
