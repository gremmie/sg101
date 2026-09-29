#!/usr/bin/env python3
"""Tests for tools/cloudflare_block_list.py, against a local stand-in for
Cloudflare's Lists API. Nothing here reaches Cloudflare or needs a token.

The stand-in serves the list lookup, the list's items (paged, with the prefix
search Cloudflare does on IP lists), adding and deleting items, and the bulk
operations those two start. An operation answers "pending" the first time it
is polled and only then takes effect, so a script that did not wait for it would
find the list unchanged. Every request is recorded, so a refusal can be shown to
have sent nothing.

The tool runs as a separate process, as fail2ban and the Makefile run it,
from a copy in a scratch tree: it looks for secrets/cloudflare.env relative to
itself, so a test can write one there without touching the real one.

    python3 tools/cloudflare_block_list_test.py
    /usr/bin/python3 tools/cloudflare_block_list_test.py    # under that interpreter

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT = 'f00dfeedf00dfeedf00dfeedf00dfeed'
LIST_NAME = 'block_list'
LIST_ID = '2c0fc9fa937b11eaa1b71c4d701ab86e'
TOKEN = f'test-token-{os.getpid()}-do-not-print'
LISTS = f'/client/v4/accounts/{ACCOUNT}/rules/lists'
ITEMS = f'{LISTS}/{LIST_ID}/items'
OPERATION = re.compile(rf'^{LISTS}/bulk_operations/(\w+)$')


class StandIn:
    """Cloudflare's Lists API, as far as the tool uses it."""

    def __init__(self) -> None:
        self.reset()
        stand_in = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def handle_request(self) -> None:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else None
                stand_in.requests.append((self.command, self.path))
                status, reply = stand_in.respond(
                    self.command, self.path, self.headers.get('Authorization'), body)
                data = json.dumps(reply).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_DELETE = handle_request

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_port}/client/v4'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def reset(self) -> None:
        self.items: list[dict] = []
        self.requests: list[tuple[str, str]] = []
        self.operations: dict[str, dict] = {}
        self.completed = 0
        self.fail_next = False
        # method -> (HTTP status, message): the next such request is refused.
        self.refuse: dict[str, tuple[int, str]] = {}

    def seed(self, ip: str, comment: str = 'fail2ban', age_days: float = 0,
             fraction: bool = True) -> None:
        """An item as if added age_days ago. Cloudflare writes created_on both
        with and without fractional seconds."""
        when = datetime.now(timezone.utc) - timedelta(days=age_days)
        stamp = when.strftime('%Y-%m-%dT%H:%M:%S.%f' if fraction else '%Y-%m-%dT%H:%M:%S')
        self.items.append({'id': uuid.uuid4().hex, 'ip': ip, 'comment': comment,
                           'created_on': stamp + 'Z', 'modified_on': stamp + 'Z'})

    def ips(self) -> list[str]:
        return sorted(item['ip'] for item in self.items)

    def by_comment(self, comment: str) -> list[str]:
        return sorted(item['ip'] for item in self.items if item['comment'] == comment)

    def methods(self) -> list[str]:
        return [method for method, _ in self.requests]

    def respond(self, method: str, path: str, auth: str | None,
                body: bytes | None) -> tuple[int, dict]:
        if auth != f'Bearer {TOKEN}':
            return 401, failure(10000, 'Authentication error')
        if method in self.refuse:
            status, message = self.refuse.pop(method)
            return status, failure(10000, message)
        url = urlsplit(path)
        query = parse_qs(url.query)
        if url.path == LISTS and method == 'GET':
            return 200, success([
                {'id': 'a11a11a11a11a11a11a11a11a11a11a1', 'name': 'allow_list',
                 'kind': 'ip', 'num_items': 3},
                {'id': LIST_ID, 'name': LIST_NAME, 'kind': 'ip',
                 'num_items': len(self.items)},
            ])
        if url.path == ITEMS:
            if method == 'GET':
                return self.page(query)
            try:
                payload = json.loads(body or b'')
            except ValueError:
                return 400, failure(10026, 'filters.api.invalid_json')
            if method == 'POST':
                return self.add(payload)
            if method == 'DELETE':
                return self.delete(payload)
        match = OPERATION.match(url.path)
        if match and method == 'GET':
            return self.poll(match.group(1))
        return 404, failure(7003, 'Could not route to ' + url.path)

    def page(self, query: dict) -> tuple[int, dict]:
        """One page of items, prefix-matched on search. The cursor is opaque to
        the tool; it is only ever handed back."""
        per_page = int(query.get('per_page', ['25'])[0])
        if not 1 <= per_page <= 500:
            return 400, failure(10021, 'per_page must be between 1 and 500')
        search = query.get('search', [''])[0]
        matching = [item for item in self.items if item['ip'].startswith(search)]
        cursor = query.get('cursor', ['start-0'])[0]
        if not cursor.startswith('start-'):
            return 400, failure(10022, 'invalid cursor')
        start = int(cursor[len('start-'):])
        reply = success(matching[start:start + per_page])
        if start + per_page < len(matching):
            reply['result_info'] = {'cursors': {'after': f'start-{start + per_page}'}}
        elif start:
            reply['result_info'] = {'cursors': {'before': f'start-{start}'}}
        return 200, reply

    def add(self, payload) -> tuple[int, dict]:
        if not isinstance(payload, list) or not all('ip' in item for item in payload):
            return 400, failure(10026, 'filters.api.invalid_body')

        def apply() -> None:
            for item in payload:
                self.seed(item['ip'], item.get('comment', ''))
        return self.start(apply)

    def delete(self, payload) -> tuple[int, dict]:
        try:
            ids = {item['id'] for item in payload['items']}
        except (TypeError, KeyError):
            return 400, failure(10026, 'filters.api.invalid_body')

        def apply() -> None:
            self.items = [item for item in self.items if item['id'] not in ids]
        return self.start(apply)

    def start(self, apply) -> tuple[int, dict]:
        op_id = uuid.uuid4().hex
        self.operations[op_id] = {'apply': apply, 'polls': 0, 'fail': self.fail_next}
        self.fail_next = False
        return 200, success({'operation_id': op_id})

    def poll(self, op_id: str) -> tuple[int, dict]:
        operation = self.operations.get(op_id)
        if operation is None:
            return 404, failure(10030, 'operation not found')
        operation['polls'] += 1
        if operation['polls'] == 1:
            return 200, success({'id': op_id, 'status': 'pending'})
        if operation['fail']:
            return 200, success({'id': op_id, 'status': 'failed',
                                 'error': 'simulated operation failure'})
        if operation['apply']:
            operation['apply']()
            operation['apply'] = None
            self.completed += 1
        return 200, success({'id': op_id, 'status': 'completed',
                             'completed': '2026-09-29T00:00:00Z'})


