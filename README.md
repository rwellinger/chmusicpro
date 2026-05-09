# thWelly's Song Production

**Your AI-powered music production workflow** — from first idea to finished release.

Capture song ideas, write lyrics with AI assistance, generate full songs, create cover art, and manage your music projects — all in one self-hosted application.

[![Build Status](https://github.com/rwellinger/chmusicpro/actions/workflows/release.yml/badge.svg)](https://github.com/rwellinger/chmusicpro/actions)
[![Angular](https://img.shields.io/badge/Angular-21-red.svg)](https://angular.dev/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

---

## The Workflow

```
Idea → Composition → Lyrics → Song → Cover → Project
```

| Stage | What happens | AI helps with |
|-------|--------------|---------------|
| **Idea** | Capture a musical concept or mood | — |
| **Composition** | Structure your idea with title, genre, mood | Generate catchy titles |
| **Lyrics** | Write verses, chorus, bridge | Improve, rewrite, extend lyrics |
| **Song** | Generate full audio from lyrics | Use your own tool (Suno, Udio, etc.) |
| **Cover** | Create album artwork | Image generation (OpenAI `gpt-image-1`) |
| **Project** | Organize files, sync with DAW | S3 storage (Hetzner), browser-based Mirror Sync |

---

## Features

### Song Compositions
Capture and organize your song ideas before they slip away. Tag with genre, mood, and tempo. Track workflow status (draft, ready, used, archived). Convert compositions directly to full songs when you're ready. Internally referred to as "sketches" in the codebase.

### Text Workshop
Dedicated lyric workspace for writing, editing, and refining song texts. Assign workshops to project folders for organized content management. Integrates with AI tools for lyric improvement and creative assistance.

### Lyric Creation
Section-based editor for verses, choruses, bridges, and more. AI-powered tools help you improve phrasing, rewrite weak lines, or extend sections. Build your song architecture with drag & drop, then export to the music generator.

### Music Generation
Use your preferred AI music generation tool (such as Suno, Udio, or others) to generate songs from your lyrics. Export lyrics directly from the lyric editor in the format your tool needs. Prompt suggestions and lyric formatting are optimized for the most popular AI music generation tools.

### Cover Art
OpenAI `gpt-image-1` integration creates album artwork. One-click AI prompt enhancement for better results. Built-in text overlay editor adds titles and artist names. Gallery view keeps all your artwork organized.

### Project Management
Complete file management for music production. Hierarchical folder structure (Arrangement, Mixing, Stems, etc.) mirrors your DAW project. S3 cloud storage with batch upload/download. Browser-based Mirror Sync for drag & drop file synchronization. ZIP download for project templates and individual folders.

### Pipeline Workflow
Guided 8-step production pipeline from lyric creation through distribution. Sticky step-bar with numbered circles shows your current progress. Dashboard tiles link directly to each pipeline stage.

### AI Chat Assistant
Provider support: OpenAI GPT and Anthropic Claude. Persistent conversation history. Reusable system context templates for consistent AI behavior. Use it for brainstorming, research, or general creative assistance.

### Equipment Tracking
Track your music production software, plugins, and gear. Secure credential storage (encrypted). License management for iLok, online activations, and serial keys.

---

## API Keys & Costs

**This project is free and open source.** However, some AI features require API keys from external providers that may incur usage costs:

| Feature | Provider | Cost |
|---------|----------|------|
| Cover Art Generation | [OpenAI](https://platform.openai.com/) (`gpt-image-1`) | Pay-per-use |
| AI Chat | [OpenAI](https://platform.openai.com/) or [Anthropic](https://console.anthropic.com/) | Pay-per-use |

**Important:**
- All API keys are configured in your local `.env` file on your own infrastructure
- You obtain and manage API keys directly with each provider
- The project author has no access to your keys or usage data

---

## Quick Start

### Prerequisites

- Python 3.12+ with Conda/Miniconda
- Node.js 20+ with npm
- Docker (via Colima on macOS) for local Postgres + MinIO
- PostgreSQL 15+ (provided via `develop-env/docker-compose.yml`)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:rwellinger/chmusicpro.git
   cd chmusicpro
   ```

2. **Backend Setup**
   ```bash
   cd chmusicprosrv
   conda create -n chmusicpro_py312 python=3.12
   conda activate chmusicpro_py312
   pip install -r requirements.txt

   # Copy and configure environment
   cp env_template .env
   # Edit .env with your API keys (OpenAI)

   # Run database migrations
   cd src && alembic upgrade head

   # Start backend
   python src/server.py
   ```

3. **Frontend Setup**
   ```bash
   cd chmusicproweb
   npm install
   npm run dev
   ```

---

## For Developers

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Angular 21, TypeScript, Angular Material, SCSS, RxJS |
| **Backend** | Python 3.12, Flask, SQLAlchemy 2.0, Pydantic 2.0 |
| **Database** | PostgreSQL 15 |
| **Storage** | S3 (Hetzner Object Storage in production, MinIO for local dev) |
| **AI Services** | OpenAI (`gpt-image-1`, GPT models), Anthropic Claude |
| **Deployment** | Docker, Docker Compose, Nginx, GitHub Actions |
| **Code Quality** | Ruff (Python), ESLint (TypeScript), import-linter |

### Architecture

This project follows a **3-layer architecture** with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Angular 21)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │  Pages  │  │Services │  │Components│  │ ApiConfigService│ │
│  └────┬────┘  └────┬────┘  └─────────┘  └────────┬────────┘ │
└───────┼────────────┼────────────────────────────┼───────────┘
        │            │                            │
        ▼            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (Flask)                          │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Controller │→ │ Orchestrator │→ │ Transformer/Service │  │
│  │  (HTTP)    │  │ (Coordinate) │  │  (Pure Functions)   │  │
│  └────────────┘  └──────┬──────┘  └──────────────────────┘  │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │              Repository Layer (CRUD)                  │   │
│  └───────────────────────┬──────────────────────────────┘   │
└──────────────────────────┼──────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
        ┌──────────────┐      ┌──────────────┐
        │  PostgreSQL  │      │  S3 Storage  │
        └──────────────┘      └──────────────┘
```

For detailed architecture documentation, see [docs/arch42/README.md](docs/arch42/README.md).

### Project Structure

```
chmusicpro/
├── chmusicprosrv/          # Python Backend (Flask)
│   ├── src/
│   │   ├── adapters/    # External API clients (OpenAI, Claude, S3)
│   │   ├── api/         # Controllers & Routes
│   │   ├── business/    # Business logic (transformers, orchestrators)
│   │   └── db/          # Repository layer (SQLAlchemy)
│   └── fonts/           # Font files for text overlays
│
├── chmusicproweb/             # Angular 21 Frontend
│   └── src/app/
│       ├── pages/       # Feature pages
│       ├── services/    # API services
│       ├── components/  # Shared components (pipeline-step-bar, etc.)
│       └── models/      # TypeScript interfaces
│
├── scripts/
│   ├── build/           # Release & build automation
│   └── db/              # Database seeding
│
├── forwardproxy/        # Nginx reverse proxy
└── docs/                # Documentation (arc42, patterns)
```

### API Documentation

The backend provides auto-generated OpenAPI documentation:
- **Swagger UI**: `http://localhost:5050/docs`
- **ReDoc**: `http://localhost:5050/redoc`

### Mirror Sync

Browser-based drag & drop file synchronization. Drop files into project folders for automatic hash-based comparison and selective upload, update, or delete. Files are filtered through `.chmusicproignore` patterns and compared via SHA-256 hashing. A preview dialog shows the diff before executing changes.

### Testing & Code Quality

```bash
# Backend
make lint-all     # Ruff + import-linter
make test         # pytest

# Frontend
make build-prod   # Linters + Tests + Production build
make lint-fix     # Auto-fix issues
```

---

## Deployment

For production deployment instructions including Docker Compose configurations, Nginx setup, and backup strategies, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Documentation

- **Architecture**: [docs/arch42/README.md](docs/arch42/README.md) - Comprehensive arc42 documentation
- **UI Patterns**: [docs/UI_PATTERNS.md](docs/UI_PATTERNS.md) - Frontend component patterns
- **Code Patterns**: [docs/CODE_PATTERNS.md](docs/CODE_PATTERNS.md) - Backend patterns
---

## License

This project is licensed under the [Elastic License 2.0 (ELv2)](LICENSE).

**You may:**
- Use, copy, and modify the software
- Use it for personal and commercial purposes
- Fork and create derivative works

**You may not:**
- Provide the software as a hosted/managed service (SaaS)
- Remove or alter license notices

---

## Author

**Robert Wellinger**

---

## Acknowledgments

- [OpenAI](https://openai.com/) - `gpt-image-1` and GPT APIs
- [Anthropic](https://www.anthropic.com/) - Claude APIs
- [Angular](https://angular.dev/) - Frontend framework
- [Flask](https://flask.palletsprojects.com/) - Backend framework
