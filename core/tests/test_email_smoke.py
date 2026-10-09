"""Tests for the coverage and safety rules of tools/email_smoke.py.

The tool itself is the verification -- it sends real mail through the real
provider and a human reads the headers, which is not something a test can do.
What is tested here is the part that must not rot between runs: that every
email category has smoke coverage, and that no recipient can ever come from the
database.

The second is the one that matters. Several of the site's mail paths derive
their recipients from a query -- notify_topic_subscribers() reads
topic.subscribers -- so a producer that took a real row would mail real members
from a tool whose whole purpose is to send test messages.

The tool is loaded by path rather than imported: tools/ holds standalone
scripts and is not a package.

"""
import base64
import contextlib
import importlib.util
import io
import logging
import os
import tempfile
import unittest
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.test.signals import template_rendered

from accounts.stats import NEW_USERS_KEY, USER_COUNT_KEY
from core.email_categories import EmailCategory
from core.services import get_redis_connection

TOOL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'tools', 'email_smoke.py')

SMOKE_TO = 'smoke-recipient@example.com'
MEMBER = 'a-real-member@example.invalid'


def load_tool():
    spec = importlib.util.spec_from_file_location('email_smoke', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoverageTestCase(unittest.TestCase):
    """The reason the tool enumerates by category rather than by call site.

    A hand-list of paths went stale in four days: task 05 added the email
    change confirmation and notice, and the task file still said seven.

    """
    def setUp(self):
        self.tool = load_tool()

    def test_every_category_is_covered(self):
        # Adding a category without giving it smoke coverage fails here, in
        # CI, rather than the next time somebody happens to run the tool.
        self.assertEqual(set(EmailCategory) - set(self.tool.COVERED), set())

    def test_no_category_is_covered_twice(self):
        self.assertEqual(len(self.tool.COVERED), len(set(EmailCategory)))

    def test_importing_the_tool_does_not_reconfigure_celery(self):
        # It used to, at import, and that reconfigured the shared app for the
        # whole suite: eleven retry tests in core.tests.test_tasks depend on an
        # eager task not propagating, and all eleven broke. The tool sets this
        # from its entry point instead.
        from sg101.celery import app
        original = app.conf.task_eager_propagates
        app.conf.task_eager_propagates = False
        try:
            load_tool()
            self.assertFalse(app.conf.task_eager_propagates)
        finally:
            app.conf.task_eager_propagates = original

    def test_only_selects_one_path(self):
        chosen = self.tool.every_path(only='registration')
        self.assertEqual([label for label, _ in chosen], ['registration'])

    def test_only_refuses_a_name_that_matches_nothing(self):
        # Silently running everything because the name was misspelled is the
        # opposite of what the flag is for: ten live messages instead of one.
        with self.assertRaises(SystemExit) as caught:
            self.tool.every_path(only='regisration')
        self.assertIn('registration', str(caught.exception))

    def test_paths_outside_the_wrapper_are_declared(self):
        # Django's error mail carries no category because it never reaches
        # core.functions.send_mail. It still has to be exercised: it is the
        # channel you need working when something else has broken.
        self.assertIn('django error mail', self.tool.UNWRAPPED_PATHS)


class ProducerTestCase(TestCase):
    """Every producer renders its real template and addresses only the
    address it was handed."""

    def setUp(self):
        self.tool = load_tool()

    def _run(self, producer):
        mail.outbox = []
        # Celery is already eager here: docker_test inherits it from
        # settings/test.py, and the tool sets it on the app at import. Both
        # matter -- override_settings cannot reconfigure a running app.
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            producer(SMOKE_TO)
        return mail.outbox

    def _run_strict(self, producer):
        mail.outbox = []
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                TEMPLATES=self.tool.strict_templates()):
            return producer(SMOKE_TO)

    def test_each_producer_sends_to_the_given_address_only(self):
        for category, producer in sorted(self.tool.COVERED.items()):
            with self.subTest(category=category):
                outbox = self._run(producer)
                self.assertTrue(outbox, 'no message sent')
                for message in outbox:
                    self.assertEqual(message.to, [SMOKE_TO])

    def test_each_producer_renders_a_non_empty_body(self):
        for category, producer in sorted(self.tool.COVERED.items()):
            with self.subTest(category=category):
                outbox = self._run(producer)
                self.assertTrue(outbox[0].body.strip())

    def test_a_removed_context_variable_is_caught(self):
        # A non-empty body is not enough, and this is measured rather than
        # assumed: Django renders a missing variable as the empty string and
        # carries on, so a template referencing one that has been deleted
        # produces a message with a hole in it and no error. Removing a
        # variable from registration_email.txt left the suite green until the
        # tool started rendering under a sentinel.
        message = mail.EmailMessage(
            subject='ok', body='link: %s' % (self.tool.MISSING % 'gone',))
        with self.assertRaises(AssertionError):
            self.tool.assert_no_missing_variables(message)

    def test_no_template_has_a_missing_context_variable(self):
        # The real templates, rendered strictly. This is the check requirement
        # 2 is actually about, and it belongs in the suite as well as the tool:
        # CI runs on every push, the tool runs when somebody remembers.
        for label, producer in self.tool.every_path():
            with self.subTest(path=label):
                self._run_strict(producer)
                for message in mail.outbox:
                    self.tool.assert_no_missing_variables(message)

    def test_every_path_renders_the_template_it_claims(self):
        # The detail column is documentation until something checks it. The
        # template_rendered signal is only sent under the test runner, which is
        # why this lives here and not in the tool.
        for label, producer in self.tool.every_path():
            claimed = producer.__doc__ or ''
            with self.subTest(path=label):
                rendered = []
                receiver = lambda sender, template, **kw: rendered.append(
                    template.name)
                template_rendered.connect(receiver)
                try:
                    detail = self._run_strict(producer)
                finally:
                    template_rendered.disconnect(receiver)
                for name in str(detail).split(' + '):
                    name = name.strip()
                    if '/' in name and name.endswith('.txt'):
                        self.assertIn(name, rendered)

    def test_no_recipient_comes_from_the_database(self):
        # The safety rule, stated as a test: a subscribed member exists, and
        # no producer may address them. A producer rewritten to use a real
        # topic instead of an in-memory one fails here.
        User.objects.create_user('smoke_member', MEMBER, 'x')
        for category, producer in sorted(self.tool.COVERED.items()):
            with self.subTest(category=category):
                for message in self._run(producer):
                    self.assertNotIn(MEMBER, message.to)

    def test_producers_leave_no_rows_behind(self):
        # Some paths need a scratch user or a PendingUser row to run at all.
        # In the tool those are written to the real database, so each producer
        # cleans up after itself.
        before = User.objects.count()
        for producer in self.tool.COVERED.values():
            self._run(producer)
        self.assertEqual(User.objects.count(), before)


