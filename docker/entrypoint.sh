#!/usr/bin/env sh
set -eu

AUTO_MIGRATE_ON_START="${AUTO_MIGRATE_ON_START:-true}"
MIGRATION_MAX_RETRIES="${MIGRATION_MAX_RETRIES:-20}"
MIGRATION_RETRY_DELAY="${MIGRATION_RETRY_DELAY:-2}"

metric_log() {
  metric_name="$1"
  metric_status="$2"
  metric_value="$3"
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "metric=${metric_name} status=${metric_status} value=${metric_value} ts=${ts}"
}

if [ -n "${DATABASE_URL:-}" ] && [ "$AUTO_MIGRATE_ON_START" = "true" ]; then
  metric_log "assessment_migration_runs_total" "started" "1"
  echo "[entrypoint] Running alembic upgrade head"
  i=1
  while [ "$i" -le "$MIGRATION_MAX_RETRIES" ]; do
    if alembic upgrade head; then
      metric_log "assessment_migration_runs_total" "succeeded" "1"
      echo "[entrypoint] Migrations applied"
      break
    fi

    if [ "$i" -eq "$MIGRATION_MAX_RETRIES" ]; then
      metric_log "assessment_migration_runs_total" "failed" "1"
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
