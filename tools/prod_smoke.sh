#!/usr/bin/env bash
#
# Smoke-test the production stack from outside it, over the network.
#
# Every request is made to an origin address with the site's own name, so the
# same checks run against the stack on this machine and against a new host
# before DNS points at it. The certificate is not verified: locally it is
# self-signed, and at an origin it is Cloudflare's, which only Cloudflare trusts.
#
# Usage:
#   tools/prod_smoke.sh               the stack on this machine
#   tools/prod_smoke.sh 203.0.113.7   a host, by address
#
# Run from the checkout: robots.txt is compared against the committed copy.
# Exits non-zero if any check fails, after running them all.

set -u

ORIGIN=${1:-127.0.0.1}
HOST=surfguitar101.com
cd "$(dirname "$0")/.." || exit 2

failures=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n      %s\n' "$1" "$2"; failures=$((failures + 1)); }

# -k: see above. --max-time so a dead origin fails a check rather than hangs.
req() {
    curl -sk --max-time 15 \
        --resolve "$HOST:443:$ORIGIN" --resolve "$HOST:80:$ORIGIN" "$@"
}

# status URL -> the HTTP status code
status() { req -o /dev/null -w '%{http_code}' "$1"; }

# expect_redirect NAME URL LOCATION
expect_redirect() {
    local got
    got=$(req -o /dev/null -w '%{http_code} %{redirect_url}' "$2")
    if [ "$got" = "301 $3" ]; then pass "$1"; else fail "$1" "wanted 301 $3, got $got"; fi
}

# expect_status NAME URL CODE
expect_status() {
    local got
    got=$(status "$2")
    if [ "$got" = "$3" ]; then pass "$1"; else fail "$1" "wanted $3, got $got"; fi
}

# --- The site, through the proxy ----------------------------------------------

# 200 and not a redirect: a 301 to itself here means the proxy stopped setting
# X-Forwarded-Proto and Django thinks every request is plain HTTP.
expect_status "home page serves over HTTPS" "https://$HOST/" 200

# The proxy must replace a client's X-Forwarded-Proto, not keep it: Django
# decides from that header whether a request was secure.
got=$(req -o /dev/null -w '%{http_code}' -H 'X-Forwarded-Proto: http' "https://$HOST/")
if [ "$got" = 200 ]; then
    pass "a client's X-Forwarded-Proto is overwritten"
else
    fail "a client's X-Forwarded-Proto is overwritten" "sent 'http', got $got"
fi

headers=$(req -D - -o /dev/null "https://$HOST/")
hsts=$(printf '%s' "$headers" | grep -ci '^strict-transport-security:')
if [ "$hsts" = 1 ] && printf '%s' "$headers" | grep -qi '^strict-transport-security: max-age=604800'; then
    pass "one HSTS header, one week"
else
    fail "one HSTS header, one week" "$(printf '%s' "$headers" | grep -i '^strict-transport-security:' | tr -d '\r' | tr '\n' '|')"
fi

server=$(printf '%s' "$headers" | grep -i '^server:' | tr -d '\r')
case "$server" in
    *[0-9]*) fail "Server header names no version" "$server" ;;
    *) pass "Server header names no version" ;;
esac

# DEBUG off: the debug 404 page lists the URL patterns it tried.
body=$(req "https://$HOST/smoke-test-no-such-page/")
if printf '%s' "$body" | grep -q 'Using the URLconf'; then
    fail "DEBUG is off" "the 404 page is Django's debug page"
else
    pass "DEBUG is off"
fi

expect_redirect "port 80 redirects to HTTPS" "http://$HOST/forums/" "https://$HOST/forums/"

# --- Files served by Apache ---------------------------------------------------

if [ "$(req "https://$HOST/robots.txt")" = "$(cat static/robots.txt)" ]; then
    pass "robots.txt is the committed one"
else
    fail "robots.txt is the committed one" "differs from static/robots.txt"
fi
expect_status "favicon.ico" "https://$HOST/favicon.ico" 200
expect_status "Google verification file" "https://$HOST/google1974c4ddc5b1ff40.html" 200
expect_status "media: a committed badge" "https://$HOST/media/badges/award_star_gold_3.png" 200

# Static files come from WhiteNoise under hashed names, marked immutable.
css=$(req "https://$HOST/" | grep -o '/static/css/[^"]*\.min\.[0-9a-f]\{12\}\.css' | head -1)
if [ -z "$css" ]; then
    fail "static: hashed stylesheet, immutable" "no hashed stylesheet on the home page"
elif req -D - -o /dev/null "https://$HOST$css" | grep -qi '^cache-control:.*immutable'; then
    pass "static: hashed stylesheet, immutable"
else
    fail "static: hashed stylesheet, immutable" "$css served without immutable"
fi

# --- Old URLs -----------------------------------------------------------------

expect_redirect "SG101 1.0 forum topic" \
    "https://$HOST/modules.php?name=Forums&file=viewtopic&t=123" "https://$HOST/forums/topic/123/"
expect_redirect "SG101 1.0 forum post" \
    "https://$HOST/modules.php?name=Forums&file=viewtopic&p=456" "https://$HOST/forums/post/456/"
expect_redirect "SG101 1.0 news story" \
    "https://$HOST/modules.php?name=News&file=article&sid=789" "https://$HOST/news/story/789/"
expect_redirect "old podcast feed" \
    "https://$HOST/modules/Podcast/feeds/feed.xml" "https://$HOST/podcast/feed.xml/"
expect_redirect "convention" \
    "https://$HOST/convention" "https://www.facebook.com/SG101Convention"

# --- Only the proxy is reachable ----------------------------------------------

# Locally these fail while the development stack is up, since it publishes all
# three; stop it first (`docker compose stop`).
# Refused (7) locally; a host firewall that drops rather than refuses times out
# (28). Anything else means something is listening.
for port in 8000 5432 6379; do
    curl -s --max-time 5 -o /dev/null "http://$ORIGIN:$port/" 2>/dev/null
    rc=$?
    case $rc in
        7|28) pass "port $port is closed" ;;
        *)    fail "port $port is closed" "curl exited $rc: something is listening" ;;
    esac
done

echo
if [ "$failures" -eq 0 ]; then
    echo "all checks passed"
else
    echo "$failures check(s) failed"
    exit 1
fi
