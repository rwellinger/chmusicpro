# thWelly's AI Toolbox

**Your AI-powered music production workflow** — from first idea to finished release.

Capture song ideas, write lyrics with AI assistance, generate full songs, create cover art, and manage your music projects — all in one self-hosted application.

[![Build Status](https://github.com/rwellinger/thwellys-ai-toolbox/actions/workflows/release.yml/badge.svg)](https://github.com/rwellinger/thwellys-ai-toolbox/actions)
[![License: ELv2](https://img.shields.io/badge/License-ELv2-blue.svg)](LICENSE)
[![Angular](https://img.shields.io/badge/Angular-20-red.svg)](https://angular.io/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

---

## The Workflow

```
Idea → Sketch → Lyrics → Song → Cover → Project
```

| Stage | What happens | AI helps with |
|-------|--------------|---------------|
| **Idea** | Capture a musical concept or mood | — |
| **Sketch** | Structure your idea with title, genre, mood | Generate catchy titles |
| **Lyrics** | Write verses, chorus, bridge | Improve, rewrite, extend lyrics |
| **Song** | Generate full audio from lyrics | Use your own tool (Suno, Mureka, etc.) |
| **Cover** | Create album artwork | Image generation (DALL-E 3) |
| **Project** | Organize files, sync with DAW | S3 storage, CLI integration |

---

## Features

### Song Sketches
Capture and organize your song ideas before they slip away. Tag with genre, mood, and tempo. Track workflow status (draft, ready, used, archived). Convert sketches directly to full songs when you're ready.

### Lyric Creation
Section-based editor for verses, choruses, bridges, and more. AI-powered tools help you improve phrasing, rewrite weak lines, or extend sections. Build your song architecture with drag & drop, then export to the music generator.

### Music Generation
Use your preferred AI music generation tool (such as Suno, Mureka, or others) to generate songs from your lyrics. Export lyrics directly from the lyric editor in the format your tool needs. Prompt suggestions and lyric formatting are optimized for the most popular AI music generation tools.

### Cover Art
DALL-E 3 integration creates album artwork. One-click AI prompt enhancement for better results. Built-in text overlay editor adds titles and artist names. Gallery view keeps all your artwork organized.

### Project Management
Complete file management for music production. Hierarchical folder structure (Arrangement, Mixing, Stems, etc.) mirrors your DAW project. S3 cloud storage with batch upload/download. CLI tool syncs files between cloud and local DAW folder.

### AI Chat Assistant
Multi-model support via Ollama (Llama, Mistral, etc.). Persistent conversation history. Use it for brainstorming, research, or general creative assistance.

### Equipment Tracking
Track your music production software, plugins, and gear. Secure credential storage (encrypted). License management for iLok, online activations, and serial keys.

---

## API Keys & Costs

**This project is free and open source.** However, some AI features require API keys from external providers that may incur usage costs:

| Feature | Provider | Cost |
|---------|----------|------|
| Cover Art Generation | [OpenAI](https://platform.openai.com/) (DALL-E 3) | Pay-per-use |
| AI Chat (cloud) | [OpenAI](https://platform.openai.com/) or [Anthropic](https://console.anthropic.com/) | Pay-per-use |
| AI Chat (local) | [Ollama](https://ollama.ai/) | Free (runs locally) |

**Important:**
- All API keys are configured in your local `.env` file on your own infrastructure
- You obtain and manage API keys directly with each provider
- The project author has no access to your keys or usage data
- Ollama provides a free, local alternative for AI chat features

---

## Quick Start

### Prerequisites

- Python 3.12+ with Conda/Miniconda
- Node.js 20+ with npm
- Docker (via Colima on macOS)
- PostgreSQL 15+
- Redis

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/rwellinger/thwellys-ai-toolbox.git
   cd thwellys-ai-toolbox
   ```

2. **Backend Setup**
   ```bash
   cd aiproxysrv
   conda create -n mac_ki_service_py312 python=3.12
   conda activate mac_ki_service_py312
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
   cd aiwebui
   npm install
   npm run dev
   ```

4. **Start Celery Worker** (for async tasks like music generation)
   ```bash
   python src/worker.py
   ```

---

## For Developers

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Angular 20, TypeScript, Angular Material, SCSS, RxJS |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic 2.0 |
| **Async Processing** | Celery 5.4, Redis |
| **Database** | PostgreSQL 15 |
| **Storage** | S3-compatible (MinIO, AWS S3, Backblaze B2) |
| **AI Services** | OpenAI (DALL-E 3, GPT), Ollama |
| **Deployment** | Docker, Docker Compose, Nginx, GitHub Actions |
| **Code Quality** | Ruff (Python), ESLint (TypeScript), import-linter |

### Architecture

This project follows a **3-layer architecture** with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Angular 20)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │  Pages  │  │Services │  │Components│  │ ApiConfigService│ │
│  └────┬────┘  └────┬────┘  └─────────┘  └────────┬────────┘ │
└───────┼────────────┼────────────────────────────┼───────────┘
        │            │                            │
        ▼            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
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
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │  S3 Storage  │
└──────────────┘  └──────────────┘  └──────────────┘
```

For detailed architecture documentation, see [docs/arch42/README.md](docs/arch42/README.md).

### Project Structure

```
thwellys-ai-toolbox/
├── aiproxysrv/          # Python Backend (FastAPI)
│   ├── src/
│   │   ├── adapters/    # External API clients (OpenAI, Ollama)
│   │   ├── api/         # Controllers & Routes
│   │   ├── business/    # Business logic (transformers, orchestrators)
│   │   ├── db/          # Repository layer (SQLAlchemy)
│   │   └── celery_app/  # Async task processing
│   └── fonts/           # Font files for text overlays
│
├── aiwebui/             # Angular 20 Frontend
│   └── src/app/
│       ├── pages/       # Feature pages
│       ├── services/    # API services
│       ├── components/  # Shared components
│       └── models/      # TypeScript interfaces
│
├── scripts/
│   ├── build/           # Release & build automation
│   ├── cli/             # CLI tool (aiproxy-cli)
│   └── db/              # Database seeding
│
├── forwardproxy/        # Nginx reverse proxy
└── docs/                # Documentation (arc42, patterns)
```

### API Documentation

The backend provides auto-generated OpenAPI documentation:
- **Swagger UI**: `http://localhost:5050/docs`
- **ReDoc**: `http://localhost:5050/redoc`

### CLI Tool

The CLI tool integrates with your local DAW workflow:

```bash
# Install
make install-cli

# Login
aiproxy-cli login

# Clone project to local folder
aiproxy-cli clone <project-id> ~/Music/Projects/ -d

# Mirror sync (local to cloud)
aiproxy-cli mirror <project-id> <folder-id> ~/path --dry-run
```

See [scripts/cli/README.md](scripts/cli/README.md) for full documentation.

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
- **CLI Tool**: [scripts/cli/README.md](scripts/cli/README.md) - Command-line interface

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

- [OpenAI](https://openai.com/) - DALL-E 3 and GPT APIs
- [Ollama](https://ollama.ai/) - Local LLM infrastructure
- [Angular](https://angular.io/) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
