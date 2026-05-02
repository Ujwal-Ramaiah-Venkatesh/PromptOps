#!/bin/bash

# PromptOps Restore Script
# ========================
#
# Restore PostgreSQL database and configuration from backup
# Phase 5A - Production Deployment
#
# Usage:
#   ./scripts/restore.sh /path/to/backup.sql.gz
#   ./scripts/restore.sh --latest
#   ./scripts/restore.sh --list
#
# Author: PromptOps Team

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-promptops-postgres}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_question() {
    echo -e "${BLUE}[QUESTION]${NC} $1"
}

# Show usage
show_usage() {
    echo "Usage:"
    echo "  $0 /path/to/backup.sql.gz  # Restore from specific backup"
    echo "  $0 --latest                # Restore from latest backup"
    echo "  $0 --list                  # List available backups"
    echo ""
    echo "Options:"
    echo "  --skip-confirm            # Skip confirmation prompt"
    echo "  --backup-current          # Backup current database before restore"
    echo ""
}

# List available backups
list_backups() {
    log_info "Available backups in $BACKUP_DIR:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    BACKUPS=$(find "$BACKUP_DIR" -name "promptops_db_*.sql.gz" -type f | sort -r)

    if [ -z "$BACKUPS" ]; then
        log_warn "No backups found"
        exit 0
    fi

    echo "$BACKUPS" | while read -r backup; do
        BACKUP_DATE=$(date -r "$backup" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || stat -c %y "$backup" | cut -d'.' -f1)
        BACKUP_SIZE=$(du -h "$backup" | cut -f1)
        echo "  $backup"
        echo "    Date: $BACKUP_DATE"
        echo "    Size: $BACKUP_SIZE"
        echo ""
    done
}

# Get latest backup
get_latest_backup() {
    LATEST=$(find "$BACKUP_DIR" -name "promptops_db_*.sql.gz" -type f | sort -r | head -1)

    if [ -z "$LATEST" ]; then
        log_error "No backups found in $BACKUP_DIR"
        exit 1
    fi

    echo "$LATEST"
}

# Confirm action
confirm_restore() {
    local backup_file="$1"

    log_warn "============================================"
    log_warn "WARNING: Database Restore Operation"
    log_warn "============================================"
    log_warn "This will:"
    log_warn "  1. Stop all database connections"
    log_warn "  2. Drop and recreate the database"
    log_warn "  3. Restore from: $backup_file"
    log_warn ""
    log_warn "ALL CURRENT DATA WILL BE LOST!"
    log_warn "============================================"
    echo ""

    log_question "Are you sure you want to continue? (yes/no): "
    read -r response

    if [ "$response" != "yes" ]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

# Backup current database before restore
backup_current() {
    log_info "Backing up current database before restore..."

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    PRE_RESTORE_BACKUP="$BACKUP_DIR/pre_restore_backup_$TIMESTAMP.sql.gz"

    POSTGRES_USER="${POSTGRES_USER:-promptops}"
    POSTGRES_DB="${POSTGRES_DB:-promptops}"

    docker exec "$POSTGRES_CONTAINER" pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --clean \
        --if-exists \
        | gzip > "$PRE_RESTORE_BACKUP"

    if [ $? -eq 0 ]; then
        log_info "Pre-restore backup saved: $PRE_RESTORE_BACKUP"
    else
        log_error "Pre-restore backup failed"
        exit 1
    fi
}

# Restore database
restore_database() {
    local backup_file="$1"

    log_info "Starting database restore from: $backup_file"

    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    # Check if PostgreSQL container is running
    if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
        log_error "PostgreSQL container '$POSTGRES_CONTAINER' is not running"
        exit 1
    fi

    POSTGRES_USER="${POSTGRES_USER:-promptops}"
    POSTGRES_DB="${POSTGRES_DB:-promptops}"

    # Stop backend service to close all connections
    log_info "Stopping backend service..."
    docker stop promptops-backend 2>/dev/null || true

    # Wait for connections to close
    sleep 2

    # Terminate remaining connections
    log_info "Terminating active database connections..."
    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" \
        2>/dev/null || true

    # Drop and recreate database
    log_info "Dropping and recreating database..."
    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c \
        "DROP DATABASE IF EXISTS $POSTGRES_DB;" \
        2>/dev/null || true

    docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c \
        "CREATE DATABASE $POSTGRES_DB;"

    # Restore from backup
    log_info "Restoring database from backup..."
    gunzip -c "$backup_file" | docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

    if [ $? -eq 0 ]; then
        log_info "Database restore completed successfully"
    else
        log_error "Database restore failed"
        exit 1
    fi

    # Restart backend service
    log_info "Restarting backend service..."
    docker start promptops-backend

    # Wait for backend to be healthy
    log_info "Waiting for backend to become healthy..."
    for i in {1..30}; do
        if docker exec promptops-backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "Backend is healthy"
            break
        fi
        sleep 2
    done
}

# Main script
main() {
    local backup_file=""
    local skip_confirm=false
    local backup_current_db=false

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --list)
                list_backups
                exit 0
                ;;
            --latest)
                backup_file=$(get_latest_backup)
                ;;
            --skip-confirm)
                skip_confirm=true
                shift
                ;;
            --backup-current)
                backup_current_db=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                backup_file="$1"
                shift
                ;;
        esac
    done

    # Validate backup file
    if [ -z "$backup_file" ]; then
        log_error "No backup file specified"
        echo ""
        show_usage
        exit 1
    fi

    log_info "Restore started at $(date)"
    log_info "Backup file: $backup_file"

    # Confirm restore
    if [ "$skip_confirm" = false ]; then
        confirm_restore "$backup_file"
    fi

    # Backup current database if requested
    if [ "$backup_current_db" = true ]; then
        backup_current
    fi

    # Perform restore
    restore_database "$backup_file"

    # Summary
    echo ""
    log_info "============================================"
    log_info "Restore completed successfully!"
    log_info "============================================"
    log_info "Restored from: $backup_file"
    log_info "Database: $POSTGRES_DB"
    log_info "Container: $POSTGRES_CONTAINER"
    log_info "Completed at: $(date)"
    log_info "============================================"

    log_info "Next steps:"
    log_info "  1. Verify application functionality"
    log_info "  2. Check backend logs: docker logs promptops-backend"
    log_info "  3. Test API endpoints"
    log_info "  4. Review dashboard"
}

# Run main function
main "$@"
