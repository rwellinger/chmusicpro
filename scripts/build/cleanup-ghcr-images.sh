#!/bin/bash

# Cleanup old images from GitHub Container Registry (GHCR)
# Usage: ./cleanup-ghcr-images.sh [--force] [--dry-run]
#
# This script keeps:
#   - The :latest tag
#   - The version tagged as :latest (e.g., if :latest points to v2.1.5, keep v2.1.5)
# All other tags will be deleted.
#
# Options:
#   --force      Skip confirmation prompt
#   --dry-run    Show what would be deleted without actually deleting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
# Determine GitHub owner dynamically (requires gh CLI)
GITHUB_OWNER="${GITHUB_OWNER:-$(gh api user --jq '.login' 2>/dev/null)}"
if [ -z "$GITHUB_OWNER" ]; then
    echo -e "${RED}Error: Could not determine GitHub owner.${NC}"
    echo "Either set GITHUB_OWNER environment variable or login with 'gh auth login'"
    exit 1
fi
REGISTRY="ghcr.io/$GITHUB_OWNER"
GITHUB_TOKEN=""
FORCE_CLEANUP=false
DRY_RUN=false

# Images to clean up
IMAGES=(
    "aiwebui-app"
    "aiproxysrv-app"
    "celery-worker-app"
)

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

# Parse arguments
parse_arguments() {
    for arg in "$@"; do
        if [ "$arg" = "--force" ]; then
            FORCE_CLEANUP=true
        elif [ "$arg" = "--dry-run" ]; then
            DRY_RUN=true
        fi
    done
}

# Check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed."
        print_info "Install with: brew install gh"
        exit 1
    fi
    print_success "GitHub CLI is available"
}

# Check authentication
check_auth() {
    if ! gh auth status &> /dev/null; then
        print_error "Not authenticated with GitHub CLI."
        print_info "Run: gh auth login"
        exit 1
    fi
    print_success "Authenticated with GitHub"
}

# Get all tags for an image using authenticated user endpoint
get_image_tags() {
    local image=$1
    local package=$image

    # Use authenticated user endpoint instead of /users/
    gh api -H "Accept: application/vnd.github+json" \
        "/user/packages/container/${package}/versions" \
        --jq '.[].metadata.container.tags[]' 2>/dev/null || echo ""
}

# Get the version that :latest points to
get_latest_version() {
    local image=$1
    local package=$image

    # Get the version ID that has the 'latest' tag (exact match)
    local latest_version_id=$(gh api -H "Accept: application/vnd.github+json" \
        "/user/packages/container/${package}/versions" \
        --jq '.[] | select(.metadata.container.tags[] == "latest") | .id' 2>/dev/null | head -1)

    if [ -z "$latest_version_id" ]; then
        echo ""
        return
    fi

    # Get all tags for this version (usually includes both 'latest' and a version tag like 'v2.7.0')
    # Sort version tags to get the highest version number
    gh api -H "Accept: application/vnd.github+json" \
        "/user/packages/container/${package}/versions" \
        --jq ".[] | select(.id == ${latest_version_id}) | .metadata.container.tags[] | select(. != \"latest\")" 2>/dev/null | sort -V | tail -1
}

# Get version ID for a specific tag
get_version_id() {
    local image=$1
    local tag=$2
    local package=$image

    gh api -H "Accept: application/vnd.github+json" \
        "/user/packages/container/${package}/versions" \
        --jq ".[] | select(.metadata.container.tags[] | contains(\"${tag}\")) | .id" 2>/dev/null | head -1
}

# Delete a specific version
delete_version() {
    local image=$1
    local version_id=$2
    local package=$image

    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY RUN] Would delete version ID: $version_id"
        return 0
    fi

    gh api --method DELETE -H "Accept: application/vnd.github+json" \
        "/user/packages/container/${package}/versions/${version_id}" 2>/dev/null
}

