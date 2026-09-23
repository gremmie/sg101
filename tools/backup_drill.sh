#!/usr/bin/env bash
#
# Drill the backup job end to end against a local S3-compatible endpoint.
#
# Provisions two buckets on a throwaway MinIO the same way the real ones are
# provisioned, runs the job as production runs it, then checks what arrived:
# that the dump restores with every row, that media is copied and only copied
# once, that the job's credential cannot delete, that a failed run is announced
# and uploads nothing, and that no dump lands anywhere on this machine.
#
# Usage:
#   tools/backup_drill.sh
#
# Needs the production stack running (its database is what gets dumped):
#   docker compose -f docker-compose.prod.yml up -d
#
# Writes to that database only to create, and then drop, a scratch database for
# the restore. The fixtures are removed on exit, and MinIO keeps nothing
# between runs.
#
# Exits non-zero if any check fails, after running them all.

set -u

cd "$(dirname "$0")/.." || exit 2

DC=(docker compose -f docker-compose.prod.yml -f docker-compose.backup-drill.yml
    --profile drill --profile backup)
DB_BUCKET=sg101-drill-db
MEDIA_BUCKET=sg101-drill-media
ALT_BUCKET=sg101-drill-alt
RESTORE_DB=sg101_drill_restore

failures=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n      %s\n' "$1" "$2"; failures=$((failures + 1)); }

# Admin-credentialed AWS CLI against MinIO; -T so stdout can be piped.
aws_admin() { "${DC[@]}" run --rm -T awscli "$@"; }
# The same, with the job's own credential.
aws_writer() {
    "${DC[@]}" run --rm -T -e AWS_ACCESS_KEY_ID=drill-writer \
        -e AWS_SECRET_ACCESS_KEY=drill-writer-secret awscli "$@"
}
psql_q() { "${DC[@]}" exec -T postgres sh -c "psql -U \"\$POSTGRES_USER\" -Atq $*"; }
# Every heartbeat path received since the fixture started, in order.
pings() { "${DC[@]}" logs --no-log-prefix heartbeat 2>/dev/null | sed -n 's/^PING //p'; }
# The job, as the host timer runs it; extra arguments go before the service.
run_backup() { "${DC[@]}" run --rm -T "$@" backup >/dev/null 2>&1; }

dump_keys() {
    aws_admin s3api list-objects-v2 --bucket "${1:-$DB_BUCKET}" \
        --query 'Contents[].Key' --output text 2>/dev/null | tr '\t' '\n' | grep '\.dump$'
}
count_versions() {
    aws_admin s3api list-object-versions --bucket "$1" \
        --query 'length(Versions)' --output text 2>/dev/null
}

# Per-table row counts, one "table count" line each, for comparing databases.
TABLE_COUNTS="select table_name || ' ' || (xpath('/row/c/text()', query_to_xml(
    format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text
    from information_schema.tables
    where table_schema = 'public' and table_type = 'BASE TABLE' order by 1"

marker=$(mktemp)
cleanup() {
    rm -f "$marker"
    psql_q -d postgres -c "\"drop database if exists $RESTORE_DB\"" >/dev/null 2>&1
    "${DC[@]}" rm -sf minio heartbeat >/dev/null 2>&1
}
trap cleanup EXIT

# --- fixtures ----------------------------------------------------------------

echo "starting fixtures"
# --renew-anon-volumes: MinIO's image declares /data a volume, which a plain
# recreate keeps -- and a bucket already holding the last run's objects passes
# checks this run never earned.
"${DC[@]}" up -d --force-recreate --renew-anon-volumes --wait minio heartbeat >/dev/null 2>&1 \
    || { echo "fixtures did not start" >&2; exit 2; }
"${DC[@]}" build -q backup >/dev/null 2>&1

echo "provisioning buckets"
provisioned=1
for bucket in "$DB_BUCKET:$MEDIA_BUCKET" "$ALT_BUCKET:$MEDIA_BUCKET"; do
    "${DC[@]}" run --rm -T \
        -e AWS_ACCESS_KEY_ID=drill-admin -e AWS_SECRET_ACCESS_KEY=drill-admin-secret \
        -e BACKUP_DB_BUCKET="${bucket%%:*}" -e BACKUP_MEDIA_BUCKET="${bucket##*:}" \
        backup provision >/dev/null 2>&1 || provisioned=0
done
# The mc image has no sed, so the bucket names go into the policy out here.
sed -e "s/@DB_BUCKET@/$DB_BUCKET/g" -e "s/@MEDIA_BUCKET@/$MEDIA_BUCKET/g" backup/policy-writer.json |
"${DC[@]}" run --rm -T mc "
    cat > /tmp/policy.json &&
    mc alias set local http://minio:9000 drill-admin drill-admin-secret >/dev/null &&
    mc admin user add local drill-writer drill-writer-secret >/dev/null &&
    mc admin policy create local sg101-backup-writer /tmp/policy.json >/dev/null &&
    mc admin policy attach local sg101-backup-writer --user drill-writer >/dev/null
