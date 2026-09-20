"""What each application records as the client's address, behind the proxy.

Six applications read ``REMOTE_ADDR`` directly to record who did something.
Behind a reverse proxy that value is the proxy, and ``RealClientIP`` replaces
it with the address the proxy worked out. These drive the real views with the
header set and read back what was stored or logged, so that a reader added or
moved later is covered by the same claim in one place rather than by a habit.

``REMOTE_ADDR`` is set to the proxy's own compose address in each request, so a
test that passes because the middleware did nothing is not possible: the value
asserted is never the one the request arrived with.
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from comments.models import Comment
from downloads.models import AllowedExtension, Category, PendingDownload
from forums.models import Forum, Post, Topic
from potd.models import Current, Photo


PROXY = '172.19.0.7'        # what the request arrives with
CLIENT = '198.51.100.7'     # what the proxy says the client is
CLIENT6 = '2606:4700:4700::1111'

PROXIED = {'REMOTE_ADDR': PROXY, 'HTTP_X_REAL_IP': CLIENT}
PROXIED6 = {'REMOTE_ADDR': PROXY, 'HTTP_X_REAL_IP': CLIENT6}

# Production puts RealClientIP first; these run the suite's own chain with it
# prepended, so the views under test are reached the way production reaches
# them.
MIDDLEWARE = ['core.middleware.RealClientIP'] + list(settings.MIDDLEWARE)


@override_settings(MIDDLEWARE=MIDDLEWARE)
class ProxiedClientAddressTests(TestCase):
    """The readers that persist an address to the database."""

    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', 'pjmoto@example.com', 'pw')
        self.assertTrue(self.client.login(username='pjmoto', password='pw'))

    def test_comment_records_the_client(self):
        photo = Photo.objects.create(pk=8192, user=self.user,
                                     date_added=timezone.now())
        Current.objects.create(pk=1, potd=photo)

        with patch('comments.views.antispam.utils.spam_check', return_value=False):
            response = self.client.post(reverse('comments-post'), data={
                'content_type': 'potd.Photo',
                'object_pk': '8192',
                'comment': 'Nice',
            }, **PROXIED)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.get().ip_address, CLIENT)

    def test_forum_topic_records_the_client(self):
        forum = Forum.objects.get(slug='shallow-end')

        with patch('forums.views.main.antispam.utils.spam_check',
                   return_value=False):
            response = self.client.post(
                reverse('forums-new_topic', kwargs={'slug': forum.slug}),
                {'name': 'A topic', 'body': 'the first post'}, **PROXIED)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.get().user_ip, CLIENT)

    def test_forum_post_records_an_ipv6_client(self):
        """The address columns are GenericIPAddressField, so the family the
        visitor arrived on is not supposed to matter -- and after this it
        does not."""
        forum = Forum.objects.get(slug='shallow-end')
        topic = Topic.objects.create(forum=forum, name='A topic', user=self.user)
        first = Post.objects.create(topic=topic, user=self.user, body='first')
        topic.last_post = first
        topic.save()

        with patch('forums.views.main.antispam.utils.spam_check',
                   return_value=False):
            response = self.client.post(
                reverse('forums-new_post', kwargs={'topic_id': topic.id}),
                {'body': 'a reply'}, **PROXIED6)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.exclude(pk=first.pk).get().user_ip, CLIENT6)

    def test_download_records_the_client(self):
        AllowedExtension.objects.create(extension='.mp3')
        category = Category.objects.create(title='Surf', slug='surf')

        response = self.client.post(reverse('downloads-add'), {
            'title': 'A track',
            'category': category.pk,
            'description': 'A description',
            'file': SimpleUploadedFile('track.mp3', b'not really an mp3'),
        }, **PROXIED)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PendingDownload.objects.get().ip_address, CLIENT)


@override_settings(MIDDLEWARE=MIDDLEWARE)
class ProxiedClientAddressLoggingTests(TestCase):
    """The readers that record the address in a log line.

    ``auth.log`` is what fail2ban reads and what the registration-spam analysis
    ran on, so the address in these lines is the one that has to be the
    visitor's.

    Logging is disabled wholesale by the test settings, so it is enabled around
    each assertion and restored afterwards; see ``contact/tests/test_views.py``.
    """

    def assertLogsWithLoggingEnabled(self, logger, level):
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)
        return self.assertLogs(logger, level)

    def test_failed_login_logs_the_client(self):
        with self.assertLogsWithLoggingEnabled('auth', 'ERROR') as captured:
            self.client.post(reverse('accounts-login'), {
                'username': 'nobody',
                'password': 'wrong',
            }, **PROXIED)

        self.assertIn('Login failure from [%s]' % CLIENT, '\n'.join(captured.output))
        self.assertNotIn(PROXY, '\n'.join(captured.output))

    def test_failed_registration_logs_the_client(self):
        with self.assertLogsWithLoggingEnabled('auth', 'ERROR') as captured:
            self.client.post(reverse('accounts-register'), {}, **PROXIED)

        self.assertIn('Register failure from [%s]' % CLIENT, '\n'.join(captured.output))
        self.assertNotIn(PROXY, '\n'.join(captured.output))
