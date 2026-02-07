#!/bin/bash

# Create a new release with version tagging
# Usage: ./create_release.sh
# Note: Reads version from scripts/VERSION file (created by setVersion.sh)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if VERSION file exists
VERSION_FILE="$SCRIPT_DIR/VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    print_error "VERSION File nicht gefunden: $VERSION_FILE"
    echo ""
    echo "Bitte zuerst Version setzen:"
    echo "  ${YELLOW}cd $SCRIPT_DIR${NC}"
    echo "  ${YELLOW}./setVersion.sh <VERSION>${NC}"
    echo ""
    echo "Beispiel:"
    echo "  ${YELLOW}./setVersion.sh 2.2.3${NC}"
    echo ""
    exit 1
fi

# Read version from file
VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')

# Validate version format (vX.Y.Z)
if ! [[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Ungültiges Versionsformat in $VERSION_FILE: $VERSION"
    print_error "Erwarte Format: vX.Y.Z (z.B. v2.1.6)"
    exit 1
fi

print_header "Release ${VERSION} erstellen"

cd "$PROJECT_DIR"

# ──────────────────────────────────────
# 0. Git fetch (optional - darf fehlschlagen)
# ──────────────────────────────────────
REMOTE_AVAILABLE=true
print_info "Aktualisiere Remote-Status..."
if ! git fetch 2>&1; then
    REMOTE_AVAILABLE=false
    print_warning "Git fetch fehlgeschlagen (Netzwerk-Problem?)"
    print_warning "Fahre trotzdem fort - lokale Checks werden durchgeführt"
else
    print_success "Remote-Status aktualisiert"
fi

# ──────────────────────────────────────
# 1. Prüfe, ob der Arbeitsbaum sauber ist
# ──────────────────────────────────────
print_info "Prüfe Git Status..."
if ! git diff-index --quiet HEAD --; then
    print_error "Der Arbeitsbaum enthält nicht committete Änderungen."
    exit 1
fi
print_success "Arbeitsbaum ist sauber"

# ──────────────────────────────────────
# 2. Prüfe, ob noch unpushed Commits existieren
# ──────────────────────────────────────
if [ "$REMOTE_AVAILABLE" = true ]; then
    if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
        if git rev-list @{u}..HEAD | grep -q .; then
            print_error "Es gibt lokale Commits, die noch nicht gepusht wurden."
            exit 1
        fi
        print_success "Alle Commits sind gepusht"
    else
        print_warning "Kein Upstream Remote gesetzt – Push Check übersprungen"
    fi
else
    print_warning "Remote nicht erreichbar - Push Check übersprungen"
fi

# ──────────────────────────────────────
# 3. Prüfen, ob Tag schon existiert
# ──────────────────────────────────────
print_info "Prüfe ob Tag ${VERSION} bereits existiert..."
if git show-ref --verify --quiet "refs/tags/${VERSION}"; then
    print_error "Tag ${VERSION} existiert bereits (lokal)."
    exit 1
fi
if [ "$REMOTE_AVAILABLE" = true ]; then
    if git ls-remote --tags origin | grep -q "refs/tags/${VERSION}\$"; then
        print_error "Tag ${VERSION} existiert bereits (remote)."
        exit 1
    fi
    print_success "Tag ${VERSION} ist verfügbar (lokal + remote)"
else
    print_warning "Remote nicht erreichbar - nur lokaler Tag-Check durchgeführt"
    print_success "Tag ${VERSION} ist lokal verfügbar"
fi

# ══════════════════════════════════════════════════════════════
# 4. QUALITY GATES - Backend (chmusicprosrv)
# ══════════════════════════════════════════════════════════════
print_header "Quality Gates: Backend (chmusicprosrv)"

cd "$PROJECT_DIR/chmusicprosrv"

# Check Conda Environment
print_info "Prüfe Conda Environment..."
if ! conda env list | grep -q "chmusicpro_py312.*\*"; then
    print_error "Conda environment 'chmusicpro_py312' ist nicht aktiv!"
    print_error "Aktiviere es mit: conda activate chmusicpro_py312"
    exit 1
fi
print_success "Conda environment OK"

# Backend Linting (Ruff + Import-Linter + Format Check)
print_info "Führe Backend Linting aus (Ruff + Architecture + Format)..."
if ! make lint-all > /dev/null 2>&1; then
    print_error "Backend Linting fehlgeschlagen!"
    echo ""
    echo "Fehler beheben mit:"
    echo "  ${YELLOW}cd chmusicprosrv && make lint-all${NC}"
    echo "  ${YELLOW}cd chmusicprosrv && make format${NC}"
    exit 1
fi
print_success "Backend Linting bestanden (Ruff + Architecture + Format)"

# Unit Tests
print_info "Führe Backend Tests aus..."
if ! make test > /dev/null 2>&1; then
    print_error "Backend Tests fehlgeschlagen!"
    echo ""
    echo "Tests ausführen:"
    echo "  ${YELLOW}cd chmusicprosrv && make test${NC}"
    exit 1
fi
print_success "Backend Tests bestanden"

# ══════════════════════════════════════════════════════════════
# 5. QUALITY GATES - Frontend (chmusicproweb)
# ══════════════════════════════════════════════════════════════
print_header "Quality Gates: Frontend (chmusicproweb)"

cd "$PROJECT_DIR/chmusicproweb"

# Check Node.js Environment
print_info "Prüfe Node.js Environment..."
if ! make check-node > /dev/null 2>&1; then
    print_error "Node.js Environment Check fehlgeschlagen!"
    echo ""
    echo "Details anzeigen:"
    echo "  ${YELLOW}cd chmusicproweb && make check-node${NC}"
    exit 1
fi
print_success "Node.js environment OK"

# Frontend Linting (TypeScript + SCSS + Architecture)
print_info "Führe Frontend Linting aus (TypeScript + SCSS + Architecture)..."
if ! make lint-all > /dev/null 2>&1; then
    print_error "Frontend Linting fehlgeschlagen!"
    echo ""
    echo "Fehler beheben mit:"
    echo "  ${YELLOW}cd chmusicproweb && make lint-all${NC}"
    echo "  ${YELLOW}cd chmusicproweb && make lint-fix${NC}"
    exit 1
fi
print_success "Frontend Linting bestanden"

# Unit Tests
print_info "Führe Frontend Unit Tests aus..."
if ! make test > /dev/null 2>&1; then
    print_error "Frontend Unit Tests fehlgeschlagen!"
    echo ""
    echo "Tests ausführen:"
    echo "  ${YELLOW}cd chmusicproweb && make test${NC}"
    exit 1
fi
print_success "Frontend Unit Tests bestanden"

# Production Build Test
print_info "Führe Production Build Test aus..."
if ! make build-dev > /dev/null 2>&1; then
    print_error "Frontend Build fehlgeschlagen!"
    echo ""
    echo "Build-Fehler analysieren:"
    echo "  ${YELLOW}cd chmusicproweb && make build-dev${NC}"
    exit 1
fi
print_success "Frontend Build bestanden"

print_success "Alle Quality Gates bestanden! 🎉"

# ──────────────────────────────────────
# 6. VERSION Files aktualisieren
# ──────────────────────────────────────
cd "$PROJECT_DIR"
print_info "Aktualisiere VERSION Files..."

echo "${VERSION}" > "$PROJECT_DIR/chmusicprosrv/VERSION"
print_success "chmusicprosrv/VERSION → ${VERSION}"

echo "${VERSION}" > "$PROJECT_DIR/chmusicproweb/VERSION"
print_success "chmusicproweb/VERSION → ${VERSION}"

# ──────────────────────────────────────
# 7. Änderungen committen
# ──────────────────────────────────────
print_info "Committe VERSION Updates..."
git add chmusicprosrv/VERSION chmusicproweb/VERSION
git commit -m "Bump version to ${VERSION}"
print_success "VERSION Files committed"

# ──────────────────────────────────────
# 8. Git Tag erstellen und pushen
# ──────────────────────────────────────
print_info "Erstelle Git Tag ${VERSION}..."
git tag ${VERSION} -m "Release ${VERSION}"
print_success "Tag ${VERSION} erstellt"

if [ "$REMOTE_AVAILABLE" = true ]; then
    print_info "Pushe Commit und Tag..."
    git push origin main
    git push origin ${VERSION}
    print_success "Tag und Commit gepusht"
else
    print_warning "Remote nicht erreichbar - Push übersprungen!"
    print_warning "Bitte manuell pushen wenn Netzwerk verfügbar:"
    echo "  ${YELLOW}git push origin main${NC}"
    echo "  ${YELLOW}git push origin ${VERSION}${NC}"
fi

# ──────────────────────────────────────────────────────────
# 9. GitHub Actions Build
# ──────────────────────────────────────────────────────────
print_header "GitHub Actions Build"

if [ "$REMOTE_AVAILABLE" = true ]; then
    print_info "Build wird automatisch in GitHub Actions gestartet..."
    echo ""
    echo "  🔗 Build Status: ${BLUE}https://github.com/rwellinger/chmusicpro/actions${NC}"
    echo ""
    print_info "GitHub Actions wird folgende Images bauen und pushen:"
    echo "  • ghcr.io/rwellinger/chmusicprosrv-app:${VERSION}"
    echo "  • ghcr.io/rwellinger/celery-worker-app:${VERSION}"
    echo "  • ghcr.io/rwellinger/chmusicproweb-app:${VERSION}"
    echo ""
    print_info "Erwartete Build-Zeit: ~10-12 Minuten"
    echo ""
else
    print_warning "Kein Push durchgeführt - GitHub Actions Build NICHT gestartet!"
    echo ""
    print_warning "Nach manuellem Push werden Images automatisch gebaut."
    echo ""
fi

print_warning "Manuelle Builds sind weiterhin möglich (Fallback):"
echo "  ./scripts/build/build-and-push-chmusicprosrv.sh ${VERSION}"
echo "  ./scripts/build/build-and-push-chmusicproweb.sh ${VERSION}"
echo ""
print_success "Release ${VERSION} erfolgreich erstellt!"
echo ""