# Process cleanup for a single image
cleanup_image() {
    local image=$1

    print_header "Processing $image"

    # Get all tags
    local all_tags=$(get_image_tags "$image")

    if [ -z "$all_tags" ]; then
        print_warning "No tags found for $image (package might not exist or is private)"
        return
    fi

    # Get the version that :latest points to
    local latest_version=$(get_latest_version "$image")

    print_info "Current tags: $(echo $all_tags | tr '\n' ' ')"

    if [ -n "$latest_version" ]; then
        print_success "Protected: latest, $latest_version"
    else
        print_success "Protected: latest"
    fi

    # Build list of tags to delete
    local tags_to_delete=()

    for tag in $all_tags; do
        # Skip 'latest' tag
        if [ "$tag" = "latest" ]; then
            continue
        fi

        # Skip the version that :latest points to
        if [ -n "$latest_version" ] && [ "$tag" = "$latest_version" ]; then
            continue
        fi

        # Add to deletion list
        tags_to_delete+=("$tag")
    done

    # Display what will be deleted
    if [ ${#tags_to_delete[@]} -eq 0 ]; then
        print_success "No old tags to delete"
        echo ""
        return
    fi

    echo ""
    echo "Tags to delete:"
    for tag in "${tags_to_delete[@]}"; do
        echo -e "  ${RED}✗${NC} $tag"
    done
    echo ""

    # Delete tags
    local deleted_count=0
    local failed_count=0

    for tag in "${tags_to_delete[@]}"; do
        local version_id=$(get_version_id "$image" "$tag")

        if [ -z "$version_id" ]; then
            print_warning "Could not find version ID for tag: $tag"
            ((failed_count++))
            continue
        fi

        if [ "$DRY_RUN" = true ]; then
            print_info "[DRY RUN] Would delete $image:$tag (ID: $version_id)"
        else
            print_info "Deleting $image:$tag (ID: $version_id)..."
            if delete_version "$image" "$version_id"; then
                print_success "Deleted $image:$tag"
                ((deleted_count++))
            else
                print_error "Failed to delete $image:$tag"
                ((failed_count++))
            fi
        fi
    done

    echo ""
    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY RUN] Would delete $deleted_count tag(s)"
    else
        print_success "Deleted $deleted_count tag(s)"
    fi

    if [ $failed_count -gt 0 ]; then
        print_warning "$failed_count tag(s) could not be deleted"
    fi
    echo ""
}

# Confirm deletion
confirm_deletion() {
    if [ "$FORCE_CLEANUP" = true ] || [ "$DRY_RUN" = true ]; then
        return 0
    fi

    echo ""
    read -p "Proceed with deletion? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Aborted by user"
        exit 1
    fi
}

# Display summary
print_summary() {
    print_header "Summary"

    if [ "$DRY_RUN" = true ]; then
        print_info "This was a DRY RUN - no changes were made"
        print_info "Run without --dry-run to actually delete tags"
    else
        print_success "GHCR cleanup completed"
    fi

    echo ""
    echo "Retention policy:"
    echo -e "  ${GREEN}✓${NC} :latest tag (always kept)"
    echo -e "  ${GREEN}✓${NC} Version that :latest points to latest version"
    echo -e "  ${RED}✗${NC} All other version tags (deleted)"
    echo ""
}

# Main execution
main() {
    print_header "GHCR Image Cleanup"

    parse_arguments "$@"

    if [ "$FORCE_CLEANUP" = true ]; then
        print_warning "Force mode enabled - skipping confirmation"
    fi

    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN mode - no changes will be made"
    fi

    check_gh_cli
    check_auth

    echo ""
    print_info "Registry: $REGISTRY"
    print_info "Images to process: ${IMAGES[*]}"

    # Show what will be protected
    echo ""
    print_info "Protection policy:"
    echo "  - Keep :latest tag"
    echo "  - Keep version that :latest points to"
    echo "  - Delete all other tags"

    confirm_deletion

    # Process each image
    for image in "${IMAGES[@]}"; do
        cleanup_image "$image"
    done

    print_summary
}

# Run main function
main "$@"
