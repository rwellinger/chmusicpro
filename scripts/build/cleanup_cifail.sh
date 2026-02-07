#!/bin/bash

# Cleanup after failed CI/CD release
# Resets VERSION files in aiproxysrv and aiwebui to last successfully released version
# Usage: ./cleanup_cifail.sh

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

print_header "Cleanup nach fehlgeschlagenem Release"

cd "$PROJECT_DIR"

# ──────────────────────────────────────
# 1. Finde letzte erfolgreich released Version
# ──────────────────────────────────────
print_info "Suche letzte erfolgreich released Version..."

# Get all tags sorted by version
LAST_VERSION=$(git tag -l 'v*.*.*' | sort -V | tail -n 1)

if [ -z "$LAST_VERSION" ]; then
    print_error "Keine Version Tags gefunden!"
    exit 1
fi

print_success "Letzte erfolgreiche Version: ${LAST_VERSION}"

# ──────────────────────────────────────
# 2. Prüfe ob Änderungen notwendig sind
# ──────────────────────────────────────
CURRENT_AIPROXYSRV=$(cat "$PROJECT_DIR/aiproxysrv/VERSION" | tr -d '[:space:]')
CURRENT_AIWEBUI=$(cat "$PROJECT_DIR/aiwebui/VERSION" | tr -d '[:space:]')

print_info "Aktuelle Versionen:"
echo "  aiproxysrv/VERSION: ${CURRENT_AIPROXYSRV}"
echo "  aiwebui/VERSION:    ${CURRENT_AIWEBUI}"

if [ "$CURRENT_AIPROXYSRV" = "$LAST_VERSION" ] && [ "$CURRENT_AIWEBUI" = "$LAST_VERSION" ]; then
    print_success "VERSION Files sind bereits auf ${LAST_VERSION} - nichts zu tun"
    exit 0
fi

# ──────────────────────────────────────
# 3. Setze VERSION Files zurück
# ──────────────────────────────────────
print_info "Setze VERSION Files auf ${LAST_VERSION} zurück..."

echo "${LAST_VERSION}" > "$PROJECT_DIR/aiproxysrv/VERSION"
print_success "aiproxysrv/VERSION → ${LAST_VERSION}"

echo "${LAST_VERSION}" > "$PROJECT_DIR/aiwebui/VERSION"
print_success "aiwebui/VERSION → ${LAST_VERSION}"

# ──────────────────────────────────────
# 4. Committe Änderungen
# ──────────────────────────────────────
if ! git diff-index --quiet HEAD --; then
    print_info "Committe VERSION Resets..."
    git add aiproxysrv/VERSION aiwebui/VERSION
    git commit -m "Reset VERSION files after failed release"
    print_success "VERSION Files committed"

    print_info "Pushe Änderungen..."
    git push origin main
    print_success "Änderungen gepusht"
else
    print_info "Keine Änderungen zum committen"
fi

# ──────────────────────────────────────
# 5. Status ausgeben
# ──────────────────────────────────────
print_header "Cleanup abgeschlossen"

REBUILD_VERSION=$(cat "$SCRIPT_DIR/VERSION" | tr -d '[:space:]')

echo "VERSION Files wurden auf ${LAST_VERSION} zurückgesetzt"
echo ""
echo "Für Rebuild von ${REBUILD_VERSION}:"
echo "  ${GREEN}./scripts/build/create_release.sh${NC}"
echo ""
