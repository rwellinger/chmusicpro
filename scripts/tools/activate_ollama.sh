#!/bin/bash
#
# Activates a specific Ollama version by creating symlinks
# Usage: sudo ./activate_ollama.sh <version>
# Example: sudo ./activate_ollama.sh 0.13.0
#

set -e

OLLAMA_BASE_DIR="/usr/local/bin"

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.13.0"
    echo ""
    echo "Available versions:"
    ls -d ${OLLAMA_BASE_DIR}/ollama.* 2>/dev/null | sed 's|.*/ollama\.||' || echo "  (none found)"
    exit 1
fi

VERSION="$1"
SOURCE_DIR="${OLLAMA_BASE_DIR}/ollama.${VERSION}"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Version directory not found: $SOURCE_DIR"
    echo ""
    echo "Available versions:"
    ls -d ${OLLAMA_BASE_DIR}/ollama.* 2>/dev/null | sed 's|.*/ollama\.||' || echo "  (none found)"
    exit 1
fi

echo "Activating Ollama version ${VERSION}..."

# Remove existing symlinks (ollama, ollama-mlx, and libggml*)
echo "Removing existing symlinks..."
find ${OLLAMA_BASE_DIR} -maxdepth 1 -type l \( -name "ollama" -o -name "ollama-mlx" -o -name "libggml*" \) -delete

# Create new symlinks for all files in the version directory
echo "Creating symlinks from ${SOURCE_DIR}..."
for file in "${SOURCE_DIR}"/*; do
    filename=$(basename "$file")
    ln -s "$file" "${OLLAMA_BASE_DIR}/${filename}"
    echo "  ${filename} -> ${file}"
done

echo ""
echo "Ollama ${VERSION} activated successfully."
echo "Verify with: ollama --version"
