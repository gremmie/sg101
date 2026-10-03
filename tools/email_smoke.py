"""Live smoke test of the site's outbound email paths.

Renders every message the site sends, through the code that really sends it,
and -- with --live -- puts real messages through the configured provider so a
human can read the headers at the far end.

    docker compose exec -T web python /app/tools/email_smoke.py
    docker compose exec -T web python /app/tools/email_smoke.py --live you@gmail.com you@outlook.com

Run it after anything that touches mail: a settings change, a new sending path,
a provider or DNS change.

The default run sends nothing. It swaps in the locmem backend, exercises every
path, and asserts the headers -- safe in CI and for anyone.

WHAT A GREEN RUN DOES NOT PROVE
------------------------------
Unlike tools/image_smoke.py, which fetches its uploaded object back and so
closes its own loop, this tool cannot verify delivery. A 250 from the provider
means accepted-for-delivery and nothing more: not that the message arrived, and
certainly not whether it landed in an inbox or a junk folder, which no SMTP
response reveals. --check-headers can read Microsoft's dest:I / dest:J out of a
saved header block, but only once a human has fetched the headers, and most
receivers say nothing at all. The acceptance test for this work is a human
reading Authentication-Results in an Outlook/Hotmail INBOX. Gmail already accepts this
site's mail and would have before any of the migration work, so a Gmail-only
check cannot tell success from failure.

--live SENDS REAL MAIL AND CANNOT BE UNDONE
-------------------------------------------
It needs the provider's credentials in the environment (the same EMAIL_*
variables the application reads) and it sends to the addresses you name on the
command line. There is no cleanup: a message to a dead address is a bounce
against this domain's sending reputation, permanently. Name addresses you own.

NO RECIPIENT EVER COMES FROM THE DATABASE
-----------------------------------------
Every address reached is one passed in. This is a rule, not an accident:
notify_topic_subscribers() derives its recipients from topic.subscribers, so a
producer built on a real topic row would mail real members from a tool whose
whole purpose is to send test messages. The forum producer therefore builds its
post in memory and stubs the subscriber query, and
core/tests/test_email_smoke.py asserts the rule holds.

"""
import argparse
import base64
import copy
import os
import sys
import traceback
from types import SimpleNamespace

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.dev')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.contrib.sites.models import Site  # noqa: E402
from django.core.mail import mail_admins  # noqa: E402
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend  # noqa: E402
from django.test import override_settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from django.utils.module_loading import import_string  # noqa: E402

from accounts.forms import (ForgotUsernameForm, RegisterForm,  # noqa: E402
                            SitePasswordResetForm)
from accounts.models import PendingEmailChange, PendingUser  # noqa: E402
from accounts.utils import (make_confirmation_token,  # noqa: E402
                            send_email_change_confirmation,
                            send_email_change_notice)
from contact.forms import ContactForm  # noqa: E402
from core.email_categories import EmailCategory  # noqa: E402
from core.functions import email_admins  # noqa: E402
from messages.forms import notify_receiver  # noqa: E402
from messages.models import Message  # noqa: E402
from forums.views.subscriptions import notify_topic_subscribers  # noqa: E402
from sg101.celery import app as celery_app  # noqa: E402

def send_inline():
    """Send on this thread rather than handing the message to a worker.

    The point of the tool is to observe the send: a deferred task succeeds by
    being queued, in a process that cannot report back here. The Celery hop
    itself is covered by core/tests/test_tasks.py, where the retry behaviour
    lives.

    Called from the entry point, never at import. Setting this at import time
    reconfigured the shared app object for anything that imported the module --
    which core/tests/test_email_smoke.py does, and which broke eleven retry
    tests that depend on an eager task NOT propagating its exception.
    """
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

SCRATCH = '_email_smoke'
LOCMEM = 'django.core.mail.backends.locmem.EmailBackend'