def success(result) -> dict:
    return {'success': True, 'errors': [], 'messages': [], 'result': result}


def failure(code: int, message: str) -> dict:
    return {'success': False, 'errors': [{'code': code, 'message': message}],
            'messages': [], 'result': None}


class CloudflareBlockListTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stand_in = StandIn()
        cls.tree = Path(tempfile.mkdtemp())
        (cls.tree / 'tools').mkdir()
        shutil.copy(ROOT / 'tools/cloudflare_block_list.py', cls.tree / 'tools')
        cls.env_file = cls.tree / 'secrets/cloudflare.env'

    @classmethod
    def tearDownClass(cls) -> None:
        cls.stand_in.server.shutdown()
        shutil.rmtree(cls.tree)

    def setUp(self) -> None:
        self.stand_in.reset()
        shutil.rmtree(self.tree / 'secrets', ignore_errors=True)

    def bl(self, *args: str, **settings: str) -> tuple[int, str]:
        """Run the tool with complete settings, each overridable; an empty
        string is how a test leaves a setting unset. Returns the exit status and
        stdout and stderr together."""
        env = {
            'PATH': os.environ['PATH'], 'HOME': os.environ.get('HOME', ''),
            'CLOUDFLARE_API_TOKEN': TOKEN, 'CLOUDFLARE_ACCOUNT_ID': ACCOUNT,
            'CLOUDFLARE_LIST_NAME': LIST_NAME, 'CLOUDFLARE_API_URL': self.stand_in.url,
            **settings,
        }
        self.stand_in.requests.clear()
        result = subprocess.run(
            [sys.executable, str(self.tree / 'tools/cloudflare_block_list.py'), *args],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=60)
        return result.returncode, result.stdout

    def ok(self, *args: str, **settings: str) -> str:
        rc, out = self.bl(*args, **settings)
        self.assertEqual(rc, 0, out)
        return out

    def searches(self) -> list[str]:
        """The search parameter of every item lookup the last run made."""
        return [parse_qs(urlsplit(path).query).get('search', [''])[0]
                for method, path in self.stand_in.requests
                if method == 'GET' and urlsplit(path).path == ITEMS]

    # --- ban and add ----------------------------------------------------------

    def test_ban_adds_the_address_commented_fail2ban(self) -> None:
        self.ok('ban', '198.51.100.7')
        self.assertEqual(self.stand_in.items[0]['ip'], '198.51.100.7')
        self.assertEqual(self.stand_in.by_comment('fail2ban'), ['198.51.100.7'])

    def test_ban_waits_for_the_operation_to_complete(self) -> None:
        self.ok('ban', '198.51.100.7')
        self.assertEqual(self.stand_in.completed, 1)

    def test_ban_takes_ipv6(self) -> None:
        self.ok('ban', '2001:db8::7')
        self.assertEqual(self.stand_in.by_comment('fail2ban'), ['2001:db8::7'])

    def test_add_comments_manual(self) -> None:
        self.ok('add', '198.51.100.7')
        self.assertEqual(self.stand_in.by_comment('manual'), ['198.51.100.7'])

    def test_a_failed_operation_is_a_failure_with_cloudflares_error(self) -> None:
        self.stand_in.fail_next = True
        rc, out = self.bl('ban', '198.51.100.7')
        self.assertEqual(rc, 2, out)
        self.assertIn('simulated operation failure', out)
        self.assertEqual(self.stand_in.items, [])

    def test_anything_but_one_address_is_refused_before_any_request(self) -> None:
        for command in ('ban', 'unban', 'add', 'remove'):
            for bad in ('198.51.100.0/24', '2001:db8::/64', 'not-an-ip', ''):
                with self.subTest(command=command, address=bad):
                    rc, out = self.bl(command, bad)
                    self.assertEqual(rc, 2, out)
                    self.assertEqual(self.stand_in.requests, [], out)

    # --- unban and remove -----------------------------------------------------

    def test_unban_finds_an_address_past_the_first_page(self) -> None:
        # jaguar's action read one unparameterised page of 25 and missed this.
        for n in range(1, 31):
            self.stand_in.seed(f'203.0.113.{n}')
        self.ok('unban', '203.0.113.28')
        self.assertNotIn('203.0.113.28', self.stand_in.ips())
        self.assertEqual(len(self.stand_in.items), 29)

    def test_unban_follows_search_results_past_one_page(self) -> None:
        # A search is a prefix match: 2001:db8::1 also finds every 2001:db8::1:N.
        for n in range(1, 601):
            self.stand_in.seed(f'2001:db8::1:{n:x}')
        self.stand_in.seed('2001:db8::1')
        self.ok('unban', '2001:db8::1')
        self.assertNotIn('2001:db8::1', self.stand_in.ips())
        self.assertEqual(len(self.stand_in.items), 600)

    def test_unban_deletes_only_the_exact_address_not_its_prefix_neighbours(self) -> None:
        for ip in ('192.0.2.1', '192.0.2.10', '192.0.2.100', '192.0.2.19'):
            self.stand_in.seed(ip)
        self.ok('unban', '192.0.2.1')
        self.assertEqual(self.stand_in.ips(), ['192.0.2.10', '192.0.2.100', '192.0.2.19'])

    def test_unban_searches_for_the_address(self) -> None:
        self.stand_in.seed('198.51.100.7')
        self.ok('unban', '198.51.100.7')
        self.assertEqual(set(self.searches()), {'198.51.100.7'})

    # Both assume Cloudflare keeps an address as sent; requirement 5 measures it.
    # A search is a string prefix, so the two sides must agree on one spelling.

    def test_ban_sends_the_canonical_spelling(self) -> None:
        self.ok('ban', '2001:DB8:0:0::5')
        self.assertEqual(self.stand_in.ips(), ['2001:db8::5'])

    def test_unban_takes_any_spelling_of_the_address(self) -> None:
        self.stand_in.seed('2001:db8::5')
        self.ok('unban', '2001:DB8:0:0::5')
        self.assertEqual(self.stand_in.items, [])

    def test_unban_of_an_address_not_on_the_list_exits_1_and_deletes_nothing(self) -> None:
        self.stand_in.seed('198.51.100.8')
        rc, out = self.bl('unban', '198.51.100.7')
        self.assertEqual(rc, 1, out)
        self.assertIn('198.51.100.7', out)
        self.assertNotIn('DELETE', self.stand_in.methods())
        self.assertEqual(self.stand_in.ips(), ['198.51.100.8'])

    def test_remove_unblocks_a_manual_entry(self) -> None:
        self.stand_in.seed('198.51.100.7', comment='manual')
        self.ok('remove', '198.51.100.7')
        self.assertEqual(self.stand_in.items, [])

    # --- show -----------------------------------------------------------------

    def test_show_prints_every_item_across_pages_with_comment_and_date(self) -> None:
        for n in range(520):
            self.stand_in.seed(f'10.0.{n // 256}.{n % 256}',
                               comment='manual' if n == 519 else 'fail2ban')
        out = self.ok('show')
        for item in self.stand_in.items:
            self.assertIn(item['ip'], out)
        [last] = [line for line in out.splitlines() if '10.0.2.7' in line.split()]
        self.assertIn('manual', last)
        self.assertIn(self.stand_in.items[-1]['created_on'][:10], last)

    def test_show_of_an_empty_list_succeeds(self) -> None:
        self.ok('show')

    # --- clear ----------------------------------------------------------------

    def seed_mixed(self) -> None:
        self.stand_in.seed('198.51.100.1', 'fail2ban', age_days=30)
        self.stand_in.seed('198.51.100.2', 'fail2ban', age_days=30, fraction=False)
        self.stand_in.seed('198.51.100.3', 'fail2ban', age_days=1)
        self.stand_in.seed('198.51.100.4', 'manual', age_days=30)
        self.stand_in.seed('198.51.100.5', 'manual', age_days=1)
        self.stand_in.seed('198.51.100.6', 'something else', age_days=30)

    def test_clear_removes_only_fail2ban_items(self) -> None:
        self.seed_mixed()
        self.ok('clear')
        self.assertEqual(self.stand_in.ips(), ['198.51.100.4', '198.51.100.5', '198.51.100.6'])

    def test_clear_all_empties_the_list(self) -> None:
        self.seed_mixed()
        self.ok('clear', '--all')
        self.assertEqual(self.stand_in.items, [])

    def test_clear_older_than_removes_only_old_fail2ban_items(self) -> None:
        self.seed_mixed()
        self.ok('clear', '--older-than', '14')
        self.assertEqual(self.stand_in.ips(),
                         ['198.51.100.3', '198.51.100.4', '198.51.100.5', '198.51.100.6'])

    def test_clear_all_older_than_removes_every_old_item(self) -> None:
        self.seed_mixed()
        self.ok('clear', '--all', '--older-than', '14')
        self.assertEqual(self.stand_in.ips(), ['198.51.100.3', '198.51.100.5'])

    def test_clear_with_nothing_to_remove_sends_no_delete(self) -> None:
        self.stand_in.seed('198.51.100.4', 'manual')
        self.ok('clear')
        self.assertNotIn('DELETE', self.stand_in.methods())

    # --- errors are failures, with Cloudflare's reason and without the token --

    def test_a_bad_token_fails_with_cloudflares_reason_and_is_not_printed(self) -> None:
        self.stand_in.seed('198.51.100.7')
        bad = f'wrong-token-{os.getpid()}'
        for args in (('ban', '198.51.100.9'), ('unban', '198.51.100.7'), ('show',)):
            with self.subTest(args=args):
                rc, out = self.bl(*args, CLOUDFLARE_API_TOKEN=bad)
                self.assertEqual(rc, 2, out)
                self.assertIn('Authentication error', out)
                self.assertNotIn(bad, out)

    def test_a_list_name_that_does_not_exist_is_a_failure(self) -> None:
        rc, out = self.bl('ban', '198.51.100.7', CLOUDFLARE_LIST_NAME='no_such_list')
        self.assertEqual(rc, 2, out)
        self.assertIn('no_such_list', out)
        self.assertNotIn('POST', self.stand_in.methods())

    def test_a_refused_add_or_delete_is_a_failure(self) -> None:
        # A 200 carrying success false is a refusal too.
        for method, status, args in (('POST', 403, ('ban', '198.51.100.7')),
                                     ('DELETE', 403, ('unban', '198.51.100.7')),
                                     ('POST', 200, ('ban', '198.51.100.7'))):
            with self.subTest(method=method, status=status):
                self.stand_in.reset()
                self.stand_in.seed('198.51.100.7')
                self.stand_in.refuse[method] = (status, 'Permission denied')
                rc, out = self.bl(*args)
                self.assertEqual(rc, 2, out)
                self.assertIn('Permission denied', out)
                self.assertNotIn(TOKEN, out)

    def test_an_unreachable_api_fails(self) -> None:
        rc, out = self.bl('ban', '198.51.100.7',
                          CLOUDFLARE_API_URL='http://127.0.0.1:1/client/v4')
        self.assertEqual(rc, 2, out)
        self.assertNotIn(TOKEN, out)

    def test_a_missing_setting_is_named_as_unset_and_nothing_is_sent(self) -> None:
        for var in ('CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_LIST_NAME'):
            with self.subTest(var=var):
                rc, out = self.bl('ban', '198.51.100.7', **{var: ''})
                self.assertEqual(rc, 2, out)
                self.assertIn(f'{var} is unset', out)
                self.assertEqual(self.stand_in.requests, [], out)

    # --- settings from secrets/cloudflare.env ---------------------------------

    def write_env_file(self, **values: str) -> None:
        self.env_file.parent.mkdir(exist_ok=True)
        self.env_file.write_text('# Cloudflare, for fail2ban\n\n' + ''.join(
            f'{key}={value}\n' for key, value in values.items()))

    def test_settings_are_read_from_the_secrets_file(self) -> None:
        self.write_env_file(CLOUDFLARE_API_TOKEN=TOKEN, CLOUDFLARE_ACCOUNT_ID=ACCOUNT,
                            CLOUDFLARE_LIST_NAME=LIST_NAME)
        self.ok('ban', '198.51.100.7', CLOUDFLARE_API_TOKEN='',
                CLOUDFLARE_ACCOUNT_ID='', CLOUDFLARE_LIST_NAME='')
        self.assertEqual(self.stand_in.ips(), ['198.51.100.7'])

    def test_the_environment_wins_over_the_secrets_file(self) -> None:
        self.write_env_file(CLOUDFLARE_API_TOKEN='the-file-token')
        self.ok('ban', '198.51.100.7')
        self.assertEqual(self.stand_in.ips(), ['198.51.100.7'])


if __name__ == '__main__':
    unittest.main()
