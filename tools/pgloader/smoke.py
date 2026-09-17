"""Smoke the running site against a converted database, reads and writes.

The unit suite runs against an empty schema and cannot speak to any of this.
The lesson that produced this script is that a green suite has already missed
whole classes of breakage on this project -- management commands that only
failed under a real worker, and a char(2) column that returned two spaces
instead of an empty string and crashed 12,854 profile pages while every test
passed.

Reads are only half of it. A converted database can serve every page and still
be unable to accept a new row: sequences left behind their table's MAX(pk)
collide on the first insert, and nothing but an insert will show it. So this
logs in and actually posts, messages and uploads, then checks the new content
comes back out, then removes what it made.

Everything is done over HTTP against the running server rather than through
the test client, so middleware, sessions, the cache and the template layer are
all in the path -- the same way a member would meet the site.

What it creates it removes again, but it cannot un-read a page: browsing
writes sessions and raises topic view counters. Run verify_data.py and the
dumpdata cross-check first, while the converted database still matches its
source exactly.

Run inside the web container, with the stack up on the database under test:

    docker compose exec -T web python tools/pgloader/smoke.py

Exits non-zero if any check fails.
"""
import os
import re
import sys
import uuid

import django

# sys.path[0] is this file's directory, not the project root, so the settings
# package is not importable without help.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.dev')
django.setup()

import requests  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.urls import reverse  # noqa: E402

BASE = os.environ.get('SMOKE_BASE_URL', 'http://localhost:8000')

# A scratch account, made and removed by this script. Real accounts cannot be
# used: their password hashes are production secrets and nobody knows the
# passwords behind them.
SMOKE_USER = 'pgsmoke_user'
SMOKE_PASSWORD = 'sm0ke-test-pw'

# Read-only pages. The list is the smoke checklist the earlier steps used,
# plus the pages the conversion specifically put at risk: a profile with no
# country set (the char(2) bug), and a band map entry carrying cp1252 text.
READ_PAGES = [
    ('/', 'home'),
    ('/forums/', 'forums index'),
    # There is no /news/ index; the stories live under /news/date/.
    ('/news/date/', 'news'),
    ('/podcast/', 'podcast'),
    ('/links/', 'links'),
    ('/downloads/', 'downloads'),
    ('/bandmap/', 'band map'),
    ('/calendar/', 'calendar'),
    ('/potd/', 'photo of the day'),
    ('/polls/', 'polls'),
    ('/donations/', 'donations'),
    ('/search/', 'search'),
    ('/accounts/login/', 'login'),
    ('/accounts/password/reset/', 'password reset'),
    # A RedirectView into the member flow: the admin's own reset views were
    # never fully wired up.
    ('/admin/password_reset/', 'admin password reset'),
    ('/admin/', 'admin'),
]


class Failure(Exception):
    pass


# The debug toolbar's redirects panel is enabled in this stack, and it answers
# a 302 with a 200 carrying an interstitial page instead. That is the toolbar
# working as intended, but it hides exactly the status codes a smoke test
# reads, so unwrap it and report the redirect underneath.
TOOLBAR_REDIRECT = re.compile(r'id="redirect_to" href="([^"]+)"')


def status_of(resp):
    """The real status and location, seen past the toolbar's interstitial."""
    if resp.status_code == 200:
        match = TOOLBAR_REDIRECT.search(resp.text)
        if match:
            return 302, match.group(1)
    return resp.status_code, resp.headers.get('Location')


def visit(session, url, hops=5):
    """GET a page, following redirects the toolbar has disguised as 200s.

    requests cannot follow those on its own, so several pages that really do
    serve would otherwise be recorded as redirects that went nowhere.
    """
    for _ in range(hops):
        resp = session.get(url, allow_redirects=False)
        status, location = status_of(resp)
        if status not in (301, 302, 303, 307, 308) or not location:
            return resp, status
        url = location if location.startswith('http') else BASE + location
    raise Failure('%s redirected more than %d times' % (url, hops))


def csrf(session, url):
    """Fetch a page and return the CSRF token its form carries."""
    resp = session.get(url)
    if resp.status_code != 200:
        raise Failure('%s returned %d while fetching a CSRF token'
                      % (url, resp.status_code))
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
    if not match:
        raise Failure('no CSRF token in the form at %s' % url)
    return match.group(1)


