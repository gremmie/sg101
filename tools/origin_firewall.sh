#!/usr/bin/env bash
#
# The origin firewall: the web ports admit only Cloudflare, and SSH stays
# reachable. Enforced by the hosting provider's firewall, outside the VM, so how
# Docker routes a published port never matters -- rules on the VM's own INPUT
# chain would not see traffic Docker forwards to a container at all.
#
# The ranges come from apache/cloudflare-ranges.txt, the file Apache also reads
# to decide whose CF-Connecting-IP to believe. One list, so the two cannot drift.
#
# Run this from your own machine, never from the VM. The provider token it will
# need can rewrite the VM's firewall; on the VM, whoever compromised the VM could
# use it to open the firewall.
#
# Usage:
#   tools/origin_firewall.sh ranges-check   compare the file with Cloudflare's lists
#   tools/origin_firewall.sh plan           print the rules the file implies
#   tools/origin_firewall.sh apply          push the rules to the provider
#   tools/origin_firewall.sh check          compare the live rules with the plan
#
# Settings, from the environment:
#   FIREWALL_SSH_FROM   where SSH is allowed from: "anywhere", or CIDRs
#                       separated by spaces
#   FIREWALL_HTTP       port 80: "allow" (from Cloudflare only) or "drop"
#   FIREWALL_PROVIDER   whose API to call; apply and check need it
#
# None of these is decided until the host is chosen, and apply refuses to run
# while any is unset: a plan with no SSH rule is one that locks you out.

# pipefail, because ranges() is read through pipes and dies on a bad line --
# without it the pipe reports the last command's success, and a check that has
# already printed every good range goes on to report a match.
set -u -o pipefail

RANGES=apache/cloudflare-ranges.txt
CF_IPV4=https://www.cloudflare.com/ips-v4
CF_IPV6=https://www.cloudflare.com/ips-v6

cd "$(dirname "$0")/.." || exit 2

die() { printf '%s\n' "$*" >&2; exit 2; }

# Every range in the file, one per line. A line that is neither a range, a
# comment nor blank is an error rather than something to skip: skipping a
# mistyped range would quietly drop it from the firewall and from Apache.
ranges() {
    local line
    [ -r "$RANGES" ] || die "cannot read $RANGES"
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|'#'*) ;;
            *) printf '%s\n' "$line" | grep -Eq '^[0-9a-fA-F:.]+/[0-9]+$' \
                   || die "$RANGES: not a range: $line"
               printf '%s\n' "$line" ;;
        esac
    done < "$RANGES"
}

ipv4() { ranges | grep -v ':'; }
ipv6() { ranges | grep ':'; }

# fetch URL -> the published ranges, one per line. The lists are served without
# a trailing newline, and the loop in ranges() is not reading these.
fetch() {
    curl -fsS --max-time 15 "$1" || die "could not fetch $1"
    echo
}

ranges_check() {
    local file published diff
    file=$(ranges | sort) || exit 2
    published=$( { fetch "$CF_IPV4"; fetch "$CF_IPV6"; } | grep -v '^$' | sort) \
        || exit 2
    diff=$(diff <(printf '%s\n' "$file") <(printf '%s\n' "$published"))
    if [ -z "$diff" ]; then
        printf 'OK  %s matches Cloudflare: %d IPv4 and %d IPv6 ranges\n' \
            "$RANGES" "$(ipv4 | wc -l)" "$(ipv6 | wc -l)"
        return 0
    fi
    printf 'DIFFERS  %s against %s and %s\n' "$RANGES" "$CF_IPV4" "$CF_IPV6"
    printf '%s\n' "$diff" | sed -n 's/^< /  only in the file:      /p; s/^> /  only at Cloudflare:    /p'
    printf 'Update the file and its "Last verified" line, then reload Apache\n'
    printf 'and re-apply the firewall: both read it.\n'
    return 1
}

plan() {
    local http=${FIREWALL_HTTP:-} ssh=${FIREWALL_SSH_FROM:-} family range
    ranges > /dev/null || exit 2

    echo "Inbound, from $RANGES:"
    for family in ipv4 ipv6; do
        printf '  tcp 443 from %d %s ranges\n' "$($family | wc -l)" "$family"
        $family | while read -r range; do printf '    %s\n' "$range"; done
    done

    case "$http" in
        allow) echo "  tcp 80  from the same ranges, both families" ;;
        drop)  echo "  tcp 80  refused" ;;
        '')    echo "  tcp 80  UNDECIDED -- set FIREWALL_HTTP to allow or drop" ;;
        *)     die "FIREWALL_HTTP must be allow or drop, not: $http" ;;
    esac

    case "$ssh" in
        '')       echo "  tcp 22  UNDECIDED -- set FIREWALL_SSH_FROM" ;;
        anywhere) echo "  tcp 22  from anywhere, both families" ;;
        *)        echo "  tcp 22  from $ssh" ;;
    esac

    echo "Everything else inbound is refused. Outbound is not restricted."
}

# The part that differs per provider. Written once the host is chosen; until
# then it says so rather than guessing at an API.
provider() {
    local action=$1
    case "${FIREWALL_PROVIDER:-}" in
        '') die "no provider configured: set FIREWALL_PROVIDER once the host is chosen" ;;
        *)  die "no $action support for provider: $FIREWALL_PROVIDER" ;;
    esac
}

case "${1:-}" in
    ranges-check) ranges_check ;;
    plan) plan ;;
    apply)
        [ -n "${FIREWALL_SSH_FROM:-}" ] || die "refusing to apply: FIREWALL_SSH_FROM is unset, and a firewall with no SSH rule locks you out"
        [ -n "${FIREWALL_HTTP:-}" ] || die "refusing to apply: FIREWALL_HTTP is unset"
        plan > /dev/null || exit 2
        provider apply ;;
    check) provider check ;;
    *) die "usage: $0 ranges-check | plan | apply | check" ;;
esac
