#!/usr/bin/env bash
#
# Send real mail through Postmark, from a throwaway container.
#
# This exists so that sending is a deliberate act rather than a property of the
# dev stack. Put the provider's settings in .env and every container built from
# it can mail the outside world -- including the site you browse at localhost,
# whose database is a production snapshot full of real member addresses. A
# forum reply there calls notify_topic_subscribers(), which reads
# topic.subscribers, and the worker delivers to real people from
# admin@surfguitar101.com. Nobody has to do anything unusual for that to happen.
#
# So the six mail variables live here instead, passed to one container that is
# discarded when it exits (--rm). Values given with -e override env_file, so
# this works whether or not .env carries mail settings.
#
# THE TOKEN IS NEVER AN ARGUMENT. `docker compose run -e VAR`, with no `=`,
# takes the value from this shell's environment, so it does not appear in the
# command line and therefore not in `ps` output or your shell history. Passing
# -e EMAIL_HOST_USER="$token" would put it in both.
#
# Postmark authenticates its SMTP interface with the *server API token* as both
# the username and the password. That is not a mistake in this script.
#
# Usage:
#   POSTMARK_TOKEN_FILE=~/.config/sg101/postmark-token \
#       tools/live_mail.sh you@outlook.com --only registration
#
#   POSTMARK_TOKEN=xxxx tools/live_mail.sh you@outlook.com you@gmail.com
#
#   tools/live_mail.sh --dry-run you@outlook.com    print the command, send nothing
#
# Everything after the flags is handed to tools/email_smoke.py after --live, so
# its own options work here: --only PATH narrows a run to a single message,
# which is what a first send against a young sending reputation wants.
#
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
    sed -n '3,40p' "$0" | sed 's/^# \{0,1\}//'
}

DRY_RUN=
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
    shift
fi

if [ $# -eq 0 ]; then
    usage
    exit 2
fi

# The token, from the environment or from a file OUTSIDE this repository.
if [ -n "${POSTMARK_TOKEN:-}" ]; then
    :
elif [ -n "${POSTMARK_TOKEN_FILE:-}" ]; then
    if [ ! -r "${POSTMARK_TOKEN_FILE}" ]; then
        echo "cannot read POSTMARK_TOKEN_FILE: ${POSTMARK_TOKEN_FILE}" >&2
        exit 2
    fi
    # Refuse a token stored inside the working tree. Nothing here would commit
    # it, but a secret one `git add -A` away from being published is not a
    # secret, and the whole point of this script is that it holds none.
    token_path=$(cd "$(dirname "${POSTMARK_TOKEN_FILE}")" && pwd)
    case "${token_path}" in
        "$(pwd)"|"$(pwd)"/*)
            echo "refusing: ${POSTMARK_TOKEN_FILE} is inside the repository." >&2
            echo "Keep it somewhere else, e.g. ~/.config/sg101/." >&2
            exit 2
            ;;
    esac
    # Read, not sourced -- sourcing a file to get one value out of it runs
    # everything else in there as shell. Same reasoning as pg_snapshot.sh.
    POSTMARK_TOKEN=$(tr -d '[:space:]' < "${POSTMARK_TOKEN_FILE}")
else
    echo "no token: set POSTMARK_TOKEN or POSTMARK_TOKEN_FILE." >&2
    echo >&2
    usage >&2
    exit 2
fi

if [ -z "${POSTMARK_TOKEN}" ]; then
    echo "the token is empty" >&2
    exit 2
fi

# If .env already carries mail settings, this script is not what is protecting
# you: every container built from that file can send. Worth saying out loud.
if grep -qE '^EMAIL_BACKEND=' .env 2>/dev/null; then
    echo "NOTE: .env sets EMAIL_BACKEND, so the dev stack itself can send mail" >&2
    echo "      to real addresses in the snapshot. Comment it out unless you" >&2
    echo "      mean it; this script does not need it." >&2
    echo >&2
fi

export EMAIL_HOST_USER="${POSTMARK_TOKEN}"
export EMAIL_HOST_PASSWORD="${POSTMARK_TOKEN}"

set -- docker compose run --rm \
    -e EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
    -e EMAIL_HOST=smtp.postmarkapp.com \
    -e EMAIL_PORT=587 \
    -e EMAIL_USE_TLS=True \
    -e EMAIL_HOST_USER \
    -e EMAIL_HOST_PASSWORD \
    web python /app/tools/email_smoke.py --live "$@"

if [ -n "${DRY_RUN}" ]; then
    printf '%q ' "$@"
    printf '\n(dry run -- nothing sent; the token is passed by name, not value)\n'
    exit 0
fi

exec "$@"