def post(session, url, data, referer=None):
    """POST a form and return the response without following any redirect.

    allow_redirects=False is load-bearing: requests follows redirects on POST
    by default, so a successful login would return the 200 it landed on rather
    than the 302 that got it there, and every "expect a 302" check here would
    fail on a working site. That went unnoticed for as long as the debug
    toolbar's RedirectsPanel was enabled, because it turned redirects into 200
    interstitials that requests could not follow -- so these assertions were
    being carried by a dev-only panel, and started failing the moment it was
    switched off. status_of() still reads the interstitial, for anyone running
    with that panel back on.
    """
    data = dict(data, csrfmiddlewaretoken=csrf(session, referer or url))
    return session.post(url, data=data, headers={'Referer': referer or url},
                        allow_redirects=False)


def check_reads(session, results):
    for path, label in READ_PAGES:
        _, status = visit(session, BASE + path)
        results.append((status == 200, 'read  %-34s %s' % (label, status)))

    # The admin must not serve itself to an anonymous visitor.
    resp = session.get(BASE + '/admin/', allow_redirects=False)
    status, location = status_of(resp)
    results.append((status == 302 and 'login' in (location or ''),
                    'read  %-34s %s -> %s' % ('admin bounces anonymous users',
                                              status, location)))


def check_risky_pages(session, results):
    """The pages this conversion put at specific risk."""
    from bio.models import UserProfile
    from bandmap.models import BandEntry
    from forums.models import Topic

    profile = UserProfile.objects.filter(country='').select_related('user') \
                                 .first()
    if profile:
        resp = session.get('%s/profile/view/%s/'
                           % (BASE, profile.user.username))
        results.append((resp.status_code == 200,
                        'read  %-34s %s' % ('profile with no country set',
                                            resp.status_code)))

    topic = Topic.objects.order_by('-id').first()
    if topic:
        resp = session.get('%s/forums/topic/%d/' % (BASE, topic.id))
        results.append((resp.status_code == 200,
                        'read  %-34s %s' % ('a real forum topic',
                                            resp.status_code)))

    # A band whose name only reads back correctly if the cp1252 decoding was
    # right; the map page is a shell, so ask the endpoint that feeds it. The
    # response is JSON with non-ASCII escaped, so it is decoded rather than
    # searched as text.
    band = BandEntry.objects.filter(name__contains='™', is_approved=True) \
                            .first()
    if band:
        resp = session.get(BASE + '/bandmap/query/')
        try:
            names = {entry.get('name') for entry in resp.json()}
        except ValueError:
            names = set()
        results.append((resp.status_code == 200 and band.name in names,
                        'read  %-34s %s' % ('cp1252 band name in map data',
                                            band.name)))


def check_login(session, results):
    url = BASE + reverse('accounts-login')
    resp = post(session, url, {'username': SMOKE_USER,
                               'password': SMOKE_PASSWORD})
    status, location = status_of(resp)
    # A rejected login re-renders the form with a 200; only a redirect means
    # the credentials were accepted. The cookie is renamed in settings, so
    # looking for Django's default name would never find it.
    from django.conf import settings
    ok = status == 302 and settings.SESSION_COOKIE_NAME in session.cookies
    results.append((ok, 'auth  %-34s %s -> %s' % ('log in', status, location)))
    if not ok:
        raise Failure('could not log in as the smoke user; the write checks '
                      'cannot run')


def check_password_reset(anon, session, results):
    """The two ways a password gets changed: reset by email when it has been
    forgotten, and change-while-logged-in.

    Mail is not the subject here -- the console backend prints to the web
    container's log rather than sending. What is being tested is the part that
    touches the database: finding the account by address, and writing a new
    hash back.
    """
    user = User.objects.get(username=SMOKE_USER)
    resp = post(anon, BASE + '/accounts/password/reset/',
                {'email': user.email})
    status, location = status_of(resp)
    results.append((status == 302,
                    'auth  %-34s %s -> %s' % ('password reset by email',
                                              status, location)))

    new_password = SMOKE_PASSWORD + '-changed'
    resp = post(session, BASE + '/accounts/password/',
                {'old_password': SMOKE_PASSWORD,
                 'new_password1': new_password,
                 'new_password2': new_password})
    status, location = status_of(resp)
    changed = User.objects.get(username=SMOKE_USER) \
                          .check_password(new_password)
    results.append((status == 302 and changed,
                    'auth  %-34s %s -> %s' % ('password change while logged '
                                              'in', status, location)))