class SpamConfidenceTestCase(unittest.TestCase):
    """Microsoft's SCL, which is neither the header that looks like it nor
    always a score at all."""

    def setUp(self):
        self.tool = load_tool()

    def _headers(self, blob, stated='1'):
        return ('X-MS-Exchange-Organization-SCL: %s\n'
                'X-Message-Delivery: %s\n' % (stated, blob))

    def test_the_encoded_score_wins_over_the_header_that_looks_official(self):
        # Measured on the 2026-08-17 capture: the org header read 1 while the
        # encoded value read 3. Reading the obvious one records a
        # neutral-reputation message as a well-trusted one.
        blob = base64.b64encode(b'V=1.1;us=0;l=0;a=0;D=1;GD=1;SCL=3').decode()
        result = self.tool.spam_confidence(self._headers(blob))
        self.assertTrue(result.startswith('3'))
        self.assertIn('1', result)

    def test_minus_one_is_reported_as_skipped_not_as_a_good_score(self):
        # -1 means the message skipped filtering because the RECEIVER trusts
        # the sender. Reporting it as a score would read as the best result
        # yet, when it is really the probe measuring its own history.
        blob = base64.b64encode(b'V=1.1;us=0;l=0;a=0;D=1;GD=1;SCL=-1').decode()
        result = self.tool.spam_confidence(self._headers(blob))
        self.assertIn('SKIPPED', result)
        self.assertIn('reputation', result)


