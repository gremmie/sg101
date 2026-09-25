#!/usr/bin/env python3
"""The origin firewall: the web ports admit only Cloudflare, and SSH stays
reachable.

Enforced by the hosting provider's firewall, outside the VM, so how Docker
routes a published port never matters -- rules on the VM's own INPUT chain would
not see traffic Docker forwards to a container at all.

The ranges come from apache/cloudflare-ranges.txt, the file Apache also reads
to decide whose CF-Connecting-IP to believe. One list, so the two cannot drift.

Run this from your own machine, never from the VM. The provider token it needs
can rewrite the VM's firewall; on the VM, whoever compromised the VM could use
it to open the firewall. Standard library only, so any python3 runs it.

    tools/origin_firewall.py ranges-check   compare the file with Cloudflare's lists
    tools/origin_firewall.py plan           print the rules the file implies
    tools/origin_firewall.py apply          replace the provider's rules with the plan
    tools/origin_firewall.py check          compare the live rules with the plan

Settings, from the environment:

    FIREWALL_SSH_FROM   where SSH is allowed from: "anywhere", or CIDR ranges
                        separated by spaces
    FIREWALL_HTTP       port 80: "allow" (from Cloudflare only) or "drop"
    FIREWALL_PROVIDER   whose API to call: "linode"

apply and check refuse to run while any of these is unset: a plan with no SSH
rule is one that locks you out.

For FIREWALL_PROVIDER=linode (Linode Cloud Firewall):

    FIREWALL_LINODE_ID  the firewall's numeric ID, from its dashboard URL
    LINODE_TOKEN        a personal access token with Firewalls read/write and
                        nothing else; it is never printed
    LINODE_API_URL      optional; defaults to https://api.linode.com/v4

Exit status: 0 OK, 1 a difference found, 2 an error or a refusal.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANGES = 'apache/cloudflare-ranges.txt'
CF_IPV4 = 'https://www.cloudflare.com/ips-v4'
CF_IPV6 = 'https://www.cloudflare.com/ips-v6'
LINODE_API_URL = 'https://api.linode.com/v4'
ANYWHERE = ['0.0.0.0/0', '::/0']
# Cloudflare answers urllib's default User-Agent with 403.
USER_AGENT = 'sg101-origin-firewall'


class Refused(Exception):
    """Stop with exit status 2, printing the message to stderr."""


def setting(name: str) -> str:
    """An environment setting, where empty counts as unset."""
    return os.environ.get(name, '')


def is_range(text: str) -> bool:
    """A network in CIDR form. A bare address is refused rather than read as a
    /32: the mask should be a decision, not a default."""
    if '/' not in text:
        return False
    try:
        ipaddress.ip_network(text)
    except ValueError:
        return False
    return True


def is_ipv6(text: str) -> bool:
    return ':' in text


def ranges() -> list[str]:
    """Every range in the file. A line that is neither a range, a comment nor
    blank is an error rather than something to skip: skipping a mistyped range
    would quietly drop it from the firewall and from Apache."""
    try:
        lines = (ROOT / RANGES).read_text().splitlines()
    except OSError:
        raise Refused(f'cannot read {RANGES}')
    found = []
    for line in lines:
        if not line or line.startswith('#'):
            continue
        if not is_range(line):
            raise Refused(f'{RANGES}: not a range: {line}')
        found.append(line)
    return found


def ssh_ranges() -> list[str]:
    """Where SSH is allowed from."""
    ssh_from = setting('FIREWALL_SSH_FROM')
    if ssh_from == 'anywhere':
        return ANYWHERE
    for entry in ssh_from.split():
        if not is_range(entry):
            raise Refused(f'FIREWALL_SSH_FROM: not a CIDR range: {entry}')
    return ssh_from.split()


def fetch(url: str) -> list[str]:
    """The ranges Cloudflare publishes at url."""
    try:
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read().decode()
    except (urllib.error.URLError, TimeoutError) as e:
        raise Refused(f'could not fetch {url}: {e}')
    return [line for line in text.splitlines() if line]


def ranges_check() -> int:
    in_file = set(ranges())
    published = set(fetch(CF_IPV4) + fetch(CF_IPV6))
    if in_file == published:
        ipv6 = [r for r in in_file if is_ipv6(r)]
        print(f'OK  {RANGES} matches Cloudflare: '
              f'{len(in_file) - len(ipv6)} IPv4 and {len(ipv6)} IPv6 ranges')
        return 0
    print(f'DIFFERS  {RANGES} against {CF_IPV4} and {CF_IPV6}')
    for r in sorted(in_file - published):
        print(f'  only in the file:      {r}')
    for r in sorted(published - in_file):
        print(f'  only at Cloudflare:    {r}')
    print('Update the file and its "Last verified" line, then reload Apache')
    print('and re-apply the firewall: both read it.')
    return 1


def validate() -> list[str]:
    """The Cloudflare ranges, once the file and every setting given are valid.
    Settings not given yet are left for the caller: plan reports them as
    undecided, apply and check refuse."""
    http = setting('FIREWALL_HTTP')
    if http not in ('', 'allow', 'drop'):
        raise Refused(f'FIREWALL_HTTP must be allow or drop, not: {http}')
    if setting('FIREWALL_SSH_FROM'):
        ssh_ranges()
    return ranges()


def plan() -> int:
    http, ssh = setting('FIREWALL_HTTP'), setting('FIREWALL_SSH_FROM')
    cloudflare = validate()

    print(f'Inbound, from {RANGES}:')
    for family, members in (('ipv4', [r for r in cloudflare if not is_ipv6(r)]),
                            ('ipv6', [r for r in cloudflare if is_ipv6(r)])):
        print(f'  tcp 443 from {len(members)} {family} ranges')
        for r in members:
            print(f'    {r}')

    print({
        'allow': '  tcp 80  from the same ranges, both families',
        'drop': '  tcp 80  refused',
        '': '  tcp 80  UNDECIDED -- set FIREWALL_HTTP to allow or drop',
    }[http])

    if not ssh:
        print('  tcp 22  UNDECIDED -- set FIREWALL_SSH_FROM')
    elif ssh == 'anywhere':
        print('  tcp 22  from anywhere, both families')
    else:
        print(f'  tcp 22  from {ssh}')

    print('Everything else inbound is refused. Outbound is not restricted.')
    return 0


def require_plan(action: str) -> None:
    """apply and check both compare against the plan, so neither runs without
    one."""
    if not setting('FIREWALL_SSH_FROM'):
        raise Refused(f'refusing to {action}: FIREWALL_SSH_FROM is unset, '
                      'and a firewall with no SSH rule locks you out')
    if not setting('FIREWALL_HTTP'):
        raise Refused(f'refusing to {action}: FIREWALL_HTTP is unset')
    validate()


# --- Linode Cloud Firewall ---------------------------------------------------


class Linode:
    def __init__(self) -> None:
        self.firewall_id = setting('FIREWALL_LINODE_ID')
        self.token = setting('LINODE_TOKEN')
        if not self.firewall_id:
            raise Refused('FIREWALL_LINODE_ID is unset: '
                          'the ID of the Linode Cloud Firewall to manage')
        if not self.firewall_id.isdigit():
            raise Refused(f'FIREWALL_LINODE_ID must be a number, not: {self.firewall_id}')
        if not self.token:
            raise Refused('LINODE_TOKEN is unset: a Linode token with Firewalls read/write')
        base = setting('LINODE_API_URL') or LINODE_API_URL
        self.url = f'{base}/networking/firewalls/{self.firewall_id}/rules'

    def body(self) -> dict:
        """The whole rule set plan describes, as the body of Linode's PUT: one
        rule per port, so the dashboard reads like the plan."""
        cloudflare = addresses(ranges())
        inbound = [accept('cloudflare-https', '443', cloudflare)]
        if setting('FIREWALL_HTTP') == 'allow':
            inbound.append(accept('cloudflare-http', '80', cloudflare))
        inbound.append(accept('ssh', '22', addresses(ssh_ranges())))
        return {'inbound_policy': 'DROP', 'inbound': inbound,
                'outbound_policy': 'ACCEPT', 'outbound': []}

    def call(self, method: str, body: dict | None = None) -> dict:
        """A status other than 2xx is a failure showing Linode's own reasons: a
        refused call never looks like success."""
        request = urllib.request.Request(
            self.url, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Authorization': f'Bearer {self.token}',
                     'Content-Type': 'application/json', 'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            raise Refused(f'Linode refused {method} {self.url}: HTTP {e.code}\n'
                          + linode_errors(e.read()))
        except (urllib.error.URLError, TimeoutError) as e:
            raise Refused(f'could not reach {self.url}: {getattr(e, "reason", e)}')

    def apply(self) -> int:
        self.call('PUT', self.body())
        print(f'Applied to Linode firewall {self.firewall_id}, replacing its rules. '
              'Now run firewall-check.')
        return 0

    def check(self) -> int:
        live = flatten(self.call('GET'))
        planned = flatten(self.body())
        if live == planned:
            print(f'OK  Linode firewall {self.firewall_id} matches the plan')
            return 0
        print(f'DIFFERS  Linode firewall {self.firewall_id} against the plan')
        for line in sorted(live - planned):
            print(f'  only live:     {line}')
        for line in sorted(planned - live):
            print(f'  only planned:  {line}')
        print('firewall-apply replaces the live rules with the plan.')
        return 1


def addresses(networks: list[str]) -> dict:
    """Linode's {"ipv4": [...], "ipv6": [...]}, leaving out a family with none."""
    by_family = {'ipv4': [n for n in networks if not is_ipv6(n)],
                 'ipv6': [n for n in networks if is_ipv6(n)]}
    return {family: members for family, members in by_family.items() if members}