# Django renders a missing context variable as the empty string and carries on,
# so a template still referencing one that has been removed produces a message
# with a hole in it rather than an error. Asserting the body is non-empty does
# not catch that -- measured, by removing a variable and watching the suite stay
# green. Rendering under a sentinel is what catches it.
# Square brackets, not angle: autoescaping renders '<<' as '&lt;&lt;', so an
# angle-bracket sentinel never matches the body it is supposed to be found in.
# The first version of this check was inert for exactly that reason, and only a
# mutation showed it -- the tool reported ok on a template with a hole in it.
MISSING = '[[MISSING-CONTEXT-VARIABLE:%s]]'
MISSING_MARK = '[[MISSING-CONTEXT-VARIABLE:'


def strict_templates():
    """settings.TEMPLATES with string_if_invalid set, for override_settings."""
    templates = copy.deepcopy(settings.TEMPLATES)
    for engine in templates:
        engine.setdefault('OPTIONS', {})['string_if_invalid'] = MISSING
    return templates


def assert_no_missing_variables(message):
    holes = set()
    for field in (message.subject, message.body):
        start = 0
        while True:
            at = field.find(MISSING_MARK, start)
            if at < 0:
                break
            holes.add(field[at + len(MISSING_MARK):].split(']]', 1)[0])
            start = at + 1
    assert not holes, \
        'template referenced context variables that do not exist: %s' % (
            sorted(holes),)

results = []


def check(label, fn):
    try:
        detail = fn()
        results.append((True, label, detail))
        print('  ok    %-34s %s' % (label, detail))
    except Exception as exc:
        results.append((False, label, '%s: %s' % (type(exc).__name__, exc)))
        print('  FAIL  %-34s %s: %s' % (label, type(exc).__name__, exc))
        traceback.print_exc()


###############################################################################
# Producers -- one per EmailCategory, each addressing only what it is given.
###############################################################################

def registration_confirmation(to):
    """accounts.forms.RegisterForm.save()"""
    form = RegisterForm(ip='127.0.0.1')
    form.cleaned_data = {'username': SCRATCH, 'email': to,
                         'password1': 'smoke-password'}
    try:
        form.save()
    finally:
        PendingUser.objects.filter(username=SCRATCH).delete()
    return 'accounts/registration_email.txt'


def forgot_username(to):
    """accounts.forms.ForgotUsernameForm.save()"""
    user = User.objects.create_user(SCRATCH, to, 'smoke-password')
    try:
        form = ForgotUsernameForm()
        form.cleaned_data = {'email': to}
        form.save()
    finally:
        user.delete()
    return 'accounts/forgot_user_email.txt'


def password_reset(to):
    """accounts.forms.SitePasswordResetForm -- the wrapper override from task 02.

    Templates and form_class are named to match accounts/urls.py; a reset run
    with Django's defaults would render a different message than the site does.
    """
    user = User.objects.create_user(SCRATCH, to, 'smoke-password')
    try:
        form = SitePasswordResetForm({'email': to})
        assert form.is_valid(), form.errors
        form.save(domain_override=Site.objects.get_current().domain,
                  email_template_name='accounts/password_reset_email.txt',
                  from_email=settings.DEFAULT_FROM_EMAIL)
    finally:
        user.delete()
    return 'accounts/password_reset_email.txt'


def email_change_confirmation(to):
    """accounts.utils.send_email_change_confirmation() -- to the NEW address."""
    user = User.objects.create_user(SCRATCH, 'old-address@example.com',
                                    'smoke-password')
    try:
        change = PendingEmailChange(user=user, new_email=to,
                                    key=make_confirmation_token())
        send_email_change_confirmation(change)
    finally:
        user.delete()
    return 'accounts/email_change_email.txt'


def email_change_notice(to):
    """accounts.utils.send_email_change_notice() -- to the address ON FILE.

    Shares EMAIL_CHANGE with the confirmation above, so COVERED maps the
    category to a producer that runs both: they are two different templates and
    a smoke run that exercised only one would miss half the path.
    """
    user = User.objects.create_user(SCRATCH, to, 'smoke-password')
    try:
        change = PendingEmailChange(user=user,
                                    new_email='new-address@example.com',
                                    key=make_confirmation_token())
        send_email_change_notice(change)
    finally:
        user.delete()
    return 'accounts/email_change_notice.txt'


def email_change_both(to):
    email_change_confirmation(to)
    email_change_notice(to)
    return 'email_change_email.txt + email_change_notice.txt'


