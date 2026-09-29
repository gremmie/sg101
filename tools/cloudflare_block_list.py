#!/usr/bin/env python3
"""Cloudflare's block list: the IP list a WAF rule drops at the edge, which
fail2ban bans into.

fail2ban's action runs ban and unban; the Makefile's blocklist-* targets run
the rest. One script, so the code that clears blocks by hand is the code
fail2ban runs. Standard library only.

    tools/cloudflare_block_list.py ban IP      add IP, commented "fail2ban"
    tools/cloudflare_block_list.py unban IP    delete IP
    tools/cloudflare_block_list.py show        print every item: address, date added, comment
    tools/cloudflare_block_list.py add IP      add IP, commented "manual"
    tools/cloudflare_block_list.py remove IP   delete IP, the same way as unban
    tools/cloudflare_block_list.py clear [--all] [--older-than DAYS]
        delete the items commented "fail2ban"; with --all, every item, "manual"
        ones included; with --older-than, only items added more than DAYS ago

An address added by hand never expires: fail2ban does not know it is there. For
a block that expires, use `fail2ban-client set sg101-auth banip IP`.

IP is one IPv4 or IPv6 address; a range is refused. The list is looked up with
Cloudflare's search, which matches by prefix, and every page of results is read,
so an address is found wherever it is on the list. Adding and deleting are
asynchronous at Cloudflare; each command waits for its operation to finish, so
the exit status is the outcome, not whether the request was accepted.

Settings, from the environment, else from secrets/cloudflare.env in the
repository (KEY=value lines; fail2ban/cloudflare.env.example lists them):

    CLOUDFLARE_API_TOKEN   an API token with Account Rule Lists edit and
                           nothing else; it is never printed
    CLOUDFLARE_ACCOUNT_ID  the account that owns the list
    CLOUDFLARE_LIST_NAME   the list's name
    CLOUDFLARE_API_URL     optional; defaults to https://api.cloudflare.com/client/v4

Exit status: 0 OK, 1 the address is not on the list (unban, remove), 2 an
error or a refusal.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
SECRETS = 'secrets/cloudflare.env'
CLOUDFLARE_API_URL = 'https://api.cloudflare.com/client/v4'
# Cloudflare answers urllib's default User-Agent with 403.
USER_AGENT = 'sg101-cloudflare-block-list'
# The most items Cloudflare returns in one page.
PER_PAGE = 500
OPERATION_TIMEOUT = 60


class Refused(Exception):
    """Stop with exit status 2, printing the message to stderr."""


def address(text: str) -> str:
    """One address, spelled the way ipaddress writes it. Cloudflare's search is a
    string prefix, so ban and unban must agree on a spelling."""
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        raise Refused(f'not a single IPv4 or IPv6 address: {text!r}')


def secrets_file() -> dict[str, str]:
    """The settings in secrets/cloudflare.env, or none if there is no file. A
    malformed line is named by number only: it may be a bare token."""
    try:
        lines = (ROOT / SECRETS).read_text().splitlines()
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise Refused(f'cannot read {SECRETS}: {e.strerror}')
    values = {}
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, equals, value = line.partition('=')
        if not equals:
            raise Refused(f'{SECRETS}, line {number}: not KEY=value')
        values[key.strip()] = value.strip()
    return values


def added(item: dict) -> datetime:
    """When an item was added. Cloudflare writes created_on with a Z, with or
    without fractional seconds; Python 3.9's fromisoformat takes neither."""
    stamp = re.sub(r'\.\d+', '', item['created_on']).replace('Z', '+00:00')
    return datetime.fromisoformat(stamp)