def check_write_post(session, results):
    """Create a topic, which inserts into forums_topic and forums_post and
    touches the denormalized counters the forums app keeps."""
    from forums.models import Forum, Topic

    forum = Forum.objects.get(slug='surf-music')
    marker = 'pg-smoke-%s' % uuid.uuid4().hex[:12]
    url = '%s/forums/forum/%s/new-topic/' % (BASE, forum.slug)
    resp = post(session, url, {'name': 'Smoke test %s' % marker,
                               'body': 'Body for %s' % marker})

    topic = Topic.objects.filter(name__contains=marker).first()
    results.append((topic is not None,
                    'write %-34s %s' % ('create forum topic + post',
                                        resp.status_code)))
    if not topic:
        return

    view = session.get('%s/forums/topic/%d/' % (BASE, topic.id))
    results.append((view.status_code == 200 and marker in view.text,
                    'write %-34s %s' % ('new post displays',
                                        view.status_code)))


def check_write_message(session, results):
    """Send a private message to another real account."""
    from messages.models import Message

    recipient = User.objects.exclude(username=SMOKE_USER) \
                            .filter(is_active=True).order_by('id').first()
    marker = 'pg-smoke-%s' % uuid.uuid4().hex[:12]
    url = BASE + '/messages/compose/'
    resp = post(session, url, {'receiver': recipient.username,
                               'subject': 'Smoke %s' % marker,
                               'message': 'Message body %s' % marker})

    msg = Message.objects.filter(subject__contains=marker).first()
    results.append((msg is not None,
                    'write %-34s %s' % ('send private message',
                                        resp.status_code)))
    if msg:
        out = session.get(BASE + '/messages/outbox/')
        results.append((out.status_code == 200 and marker in out.text,
                        'write %-34s %s' % ('message appears in outbox',
                                            out.status_code)))


def check_write_photo(session, results):
    """Insert a user photo.

    The upload view sends the image to S3 before it writes the row, and there
    are no working S3 credentials in a dev environment -- that leg belongs to
    the object-storage work, not to this database. What is exercised here is
    the part the conversion could have broken: the insert itself, against a
    sequence that pgloader reset, and the page that renders the result.
    """
    from user_photos.models import Photo

    user = User.objects.get(username=SMOKE_USER)
    marker = uuid.uuid4().hex[:12]
    photo = Photo.objects.create(
        user=user,
        url='https://example.invalid/%s.jpg' % marker,
        thumb_url='https://example.invalid/%s_thumb.jpg' % marker)
    results.append((photo.pk is not None,
                    'write %-34s pk=%s' % ('insert user photo', photo.pk)))

    resp, status = visit(session, '%s/user_photos/gallery/%s/'
                         % (BASE, SMOKE_USER))
    results.append((status == 200 and marker in resp.text,
                    'write %-34s %s' % ('new photo shows in the gallery',
                                        status)))

    detail, status = visit(session, '%s/user_photos/photo/%d/'
                           % (BASE, photo.pk))
    results.append((status == 200,
                    'write %-34s %s' % ('photo detail page', status)))


def check_admin(session, results):
    """The admin, logged in as a superuser, over a few of its pages."""
    user = User.objects.get(username=SMOKE_USER)
    user.is_staff = user.is_superuser = True
    user.save()

    admin_session = requests.Session()
    post(admin_session, BASE + reverse('accounts-login'),
         {'username': SMOKE_USER, 'password': SMOKE_PASSWORD})
    for path, label in [('/admin/', 'admin index'),
                        ('/admin/auth/user/', 'admin user list'),
                        ('/admin/forums/topic/', 'admin topic list'),
                        ('/admin/news/story/', 'admin news list')]:
        resp = admin_session.get(BASE + path)
        results.append((resp.status_code == 200,
                        'admin %-34s %s' % (label, resp.status_code)))


def check_debug_toolbar(session, results):
    resp = session.get(BASE + '/')
    results.append(('djDebug' in resp.text,
                    'misc  %-34s %s' % ('debug toolbar renders',
                                        'present' if 'djDebug' in resp.text
                                        else 'MISSING')))


def setup_user():
    remove_smoke_user()
    return User.objects.create_user(SMOKE_USER, 'pgsmoke@example.invalid',
                                    SMOKE_PASSWORD)


