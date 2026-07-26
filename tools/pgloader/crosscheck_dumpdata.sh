#!/usr/bin/env bash
#
# Cross-check a converted database against its MySQL source using Django's own
# serializer, as a second opinion on pgloader.
#
# verify_data.py compares the two databases by talking SQL to each of them.
# That shares an assumption with the conversion itself -- that the column types
# pgloader chose mean what we think they mean. dumpdata comes at the same rows
# from the other end: through the ORM, each value loaded into the Python type
# its model field declares and serialized by code that knows nothing about
# either engine. A decimal that lost its scale, a boolean stored as a string or
# a datetime that moved shows up here as a plain text difference.
#
# Models are chosen to cover the conversions that can go wrong quietly rather
# than to be exhaustive -- cp1252 text, floats, decimals, dates, times, inet,
# and long markup bodies.
#
# Usage:
#   tools/pgloader/crosscheck_dumpdata.sh
#   MYSQL_DB=sg101_pristine PG_DB=sg101 tools/pgloader/crosscheck_dumpdata.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

MYSQL_DB="${MYSQL_DB:-sg101_pristine}"
PG_DB="${PG_DB:-sg101}"

MODELS=(
    bandmap.BandEntry        # cp1252 text, two doubles
    contests.Contest         # cp1252 text with non-ASCII
    donations.Donation       # decimal(8,2), where scale matters
    downloads.Download       # double, and an inet that was char(39)
    gcalendar.Event          # the only date + time columns in the schema
    news.Story               # long markup bodies, date and datetime
    potd.Photo               # date
    weblinks.Link            # urls and text
    polls.Choice             # small, plain
    smiley.Smiley            # small, plain
    elsewhere.SocialNetwork  # small, plain
    antispam.SpamPhrase      # small, plain
)

out="tools/pgloader/logs/crosscheck"
mkdir -p "$out"

# dumpdata emits an unordered queryset, so the two engines are free to return
# the same rows in different orders -- Postgres especially, after a fresh load.
# Sorting by primary key here is what makes a plain diff meaningful.
normalize='
import json, sys
rows = json.load(sys.stdin)
rows.sort(key=lambda r: (r["model"], str(r["pk"])))
json.dump(rows, sys.stdout, indent=2, sort_keys=True, default=str)
'

status=0
for model in "${MODELS[@]}"; do
    for engine in mysql postgresql; do
        # Both engines are named explicitly. The container may already have
        # DB_ENGINE set -- it does whenever the stack was brought up against
        # Postgres -- and relying on the default would then read the MySQL
        # half out of Postgres.
        if [ "$engine" = mysql ]; then
            env_args=(-e DB_ENGINE=mysql -e "DB_NAME=$MYSQL_DB")
        else
            env_args=(-e DB_ENGINE=postgresql -e "DB_NAME=$PG_DB")
        fi
        docker compose exec -T "${env_args[@]}" web \
            python manage.py dumpdata "$model" \
            | docker compose exec -T web python -c "$normalize" \
            > "$out/$model.$engine.json"
    done

    if diff -q "$out/$model.mysql.json" "$out/$model.postgresql.json" >/dev/null
    then
        printf '  ok       %-26s %s rows\n' "$model" \
            "$(grep -c '"pk"' "$out/$model.mysql.json")"
    else
        printf '  DIFFERS  %-26s\n' "$model"
        diff "$out/$model.mysql.json" "$out/$model.postgresql.json" | head -40
        status=1
    fi
done

echo
if [ "$status" -eq 0 ]; then
    echo "OK -- Django's serializer sees identical data on both engines"
else
    echo "FAILED -- see the diffs above; dumps are in $out/"
fi
exit "$status"