def topic_notification(to):
    """forums.views.subscriptions.notify_topic_subscribers()

    Built in memory and duck-typed on purpose. The function reads exactly
    post.topic.subscribers, post.user, post.body and post.get_absolute_url(),
    and the subscriber query is the one place a real member's address could
    enter this tool. An AttributeError here means the function grew a new
    dependency and this stand-in needs to grow with it -- which is the failure
    mode to want, since the alternative is writing forum rows: Forum.last_post
    is a CASCADE pointing the wrong way, and deleting the post a forum points at
    once took the forum, its topics and its posts with it.
    """
    class Subscribers(object):
        def exclude(self, **kwargs):
            return self

        def values_list(self, *fields, **kwargs):
            return [to]

    topic = SimpleNamespace(name='Smoke test topic', subscribers=Subscribers())
    post = SimpleNamespace(
        topic=topic,
        user=SimpleNamespace(id=0, username=SCRATCH),
        body='Body of the post that triggered this notification.',
        get_absolute_url=lambda: '/forums/goto/0/')
    notify_topic_subscribers(post)
    return 'forums/topic_notify_email.txt'


def pm_notification(to):
    """messages.forms.notify_receiver()"""
    receiver = User(username=SCRATCH + '_to', email=to)
    sender = User(username=SCRATCH + '_from', email='sender@example.com')
    message = Message(sender=sender, receiver=receiver,
                      subject='Smoke test private message',
                      message='Body of the private message.',
                      html='<p>Body of the private message.</p>',
                      send_date=timezone.now())
    notify_receiver(message)
    return 'messages/notification_email.txt'


def contact_form(to):
    """contact.forms.ContactForm.save()

    cleaned_data is set directly: clean() calls out to the CAPTCHA provider,
    and the message this renders is the same either way.
    """
    form = ContactForm()
    form.cleaned_data = {
        'name': 'Email Smoke',
        'email': 'visitor@example.com',
        'subject': 'Smoke test',
        'message': 'Body of the contact form message.',
    }
    form.recipient_list = [to]
    form.save()
    return 'contact/contact_email.txt'


def admin_notification(to):
    """core.functions.email_admins() -- the flag/spam/pending-approval family."""
    with override_settings(ADMINS=(('Email smoke', to),)):
        email_admins('Smoke test admin notification',
                     'Body of the admin notification.')
    return 'core.functions.email_admins'


def django_error_mail(to):
    """django.core.mail.mail_admins() -- what AdminEmailHandler calls.

    Outside the wrapper, so it carries no category and never reaches email.log.
    It is also the channel you need working when something else has broken,
    which is why it is exercised rather than assumed.
    """
    with override_settings(ADMINS=(('Email smoke', to),)):
        mail_admins('Smoke test error report', 'Traceback would go here.')
    return 'SERVER_EMAIL=%s' % settings.SERVER_EMAIL


# Every category maps to a producer. A category added later fails
# core/tests/test_email_smoke.py until it appears here.
COVERED = {
    EmailCategory.REGISTRATION: registration_confirmation,
    EmailCategory.FORGOT_USERNAME: forgot_username,
    EmailCategory.PASSWORD_RESET: password_reset,
    EmailCategory.EMAIL_CHANGE: email_change_both,
    EmailCategory.TOPIC_NOTIFICATION: topic_notification,
    EmailCategory.PM_NOTIFICATION: pm_notification,
    EmailCategory.CONTACT_FORM: contact_form,
    EmailCategory.ADMIN_NOTIFICATION: admin_notification,
    # Nothing sends as UNCATEGORIZED deliberately -- it exists for a caller
    # that forgot one, or a task serialized before the vocabulary did. The
    # wrapper is exercised directly so the default itself is covered.
    EmailCategory.UNCATEGORIZED: lambda to: _uncategorized(to),
}

# Paths that never reach core.functions.send_mail, so they have no category.
UNWRAPPED_PATHS = {
    'django error mail': django_error_mail,
}


def _uncategorized(to):
    """core.functions.send_mail() with no category passed."""
    from core.functions import send_mail
    send_mail('Smoke test uncategorized', 'Body.',
              settings.DEFAULT_FROM_EMAIL, [to])
    return 'core.functions.send_mail default category'


