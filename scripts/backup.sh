#!/bin/bash
# =============================================================================
# AI Film Studio — Database & File Backup Script
# =============================================================================
# Usage: ./scripts/backup.sh [backup_dir]
#
# Backs up:
#   1. PostgreSQL database (pg_dump)
#   2. SQLite database file (if using SQLite)
#   3. Uploaded files (uploads/ directory)
#   4. Generated media (media/ directory)
#
# Schedule with cron for automatic backups:
#   0 2 * * * /path/to/AI-Film-Studio/scripts/backup.sh >> /var/log/ai-film-backup.log 2>&1
# =============================================================================

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
RETAIN_DAYS=30

echo "=== AI Film Studio Backup — $TIMESTAMP ==="

mkdir -p "$BACKUP_PATH"

# --- PostgreSQL Backup ---
if [ -n "${DATABASE_URL:-}" ] && echo "$DATABASE_URL" | grep -q "postgresql"; then
    echo "[1/4] Backing up PostgreSQL database..."
    # Extract connection params from DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*//\([^:]*\):.*|\1|p')

    PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p') \
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" \
        --format=custom \
        --file="$BACKUP_PATH/database.dump"

    echo "  PostgreSQL backup: $BACKUP_PATH/database.dump"
else
    echo "[1/4] Skipping PostgreSQL (DATABASE_URL not set or not PostgreSQL)"
fi

# --- SQLite Backup ---
SQLITE_FILE="backend/ai_film_studio.db"
if [ -f "$SQLITE_FILE" ]; then
    echo "[2/4] Backing up SQLite database..."
    cp "$SQLITE_FILE" "$BACKUP_PATH/ai_film_studio.db"
    echo "  SQLite backup: $BACKUP_PATH/ai_film_studio.db"
else
    echo "[2/4] Skipping SQLite (no file found)"
fi

# --- Uploads Backup ---
UPLOADS_DIR="backend/uploads"
if [ -d "$UPLOADS_DIR" ] && [ "$(ls -A "$UPLOADS_DIR" 2>/dev/null)" ]; then
    echo "[3/4] Backing up uploaded files..."
    tar czf "$BACKUP_PATH/uploads.tar.gz" -C backend uploads/
    echo "  Uploads backup: $BACKUP_PATH/uploads.tar.gz"
else
    echo "[3/4] Skipping uploads (directory empty or not found)"
fi

# --- Media Backup ---
MEDIA_DIR="backend/media"
if [ -d "$MEDIA_DIR" ] && [ "$(find "$MEDIA_DIR" -type f 2>/dev/null | head -1)" ]; then
    echo "[4/4] Backing up generated media..."
    tar czf "$BACKUP_PATH/media.tar.gz" -C backend media/
    echo "  Media backup: $BACKUP_PATH/media.tar.gz"
else
    echo "[4/4] Skipping media (directory empty or not found)"
fi

# --- Cleanup old backups ---
if [ -d "$BACKUP_DIR" ]; then
    OLD_BACKUPS=$(find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +$RETAIN_DAYS -not -name "$(basename "$BACKUP_DIR")" 2>/dev/null)
    if [ -n "$OLD_BACKUPS" ]; then
        echo ""
        echo "Cleaning up backups older than $RETAIN_DAYS days..."
        echo "$OLD_BACKUPS" | xargs rm -rf
        echo "  Removed old backups."
    fi
fi

echo ""
echo "=== Backup complete: $BACKUP_PATH ==="
ls -lh "$BACKUP_PATH/"
