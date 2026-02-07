# Rebranding Status Tracker

## Rename Mapping
| Alt | Neu |
|-----|-----|
| `aiproxysrv/` | `chmusicprosrv/` |
| `aiwebui/` | `chmusicproweb/` |
| `aiproxysrv-app` (Docker) | `chmusicprosrv-app` |
| `aiwebui-app` (Docker) | `chmusicproweb-app` |
| `/aiproxysrv` (Prod URL) | `/musicproapi` |
| `/aiwebui/` (Base Href) | `/chmusicproweb/` |
| `aiproxy-cli` | `chmusicpro-cli` |
| `~/.aiproxy/` | `~/.chmusicpro/` |

## Guardrails (NICHT aendern)
- DB-Name: `aiproxysrv`, DB-User: `aiproxy`, S3-Bucket: `aiproxy-media`

---

## Session 1: Backend Directory Rename -- DONE
- [x] musicprosrv/ loeschen
- [x] git mv aiproxysrv chmusicprosrv
- [x] pyproject.toml (name + entry point)
- [x] Dockerfile (Kommentar)
- [x] docker-compose.dev.yml (Service + Image)
- [x] Makefile (Kommentar)
- [x] src/api/app.py (Kommentar)
- [x] __init__.py Docstrings (tests, business, utils)
- [x] .dockerignore
- [x] scripts/compare_db_schemas.py (Kommentar)
- [x] Verifikation: make lint-all (passed) && make test (625 passed, 96% coverage)

## Session 2: Frontend Directory Rename -- DONE
- [x] git mv aiwebui chmusicproweb
- [x] angular.json (6 Stellen)
- [x] package.json (name)
- [x] src/index.html (base href)
- [x] Makefile (alle Referenzen)
- [x] Dockerfile (2 Stellen)
- [x] docker-compose.dev.yml
- [x] version-check.service.ts
- [x] app.component.ts + spec
- [x] .npmrc
- [x] environment.prod.ts (URL -> /musicproapi)
- [x] auth.interceptor.ts (3 Stellen -> /musicproapi)
- [x] Verifikation: make build-prod (lint passed, build 7.2s)

## Session 3: Build Scripts + CI/CD -- DONE
- [x] git mv build-and-push-aiproxysrv.sh -> chmusicprosrv
- [x] git mv build-and-push-aiwebui.sh -> chmusicproweb
- [x] create_release.sh (alle Referenzen)
- [x] cleanup_cifail.sh (alle Referenzen)
- [x] setVersion.sh (alle Referenzen)
- [x] cleanup-docker-images.sh (Image-Namen)
- [x] cleanup-ghcr-images.sh (Image-Namen)
- [x] .github/workflows/release.yml (alle Referenzen)
- [x] Verifikation: bash -n + yaml parse (alle OK)

## Session 4: CLI + Root Config + IDE -- DONE
- [x] git mv aiproxy-cli.py -> chmusicpro-cli.py
- [x] git mv .aiproxyignore.default -> .chmusicproignore.default
- [x] chmusicpro-cli.py (Docstring, CONFIG_DIR, URLs, alle Referenzen)
- [x] scripts/cli/README.md (alle Referenzen)
- [x] Root Makefile (alle Referenzen, Config-Pfade, URLs)
- [x] .gitignore (alle aiproxysrv + aiwebui Pfade)
- [x] .run/ IDE Configs (git mv + Inhalt)
- [x] develop-env/docker-compose.yml (keine Aenderung - nur DB-Refs)
- [x] .github/secret_scanning.yml (Pfad)
- [x] Verifikation: make help (passed), CLI syntax (passed)

## Session 5: Dokumentation
- [ ] CLAUDE.md
- [ ] docs/DEPLOYMENT.md
- [ ] docs/arch42/README.md
- [ ] docs/MIGRATION_PROCESS.md
- [ ] docs/TROUBLESHOOTING.md
- [ ] docs/PRODUCTION_RECOVERY_PLAN.md
- [ ] docs/CI_CD.md
- [ ] docs/DB_IMPL_DEVS.md
- [ ] ollamasrv/README.md
- [ ] README.md
- [ ] docs/ARCHITECTURE.md
- [ ] docs/README_USER_SETUP.md
- [ ] Mermaid-Diagramme
- [ ] Verifikation: grep check

## Session 6: Abschluss
- [ ] Globale grep-Suche
- [ ] Backend Build
- [ ] Frontend Build
- [ ] MEMORY.md updaten
- [ ] Status-File finalisieren
