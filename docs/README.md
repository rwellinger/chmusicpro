# Documentation Overview

This directory contains technical documentation for the Mac AI Service project.

## Architecture Documentation

**Primary Architecture Reference:**

- [**ARCHITECTURE.md**](ARCHITECTURE.md) - Quick reference with links to detailed arc42 documentation
  - Tech Stack overview
  - Key Components summary
  - Core Features list
  - → Links to complete [arc42 Architecture Documentation](arch42/README.md)

The arc42 documentation includes:
- System overview and context
- Building blocks and components
- Runtime views and workflows
- Deployment architecture
- Database schema with ER diagrams
- Quality requirements

## Service Documentation

Documentation for individual services and components:

- [**aiproxysrv**](../aiproxysrv/README.md) - Backend API service (FastAPI/Python)
- [**aiwebui**](../aiwebui/README.md) - Angular 20 frontend application
- [**forwardproxy**](../forwardproxy/README.md) - Nginx reverse proxy configuration
- [**ollamasrv**](../ollamasrv/README.md) - Ollama LLM backend service

## Development Guides

Technical guides for developers:

- [**Code Patterns**](CODE_PATTERNS.md) - Complete code examples (Angular, Python, Testing)
- [**Troubleshooting**](TROUBLESHOOTING.md) - Debug commands and common issues
- [**CI/CD**](CI_CD.md) - GitHub Actions, build pipeline, release workflow
- [**Database Implementation & Migrations**](DB_IMPL_DEVS.md) - SQLAlchemy models and Alembic workflow
- [**Docker/Colima Installation**](DOCKER-INSTALL.md) - Container runtime setup for macOS
- [**User Management Setup**](README_USER_SETUP.md) - Initial user creation and authentication
- [**Migration Process**](MIGRATION_PROCESS.md) - Database migration workflow with init-container pattern
- [**Production Recovery Plan**](PRODUCTION_RECOVERY_PLAN.md) - Emergency recovery procedures

## Quick Start

1. **Architecture Overview**: Start with [ARCHITECTURE.md](ARCHITECTURE.md) for a quick reference
2. **Detailed Architecture**: Dive into [arc42 Documentation](arch42/README.md) for comprehensive details
3. **Service Setup**: Refer to individual service README files for setup instructions
4. **Development Patterns**: Check [CODE_PATTERNS.md](CODE_PATTERNS.md) for implementation examples
