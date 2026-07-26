#!/usr/bin/env bash
#
# Convert a MySQL database to PostgreSQL with pgloader.
#
# Reads connection details from .env (see .env.example) and runs pgloader in a
# container on the compose network, so nothing has to be installed on the host.
# The target database is dropped and recreated first, so the run always starts
# from empty and repeating it gives the same result.
#
# Usage:
#   tools/pgloader/convert.sh                 # convert $DB_NAME
#   MYSQL_DB=sg101_pristine tools/pgloader/convert.sh
#
# The summary is printed and also written to tools/pgloader/logs/.
set -euo pipefail

cd "$(dirname "$0")/../.."

# .env is a config file, not a shell script -- values may contain characters
# the shell would expand ($8 in the secret key, for one), so read the keys we
# need literally instead of sourcing it.
env_value() {
    [ -f .env ] || return 0
    sed -n "s/^$1=//p" .env | head -1
}

env_db_user="$(env_value DB_USER)"
env_db_password="$(env_value DB_PASSWORD)"
env_db_name="$(env_value DB_NAME)"

# Source: the MySQL service. Override MYSQL_DB to convert a different database
# on the same server -- that is how the pristine snapshot is converted without
# disturbing the working one.
MYSQL_HOST="${MYSQL_HOST:-db}"
MYSQL_USER="${MYSQL_USER:-$env_db_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-$env_db_password}"
MYSQL_DB="${MYSQL_DB:-$env_db_name}"

# Target: the Postgres service.
PG_HOST="${PG_HOST:-postgres}"
PG_USER="${PG_USER:-$env_db_user}"
PG_PASSWORD="${PG_PASSWORD:-$env_db_password}"
PG_DB="${PG_DB:-$env_db_name}"

: "${MYSQL_USER:?DB_USER not set in .env and MYSQL_USER not given}"
: "${MYSQL_DB:?DB_NAME not set in .env and MYSQL_DB not given}"

# The timezone the naive MySQL datetimes are written in. Read from Django so
# the two cannot drift apart; the fallback covers running this with the web
# container down.
APP_TIME_ZONE="${APP_TIME_ZONE:-$(docker compose exec -T web \
    python -c 'from django.conf import settings; print(settings.TIME_ZONE)' \
    2>/dev/null | tr -d '\r' || true)}"
APP_TIME_ZONE="${APP_TIME_ZONE:-America/Chicago}"

NETWORK="${COMPOSE_NETWORK:-sg101_default}"
# pgloader publishes amd64 only, so this runs under emulation on Apple
# Silicon. It is a one-off conversion, so the penalty is acceptable; declaring
# the platform keeps Docker from warning on every run.
IMAGE="${PGLOADER_IMAGE:-dimitri/pgloader:latest}"

log_dir="tools/pgloader/logs"
mkdir -p "$log_dir"
log_file="$log_dir/convert-$(date +%Y%m%d-%H%M%S).log"

echo "Converting mysql://${MYSQL_HOST}/${MYSQL_DB} -> postgresql://${PG_HOST}/${PG_DB}"
echo "Naive datetimes will be read as ${APP_TIME_ZONE}"

# Recreate the target. postgres is the maintenance database; you cannot drop
# the one you are connected to.
#
# The timezone is set on the database, before the load, and it is not
# cosmetic. MySQL datetime columns hold no offset, and with USE_TZ off Django
# wrote local wall-clock time into them -- the 02:00 hour is empty on every
# DST spring-forward day, which is the gap that only local time has. Django
# maps DateTimeField to timestamptz on PostgreSQL, so pgloader hands those
# naive strings to a column that must place them on the timeline, and it does
# that using the session timezone. Left at the server default of UTC they are
# stored as UTC instants; Django then reads them back in TIME_ZONE and every
# datetime in the database comes out 5-6 hours early.
docker compose exec -T postgres psql -U "$PG_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$PG_DB\" WITH (FORCE);" \
    -c "CREATE DATABASE \"$PG_DB\" ENCODING 'UTF8';" \
    -c "ALTER DATABASE \"$PG_DB\" SET timezone TO '$APP_TIME_ZONE';"

# Fill in the {{...}} placeholders. pgloader has a --context option for this,
# but its key lookup does not match a keyword alist in 3.6.7 -- the
# placeholders render as empty strings and the connection URLs come out as
# "mysql://:@/". Substituting here is one less moving part, and bash's
# replacement is literal, so a password containing regex or sed metacharacters
# cannot break it.
rendered="tools/pgloader/.sg101.rendered.load"
trap 'rm -f "$rendered"' EXIT

template=$(cat tools/pgloader/sg101.load)
template=${template//\{\{mysql_host\}\}/$MYSQL_HOST}
template=${template//\{\{mysql_user\}\}/$MYSQL_USER}
template=${template//\{\{mysql_password\}\}/$MYSQL_PASSWORD}
template=${template//\{\{mysql_db\}\}/$MYSQL_DB}
template=${template//\{\{pg_host\}\}/$PG_HOST}
template=${template//\{\{pg_user\}\}/$PG_USER}
template=${template//\{\{pg_password\}\}/$PG_PASSWORD}
template=${template//\{\{pg_db\}\}/$PG_DB}
printf '%s\n' "$template" > "$rendered"

if grep -q '{{' "$rendered"; then
    echo "error: unsubstituted placeholders remain:" >&2
    grep -n '{{' "$rendered" >&2
    exit 1
fi

# --root-dir points at a mounted directory so any rejected rows are readable
# afterwards. pgloader defaults to /tmp inside the container, where they
# vanish with it -- and a rejection that cannot be read cannot be explained.
reject_dir="$log_dir/rejects"
mkdir -p "$reject_dir"

docker run --rm \
    --platform linux/amd64 \
    --network "$NETWORK" \
    -v "$PWD/tools/pgloader:/work:ro" \
    -v "$PWD/$reject_dir:/output" \
    "$IMAGE" \
    pgloader --root-dir /output /work/.sg101.rendered.load 2>&1 | tee "$log_file"

echo
echo "Summary written to $log_file"