class ServerEmailTestCase(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()

    @override_settings(SERVER_EMAIL='root@localhost')
    def test_rejects_the_django_default(self):
        # An unset SERVER_EMAIL sends crash reports from root@localhost, which
        # a provider will not sign for. The regression would otherwise surface
        # only during an outage.
        with self.assertRaises(AssertionError):
            self.tool.check_server_email()

    @override_settings(SERVER_EMAIL='admin@surfguitar101.com')
    def test_accepts_a_real_address(self):
        self.assertIn('admin@surfguitar101.com', self.tool.check_server_email())


class LiveModeTestCase(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()

    def test_live_mode_refuses_to_run_without_recipients(self):
        # --live with no addresses would fall back to whatever the producers
        # default to. It must refuse instead.
        with self.assertRaises(SystemExit):
            self.tool.require_recipients([])

    def test_live_mode_accepts_addresses(self):
        self.assertEqual(self.tool.require_recipients([SMOKE_TO]), [SMOKE_TO])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        EMAIL_HOST='localhost', EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='',
        EMAIL_USE_TLS=False)
    def test_live_refuses_when_mail_cannot_leave_the_box(self):
        # The false green this exists to stop: with no provider configured the
        # container falls back to the console backend, and --live printed all
        # ten messages to stdout and reported 23/23 passed having sent nothing.
        with self.assertRaises(SystemExit) as caught:
            self.tool.check_live_backend()
        message = str(caught.exception)
        self.assertIn('EMAIL_BACKEND', message)
        self.assertIn('EMAIL_HOST', message)
        self.assertIn('EMAIL_USE_TLS', message)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.postmarkapp.com', EMAIL_HOST_USER='token',
        EMAIL_HOST_PASSWORD='token', EMAIL_USE_TLS=True)
    def test_live_accepts_a_configured_provider(self):
        self.assertIn('smtp.postmarkapp.com', self.tool.check_live_backend())

    @override_settings(
        EMAIL_BACKEND='core.mail_backends.AllowlistEmailBackend',
        EMAIL_HOST='smtp.postmarkapp.com', EMAIL_HOST_USER='token',
        EMAIL_HOST_PASSWORD='token', EMAIL_USE_TLS=True)
    def test_live_accepts_the_allowlisting_backend(self):
        # It sends over SMTP, so the beta can prove its allowlist with --live.
        # A check on the backend's dotted path refused it: no "smtp" in it.
        self.assertIn('smtp.postmarkapp.com', self.tool.check_live_backend())

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
        EMAIL_HOST='smtp.postmarkapp.com', EMAIL_HOST_USER='token',
        EMAIL_HOST_PASSWORD='token', EMAIL_USE_TLS=True)
    def test_live_refuses_a_backend_that_does_not_send_over_smtp(self):
        # The provider settings alone are not enough: the backend must use them.
        with self.assertRaises(SystemExit) as caught:
            self.tool.check_live_backend()
        self.assertIn('EMAIL_BACKEND', str(caught.exception))


class MemberRecipientTestCase(TestCase):
    """A recipient that is a member's address is refused before anything runs.

    The scratch users some paths need carry the recipient's address, and the
    database allows one account per address, case-insensitively: on 2026-10-07
    the first live run against an address with an account rendered nothing and
    sent nothing. Avoiding the collision would not be enough either -- the
    site's own lookups would then find the real account, and the password reset
    path would mail a working reset link for it.
    """

    def setUp(self):
        self.tool = load_tool()
        User.objects.create_user('a_member', 'Member@Example.com', 'x')

    def test_a_member_address_is_refused_whatever_its_case(self):
        with self.assertRaises(SystemExit) as raised:
            self.tool.check_recipients_are_not_members(
                ['other@example.com', 'member@example.com'])
        message = str(raised.exception)
        self.assertIn('member@example.com', message)
        self.assertIn('plus-address', message)
        self.assertNotIn('other@example.com', message)

    def test_addresses_without_an_account_pass(self):
        self.tool.check_recipients_are_not_members(
            ['member+smoke@example.com', 'nobody@example.com'])

    def test_a_live_run_to_a_member_stops_before_rendering(self):
        # send_inline reconfigures the shared Celery app and the live-backend
        # check refuses the test settings; neither is what is under test.
        with patch.object(self.tool, 'send_inline'), \
                patch.object(self.tool, 'check_live_backend'), \
                patch.object(self.tool, 'render_pass') as render_pass, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.tool.main(live_to=['member@example.com'])
        render_pass.assert_not_called()


