#!/bin/bash

###############################################################################
# setVersion.sh
#
# Updates version number across all SOURCE project configuration files
# Usage: ./setVersion.sh <version>
# Example: ./setVersion.sh 2.1.8
#
# Updates:
# - aiproxysrv/pyproject.toml
# - aitestmock/pyproject.toml
# - aiwebui/package.json
#
# NOTE: Does NOT update production docker-compose.yml files
#       (those are in separate deployment repo and updated manually)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory (2 levels up from scripts/build)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# File paths
AIPROXYSRV_TOML="$PROJECT_ROOT/aiproxysrv/pyproject.toml"
AITESTMOCK_TOML="$PROJECT_ROOT/aitestmock/pyproject.toml"
AIWEBUI_PACKAGE="$PROJECT_ROOT/aiwebui/package.json"

# Function to print usage
usage() {
    echo -e "${YELLOW}Usage:${NC} $0 <version>"
    echo -e "${YELLOW}Example:${NC} $0 2.1.8"
    echo ""
    echo "Updates version in SOURCE files:"
    echo "  - aiproxysrv/pyproject.toml"
    echo "  - aitestmock/pyproject.toml"
    echo "  - aiwebui/package.json"
    echo ""
    echo "Production docker-compose.yml files are in separate deployment repo"
    echo "and must be updated manually after release."
    exit 1
}

# Function to validate version format
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}Error:${NC} Invalid version format. Expected X.Y.Z (e.g., 2.1.8)"
        exit 1
    fi
}

# Function to update pyproject.toml
update_pyproject() {
    local file=$1
    local new_version=$2
    local old_version

    # Extract current version
    old_version=$(grep '^version = ' "$file" | head -1 | sed 's/version = "\(.*\)"/\1/')

    # Update version using sed (macOS compatible)
    sed -i '' "s/^version = \".*\"/version = \"$new_version\"/" "$file"

    echo -e "${GREEN}✓${NC} Updated $file"
    echo -e "  ${YELLOW}$old_version${NC} → ${GREEN}$new_version${NC}"
}

# Function to update package.json
update_package_json() {
    local file=$1
    local new_version=$2
    local old_version

    # Extract current version
    old_version=$(grep '"version":' "$file" | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')

    # Update version using sed (macOS compatible)
    sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_version\"/" "$file"

    echo -e "${GREEN}✓${NC} Updated $file"
    echo -e "  ${YELLOW}$old_version${NC} → ${GREEN}$new_version${NC}"
}

# Function to update docker-compose.yml
update_docker_compose() {
    local file=$1
    local new_version=$2
    local image_name=$3
    local old_version

    # Extract current version for the specific image
    old_version=$(grep "image: ghcr.io/rwellinger/${image_name}:" "$file" | sed "s/.*:v\(.*\)/\1/")

    # Update version using sed (macOS compatible)
    sed -i '' "s|image: ghcr.io/rwellinger/${image_name}:v.*|image: ghcr.io/rwellinger/${image_name}:v${new_version}|g" "$file"

    echo -e "${GREEN}✓${NC} Updated $file (${image_name})"
    echo -e "  ${YELLOW}v$old_version${NC} → ${GREEN}v$new_version${NC}"
}

# Main script
main() {
    # Check if version argument is provided
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error:${NC} No version specified"
        usage
    fi

    NEW_VERSION=$1

    # Validate version format
    validate_version "$NEW_VERSION"

    # Check if all files exist
    for file in "$AIPROXYSRV_TOML" "$AITESTMOCK_TOML" "$AIWEBUI_PACKAGE"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}Error:${NC} File not found: $file"
            exit 1
        fi
    done

    echo ""
    echo -e "${YELLOW}Updating SOURCE version to ${GREEN}${NEW_VERSION}${NC}..."
    echo ""

    # Update source files only
    update_pyproject "$AIPROXYSRV_TOML" "$NEW_VERSION"
    update_pyproject "$AITESTMOCK_TOML" "$NEW_VERSION"
    update_package_json "$AIWEBUI_PACKAGE" "$NEW_VERSION"

    echo ""

    # Write VERSION file in scripts directory
    VERSION_FILE="$SCRIPT_DIR/VERSION"
    echo "v${NEW_VERSION}" > "$VERSION_FILE"
    echo -e "${GREEN}✓${NC} Created $VERSION_FILE"
    echo -e "  Content: ${GREEN}v${NEW_VERSION}${NC}"

    echo ""
    echo -e "${GREEN}✓ Successfully updated all SOURCE version files to ${NEW_VERSION}${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Review changes: git diff"
    echo "  2. Commit changes: git add . && git commit -m \"Bump version to v${NEW_VERSION}\""
    echo "  3. Create release: cd scripts/build && ./create_release.sh"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
    echo "  After release, manually update image versions in your deployment docker-compose.yml files."
    echo ""
}

# Run main function
main "$@"
