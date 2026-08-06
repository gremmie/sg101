#!/usr/bin/env bash
#
# Take and restore PostgreSQL snapshots of the dev database.
#
# The MySQL service is already a fallback of sorts, but restoring from it means
# a full pgloader conversion and a cross-engine copy that has to get column
# types, booleans and the timezone seam right by hand. A PostgreSQL dump
# restores into a target that already has the right types, and the custom format
# lets you pull back a single table instead of the whole database.
#
# The search index is deliberately dumped WITHOUT its data. It is two thirds of
# the database (1.1 GB of 1.7 GB) and it is derived -- `reindex_search` rebuilds
# all 516,858 documents in about a minute and a half. A stale index is worse
# than an empty one, because `reconcile_search` would then report drift you have
# to reason about rather than a rebuild you can just run.
#
# Usage:
#   tools/pg_snapshot.sh dump [label]        take a snapshot, optionally labelled
#   tools/pg_snapshot.sh list                list snapshots, newest first
#   tools/pg_snapshot.sh restore FILE        replace the whole database (destructive)
#   tools/pg_snapshot.sh scratch FILE [T...] restore into a scratch database, to
#                                            cherry-pick rows from
#
set -euo pipefail

cd "$(dirname "$0")/.."

SNAPSHOT_DIR=snapshots
SERVICE=postgres
APP_SERVICES="web worker beat"
SCRATCH_DB=sg101_scratch

# The database name and user come from .env, the same place the app reads them,
# so this follows a database that has been pointed somewhere else. Read, not
# sourced: .env holds a SECRET_KEY, and sourcing a file to get two values out of
# it runs everything else in there as shell.
env_value() {
    [ -f .env ] || return 0
    sed -n "s/^$1=//p" .env | tail -1 | sed 's/^["'\'']//;s/["'\'']$//'
}
DB_NAME=${DB_NAME:-$(env_value DB_NAME)}
DB_USER=${DB_USER:-$(env_value DB_USER)}
DB_NAME=${DB_NAME:-sg101}
DB_USER=${DB_USER:-sg101}

# The snapshots directory is mounted read-only into the container, so a dump is
# streamed out over stdout rather than written from inside it.
pg() { docker compose exec -T "$SERVICE" "$@"; }

usage() { sed -n '3,26p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

case "${1:-}" in

dump)
    label=${2:-}
    [ -n "$label" ] && label="-$label"
    out="$SNAPSHOT_DIR/${DB_NAME}-$(date +%Y%m%d-%H%M%S)${label}.dump"
    mkdir -p "$SNAPSHOT_DIR"
    echo "dumping $DB_NAME -> $out"
    # -Fc: the custom format, which is compressed and, unlike plain SQL, lets
    # pg_restore pick individual tables out of the archive later.
    pg pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
        --exclude-table-data=search_searchdocument > "$out"
    echo "wrote $(du -h "$out" | cut -f1)  ($(basename "$out"))"
    echo "note: the search index is schema-only in this dump; rebuild it after a"
    echo "      full restore with: docker compose exec web python manage.py reindex_search"
    ;;

list)
    ls -lht "$SNAPSHOT_DIR"/*.dump 2>/dev/null || echo "no snapshots in $SNAPSHOT_DIR/"
    ;;

restore)
    file=${2:?usage: $0 restore FILE}
    base=$(basename "$file")
    [ -f "$SNAPSHOT_DIR/$base" ] || { echo "no such snapshot: $SNAPSHOT_DIR/$base" >&2; exit 1; }

    echo "This REPLACES the whole '$DB_NAME' database with $base."
    echo "Everything in it now is lost, including anything created since that snapshot."
    printf 'Type the database name to confirm: '
    read -r confirm
    [ "$confirm" = "$DB_NAME" ] || { echo "aborted"; exit 1; }

    # The app holds connections, and they block the drops --clean has to do.
    echo "stopping $APP_SERVICES"
    # shellcheck disable=SC2086
    docker compose stop $APP_SERVICES >/dev/null

    echo "restoring $base"
    # --clean --if-exists drops each object before recreating it, so this is a
    # replacement rather than a merge. Ordinary restores print notices about
    # objects that did not exist; --exit-on-error is deliberately not used.
    pg pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists \
        --no-owner --no-privileges "/snapshots/$base" || true

    # shellcheck disable=SC2086
    docker compose start $APP_SERVICES >/dev/null
    echo "started $APP_SERVICES"
    echo
    echo "the search index was not in the dump -- rebuild it now:"
    echo "  docker compose exec web python manage.py reindex_search"
    echo "then confirm with:"
    echo "  docker compose exec web python manage.py reconcile_search"
    ;;

scratch)
    file=${2:?usage: $0 scratch FILE [TABLE...]}
    base=$(basename "$file")
    shift 2 || true
    [ -f "$SNAPSHOT_DIR/$base" ] || { echo "no such snapshot: $SNAPSHOT_DIR/$base" >&2; exit 1; }

    tables=()
    for t in "$@"; do tables+=(-t "$t"); done

    echo "rebuilding $SCRATCH_DB from $base"
    pg psql -U "$DB_USER" -d postgres -q -c "drop database if exists $SCRATCH_DB"
    pg psql -U "$DB_USER" -d postgres -q -c "create database $SCRATCH_DB"
    pg pg_restore -U "$DB_USER" -d "$SCRATCH_DB" --no-owner --no-privileges \
        "${tables[@]}" "/snapshots/$base" || true

    echo
    echo "restored into '$SCRATCH_DB', alongside '$DB_NAME' and untouched by it."
    echo
    echo "To put rows back, copy them between the two databases -- both are in the"
    echo "same cluster, and piping \\copy keeps every column type intact, which is"
    echo "the whole reason to come through PostgreSQL rather than the MySQL snapshot:"
    echo
    echo "  docker compose exec -T $SERVICE sh -c \"psql -U $DB_USER -d $SCRATCH_DB \\"
    echo "    -c \\\\\"\\\\copy (select * from forums_topic where forum_id=3) to stdout\\\\\" | \\"
    echo "    psql -U $DB_USER -d $DB_NAME -c \\\\\"\\\\copy forums_topic from stdin\\\\\"\""
    echo
    echo "Mind the order when rows reference each other: forums_forum.last_post_id and"
    echo "forums_topic.last_post_id point at posts, so restore those columns after the"
    echo "posts exist, and reset sequences with setval() before anything inserts."
    echo
    echo "Drop it when you are done:"
    echo "  docker compose exec -T $SERVICE psql -U $DB_USER -d postgres -c 'drop database $SCRATCH_DB'"
    ;;

*)
    usage
    ;;
esac