class BlockList:
    def __init__(self) -> None:
        from_file = secrets_file()

        def setting(name: str) -> str:
            return os.environ.get(name) or from_file.get(name, '')

        self.token = setting('CLOUDFLARE_API_TOKEN')
        account = setting('CLOUDFLARE_ACCOUNT_ID')
        self.name = setting('CLOUDFLARE_LIST_NAME')
        for name, value, what in (
                ('CLOUDFLARE_API_TOKEN', self.token, 'a token with Account Rule Lists edit'),
                ('CLOUDFLARE_ACCOUNT_ID', account, 'the account that owns the list'),
                ('CLOUDFLARE_LIST_NAME', self.name, "the list's name")):
            if not value:
                raise Refused(f'{name} is unset: {what}')
        base = setting('CLOUDFLARE_API_URL') or CLOUDFLARE_API_URL
        self.lists_url = f'{base}/accounts/{account}/rules/lists'
        self.items_url = f'{self.lists_url}/{self.list_id()}/items'

    def call(self, method: str, url: str, body: dict | list | None = None) -> dict:
        """A status other than 2xx, or success false, is a failure showing
        Cloudflare's own reasons: a refused call never looks like success."""
        request = urllib.request.Request(
            url, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Authorization': f'Bearer {self.token}',
                     'Content-Type': 'application/json', 'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                reply = json.load(response)
        except urllib.error.HTTPError as e:
            raise Refused(f'Cloudflare refused {method} {url}: HTTP {e.code}\n'
                          + cloudflare_errors(e.read()))
        except (urllib.error.URLError, TimeoutError) as e:
            raise Refused(f'could not reach {url}: {getattr(e, "reason", e)}')
        except ValueError:
            raise Refused(f'Cloudflare answered {method} {url} with something not JSON')
        if not reply.get('success'):
            raise Refused(f'Cloudflare refused {method} {url}\n'
                          + cloudflare_errors(json.dumps(reply).encode()))
        return reply

    def list_id(self) -> str:
        for found in self.call('GET', self.lists_url)['result']:
            if found.get('name') == self.name:
                return found['id']
        raise Refused(f'no list named {self.name} in this account')

    def items(self, search: str = '') -> list[dict]:
        """Every item, or every item whose address starts with search, reading
        page after page until Cloudflare gives no cursor to continue from."""
        query = {'per_page': PER_PAGE, **({'search': search} if search else {})}
        found = []
        while True:
            reply = self.call('GET', f'{self.items_url}?{urlencode(query)}')
            found += reply['result']
            after = ((reply.get('result_info') or {}).get('cursors') or {}).get('after')
            if not after:
                return found
            query['cursor'] = after

    def find(self, ip: str) -> list[dict]:
        """The items holding exactly this address. The search also returns every
        address it is a prefix of: 192.0.2.1 finds 192.0.2.10 as well."""
        wanted = ipaddress.ip_network(ip)
        return [item for item in self.items(search=ip) if same(item['ip'], wanted)]

    def add(self, ip: str, comment: str) -> None:
        reply = self.call('POST', self.items_url, [{'ip': ip, 'comment': comment}])
        self.wait(reply['result']['operation_id'], f'add {ip}')

    def delete(self, items: list[dict], what: str) -> None:
        reply = self.call('DELETE', self.items_url,
                          {'items': [{'id': item['id']} for item in items]})
        self.wait(reply['result']['operation_id'], what)

    def wait(self, operation_id: str, what: str) -> None:
        """Poll a bulk operation until Cloudflare says it completed or failed."""
        url = f'{self.lists_url}/bulk_operations/{operation_id}'
        deadline = time.monotonic() + OPERATION_TIMEOUT
        delay = 0.1
        while True:
            result = self.call('GET', url)['result']
            status = result.get('status')
            if status == 'completed':
                return
            if status == 'failed':
                raise Refused(f'Cloudflare could not {what}: {result.get("error")}')
            if time.monotonic() > deadline:
                raise Refused(f'Cloudflare had not finished trying to {what} after '
                              f'{OPERATION_TIMEOUT} s: operation {operation_id} is {status}')
            time.sleep(delay)
            delay = min(delay * 2, 2)


def same(listed: str, wanted: ipaddress.IPv4Network | ipaddress.IPv6Network) -> bool:
    try:
        return ipaddress.ip_network(listed, strict=False) == wanted
    except ValueError:
        return False


def cloudflare_errors(raw: bytes) -> str:
    """Cloudflare's {"errors": [{"code", "message"}]} as indented lines, or the
    raw body if it is not that shape."""
    try:
        errors = json.loads(raw)['errors']
        return '\n'.join(f'  {e["code"]}: {e["message"]}' for e in errors)
    except (ValueError, KeyError, TypeError):
        return '  ' + raw.decode(errors='replace').strip()


def block(ip: str, comment: str) -> int:
    blocklist = BlockList()
    blocklist.add(ip, comment)
    print(f'added {ip} to {blocklist.name}, commented "{comment}"')
    return 0


def unblock(ip: str) -> int:
    blocklist = BlockList()
    found = blocklist.find(ip)
    if not found:
        print(f'{ip} is not on {blocklist.name}: nothing removed', file=sys.stderr)
        return 1
    blocklist.delete(found, f'remove {ip}')
    print(f'removed {ip} from {blocklist.name}')
    return 0


def show() -> int:
    blocklist = BlockList()
    items = blocklist.items()
    for item in items:
        stamp = item['created_on'][:16].replace('T', ' ')
        print(f'{item["ip"]:<39}  {stamp}  {item.get("comment") or ""}')
    print(f'{len(items)} items on {blocklist.name}')
    return 0


def clear(everything: bool, older_than: int | None) -> int:
    blocklist = BlockList()
    items = blocklist.items()
    cutoff = None
    if older_than is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than)
    doomed = [item for item in items
              if (everything or item.get('comment') == 'fail2ban')
              and (cutoff is None or added(item) < cutoff)]
    if not doomed:
        print(f'nothing to remove: {len(items)} items on {blocklist.name}, none matching')
        return 0
    blocklist.delete(doomed, f'remove {len(doomed)} items')
    print(f'removed {len(doomed)} of {len(items)} items from {blocklist.name}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('ban', 'unban', 'add', 'remove'):
        commands.add_parser(name).add_argument('ip')
    commands.add_parser('show')
    clear_parser = commands.add_parser('clear')
    clear_parser.add_argument('--all', action='store_true')
    clear_parser.add_argument('--older-than', type=int, metavar='DAYS')
    args = parser.parse_args()
    try:
        if args.command in ('ban', 'add'):
            return block(address(args.ip), 'fail2ban' if args.command == 'ban' else 'manual')
        if args.command in ('unban', 'remove'):
            return unblock(address(args.ip))
        if args.command == 'show':
            return show()
        return clear(args.all, args.older_than)
    except Refused as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