class RenderPassLogTestCase(TestCase):
    """The render pass sends nothing, so it must log nothing.

    email.log records one line per message, written whatever the backend, and
    the 2026-10-07 run wrote 37 `outcome=sent` lines for messages that went into
    an in-memory outbox -- indistinguishable from real sends in the log that
    exists to count them.
    """

    def setUp(self):
        self.tool = load_tool()
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

    def test_a_producer_on_its_own_does_log(self):
        # Without this the test below would pass with logging still off.
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            with self.assertLogs('email', level='INFO'):
                self.tool.contact_form(SMOKE_TO)

    def test_the_render_pass_logs_nothing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertNoLogs('email', level='INFO'):
                self.tool.render_pass(self.tool.every_path(), [SMOKE_TO])
        self.assertTrue(all(ok for ok, _, _ in self.tool.results),
                        self.tool.results)
        # And the live sends that follow it are logged again.
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            with self.assertLogs('email', level='INFO'):
                self.tool.contact_form(SMOKE_TO)


class PasswordResetLinkTestCase(TestCase):
    """The reset link a member gets is https; the tool's should be too."""

    def test_the_reset_link_is_https(self):
        tool = load_tool()
        mail.outbox = []
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            tool.password_reset(SMOKE_TO)
        body = mail.outbox[0].body
        self.assertIn('https://', body)
        self.assertNotIn('http://', body)


class ScratchUserStatsTestCase(TestCase):
    """Scratch users never reach the newest-members list or the user count.

    Creating a User fires accounts.stats' new-user task, which on 2026-10-07 put
    `_email_smoke` ten times into the home page's newest members and counted
    users that were deleted again. Runs against the real test Redis (db 14),
    since what is asserted is what lands there.
    """

    def setUp(self):
        self.tool = load_tool()
        self.conn = get_redis_connection()
        self.flush()
        self.addCleanup(self.flush)
        self.conn.set(USER_COUNT_KEY, 100)
        self.conn.rpush(NEW_USERS_KEY, 'newest_member')

    def flush(self):
        self.conn.delete(USER_COUNT_KEY, NEW_USERS_KEY)

    def test_producers_leave_the_user_stats_alone(self):
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            for producer in self.tool.COVERED.values():
                producer(SMOKE_TO)
        self.assertEqual(self.conn.get(USER_COUNT_KEY), '100')
        self.assertEqual(self.conn.lrange(NEW_USERS_KEY, 0, -1),
                         ['newest_member'])

    def test_the_stats_receiver_is_reconnected_afterwards(self):
        with override_settings(
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            self.tool.forgot_username(SMOKE_TO)
        User.objects.create_user('real_newcomer', 'new@example.com', 'x')
        self.assertEqual(self.conn.lindex(NEW_USERS_KEY, 0), 'real_newcomer')


class DeadDomainTestCase(unittest.TestCase):
    """Postmark replaces Django's Message-ID, so the dead domain belongs nowhere.

    Before the move the guidance was that Message-ID would still carry it; D1
    on 2026-10-07 found `<...@mtasv.net>` instead. Seeing it anywhere now means
    a message did not go through Postmark.
    """

    def test_the_dead_domain_in_message_id_is_flagged(self):
        tool = load_tool()
        headers = ('Authentication-Results: mx.example; dmarc=pass\n'
                   'Message-ID: <123@%s>\n' % tool.DEAD_DOMAIN)
        with tempfile.NamedTemporaryFile('w', suffix='.txt') as fp:
            fp.write(headers)
            fp.flush()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                tool.read_headers(fp.name)
        self.assertIn('NOTE', out.getvalue())

    def test_the_guidance_no_longer_expects_it(self):
        tool = load_tool()
        self.assertNotIn('STILL carries the dead domain',
                         tool.HEADER_EXPECTATIONS)