" >/dev/null 2>&1 || provisioned=0
if [ "$provisioned" = 1 ]; then pass "buckets, versioning, lifecycle and the job's user provisioned"
else fail "provisioning" "backup provision or the mc user/policy step failed"; fi

# --- a successful run --------------------------------------------------------

touch "$marker"
media_before=$(count_versions "$MEDIA_BUCKET")
if { [ -z "$media_before" ] || [ "$media_before" = None ]; } && [ -z "$(dump_keys)" ]; then pass "the buckets start empty"
else fail "the buckets start empty" "media versions '$media_before', dumps '$(dump_keys | tr '\n' ' ')'"; fi
if run_backup -e HEARTBEAT_URL=http://heartbeat:8000/ok; then
    pass "a backup run exits 0"
else
    fail "a backup run exits 0" "exit status $?"
fi

got=$(pings | grep '^/ok' | tr '\n' ' ')
if [ "$got" = "/ok/start /ok " ]; then pass "heartbeat: start, then success"
else fail "heartbeat: start, then success" "wanted '/ok/start /ok', got '$got'"; fi

key=$(dump_keys | sort | tail -1)
if [ -z "$key" ]; then
    fail "a dump reached the dumps bucket" "no *.dump object in $DB_BUCKET"
else
    pass "a dump reached the dumps bucket ($key)"
    toc=$(aws_admin s3 cp "s3://$DB_BUCKET/$key" - 2>/dev/null |
        "${DC[@]}" exec -T postgres pg_restore --list 2>/dev/null)
    if grep -q 'TABLE DATA public forums_post ' <<<"$toc"; then
        pass "the dump is a readable custom-format archive"
    else
        fail "the dump is a readable custom-format archive" "pg_restore --list did not list forums_post data"
    fi
    if grep -q 'TABLE DATA public search_searchdocument ' <<<"$toc"; then
        fail "the search index's data is excluded" "search_searchdocument data is in the archive"
    elif grep -q 'TABLE public search_searchdocument ' <<<"$toc"; then
        pass "the search index's data is excluded, its table kept"
    else
        fail "the search index's data is excluded" "search_searchdocument is missing entirely"
    fi

    # The restore: into a scratch database, every table's row count compared.
    psql_q -d postgres -c "\"drop database if exists $RESTORE_DB\"" >/dev/null 2>&1
    psql_q -d postgres -c "\"create database $RESTORE_DB\"" >/dev/null 2>&1
    aws_admin s3 cp "s3://$DB_BUCKET/$key" - 2>/dev/null |
        "${DC[@]}" exec -T postgres sh -c \
        "pg_restore -U \"\$POSTGRES_USER\" -d $RESTORE_DB --no-owner --no-privileges" \
        >/dev/null 2>&1
    source_counts=$(psql_q -d '"$POSTGRES_DB"' -c "\"$TABLE_COUNTS\"" 2>/dev/null |
        grep -v '^search_searchdocument ')
    restored_counts=$(psql_q -d $RESTORE_DB -c "\"$TABLE_COUNTS\"" 2>/dev/null |
        grep -v '^search_searchdocument ')
    tables=$(grep -c . <<<"$source_counts")
    if [ "$tables" -gt 0 ] && [ "$source_counts" = "$restored_counts" ]; then
        pass "restored: all $tables tables' row counts match the source"
    else
        fail "restored row counts match the source" \
            "$(diff <(echo "$source_counts") <(echo "$restored_counts") | head -5 | tr '\n' ' ')"
    fi
fi

local_files=$(find media -type f | wc -l | tr -d ' ')
bucket_files=$(aws_admin s3 ls --recursive "s3://$MEDIA_BUCKET/" 2>/dev/null | wc -l | tr -d ' ')
if [ "$local_files" -gt 0 ] && [ "$local_files" = "$bucket_files" ]; then
    pass "media: all $local_files files are in the media bucket"
else
    fail "media: every file is in the media bucket" "$local_files on disk, $bucket_files in the bucket"
fi

