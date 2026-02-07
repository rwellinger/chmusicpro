# Architecture Documentation

**Project:** Multi-AI Creative Platform

This project uses the **arc42 architecture template** for comprehensive documentation.

📖 **Full Architecture Documentation**: [`docs/arch42/README.md`](arch42/README.md)

---

## Quick Links

- [System Overview](arch42/README.md#51-system-overview) - Architecture layers & components
- [Database Schema](arch42/README.md#13-database-schema) - ER diagram & table definitions
- [API Endpoints](arch42/README.md#8-api-documentation) - Complete REST API reference
- [Directory Structure](arch42/README.md#52-component-details) - Frontend & backend layout
- [Deployment](arch42/README.md#7-deployment-view) - Dev & production environments
- [Design Patterns](arch42/README.md#4-solution-strategy) - Architecture approach
- [Runtime Views](arch42/README.md#6-runtime-view) - Sequence diagrams (Image, Song, Chat, Lyrics)
- [Quality Requirements](arch42/README.md#11-quality-requirements) - Performance, Security, Monitoring
- [Glossary](arch42/README.md#12-glossary) - Technical terms & definitions

---

## Quick Reference

### Tech Stack
- **Frontend**: Angular 20, Material Design, TypeScript, RxJS, ngx-translate
- **Backend**: FastAPI, Python 3.12.12, Celery, SQLAlchemy, Alembic
- **Database**: PostgreSQL, Redis
- **Deployment**: Docker (Colima), Nginx
- **Hardware**: Apple Silicon (M1/M4)

### Key Components
- **aiwebui**: Angular 20 frontend with Material Design
- **aiproxysrv**: FastAPI backend + proxy for external APIs (OpenAI, Mureka, Ollama)
- **forwardproxy**: Nginx reverse proxy (production)
- **aitestmock**: Mock API for cost-free testing

### Core Features
- **Image Generation** (DALL-E/OpenAI): Fast Enhancement, Gallery, Detail View
- **Song Generation** (Mureka API): Sketches, Styles, FLAC/MP3/Stems, Playback
- **Lyric Creation**: AI-assisted editor, Lyric Architect, Parsing Rules
- **Chat**: Ollama (local) & OpenAI, Multi-conversation, Streaming, Export
- **Prompt Management**: Templates, Categories, Pre/post-conditions
- **User Profiles**: JWT Auth, Language Preferences (EN/DE)

---

For detailed architecture documentation, diagrams, and workflows, see the **[arc42 documentation](arch42/README.md)**.
