#!/bin/bash

# -------------------------------------------------------------
# PostgreSQL Database Restore Script
# -------------------------------------------------------------
# Restores a PostgreSQL database backup from a .sql.gz file
# Runs directly on NAS (Bash 4.4)
# -------------------------------------------------------------

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# -------------------------------------------------------------
# 1. Configuration
# -------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Docker
DOCKER_CMD="/usr/local/bin/docker"
POSTGRES_CONTAINER="postgres"

# -------------------------------------------------------------
# 2. Usage
# -------------------------------------------------------------
usage() {
    echo "Usage: $0 <backup-file.sql.gz>"
    echo ""
    echo "Example:"
    echo "  $0 /volumeUSB1/usbshare/backup/postgres/20250124_213000_aiproxysrv_full.sql.gz"
    echo ""
    exit 1
}

# -------------------------------------------------------------
# 3. Check Arguments
# -------------------------------------------------------------
if [[ $# -ne 1 ]]; then
    echo "ERROR: Missing backup file argument"
    usage
fi

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if file is gzipped
if [[ ! "$BACKUP_FILE" =~ \.sql\.gz$ ]]; then
    echo "ERROR: Backup file must be a .sql.gz file"
    echo "Got: $BACKUP_FILE"
    exit 1
fi

# -------------------------------------------------------------
# 4. Load Database Credentials from .env
# -------------------------------------------------------------
echo "Loading database credentials from .env..."

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env file not found at: $ENV_FILE"
    exit 1
fi

# Export POSTGRES_* variables from .env
while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" == \#* ]] && continue

    # Only export POSTGRES_* variables
    if [[ "$line" =~ ^POSTGRES_ ]]; then
        export "$line"
    fi
done < "$ENV_FILE"

# Verify required variables are set
if [[ -z "${POSTGRES_USER:-}" ]]; then
    echo "ERROR: POSTGRES_USER not found in .env"
    exit 1
fi

if [[ -z "${POSTGRES_DB:-}" ]]; then
    echo "ERROR: POSTGRES_DB not found in .env"
    exit 1
fi

if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
    echo "ERROR: POSTGRES_PASSWORD not found in .env"
    exit 1
fi

echo "Database credentials loaded successfully"

# -------------------------------------------------------------
# 5. Check Prerequisites
# -------------------------------------------------------------
echo "Checking prerequisites..."

# Check if Docker is available
if [[ ! -x "$DOCKER_CMD" ]]; then
    echo "ERROR: Docker not found at: $DOCKER_CMD"
    exit 1
fi

# Check if PostgreSQL container is running
if ! $DOCKER_CMD ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo "ERROR: PostgreSQL container '${POSTGRES_CONTAINER}' is not running"
    exit 1
fi

echo "Prerequisites check passed"

# -------------------------------------------------------------
# 6. Confirm Restore
# -------------------------------------------------------------
echo ""
echo "=========================================="
echo "WARNING: DATABASE RESTORE"
echo "=========================================="
echo "This will REPLACE the current database content!"
echo ""
echo "  Database: $POSTGRES_DB"
echo "  Backup:   $BACKUP_FILE"
echo ""
echo "Current database will be DROPPED and recreated!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo "Restore cancelled by user"
    exit 0
fi

# -------------------------------------------------------------
# 7. Restore Database
# -------------------------------------------------------------
echo ""
echo "Starting database restore..."

# Decompress and pipe to Docker container
if gunzip -c "$BACKUP_FILE" | $DOCKER_CMD exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
    echo ""
    echo "=========================================="
    echo "Database Restored Successfully"
    echo "=========================================="
    echo "  Database: $POSTGRES_DB"
    echo "  Backup:   $BACKUP_FILE"
    echo ""
    exit 0
else
    echo ""
    echo "=========================================="
    echo "ERROR: Database Restore Failed"
    echo "=========================================="
    echo ""
    echo "The database may be in an inconsistent state!"
    echo "Check the error messages above for details."
    echo ""
    exit 1
fi
