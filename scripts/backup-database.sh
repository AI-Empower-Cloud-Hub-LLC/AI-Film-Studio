#!/bin/bash
set -e

# Database Backup Script for PostgreSQL
# Usage: ./backup-database.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_film_studio_$TIMESTAMP.sql.gz"

# Load environment
if [ ! -f ".env.production" ]; then
    echo "Error: .env.production not found"
    exit 1
fi

source .env.production

# Extract database URL components
DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:\/]+).*/\1/')
DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+).*/\1/')
DB_USER=$(echo $DATABASE_URL | sed -E 's/.*:\/\/([^:]+).*/\1/')
DB_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/([^?]+).*/\1/')

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."
echo "Database: $DB_NAME on $DB_HOST:$DB_PORT"

# Create backup
PGPASSWORD=$(echo $DATABASE_URL | sed -E 's/.*:([^@]+)@.*/\1/') \
pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    | gzip > "$BACKUP_FILE"

echo "✓ Backup created: $BACKUP_FILE"
echo "  File size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "ai_film_studio_*.sql.gz" -mtime +30 -delete
echo "✓ Cleaned up old backups (older than 30 days)"
