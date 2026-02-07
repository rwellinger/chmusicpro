#!/bin/bash

# -------------------------------------------------------------
# NAS Backup Script - MinIO + PostgreSQL
# -------------------------------------------------------------
# Runs directly on NAS (Bash 4.4)
# Backs up MinIO data and PostgreSQL database to USB volume
# Automatic cleanup of backups older than 7 days
# -------------------------------------------------------------

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# -------------------------------------------------------------
# 1. Configuration
# -------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Backup paths
MINIO_SOURCE="/volume1/minio-data"
BACKUP_BASE="/volumeUSB1/usbshare/backup"
MINIO_BACKUP_DIR="${BACKUP_BASE}/minio"
POSTGRES_BACKUP_DIR="${BACKUP_BASE}/postgres"
LOG_FILE="${BACKUP_BASE}/backup.log"

# Retention
RETENTION_DAYS=3

# Docker
DOCKER_CMD="/usr/local/bin/docker"
POSTGRES_CONTAINER="postgres"

# Timestamp
DATESTAMP="$(date +%Y%m%d_%H%M%S)"

# -------------------------------------------------------------
# 2. Logging Functions
# -------------------------------------------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# -------------------------------------------------------------
# 3. Check Prerequisites
# -------------------------------------------------------------
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if .env exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found at: $ENV_FILE"
        exit 1
    fi

    # Check if MinIO source exists
    if [[ ! -d "$MINIO_SOURCE" ]]; then
        log_error "MinIO source directory not found: $MINIO_SOURCE"
        exit 1
    fi

    # Check if backup base exists
    if [[ ! -d "$BACKUP_BASE" ]]; then
        log_error "Backup base directory not found: $BACKUP_BASE"
        log_error "Is USB drive mounted at /volumeUSB1?"
        exit 1
    fi

    # Check if Docker is available
    if [[ ! -x "$DOCKER_CMD" ]]; then
        log_error "Docker not found at: $DOCKER_CMD"
        exit 1
    fi

    # Check if PostgreSQL container is running
    if ! $DOCKER_CMD ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
        log_error "PostgreSQL container '${POSTGRES_CONTAINER}' is not running"
        exit 1
    fi

    log "Prerequisites check passed"
}

# -------------------------------------------------------------
# 4. Load Database Credentials from .env
# -------------------------------------------------------------
load_db_credentials() {
    log "Loading database credentials from .env..."

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
        log_error "POSTGRES_USER not found in .env"
        exit 1
    fi

    if [[ -z "${POSTGRES_DB:-}" ]]; then
        log_error "POSTGRES_DB not found in .env"
        exit 1
    fi

    if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
        log_error "POSTGRES_PASSWORD not found in .env"
        exit 1
    fi

    log "Database credentials loaded successfully"
}

# -------------------------------------------------------------
# 5. Backup MinIO Data
# -------------------------------------------------------------
backup_minio() {
    log "Starting MinIO backup..."

    # Create backup directory if it doesn't exist
    mkdir -p "$MINIO_BACKUP_DIR"

    # Backup filename (directly on USB SSD)
    MINIO_BACKUP_FILE="${MINIO_BACKUP_DIR}/${DATESTAMP}_minio-data.tar"

    log "Creating tar archive directly on USB SSD: $MINIO_BACKUP_FILE"

    # Create tar archive directly on USB SSD (no compression for speed)
    if tar -cf "$MINIO_BACKUP_FILE" -C "$(dirname "$MINIO_SOURCE")" "$(basename "$MINIO_SOURCE")"; then
        # Get file size
        BACKUP_SIZE=$(du -h "$MINIO_BACKUP_FILE" | cut -f1)
        log "MinIO backup completed successfully: $MINIO_BACKUP_FILE ($BACKUP_SIZE)"
    else
        log_error "MinIO backup failed"
        rm -f "$MINIO_BACKUP_FILE"
        exit 1
    fi
}

# -------------------------------------------------------------
# 6. Backup PostgreSQL Database
# -------------------------------------------------------------
backup_postgres() {
    log "Starting PostgreSQL backup..."

    # Create backup directory if it doesn't exist
    mkdir -p "$POSTGRES_BACKUP_DIR"

    # Backup filename
    POSTGRES_BACKUP_FILE="${POSTGRES_BACKUP_DIR}/${DATESTAMP}_${POSTGRES_DB}_full.sql"
    POSTGRES_TEMP_FILE="${POSTGRES_BACKUP_FILE}.tmp"

    log "Creating database dump: $POSTGRES_BACKUP_FILE"
    log "  Database: $POSTGRES_DB"
    log "  User: $POSTGRES_USER"

    # Create pg_dump via Docker (atomic operation via temp file)
    if $DOCKER_CMD exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$POSTGRES_TEMP_FILE"; then
        mv "$POSTGRES_TEMP_FILE" "$POSTGRES_BACKUP_FILE"

        log "Compressing database dump..."
        if gzip "$POSTGRES_BACKUP_FILE"; then
            BACKUP_SIZE=$(du -h "${POSTGRES_BACKUP_FILE}.gz" | cut -f1)
            log "PostgreSQL backup completed successfully: ${POSTGRES_BACKUP_FILE}.gz ($BACKUP_SIZE)"
        else
            log_error "Failed to compress database dump"
            rm -f "$POSTGRES_BACKUP_FILE"
            exit 1
        fi
    else
        log_error "PostgreSQL backup failed"
        rm -f "$POSTGRES_TEMP_FILE"
        exit 1
    fi
}

# -------------------------------------------------------------
# 7. Cleanup Old Backups
# -------------------------------------------------------------
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."

    # Cleanup MinIO backups
    if [[ -d "$MINIO_BACKUP_DIR" ]]; then
        DELETED_COUNT=$(find "$MINIO_BACKUP_DIR" -name "*.tar" -type f -mtime +${RETENTION_DAYS} -delete -print | wc -l)
        log "Deleted $DELETED_COUNT old MinIO backup(s)"
    fi

    # Cleanup PostgreSQL backups
    if [[ -d "$POSTGRES_BACKUP_DIR" ]]; then
        DELETED_COUNT=$(find "$POSTGRES_BACKUP_DIR" -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete -print | wc -l)
        log "Deleted $DELETED_COUNT old PostgreSQL backup(s)"
    fi

    log "Cleanup completed"
}

# -------------------------------------------------------------
# 8. Main Execution
# -------------------------------------------------------------
main() {
    log "=========================================="
    log "NAS Backup Started"
    log "=========================================="

    # Check prerequisites
    check_prerequisites

    # Load database credentials
    load_db_credentials

    # Perform backups (DB first for consistency)
    backup_postgres
    backup_minio

    # Cleanup old backups
    cleanup_old_backups

    log "=========================================="
    log "NAS Backup Completed Successfully"
    log "=========================================="

    exit 0
}

# -------------------------------------------------------------
# 9. Error Handler
# -------------------------------------------------------------
trap 'log_error "Script failed at line $LINENO"; exit 1' ERR

# Run main function
main
