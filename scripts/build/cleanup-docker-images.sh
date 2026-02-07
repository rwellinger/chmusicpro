#!/bin/bash

# Cleanup locally built Docker images
# Usage: ./cleanup-docker-images.sh [--force] [--all]
#
# Options:
#   --force    Skip confirmation prompt
#   --all      Also remove dangling images (untagged)

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
FORCE_CLEANUP=false
CLEANUP_DANGLING=false

# Images to clean up (both local and registry-tagged)
IMAGES=(
    "aiproxysrv-app"
    "celery-worker-app"
    "aiwebui-app"
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
        elif [ "$arg" = "--all" ]; then
            CLEANUP_DANGLING=true
        fi
    done
}

# Get list of images to delete
get_images_to_delete() {
    local all_images=()

    for image in "${IMAGES[@]}"; do
        # Find all local tags for this image
        local image_list=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${image}:" || true)
        if [ -n "$image_list" ]; then
            while IFS= read -r img; do
                all_images+=("$img")
            done <<< "$image_list"
        fi

        # Find all registry-tagged versions
        local registry_list=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${REGISTRY}/${image}:" || true)
        if [ -n "$registry_list" ]; then
            while IFS= read -r img; do
                all_images+=("$img")
            done <<< "$registry_list"
        fi
    done

    printf '%s\n' "${all_images[@]}"
}

# Display images to be deleted
display_images() {
    local images=("$@")

    if [ ${#images[@]} -eq 0 ]; then
        print_info "No images found to delete"
        return 1
    fi

    echo "The following images will be deleted:"
    echo ""
    for img in "${images[@]}"; do
        local size=$(docker images --format "{{.Size}}" "$img" 2>/dev/null || echo "unknown")
        echo -e "  ${RED}✗${NC} $img ${YELLOW}($size)${NC}"
    done
    echo ""

    return 0
}

# Confirm deletion
confirm_deletion() {
    if [ "$FORCE_CLEANUP" = true ]; then
        return 0
    fi

    read -p "Proceed with deletion? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Aborted by user"
        exit 1
    fi
}

# Delete images
delete_images() {
    local images=("$@")
    local deleted_count=0
    local failed_count=0

    print_header "Deleting Images"

    for img in "${images[@]}"; do
        print_info "Deleting $img..."
        if docker rmi "$img" 2>/dev/null; then
            print_success "Deleted $img"
            ((deleted_count++))
        else
            print_warning "Failed to delete $img (might be in use)"
            ((failed_count++))
        fi
    done

    echo ""
    print_success "Deleted $deleted_count image(s)"
    if [ $failed_count -gt 0 ]; then
        print_warning "$failed_count image(s) could not be deleted"
    fi
}

# Cleanup dangling images
cleanup_dangling() {
    print_header "Cleaning Up Dangling Images"

    local dangling=$(docker images -f "dangling=true" -q)
    if [ -z "$dangling" ]; then
        print_info "No dangling images found"
        return
    fi

    print_info "Removing dangling images..."
    docker image prune -f > /dev/null 2>&1
    print_success "Dangling images removed"
}

# Display protected images
display_protected() {
    print_header "Protected Images"
    echo "These images will NOT be deleted:"
    echo ""
    echo -e "  ${GREEN}✓${NC} postgres:*"
    echo -e "  ${GREEN}✓${NC} redis:*"
    echo -e "  ${GREEN}✓${NC} nginx:*"
    echo -e "  ${GREEN}✓${NC} (and any other non-project images)"
    echo ""
}

# Calculate freed space
calculate_freed_space() {
    local images=("$@")
    local total_size=0

    for img in "${images[@]}"; do
        local size=$(docker images --format "{{.Size}}" "$img" 2>/dev/null | sed 's/GB/*1000000000/;s/MB/*1000000/;s/KB/*1000/' | bc 2>/dev/null || echo "0")
        total_size=$(echo "$total_size + $size" | bc)
    done

    # Convert to human readable
    if [ "$total_size" -gt 1000000000 ]; then
        echo "$(echo "scale=2; $total_size / 1000000000" | bc)GB"
    elif [ "$total_size" -gt 1000000 ]; then
        echo "$(echo "scale=2; $total_size / 1000000" | bc)MB"
    else
        echo "$(echo "scale=2; $total_size / 1000" | bc)KB"
    fi
}

# Main execution
main() {
    print_header "Docker Image Cleanup"

    parse_arguments "$@"

    if [ "$FORCE_CLEANUP" = true ]; then
        print_warning "Force mode enabled - skipping confirmation"
    fi

    # Get images to delete (compatible with Bash 3.2)
    local images_to_delete=()
    while IFS= read -r line; do
        images_to_delete+=("$line")
    done < <(get_images_to_delete)

    # Display what will be protected
    display_protected

    # Display what will be deleted
    if ! display_images "${images_to_delete[@]}"; then
        print_success "Nothing to clean up!"
        exit 0
    fi

    # Confirm deletion
    confirm_deletion

    # Delete images
    delete_images "${images_to_delete[@]}"

    # Cleanup dangling if requested
    if [ "$CLEANUP_DANGLING" = true ]; then
        cleanup_dangling
    fi

    print_header "Cleanup Complete"
    print_success "Local Docker images cleaned up successfully"

    if [ "$CLEANUP_DANGLING" = false ]; then
        print_info "Tip: Use --all flag to also remove dangling images"
    fi
}

# Run main function
main "$@"