def delete_topic(topic):
    """Delete a topic the way the forums app does it.

    Forum.last_post and Topic.last_post are OneToOneFields to Post with the
    default on_delete=CASCADE, which points the wrong way round: deleting the
    post a forum happens to point at takes the forum -- and therefore every
    topic and post inside it -- with it. The app has carried
    last_post_pre_delete() for years to step around that, and anything
    removing a post has to use it.
    """
    forum = topic.forum
    if forum.last_post and forum.last_post.topic_id == topic.id:
        forum.last_post_pre_delete(deleting_topic=True)
        forum.save()
    topic.delete()
    forum.sync()
    forum.save()


def purge_smoke_content(user):
    """Remove everything the scratch account owns, in an order the database
    will accept.

    This runs at the start of a run as much as at the end: a run that dies
    part way through -- or is killed -- leaves content behind, and the next
    run has to be able to pick up after it without a person intervening.
    """
    from forums.models import Forum, Post, Topic
    from messages.models import Message
    from user_photos.models import Photo

    for topic in Topic.objects.filter(user=user):
        delete_topic(topic)

    # Replies the account left in other people's topics. Both the topic and
    # the forum may be pointing at one, and each has to be moved off it first.
    stray = Post.objects.filter(user=user).select_related('topic',
                                                          'topic__forum')
    touched_topics, touched_forums = set(), set()
    for post in stray:
        topic, forum = post.topic, post.topic.forum
        if topic.last_post_id == post.id:
            topic.last_post_pre_delete()
            topic.save()
        if forum.last_post_id == post.id:
            forum.last_post_pre_delete()
            forum.save()
        post.delete()
        touched_topics.add(topic.id)
        touched_forums.add(forum.id)

    for topic in Topic.objects.filter(id__in=touched_topics):
        topic.post_count_update()
        topic.save()
    for forum in Forum.objects.filter(id__in=touched_forums):
        forum.sync()
        forum.save()

    Message.objects.filter(sender=user).delete()
    Message.objects.filter(receiver=user).delete()
    Photo.objects.filter(user=user).delete()


def remove_smoke_user():
    """Delete the scratch account, once nothing large hangs off it.

    A plain delete() here once proposed to take 6,686 topics and 98,450 posts
    with it, because the account's one new post had become a forum's
    last_post. So the content goes first, by a route that repoints those
    references, and the cascade is measured before it is allowed to run.
    """
    from django.db import router
    from django.db.models.deletion import Collector

    user = User.objects.filter(username=SMOKE_USER).first()
    if not user:
        return

    purge_smoke_content(user)

    collector = Collector(using=router.db_for_write(User))
    collector.collect([user])
    oversized = {model.__name__: len(objs)
                 for model, objs in collector.data.items() if len(objs) > 5}
    if oversized:
        raise Failure('refusing to delete the smoke user: even after clearing '
                      'its content, deleting it would cascade to %s' % oversized)
    user.delete()


def teardown():
    """Leave the database as it was found, so the row counts verified before
    this ran still hold and the script can be run again.

    Everything the run creates is owned by the scratch account, so removing
    that account is the whole job -- the same path setup uses to recover from
    a previous run that did not finish.
    """
    try:
        remove_smoke_user()
    except Failure as exc:
        print('  cleanup: %s' % exc)


def main():
    from django.db import connection
    print('smoking %s against %s/%s\n'
          % (BASE, connection.vendor, connection.settings_dict['NAME']))

    results = []
    anon = requests.Session()
    session = requests.Session()
    try:
        setup_user()
        check_reads(anon, results)
        check_risky_pages(anon, results)
        check_debug_toolbar(anon, results)
        check_login(session, results)
        check_password_reset(anon, session, results)
        check_write_post(session, results)
        check_write_message(session, results)
        check_write_photo(session, results)
        check_admin(session, results)
    except Failure as exc:
        results.append((False, 'ABORTED: %s' % exc))
    finally:
        teardown()

    for ok, line in results:
        print('  %s %s' % ('ok  ' if ok else 'FAIL', line))

    failed = [line for ok, line in results if not ok]
    print()
    if failed:
        print('FAILED -- %d check(s):' % len(failed))
        for line in failed:
            print('  %s' % line)
        return 1
    print('OK -- %d checks passed, reads and writes' % len(results))
    return 0


if __name__ == '__main__':
    sys.exit(main())
