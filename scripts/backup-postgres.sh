#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_DB:=realityos}"
: "${POSTGRES_USER:=realityos}"
: "${BACKUP_DIR:=./backups}"
mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose -f infrastructure/docker-compose.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$BACKUP_DIR/realityos-$stamp.dump"
echo "Created $BACKUP_DIR/realityos-$stamp.dump"
