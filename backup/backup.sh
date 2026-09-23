#!/usr/bin/env bash
#
# Dump the database to the dumps bucket and copy /media to the media bucket.
#
# Configuration is the environment: PGHOST/PGUSER/PGPASSWORD/PGDATABASE from
# docker-compose.prod.yml, and from secrets/backup.env the buckets, the job's
# credential, AWS_ENDPOINT_URL for anything that is not AWS itself, and
# HEARTBEAT_URL.
#
# The heartbeat is what makes a missed night visible. The service is pinged at
# start, on success and at /fail, and it raises the alarm on a /fail or when a
# success is overdue -- which covers the failures this script cannot report
# itself: the timer not firing, the image not building, the machine being off.

set -euo pipefail

ping() {
    if [ -z "${HEARTBEAT_URL:-}" ]; then return 0; fi
    curl -fsS -m 10 --retry 3 -o /dev/null "$HEARTBEAT_URL$1" \
        || echo "backup: heartbeat $1 not delivered" >&2
}

dump=
finish() {
    status=$?
    rm -f "$dump"
    if [ "$status" -ne 0 ]; then
        echo "backup: FAILED, exit $status" >&2
        ping /fail
    fi
}
trap finish EXIT

: "${BACKUP_DB_BUCKET:?}" "${BACKUP_MEDIA_BUCKET:?}"
if [ -z "${HEARTBEAT_URL:-}" ]; then
    echo "backup: HEARTBEAT_URL is not set; nothing will notice if this fails" >&2
fi
ping /start

# Into the container's own filesystem, never streamed to the upload: if pg_dump
# dies partway, a stream still completes as a truncated object that looks like a
# backup, and this job's credential cannot delete it. Here set -e stops the job
# before anything is uploaded.
#
# The search index's rows are left out: two thirds of the database, and derived
# -- `manage.py reindex_search` rebuilds them after a restore.
dump=$(mktemp /tmp/sg101-XXXXXX.dump)
key="sg101-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump -Fc --exclude-table-data=search_searchdocument -f "$dump"
aws s3 cp --no-progress --only-show-errors "$dump" "s3://$BACKUP_DB_BUCKET/$key"
echo "backup: $key, $(du -h "$dump" | cut -f1)"

# Copies new and changed files only, and never --delete: a file removed from
# the site stays in the bucket, which is what a backup is for.
aws s3 sync --no-progress --only-show-errors /media "s3://$BACKUP_MEDIA_BUCKET/"
echo "backup: media synced"

ping ""
