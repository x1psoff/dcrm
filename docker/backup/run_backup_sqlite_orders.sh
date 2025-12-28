#!/usr/bin/env bash
set -euo pipefail

# High-frequency SQLite-only backups:
# - Uses sqlite3 online .backup to produce an atomic snapshot file
# - Feeds it to restic via --stdin (restic cannot mix --stdin with file args)
# - Runs prune at most once per PRUNE_INTERVAL_MIN (default 60 min)

: "${BACKUP_PREFIX:=dcrm_orders}"
: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY required}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD required}"

: "${BACKUP_SQLITE_PATH:=/data/db.sqlite3}"

# retention (keep-last preferred for high-frequency)
: "${RETENTION_KEEP_LAST:=2000}"
: "${PRUNE_INTERVAL_MIN:=60}"

echo "[backup-orders] repo=${RESTIC_REPOSITORY}"

if ! restic snapshots >/dev/null 2>&1; then
  echo "[backup-orders] restic repo not initialized, running restic init..."
  restic init
fi

if [ ! -f "${BACKUP_SQLITE_PATH}" ]; then
  echo "[backup-orders] ERROR: sqlite db file not found: ${BACKUP_SQLITE_PATH}"
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
tmpdb="${tmpdir}/db.sqlite3"

echo "[backup-orders] creating atomic sqlite backup via .backup ..."
sqlite3 "${BACKUP_SQLITE_PATH}" ".backup '${tmpdb}'"

echo "[backup-orders] validating sqlite integrity..."
sqlite3 "${tmpdb}" "PRAGMA integrity_check;" | grep -qx "ok"

echo "[backup-orders] backing up db via stdin as data/db.sqlite3"
cat "${tmpdb}" | restic backup --stdin --stdin-filename "data/db.sqlite3" --tag "sqlite" --tag "${BACKUP_PREFIX}"

should_prune=1
if [ "${PRUNE_INTERVAL_MIN}" = "0" ] || [ "${PRUNE_INTERVAL_MIN}" = "always" ]; then
  should_prune=1
else
  stamp="/tmp/restic_last_prune_epoch"
  now="$(date +%s)"
  last="0"
  if [ -f "${stamp}" ]; then
    last="$(cat "${stamp}" || echo 0)"
  fi
  interval_sec=$(( PRUNE_INTERVAL_MIN * 60 ))
  if [ $(( now - last )) -lt "${interval_sec}" ]; then
    should_prune=0
  fi
fi

if [ "${should_prune}" = "1" ]; then
  echo "[backup-orders] applying retention policy (keep-last ${RETENTION_KEEP_LAST})..."
  restic forget --prune --keep-last "${RETENTION_KEEP_LAST}"
  date +%s > /tmp/restic_last_prune_epoch || true
else
  echo "[backup-orders] skipping prune (PRUNE_INTERVAL_MIN=${PRUNE_INTERVAL_MIN})"
fi

echo "[backup-orders] done"