###############################################################################
# Assertions
###############################################################################

def missing_categories():
    return set(EmailCategory) - set(COVERED)


def check_server_email():
    """Django's default sends crash reports from root@localhost.

    A local relay accepted that; a provider will not sign for it. The
    regression would otherwise surface only during an outage, which is the
    worst moment to discover the error channel is refused.
    """
    assert settings.SERVER_EMAIL != 'root@localhost', \
        'SERVER_EMAIL is root@localhost; a provider will reject it'
    return 'SERVER_EMAIL=%s' % settings.SERVER_EMAIL


def check_live_backend():
    """Refuse --live unless mail can actually leave this process.

    Without this the run is a false green, and it was: with no provider
    configured the container falls back to the console backend on
    localhost:1025, so --live printed all ten messages to stdout, announced
    "real messages through localhost", and reported every check passed having
    sent nothing. A tool that exists to tell success from failure must not be
    the thing that confuses them.
    """
    problems = []
    # By class, not by name: the allowlisting backend sends over SMTP too.
    if not issubclass(import_string(settings.EMAIL_BACKEND), SMTPBackend):
        problems.append('EMAIL_BACKEND is %s, which sends nothing off this box'
                        % settings.EMAIL_BACKEND)
    if settings.EMAIL_HOST in ('', 'localhost', '127.0.0.1'):
        problems.append('EMAIL_HOST is %r, not a provider'
                        % settings.EMAIL_HOST)
    if not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        problems.append('EMAIL_HOST_USER/EMAIL_HOST_PASSWORD are empty; '
                        'Postmark wants the server token as both')
    if not settings.EMAIL_USE_TLS:
        problems.append('EMAIL_USE_TLS is off; the credentials would cross '
                        'the wire in the clear')
    if problems:
        raise SystemExit(
            '\n  --live cannot send from this environment:\n'
            + ''.join('    - %s\n' % p for p in problems)
            + '\n  Set the mail variables in .env (task 01 made them all\n'
              '  environmental) and restart the container, then try again.\n'
              '  Without --live the tool still renders every path.')
    return '%s via %s' % (settings.EMAIL_BACKEND.rsplit('.', 2)[-2],
                          settings.EMAIL_HOST)


def require_recipients(recipients):
    """--live with no addresses would fall back to the producers' defaults."""
    if not recipients:
        raise SystemExit('  --live needs at least one recipient address')
    return recipients


def check_email_a_friend_gone():
    """Task 04 deleted the site's only send-to-an-arbitrary-address path.

    A smoke tool that still knows how to exercise a deleted feature is a smoke
    tool nobody updated, so the absence is asserted rather than assumed.
    """
    from django.urls import NoReverseMatch, reverse
    for name in ('news-email_story', 'news-email_friend'):
        try:
            reverse(name)
        except NoReverseMatch:
            continue
        raise AssertionError(
            '%s still resolves; email-a-friend was deleted in task 04' % name)
    return 'no email-a-friend route'


###############################################################################
# Header reading -- the part only a human can start
###############################################################################

# What the 2026-08-12 capture got wrong, and what each should read now. The
# Message-ID entry is the one to read carefully: it is EXPECTED to fail.
HEADER_EXPECTATIONS = """
  spf=pass        envelope is pm-bounces.surfguitar101.com, aligned relaxed
  dkim=pass       header.d=surfguitar101.com (Postmark's selector, not 'dkim')
  dmarc=pass      absent entirely in the 2026-08-12 baseline
  compauth=pass   Microsoft only; reason=100 is the good one
  HELO            Postmark's, never jaguar.deathofagremmie.com
  Message-ID      STILL carries the dead domain -- Django builds it, not
                  Postfix, so neither the interim fix nor Postmark changes it.
                  A pass here would need explaining, not celebrating.
  SCL             Microsoft only. The pre-Postmark capture scored SCL=3 while
                  still reaching the Inbox; record it, because if it does not
                  improve the provider move did not buy what it was for.
"""

DEAD_DOMAIN = 'jaguar.deathofagremmie.com'


