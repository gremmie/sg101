#!/usr/bin/env python3
"""Tests for tools/origin_firewall.py's Linode adapter, against a local
stand-in for Linode's firewall rules API. Nothing here reaches Linode or needs a
token.

The stand-in serves GET and PUT /v4/networking/firewalls/<id>/rules from a
dict the tests can edit, playing the part of someone changing the rules in the
dashboard, and records each request so a refusal can be shown to have sent
nothing. It returns rules and addresses in the reverse of the order they were
stored, so a check that depended on order would fail here.

The tool runs as a separate process, as it does from the Makefile. It and the
ranges file are copied into a scratch tree first: the tool finds its files
relative to itself, so a test can break the copy without touching the real one.
The tree starts with no settings file, so a test sees only the settings it
passes unless it writes one.

The login keychain is replaced too: a stand-in `security` comes first on PATH,
answering with FAKE_KEYCHAIN_TOKEN, or "not found" when that is empty, and
logging its arguments. The real keychain is never asked, so a token stored there
cannot reach the stand-in API or change what a refusal test sees.

    python3 tools/origin_firewall_test.py
    /usr/bin/python3 tools/origin_firewall_test.py    # the tool under that interpreter

Standard library only.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIREWALL_ID = '4242'
TOKEN = f'test-token-{os.getpid()}-do-not-print'
EMERGENCY = {'action': 'ACCEPT', 'protocol': 'TCP', 'ports': '443', 'label': 'emergency',
             'addresses': {'ipv4': ['203.0.113.7/32']}}
RULES_PATH = re.compile(r'^/v4/networking/firewalls/(\d+)/rules$')
KEYCHAIN_SERVICE = 'sg101-linode-firewall'
FAKE_SECURITY = """#!{python}
import os, sys
with open(os.environ['FAKE_KEYCHAIN_LOG'], 'a') as log:
    log.write(' '.join(sys.argv[1:]) + '\\n')
token = os.environ.get('FAKE_KEYCHAIN_TOKEN', '')
if not token:
    print('security: SecKeychainSearchCopyNext: The specified item could not '
          'be found in the keychain.', file=sys.stderr)
    sys.exit(44)
print(token)
"""


class StandIn:
    """Linode's firewall rules endpoint, as far as the tool uses it."""

    def __init__(self) -> None:
        self.reset()
        stand_in = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def reply(self, status: int, body: dict) -> None:
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def handle_request(self) -> None:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else None
                stand_in.requests.append((self.command, self.path))
                status, reply = stand_in.respond(
                    self.command, self.path, self.headers.get('Authorization'), body)
                self.reply(status, reply)

            do_GET = do_PUT = handle_request

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.server.server_port}/v4'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def reset(self) -> None:
        self.rules = {'inbound': [], 'inbound_policy': 'ACCEPT',
                      'outbound': [], 'outbound_policy': 'ACCEPT'}
        self.requests: list[tuple[str, str]] = []

    def respond(self, method: str, path: str, auth: str | None,
                body: bytes | None) -> tuple[int, dict]:
        if auth != f'Bearer {TOKEN}':
            return 401, errors((None, 'Invalid Token'))
        match = RULES_PATH.match(path)
        if not match or match.group(1) != FIREWALL_ID:
            return 404, errors((None, 'Not found'))
        if method == 'GET':
            rules = copy.deepcopy(self.rules)
            for direction in ('inbound', 'outbound'):
                rules[direction].reverse()
                for rule in rules[direction]:
                    for family in rule.get('addresses', {}).values():
                        family.reverse()
            return 200, {**rules, 'fingerprint': '0badf00d', 'version': 7}
        try:
            rules = json.loads(body or b'')
        except ValueError:
            return 400, errors((None, 'Invalid JSON'))
        problems = validate(rules)
        if problems:
            return 400, errors(*problems)
        self.rules = {key: rules[key] for key in
                      ('inbound', 'inbound_policy', 'outbound', 'outbound_policy')}
        return 200, self.rules

    def rules_on(self, port: str) -> list[dict]:
        return [rule for rule in self.rules['inbound'] if rule.get('ports') == port]

    def addresses_on(self, port: str) -> list[str]:
        """Every address the stored rules allow on that port, sorted."""
        return sorted(address for rule in self.rules_on(port)
                      for family in rule['addresses'].values() for address in family)


