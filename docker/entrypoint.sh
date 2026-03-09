#!/usr/bin/env sh
set -eu

AUTO_MIGRATE_ON_START="${AUTO_MIGRATE_ON_START:-true}"
MIGRATION_MAX_RETRIES="${MIGRATION_MAX_RETRIES:-20}"
MIGRATION_RETRY_DELAY="${MIGRATION_RETRY_DELAY:-2}"

if [ -n "${DATABASE_URL:-}" ] && [ "$AUTO_MIGRATE_ON_START" = "true" ]; then
  echo "[entrypoint] Running alembic upgrade head"
  i=1
  while [ "$i" -le "$MIGRATION_MAX_RETRIES" ]; do
    if alembic upgrade head; then
      echo "[entrypoint] Migrations applied"
      break
    fi

    if [ "$i" -eq "$MIGRATION_MAX_RETRIES" ]; then
      echo "[entrypoint] Migration failed after $MIGRATION_MAX_RETRIES attempts"
      exit 1
    fi

    echo "[entrypoint] Migration attempt $i failed, retry in ${MIGRATION_RETRY_DELAY}s"
    sleep "$MIGRATION_RETRY_DELAY"
    i=$((i + 1))
  done
else
  echo "[entrypoint] Skip migrations (DATABASE_URL empty or AUTO_MIGRATE_ON_START!=true)"
fi

exec "$@"