def spam_confidence(text):
    """Microsoft's real spam score, which is not the header that looks like it.

    X-MS-Exchange-Organization-SCL read 1 in the 2026-08-17 capture while the
    base64 X-Message-Delivery on the same message decoded to SCL=3. Reading the
    obvious header is how a neutral-reputation message gets recorded as a
    well-trusted one, so the encoded value wins and a disagreement is printed
    rather than resolved silently.
    """
    stated = encoded = None
    for line in text.splitlines():
        low = line.lower()
        if 'x-ms-exchange-organization-scl:' in low:
            stated = line.split(':', 1)[1].strip()
        elif 'x-message-delivery:' in low:
            blob = line.split(':', 1)[1].strip()
            try:
                decoded = base64.b64decode(blob + '===').decode('ascii', 'replace')
            except Exception:
                continue
            for field in decoded.split(';'):
                if field.upper().startswith('SCL='):
                    encoded = field.split('=', 1)[1]
    if encoded == '-1':
        # Not a score. Exchange stamps -1 when the message SKIPPED filtering --
        # a safe-sender list, a contact, or an allow rule at the receiver. It
        # says the recipient trusts this sender, which is not the same claim as
        # the sender having a good reputation, and it cannot be compared with a
        # baseline that was actually scored. A mailbox used for repeated tests
        # acquires this, so the probe ends up measuring its own history.
        return ('-1 -- FILTERING SKIPPED, not a score. This mailbox already '
                'trusts the sender (safe-sender list, contact, or allow rule), '
                'so the message was never scored%s. It measures nothing about '
                'reputation: to see that, use a receiver that has never been '
                'told to trust this sender.'
                % ('' if not stated
                   else '; the org header stamped SCL=%s' % stated))
    if encoded and stated and encoded != stated:
        return ('%s  (X-MS-Exchange-Organization-SCL says %s -- the encoded '
                'one is the real score)' % (encoded, stated))
    return encoded or stated or '<absent>'


def delivered_to(text):
    """Inbox or junk, when Microsoft's mailbox-delivery header is present.

    No SMTP response distinguishes them and most receivers say nothing, but
    Microsoft records dest:I for Inbox and dest:J for Junk. Where it is absent
    this stays unanswered rather than guessing -- a human opens the mailbox.
    """
    for line in text.splitlines():
        if 'dest:' in line.lower():
            dest = line.lower().split('dest:', 1)[1].split(';')[0].strip()
            return {'i': 'Inbox (dest:I)',
                    'j': 'JUNK (dest:J)'}.get(dest, 'dest:%s' % dest)
    return '<no header says; confirm by eye>'


def read_headers(path):
    """Parse a saved header block and report the verdicts it carries.

    The tool cannot fetch these: it has no mailbox at the far end. What it can
    do is stop a human from eyeballing a wall of headers and seeing what they
    expect to see.
    """
    with open(path) as fp:
        text = fp.read()
    lowered = text.lower()

    found = {}
    for key in ('spf', 'dkim', 'dmarc', 'compauth'):
        verdicts = set()
        start = 0
        while True:
            at = lowered.find(key + '=', start)
            if at < 0:
                break
            verdicts.add(lowered[at + len(key) + 1:].split(None, 1)[0].strip(';,'))
            start = at + 1
        found[key] = sorted(verdicts) or ['<absent>']

    for key in ('spf', 'dkim', 'dmarc', 'compauth'):
        print('  %-10s %s' % (key, ', '.join(found[key])))

    scl = spam_confidence(text)
    print('  %-10s %s' % ('SCL', scl))
    print('  %-10s %s' % ('delivered to', delivered_to(text)))

    # Folded continuation lines belong to the header above them, so track the
    # last real header name rather than splitting whatever line matched.
    where, header = [], '?'
    for line in text.splitlines():
        if line[:1] not in (' ', '\t') and ':' in line:
            header = line.split(':', 1)[0]
        if DEAD_DOMAIN in line.lower() and header not in where:
            where.append(header)
    print('  %-10s %s' % ('dead domain', ', '.join(where) or 'absent'))
    if where and where != ['Message-ID']:
        print('  NOTE: %s appears outside Message-ID, which is NOT expected'
              % DEAD_DOMAIN)

    assert 'pass' in found['dmarc'], \
        'no dmarc=pass in these headers -- that is the whole point of the step'
    return 'dmarc=pass present; SCL=%s' % scl


