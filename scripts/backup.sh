#!/bin/bash

# PromptOps Backup Script
# =======================
#
# Automated backup script for PostgreSQL database and configuration
# Phase 5A - Production Deployment
#
# Usage:
#   ./scripts/backup.sh
#   ./scripts/backup.sh --retention-days 30
#
# Author: PromptOps Team

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${1:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-promptops-postgres}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"
log_info "Backup directory: $BACKUP_DIR"

# Check if PostgreSQL container is running
if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
    log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
    exit 1
fi

log_info "Starting backup at $(date)"

# ============================================================================
# 1. Backup PostgreSQL Database
# ============================================================================

log_info "Backing up PostgreSQL database..."

POSTGRES_USER="${POSTGRES_USER:-promptops}"
POSTGRES_DB="${POSTGRES_DB:-promptops}"
DB_BACKUP_FILE="$BACKUP_DIR/promptops_db_$TIMESTAMP.sql.gz"

docker exec "$POSTGRES_CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --create \
    | gzip > "$DB_BACKUP_FILE"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
    log_info "Database backup completed: $DB_BACKUP_FILE ($BACKUP_SIZE)"
else
    log_error "Database backup failed"
    exit 1
fi

# ============================================================================
# 2. Backup Configuration Files
# ============================================================================

log_info "Backing up configuration files..."

CONFIG_BACKUP_FILE="$BACKUP_DIR/promptops_config_$TIMESTAMP.tar.gz"

tar -czf "$CONFIG_BACKUP_FILE" \
    --exclude='*.log' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='backups' \
    docker/.env \
    monitoring/ \
    2>/dev/null || true

if [ $? -eq 0 ]; then
    CONFIG_SIZE=$(du -h "$CONFIG_BACKUP_FILE" | cut -f1)
    log_info "Configuration backup completed: $CONFIG_BACKUP_FILE ($CONFIG_SIZE)"
else
    log_warn "Configuration backup had warnings (non-critical)"
fi

# ============================================================================
# 3. Backup ML Models
# ============================================================================

log_info "Backing up ML models..."

if [ -d "phase4-ml/models" ]; then
    MODELS_BACKUP_FILE="$BACKUP_DIR/promptops_models_$TIMESTAMP.tar.gz"

    tar -czf "$MODELS_BACKUP_FILE" phase4-ml/models/

    if [ $? -eq 0 ]; then
        MODELS_SIZE=$(du -h "$MODELS_BACKUP_FILE" | cut -f1)
        log_info "ML models backup completed: $MODELS_BACKUP_FILE ($MODELS_SIZE)"
    else
        log_warn "ML models backup failed (non-critical)"
    fi
else
    log_warn "No ML models directory found, skipping"
fi

# ============================================================================
# 4. Create Backup Manifest
# ============================================================================

log_info "Creating backup manifest..."

MANIFEST_FILE="$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"

cat > "$MANIFEST_FILE" <<EOF
PromptOps Backup Manifest
=========================

Backup Date: $(date)
Backup Timestamp: $TIMESTAMP

Files:
- Database: $DB_BACKUP_FILE
- Configuration: $CONFIG_BACKUP_FILE
- ML Models: $MODELS_BACKUP_FILE

Database Info:
- Container: $POSTGRES_CONTAINER
- User: $POSTGRES_USER
- Database: $POSTGRES_DB

System Info:
- Hostname: $(hostname)
- OS: $(uname -s)
- Kernel: $(uname -r)

Docker Containers:
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}")

Backup Checksums:
$(md5sum "$DB_BACKUP_FILE" 2>/dev/null || echo "N/A")
$(md5sum "$CONFIG_BACKUP_FILE" 2>/dev/null || echo "N/A")
$(md5sum "$MODELS_BACKUP_FILE" 2>/dev/null || echo "N/A")
EOF

log_info "Manifest created: $MANIFEST_FILE"

# ============================================================================
# 5. Cleanup Old Backups
# ============================================================================

log_info "Cleaning up backups older than $RETENTION_DAYS days..."

if [ "$RETENTION_DAYS" -gt 0 ]; then
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "promptops_*" -type f -mtime +$RETENTION_DAYS)

    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | while read -r file; do
            log_info "Removing old backup: $file"
            rm -f "$file"
        done

        REMOVED_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
        log_info "Removed $REMOVED_COUNT old backup(s)"
    else
        log_info "No old backups to remove"
    fi
else
    log_warn "Backup retention disabled (RETENTION_DAYS=0)"
fi

# ============================================================================
# 6. Backup Summary
# ============================================================================

TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
log_info "============================================"
log_info "Backup completed successfully!"
log_info "============================================"
log_info "Backup location: $BACKUP_DIR"
log_info "Total backup size: $TOTAL_SIZE"
log_info "Retention: $RETENTION_DAYS days"
log_info ""
log_info "Files created:"
log_info "  - $DB_BACKUP_FILE"
log_info "  - $CONFIG_BACKUP_FILE"
[ -f "$MODELS_BACKUP_FILE" ] && log_info "  - $MODELS_BACKUP_FILE"
log_info "  - $MANIFEST_FILE"
log_info "============================================"

# ============================================================================
# 7. Optional: Upload to Cloud Storage (Uncomment if needed)
# ============================================================================

# log_info "Uploading backups to cloud storage..."

# AWS S3 Example:
# aws s3 cp "$DB_BACKUP_FILE" "s3://your-bucket/promptops/backups/"
# aws s3 cp "$CONFIG_BACKUP_FILE" "s3://your-bucket/promptops/backups/"

# Google Cloud Storage Example:
# gsutil cp "$DB_BACKUP_FILE" "gs://your-bucket/promptops/backups/"
# gsutil cp "$CONFIG_BACKUP_FILE" "gs://your-bucket/promptops/backups/"

# Azure Blob Storage Example:
# az storage blob upload --file "$DB_BACKUP_FILE" --container promptops --name "backups/$(basename $DB_BACKUP_FILE)"

# log_info "Cloud upload completed"

exit 0