def errors(*problems: tuple[str | None, str]) -> dict:
    return {'errors': [{'reason': reason, **({'field': field} if field else {})}
                       for field, reason in problems]}


def validate(rules: dict) -> list[tuple[str, str]]:
    """What Linode would refuse in a PUT body, within its documented limits."""
    problems = [(policy, 'Must be ACCEPT or DROP')
                for policy in ('inbound_policy', 'outbound_policy')
                if rules.get(policy) not in ('ACCEPT', 'DROP')]
    for direction in ('inbound', 'outbound'):
        for i, rule in enumerate(rules.get(direction, [])):
            where = f'{direction}[{i}]'
            if rule.get('action') not in ('ACCEPT', 'DROP'):
                problems.append((f'{where}.action', 'Must be ACCEPT or DROP'))
            if rule.get('protocol') not in ('TCP', 'UDP', 'ICMP', 'IPENCAP'):
                problems.append((f'{where}.protocol', 'Invalid protocol'))
            label = rule.get('label')
            if label is not None and not 3 <= len(label) <= 32:
                problems.append((f'{where}.label', 'Length must be 3-32 characters'))
            count = sum(len(family) for family in (rule.get('addresses') or {}).values())
            if not count:
                problems.append((f'{where}.addresses', 'Must contain ipv4 or ipv6 addresses'))
            if count > 255:
                problems.append((f'{where}.addresses', 'Too many addresses'))
    if len(rules.get('inbound', [])) + len(rules.get('outbound', [])) > 25:
        problems.append(('inbound', 'Too many rules'))
    return problems


class OriginFirewallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stand_in = StandIn()
        cls.tree = Path(tempfile.mkdtemp())
        (cls.tree / 'tools').mkdir()
        (cls.tree / 'apache').mkdir()
        shutil.copy(ROOT / 'tools/origin_firewall.py', cls.tree / 'tools')
        shutil.copy(ROOT / 'apache/cloudflare-ranges.txt', cls.tree / 'apache')
        cls.ranges_file = cls.tree / 'apache/cloudflare-ranges.txt'
        cls.good_ranges = cls.ranges_file.read_text()
        (cls.tree / 'firewall').mkdir()
        cls.settings_file = cls.tree / 'firewall/settings.env'
        cls.fake_bin = cls.tree / 'fake-bin'
        cls.fake_bin.mkdir()
        security = cls.fake_bin / 'security'
        security.write_text(FAKE_SECURITY.format(python=sys.executable))
        security.chmod(0o755)
        cls.keychain_log = cls.tree / 'keychain.log'

    @classmethod
    def tearDownClass(cls) -> None:
        cls.stand_in.server.shutdown()
        shutil.rmtree(cls.tree)

    def setUp(self) -> None:
        self.stand_in.reset()
        self.ranges_file.write_text(self.good_ranges)
        self.settings_file.unlink(missing_ok=True)
        self.keychain_log.write_text('')

    def fw(self, action: str, **settings: str) -> tuple[int, str]:
        """Run the tool with complete settings, each overridable; an empty
        string is how a test leaves a setting unset. Returns the exit status and
        stdout and stderr together."""
        env = {
            'PATH': f'{self.fake_bin}{os.pathsep}{os.environ["PATH"]}',
            'HOME': os.environ.get('HOME', ''),
            'FAKE_KEYCHAIN_LOG': str(self.keychain_log), 'FAKE_KEYCHAIN_TOKEN': '',
            'FIREWALL_PROVIDER': 'linode', 'FIREWALL_LINODE_ID': FIREWALL_ID,
            'LINODE_TOKEN': TOKEN, 'LINODE_API_URL': self.stand_in.url,
            'FIREWALL_HTTP': 'allow', 'FIREWALL_SSH_FROM': 'anywhere',
            **settings,
        }
        self.stand_in.requests.clear()
        result = subprocess.run(
            [sys.executable, str(self.tree / 'tools/origin_firewall.py'), action],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return result.returncode, result.stdout

    def apply(self, **settings: str) -> None:
        rc, out = self.fw('apply', **settings)
        self.assertEqual(rc, 0, out)

    def planned_ranges(self) -> list[str]:
        rc, out = self.fw('plan')
        return sorted(line[4:] for line in out.splitlines() if line.startswith('    '))

    # --- apply: the request holds what plan prints ----------------------------

    def test_plan_lists_22_ranges(self) -> None:
        self.assertEqual(len(self.planned_ranges()), 22)

    def test_apply_sends_one_put_and_exits_0(self) -> None:
        rc, out = self.fw('apply')
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.stand_in.requests,
                         [('PUT', f'/v4/networking/firewalls/{FIREWALL_ID}/rules')])

    def test_443_is_one_rule_holding_exactly_the_planned_ranges(self) -> None:
        self.apply()
        self.assertEqual(len(self.stand_in.rules_on('443')), 1)
        self.assertEqual(self.stand_in.addresses_on('443'), self.planned_ranges())

    def test_http_allow_opens_80_from_the_same_ranges(self) -> None:
        self.apply(FIREWALL_HTTP='allow')
        self.assertEqual(self.stand_in.addresses_on('80'), self.planned_ranges())

    def test_ssh_from_anywhere_is_every_address_in_both_families(self) -> None:
        self.apply(FIREWALL_SSH_FROM='anywhere')
        [ssh] = self.stand_in.rules_on('22')
        self.assertEqual(ssh['addresses'], {'ipv4': ['0.0.0.0/0'], 'ipv6': ['::/0']})

    def test_policies_and_rule_shapes(self) -> None:
        self.apply()
        rules = self.stand_in.rules
        self.assertEqual(rules['inbound_policy'], 'DROP')
        self.assertEqual(rules['outbound_policy'], 'ACCEPT')
        self.assertEqual(rules['outbound'], [])
        self.assertEqual(len(rules['inbound']), 3)
        self.assertEqual({(r['action'], r['protocol']) for r in rules['inbound']},
                         {('ACCEPT', 'TCP')})

    def test_http_drop_leaves_out_80_and_ssh_ranges_split_by_family(self) -> None:
        self.apply(FIREWALL_HTTP='drop', FIREWALL_SSH_FROM='198.51.100.7/32 2001:db8::/48')
        self.assertEqual(sorted(r['ports'] for r in self.stand_in.rules['inbound']),
                         ['22', '443'])
        [ssh] = self.stand_in.rules_on('22')
        self.assertEqual(ssh['addresses'],
                         {'ipv4': ['198.51.100.7/32'], 'ipv6': ['2001:db8::/48']})

    def test_ssh_from_ipv4_only_applies_and_checks_ok(self) -> None:
        self.apply(FIREWALL_SSH_FROM='198.51.100.7/32')
        rc, out = self.fw('check', FIREWALL_SSH_FROM='198.51.100.7/32')
        self.assertEqual(rc, 0, out)

    # --- check: OK when live matches, and drift named in every direction ------

    def test_check_after_apply_is_ok_with_one_get(self) -> None:
        self.apply()
        rc, out = self.fw('check')
        self.assertEqual(rc, 0, out)
        self.assertTrue(out.startswith('OK'), out)
        self.assertEqual([method for method, _ in self.stand_in.requests], ['GET'])

    def test_check_reads_a_respelled_address_as_the_same_range(self) -> None:
        self.apply()
        [https] = self.stand_in.rules_on('443')
        v6 = https['addresses']['ipv6']
        v6[v6.index('2400:cb00::/32')] = '2400:CB00:0000::/32'
        rc, out = self.fw('check')
        self.assertEqual(rc, 0, out)

    def assert_drift(self, *expected_lines: str) -> None:
        rc, out = self.fw('check')
        self.assertEqual(rc, 1, out)
        self.assertTrue(out.startswith('DIFFERS'), out)
        for line in expected_lines:
            self.assertIn(line, out)

    def test_check_catches_a_missing_range(self) -> None:
        self.apply()
        self.stand_in.rules_on('443')[0]['addresses']['ipv4'].remove('173.245.48.0/20')
        self.assert_drift('only planned:  inbound ACCEPT TCP 443 173.245.48.0/20')

    def test_check_catches_a_stray_range(self) -> None:
        self.apply()
        self.stand_in.rules_on('443')[0]['addresses']['ipv6'].append('2001:db8:bad::/48')
        self.assert_drift('only live:     inbound ACCEPT TCP 443 2001:db8:bad::/48')

    def test_check_catches_an_extra_rule(self) -> None:
        self.apply()
        self.stand_in.rules['inbound'].append(copy.deepcopy(EMERGENCY))
        self.assert_drift('only live:     inbound ACCEPT TCP 443 203.0.113.7/32')

    def test_check_catches_a_changed_port(self) -> None:
        self.apply()
        self.stand_in.rules_on('22')[0]['ports'] = '2222'
        self.assert_drift('only live:     inbound ACCEPT TCP 2222 0.0.0.0/0',
                          'only planned:  inbound ACCEPT TCP 22 0.0.0.0/0')

    def test_check_catches_a_changed_inbound_policy(self) -> None:
        self.apply()
        self.stand_in.rules['inbound_policy'] = 'ACCEPT'
        self.assert_drift('only live:     inbound_policy ACCEPT',
                          'only planned:  inbound_policy DROP')

    def test_check_catches_an_outbound_rule(self) -> None:
        self.apply()
        self.stand_in.rules['outbound'].append(
            {'action': 'DROP', 'protocol': 'TCP', 'ports': '25', 'label': 'no-smtp',
             'addresses': {'ipv4': ['0.0.0.0/0']}})
        self.assert_drift('only live:     outbound DROP TCP 25 0.0.0.0/0')

    def test_check_catches_a_changed_outbound_policy(self) -> None:
        self.apply()
        self.stand_in.rules['outbound_policy'] = 'DROP'
        self.assert_drift('only live:     outbound_policy DROP')

    # --- apply replaces rather than adds --------------------------------------

    def test_apply_removes_a_hand_added_rule(self) -> None:
        self.apply()
        self.stand_in.rules['inbound'].append(copy.deepcopy(EMERGENCY))
        self.apply()
        rc, out = self.fw('check')
        self.assertEqual(rc, 0, out)
        self.assertNotIn('203.0.113.7', json.dumps(self.stand_in.rules))

    # --- errors are failures, with Linode's reason and without the token ------

    def test_a_bad_token_fails_with_linodes_reason_and_is_not_printed(self) -> None:
        for action in ('apply', 'check'):
            with self.subTest(action=action):
                bad = f'wrong-token-{os.getpid()}'
                rc, out = self.fw(action, LINODE_TOKEN=bad)
                self.assertEqual(rc, 2, out)
                self.assertIn('Invalid Token', out)
                self.assertNotIn(bad, out)

    def test_a_wrong_firewall_id_fails_with_linodes_reason(self) -> None:
        for action in ('apply', 'check'):
            with self.subTest(action=action):
                rc, out = self.fw(action, FIREWALL_LINODE_ID='999')
                self.assertEqual(rc, 2, out)
                self.assertIn('Not found', out)
                self.assertNotIn(TOKEN, out)

    def test_an_unreachable_api_fails(self) -> None:
        for action in ('apply', 'check'):
            with self.subTest(action=action):
                rc, out = self.fw(action, LINODE_API_URL='http://127.0.0.1:1/v4')
                self.assertEqual(rc, 2, out)
                self.assertNotIn(TOKEN, out)

    # --- refusals send nothing ------------------------------------------------

    def assert_refuses(self, action: str, **settings: str) -> str:
        rc, out = self.fw(action, **settings)
        self.assertEqual(rc, 2, out)
        self.assertEqual(self.stand_in.requests, [], out)
        self.assertNotIn(TOKEN, out)
        return out

    def test_refusals_send_nothing(self) -> None:
        cases = {
            'no token': {'LINODE_TOKEN': ''},
            'no firewall ID': {'FIREWALL_LINODE_ID': ''},
            'no SSH source': {'FIREWALL_SSH_FROM': ''},
            'no port 80 decision': {'FIREWALL_HTTP': ''},
            'an SSH address with no mask': {'FIREWALL_SSH_FROM': '198.51.100.7'},
            "'anywhere' mixed with addresses": {'FIREWALL_SSH_FROM': 'anywhere 198.51.100.7/32'},
        }
        for action in ('apply', 'check'):
            for name, settings in cases.items():
                with self.subTest(action=action, case=name):
                    self.assert_refuses(action, **settings)

    def test_an_unknown_provider_is_refused(self) -> None:
        self.assert_refuses('apply', FIREWALL_PROVIDER='nosuchcloud')

    def test_a_missing_setting_is_named_as_unset(self) -> None:
        for var in ('FIREWALL_LINODE_ID', 'LINODE_TOKEN'):
            with self.subTest(var=var):
                out = self.assert_refuses('apply', **{var: ''})
                self.assertIn(f'{var} is unset', out)

    def test_no_token_anywhere_asks_the_keychain_and_says_so(self) -> None:
        out = self.assert_refuses('check', LINODE_TOKEN='')
        self.assertIn(KEYCHAIN_SERVICE, out)
        self.assertIn(f'-s {KEYCHAIN_SERVICE} -w', self.keychain_log.read_text())

    # --- the settings file and the keychain -----------------------------------

    def write_settings(self, *lines: str) -> None:
        self.settings_file.write_text('# a comment, then a blank line\n\n'
                                      + ''.join(f'{line}\n' for line in lines))

    def settled(self) -> None:
        """The settings file as committed, but naming the stand-in's firewall."""
        self.write_settings('FIREWALL_PROVIDER=linode',
                            f'FIREWALL_LINODE_ID={FIREWALL_ID}',
                            'FIREWALL_SSH_FROM=anywhere', 'FIREWALL_HTTP=drop')

    UNSET = {'FIREWALL_PROVIDER': '', 'FIREWALL_LINODE_ID': '',
             'FIREWALL_SSH_FROM': '', 'FIREWALL_HTTP': ''}

    def test_the_settings_file_supplies_what_the_environment_does_not(self) -> None:
        self.settled()
        self.apply(**self.UNSET)
        self.assertEqual(sorted(r['ports'] for r in self.stand_in.rules['inbound']),
                         ['22', '443'])
        rc, out = self.fw('check', **self.UNSET)
        self.assertEqual(rc, 0, out)

    def test_plan_shows_the_settings_files_decisions(self) -> None:
        self.settled()
        rc, out = self.fw('plan', **self.UNSET)
        self.assertEqual(rc, 0, out)
        self.assertNotIn('UNDECIDED', out)
        self.assertIn('tcp 80  refused', out)

    def test_the_environment_overrides_the_settings_file(self) -> None:
        self.settled()
        self.apply(FIREWALL_HTTP='allow', FIREWALL_SSH_FROM='198.51.100.7/32')
        self.assertEqual(self.stand_in.addresses_on('80'), self.planned_ranges())
        self.assertEqual(self.stand_in.addresses_on('22'), ['198.51.100.7/32'])

    def test_the_token_comes_from_the_keychain_when_unset(self) -> None:
        rc, out = self.fw('apply', LINODE_TOKEN='', FAKE_KEYCHAIN_TOKEN=TOKEN)
        self.assertEqual(rc, 0, out)
        self.assertNotIn(TOKEN, out)

    def test_a_token_in_the_environment_is_used_before_the_keychain(self) -> None:
        rc, out = self.fw('apply', FAKE_KEYCHAIN_TOKEN=f'stale-{os.getpid()}')
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.keychain_log.read_text(), '')

    def test_a_token_in_the_settings_file_is_refused_and_not_printed(self) -> None:
        self.settled()
        self.settings_file.write_text(self.settings_file.read_text()
                                      + f'LINODE_TOKEN={TOKEN}\n')
        for action in ('plan', 'apply', 'check'):
            with self.subTest(action=action):
                rc, out = self.fw(action, **self.UNSET)
                self.assertEqual(rc, 2, out)
                self.assertEqual(self.stand_in.requests, [], out)
                self.assertIn('LINODE_TOKEN does not belong', out)
                self.assertNotIn(TOKEN, out)

    def test_a_bad_settings_line_is_refused(self) -> None:
        cases = {'not KEY=value': f'{TOKEN}',
                 'an unknown setting': 'FIREWALL_HTTPS=drop',
                 'a mistyped value': 'FIREWALL_HTTP=dorp'}
        for name, line in cases.items():
            for action in ('plan', 'apply', 'check'):
                with self.subTest(case=name, action=action):
                    self.write_settings(line)
                    rc, out = self.fw(action, FIREWALL_HTTP='')
                    self.assertEqual(rc, 2, out)
                    self.assertEqual(self.stand_in.requests, [], out)
                    self.assertNotIn(TOKEN, out)

    def test_a_malformed_ranges_line_is_refused(self) -> None:
        self.ranges_file.write_text(self.good_ranges + 'not-a-range\n')
        for action in ('apply', 'check'):
            with self.subTest(action=action):
                self.assert_refuses(action)


if __name__ == '__main__':
    unittest.main()