###############################################################################

def main(live_to=None, only=None):
    send_inline()
    check('server email', check_server_email)
    check('email-a-friend gone', check_email_a_friend_gone)
    check('category coverage',
          lambda: 'all %d covered' % len(EmailCategory)
          if not missing_categories()
          else _raise('categories with no smoke coverage: %s'
                      % sorted(missing_categories())))

    paths = every_path(only)          # validates --only before anything prints
    if live_to:
        check_live_backend()
    recipients = require_recipients(live_to) if live_to else ['nobody@example.com']

    # Pass one always runs, and always into locmem under the sentinel. It is
    # what makes a live send safe: a template with a hole in it is caught here,
    # before anything is put on the wire. Rendering strictly during the live
    # pass instead would mail the sentinel to a real person, and with no outbox
    # to inspect nothing would notice.
    print('\n== rendering %s, nothing sent'
          % ('every path' if only is None else only))
    with override_settings(EMAIL_BACKEND=LOCMEM,
                           TEMPLATES=strict_templates()):
        for label, producer in paths:
            for to in recipients:
                check('%s -> %s' % (label, to),
                      lambda p=producer, t=to: render_and_inspect(p, t))

    if live_to:
        if [r for r in results if not r[0]]:
            raise SystemExit('\n  rendering failed above; nothing was sent')
        print('\n== LIVE -- real messages through %s, ordinary templates'
              % check_live_backend())
        for label, producer in paths:
            for to in recipients:
                check('%s -> %s (live)' % (label, to),
                      lambda p=producer, t=to: p(t))

    if live_to:
        print('\nNow read the headers. What to look for:')
        print(HEADER_EXPECTATIONS)
        print('  Inbox or junk is not in any header and no SMTP response '
              'reveals it.\n  Confirm it by eye, in each mailbox.')
        print('\n  Save a header block and run:')
        print('    python /app/tools/email_smoke.py --check-headers FILE')


def every_path(only=None):
    """Every producer with a printable label: the categories, then the paths
    that carry none.

    `only` narrows the run to one label. A first live send against a young
    sending reputation is better as one message than ten, and a re-test after
    fixing one path should not mail the other nine.
    """
    paths = [(str(category), producer)
             for category, producer in sorted(COVERED.items())]
    paths += sorted(UNWRAPPED_PATHS.items())
    if only is None:
        return paths
    chosen = [(label, producer) for label, producer in paths if label == only]
    if not chosen:
        raise SystemExit('  --only %r matches nothing. Choose one of:\n%s'
                         % (only, ''.join('    %s\n' % label
                                          for label, _ in paths)))
    return chosen


def render_and_inspect(producer, to):
    """Run one producer into locmem and check what it actually rendered."""
    from django.core import mail as mail_module
    before = len(getattr(mail_module, 'outbox', []))
    detail = producer(to)
    for message in getattr(mail_module, 'outbox', [])[before:]:
        assert_no_missing_variables(message)
    return detail


def _raise(message):
    raise AssertionError(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--live', nargs='+', metavar='ADDRESS', default=None,
        help='SEND REAL MAIL through the configured provider to these '
             'addresses; include an Outlook.com or Hotmail one, which is the '
             'acceptance test (see the module docstring)')
    parser.add_argument(
        '--check-headers', metavar='FILE', default=None,
        help='parse a saved header block from a received message and report '
             'its spf/dkim/dmarc verdicts, SCL, and whether the dead domain '
             'appears anywhere but Message-ID')
    parser.add_argument(
        '--only', metavar='PATH', default=None,
        help='run one path instead of all of them, named as it appears in the '
             'output (e.g. registration); a first live send is better as one '
             'message than ten')
    args = parser.parse_args()

    if args.check_headers:
        check('headers', lambda: read_headers(args.check_headers))
    else:
        backend = settings.EMAIL_BACKEND if args.live else LOCMEM
        with override_settings(EMAIL_BACKEND=backend):
            main(live_to=args.live, only=args.only)

    failed = [r for r in results if not r[0]]
    print('\n%d/%d checks passed' % (len(results) - len(failed), len(results)))
    sys.exit(1 if failed else 0)