def accept(label: str, port: str, addresses: dict) -> dict:
    return {'label': label, 'action': 'ACCEPT', 'protocol': 'TCP', 'ports': port,
            'addresses': addresses}


def canonical(network: str) -> str:
    """The network as ipaddress writes it, so a provider's respelling of an
    address (case, zero compression) is not reported as a difference."""
    try:
        return str(ipaddress.ip_network(network, strict=False))
    except ValueError:
        return network


def flatten(rules: dict) -> set[str]:
    """A rule set as one line per thing it allows, plus the two policies, so
    that two rule sets compare whatever order the rules and addresses come in."""
    lines = {f'inbound_policy {rules.get("inbound_policy")}',
             f'outbound_policy {rules.get("outbound_policy")}'}
    for direction in ('inbound', 'outbound'):
        for rule in rules.get(direction) or []:
            found = rule.get('addresses') or {}
            for network in (found.get('ipv4') or []) + (found.get('ipv6') or []):
                lines.add(f'{direction} {rule.get("action")} {rule.get("protocol")} '
                          f'{rule.get("ports") or "all"} {canonical(network)}')
    return lines


def linode_errors(raw: bytes) -> str:
    """Linode's {"errors": [{"field", "reason"}]} as indented lines, or the raw
    body if it is not that shape."""
    try:
        errors = json.loads(raw)['errors']
        return '\n'.join(
            '  ' + (f'{e["field"]}: ' if e.get('field') else '') + e['reason']
            for e in errors)
    except (ValueError, KeyError, TypeError):
        return '  ' + raw.decode(errors='replace').strip()


PROVIDERS = {'linode': Linode}


def provider():
    name = setting('FIREWALL_PROVIDER')
    if not name:
        raise Refused('no provider configured: set FIREWALL_PROVIDER')
    if name not in PROVIDERS:
        raise Refused(f'no support for provider: {name}')
    return PROVIDERS[name]()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['ranges-check', 'plan', 'apply', 'check'])
    action = parser.parse_args().action
    try:
        if action == 'ranges-check':
            return ranges_check()
        if action == 'plan':
            return plan()
        require_plan(action)
        firewall = provider()
        return firewall.apply() if action == 'apply' else firewall.check()
    except Refused as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
