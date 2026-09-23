#!/usr/bin/env bash
#
# Create the two backup buckets, or bring existing ones into line: versioning on
# for both, lifecycle-db.json on the dumps bucket, and no lifecycle at all on the
# media bucket -- nothing there ever expires, and a rule someone adds by hand is
# removed. Safe to re-run.
#
# Run with an administrative credential, never the job's -- the job's cannot
# change bucket configuration, which is the point of it:
#     docker compose -f docker-compose.prod.yml run --rm \
#         -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... backup provision
#
# The job's own user and its policy (policy-writer.json) are created separately,
# because that is the one part the S3 API does not cover and each provider does
# differently.

set -euo pipefail

: "${BACKUP_DB_BUCKET:?}" "${BACKUP_MEDIA_BUCKET:?}"
region=${AWS_DEFAULT_REGION:-us-east-1}

for pair in "$BACKUP_DB_BUCKET:db" "$BACKUP_MEDIA_BUCKET:media"; do
    bucket=${pair%%:*}
    kind=${pair##*:}

    if ! aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
        # us-east-1 is the one region that rejects its own name as a constraint.
        if [ "$region" = us-east-1 ]; then
            aws s3api create-bucket --bucket "$bucket" >/dev/null
        else
            aws s3api create-bucket --bucket "$bucket" \
                --create-bucket-configuration LocationConstraint="$region" >/dev/null
        fi
        echo "created $bucket"
    fi

    # Versioning is what makes a put-only credential safe: it can overwrite, and
    # the overwritten object is kept as a prior version.
    aws s3api put-bucket-versioning --bucket "$bucket" \
        --versioning-configuration Status=Enabled
    if [ "$kind" = db ]; then
        aws s3api put-bucket-lifecycle-configuration --bucket "$bucket" \
            --lifecycle-configuration file:///etc/sg101-backup/lifecycle-db.json
        echo "$bucket: versioning on, dumps expire after 90 days"
    else
        aws s3api delete-bucket-lifecycle --bucket "$bucket"
        echo "$bucket: versioning on, nothing expires"
    fi
done