sample=$(find media -type f | sort | head -1)
sample_key=${sample#media/}
if [ -n "$sample" ] && [ "$(md5 -q "$sample" 2>/dev/null || md5sum "$sample" | cut -d' ' -f1)" = \
     "$(aws_admin s3 cp "s3://$MEDIA_BUCKET/$sample_key" - 2>/dev/null | { md5 -q 2>/dev/null || md5sum | cut -d' ' -f1; })" ]; then
    pass "media: a sample file's content matches ($sample_key)"
else
    fail "media: a sample file's content matches" "checksum differs or missing for $sample_key"
fi

# --- a second run copies no media again, and deletes nothing -------------------

# Stands in for a file since removed from the site: in the bucket, not on disk.
echo removed | aws_admin s3 cp - "s3://$MEDIA_BUCKET/drill-removed-from-site.txt" >/dev/null 2>&1
media_after_first=$(count_versions "$MEDIA_BUCKET")
if run_backup -e HEARTBEAT_URL=http://heartbeat:8000/again &&
   aws_admin s3api head-object --bucket "$MEDIA_BUCKET" --key drill-removed-from-site.txt >/dev/null 2>&1; then
    pass "media: a file gone from the site stays in the bucket"
else
    fail "media: a file gone from the site stays in the bucket" "the run failed, or the object was removed"
fi
media_after_second=$(count_versions "$MEDIA_BUCKET")
if [ -n "$media_after_first" ] && [ "$media_after_first" != None ] &&
   [ "$media_after_first" = "$media_after_second" ]; then
    pass "media: a second run uploads nothing ($media_after_second versions)"
else
    fail "media: a second run uploads nothing" "versions $media_after_first -> $media_after_second"
fi

# --- the job's credential ------------------------------------------------------

if [ -z "$key" ]; then
    fail "the job's credential cannot delete" "no dump to try it on"
elif ! aws_writer s3api delete-object --bucket "$DB_BUCKET" --key "$key" >/dev/null 2>&1 &&
     ! aws_writer s3api delete-object --bucket "$MEDIA_BUCKET" --key "$sample_key" >/dev/null 2>&1; then
    pass "the job's credential cannot delete, in either bucket"
else
    fail "the job's credential cannot delete" "a delete-object call succeeded"
fi

if [ -n "$sample_key" ] &&
   echo overwritten | aws_writer s3 cp - "s3://$MEDIA_BUCKET/$sample_key" >/dev/null 2>&1; then
    oldest=$(aws_admin s3api list-object-versions --bucket "$MEDIA_BUCKET" --prefix "$sample_key" \
        --query 'Versions[?IsLatest==`false`].VersionId | [0]' --output text 2>/dev/null)
    original=$(md5 -q "$sample" 2>/dev/null || md5sum "$sample" | cut -d' ' -f1)
    # get-object writes the body to a file and its metadata to stdout, and
    # `aws s3 cp` cannot name a version -- so fetch inside the container, then cat.
    kept=$("${DC[@]}" run --rm -T --entrypoint sh awscli -c \
        "aws s3api get-object --bucket $MEDIA_BUCKET --key '$sample_key' --version-id '$oldest' /tmp/v >/dev/null && cat /tmp/v" \
        2>/dev/null | { md5 -q 2>/dev/null || md5sum | cut -d' ' -f1; })
    if [ -n "$oldest" ] && [ "$oldest" != None ] && [ "$kept" = "$original" ]; then
        pass "an overwrite by the job's credential keeps the original version"
    else
        fail "an overwrite keeps the original version" "no prior version, or its content differs"
    fi
else
    fail "an overwrite keeps the original version" "the overwrite itself failed"
fi

for b in "$DB_BUCKET" "$MEDIA_BUCKET"; do
    v=$(aws_admin s3api get-bucket-versioning --bucket "$b" --query Status --output text 2>/dev/null)
    if [ "$v" = Enabled ]; then pass "versioning is on: $b"
    else fail "versioning is on: $b" "status '$v'"; fi
done

# --- retention -------------------------------------------------------------------

# The rules as the bucket reports them; "{}" when it has none.
lifecycle() {
    aws_admin s3api get-bucket-lifecycle-configuration --bucket "$1" 2>/dev/null || echo '{}'
}
db_ok=$(lifecycle "$DB_BUCKET" | python3 -c "import json, sys
rs = [r for r in json.load(sys.stdin).get('Rules', []) if r['Status'] == 'Enabled']
def whole(r):
    f = r.get('Filter', {})
    return not r.get('Prefix') and not f.get('Prefix') and 'Tag' not in f and 'And' not in f
print(any(whole(r) and r.get('Expiration', {}).get('Days') == 90 for r in rs))" 2>/dev/null)
if [ "$db_ok" = True ]; then pass "dumps bucket: a whole-bucket 90-day expiry"
else fail "dumps bucket: a whole-bucket 90-day expiry" "lifecycle read back as '${db_ok:-unreadable}'"; fi

media_rules=$(lifecycle "$MEDIA_BUCKET" | python3 -c "import json, sys
print(len(json.load(sys.stdin).get('Rules', [])))" 2>/dev/null)
if [ "$media_rules" = 0 ]; then pass "media bucket: no lifecycle rules, so nothing ever expires"
else fail "media bucket: no lifecycle rules" "${media_rules:-unreadable} rule(s)"; fi

# Re-provisioning is how drift is corrected, so it must be safe to repeat and
# must take away a media rule someone added by hand.
aws_admin s3api put-bucket-lifecycle-configuration --bucket "$MEDIA_BUCKET" \
    --lifecycle-configuration '{"Rules":[{"ID":"hand-added","Status":"Enabled","Filter":{},"Expiration":{"Days":30}}]}' \
    >/dev/null 2>&1
if "${DC[@]}" run --rm -T \
       -e AWS_ACCESS_KEY_ID=drill-admin -e AWS_SECRET_ACCESS_KEY=drill-admin-secret \
       backup provision >/dev/null 2>&1 &&
   [ "$(lifecycle "$MEDIA_BUCKET" | python3 -c "import json, sys
print(len(json.load(sys.stdin).get('Rules', [])))" 2>/dev/null)" = 0 ]; then
    pass "provision re-runs cleanly and removes a hand-added media rule"
else
    fail "provision re-runs cleanly and removes a hand-added media rule" "it failed, or the rule survived"
fi

uid=$("${DC[@]}" run --rm -T --entrypoint id backup -u 2>/dev/null)
if [ -n "$uid" ] && [ "$uid" != 0 ]; then pass "the job runs as an ordinary user (uid $uid)"
else fail "the job runs as an ordinary user" "uid '${uid:-unknown}'"; fi

# --- the destination is configuration ---------------------------------------------

run_backup -e BACKUP_DB_BUCKET="$ALT_BUCKET" \
    -e AWS_ACCESS_KEY_ID=drill-admin -e AWS_SECRET_ACCESS_KEY=drill-admin-secret \
    -e HEARTBEAT_URL=http://heartbeat:8000/alt
if [ -n "$(dump_keys "$ALT_BUCKET")" ]; then pass "the bucket is configuration: a changed name is followed"
else fail "the bucket is configuration" "no dump arrived in $ALT_BUCKET"; fi

# --- failures are announced, and upload nothing --------------------------------------

dumps_before=$(dump_keys | wc -l | tr -d ' ')
if run_backup -e PGPASSWORD=wrong -e HEARTBEAT_URL=http://heartbeat:8000/badpw; then
    fail "a database failure fails the job" "exit status 0"
else
    pass "a database failure fails the job"
fi
if pings | grep -qx '/badpw/fail'; then pass "a database failure pings /fail"
else fail "a database failure pings /fail" "got '$(pings | grep '^/badpw' | tr '\n' ' ')'"; fi
if [ "$(dump_keys | wc -l | tr -d ' ')" = "$dumps_before" ]; then pass "a database failure uploads no dump"
else fail "a database failure uploads no dump" "a new object appeared"; fi

# A dump cut off mid-stream: kill pg_dump's connection while it is copying.
"${DC[@]}" run --rm -T -e HEARTBEAT_URL=http://heartbeat:8000/cut backup >/dev/null 2>&1 &
job=$!
killed=0
for _ in $(seq 1 200); do
    n=$(psql_q -d postgres -c "\"select count(pg_terminate_backend(pid)) from pg_stat_activity
        where application_name = 'pg_dump' and query ilike 'copy %'\"" 2>/dev/null)
    [ "${n:-0}" -gt 0 ] && { killed=1; break; }
    sleep 0.05
done
wait "$job"; status=$?
if [ "$killed" = 0 ]; then
    fail "a dump cut short fails the job" "never caught pg_dump mid-copy"
elif [ "$status" != 0 ] && pings | grep -qx '/cut/fail' &&
     [ "$(dump_keys | wc -l | tr -d ' ')" = "$dumps_before" ]; then
    pass "a dump cut short fails the job, pings /fail, and uploads nothing"
else
    fail "a dump cut short fails the job, pings /fail, and uploads nothing" \
        "exit $status; pings '$(pings | grep '^/cut' | tr '\n' ' ')'; dumps $dumps_before -> $(dump_keys | wc -l | tr -d ' ')"
fi

# --- nothing lands on this machine ------------------------------------------------------

landed=$(find . -path ./.git -prune -o -path ./var/log -prune -o -type f -newer "$marker" -print 2>/dev/null |
    grep -E '\.dump$|^\./(media|static|var/public|var/maintenance)/' | head -5)
if [ -z "$landed" ]; then pass "no dump, and nothing under a served path, was written on the host"
else fail "nothing written on the host" "$(tr '\n' ' ' <<<"$landed")"; fi

echo
if [ "$failures" -eq 0 ]; then echo "all checks passed"; else echo "$failures check(s) failed"; fi
exit $((failures > 0))
