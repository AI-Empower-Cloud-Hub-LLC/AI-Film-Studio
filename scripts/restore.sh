#!/bin/bash
# =============================================================================
# AI Film Studio — Restore Script
# =============================================================================
# Usage: ./scripts/restore.sh <backup_dir>
#
# Example: ./scripts/restore.sh ./backups/20260101_020000
# =============================================================================

set -euo pipefail

BACKUP_PATH="${1:?Usage: $0 <backup_directory>}"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup directory not found: $BACKUP_PATH"
    exit 1
fi

echo "=== AI Film Studio Restore — from $BACKUP_PATH ==="

# --- PostgreSQL Restore ---
if [ -f "$BACKUP_PATH/database.dump" ] && [ -n "${DATABASE_URL:-}" ]; then
    echo "[1/4] Restoring PostgreSQL database..."
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*//\([^:]*\):.*|\1|p')

    PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p') \
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --clean --if-exists \
        "$BACKUP_PATH/database.dump"

    echo "  PostgreSQL restored."
else
    echo "[1/4] Skipping PostgreSQL restore"
fi

# --- SQLite Restore ---
if [ -f "$BACKUP_PATH/ai_film_studio.db" ]; then
    echo "[2/4] Restoring SQLite database..."
    cp "$BACKUP_PATH/ai_film_studio.db" backend/ai_film_studio.db
    echo "  SQLite restored."
else
    echo "[2/4] Skipping SQLite restore"
fi

# --- Uploads Restore ---
if [ -f "$BACKUP_PATH/uploads.tar.gz" ]; then
    echo "[3/4] Restoring uploaded files..."
    tar xzf "$BACKUP_PATH/uploads.tar.gz" -C backend/
    echo "  Uploads restored."
else
    echo "[3/4] Skipping uploads restore"
fi

# --- Media Restore ---
if [ -f "$BACKUP_PATH/media.tar.gz" ]; then
    echo "[4/4] Restoring generated media..."
    tar xzf "$BACKUP_PATH/media.tar.gz" -C backend/
    echo "  Media restored."
else
    echo "[4/4] Skipping media restore"
fi

echo ""
echo "=== Restore complete ==="
