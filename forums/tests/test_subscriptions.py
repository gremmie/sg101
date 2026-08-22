"""
Characterization tests for forum topic subscriptions and favorites.

Subscriptions drive the "new reply" email notifications; favorites are personal
bookmarks. The two view modules are near-parallel, but differ in one telling way:
subscribing to an inaccessible topic raises Http404 while favoriting one returns
403 -- both are pinned below.
"""
import logging

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.urls import reverse
from django.test import TestCase

from forums.models import Forum, Post, Topic
from forums.views.subscriptions import notify_topic_subscribers


def make_topic(forum, user, name='a topic'):
    topic = Topic.objects.create(forum=forum, name=name, user=user)
    post = Post.objects.create(topic=topic, user=user, body='first post')
    topic.last_post = post
    topic.save()
    return topic


class SubscriptionTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        # forums.permissions caches category group membership in the LocMem
        # cache, which persists across tests; clear it so can_access sees the
        # current groups.
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.member = User.objects.create_user('member', '', 'pw')
        self.topic = make_topic(self.forum, self.author)
        self.client.login(username='member', password='pw')

    def tearDown(self):
        cache.clear()

    def test_subscribe_adds_user(self):
        response = self.client.post(
            reverse('forums-subscribe_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.member, self.topic.subscribers.all())

    def test_subscribe_requires_post(self):
        response = self.client.get(
            reverse('forums-subscribe_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 405)

    def test_subscribe_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse('forums-subscribe_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 302)  # -> login

    def test_subscribe_to_inaccessible_topic_is_404(self):
        secret = Group.objects.create(name='Inner Circle')
        self.forum.category.groups.add(secret)
        response = self.client.post(
            reverse('forums-subscribe_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(self.member, self.topic.subscribers.all())

    def test_the_notification_is_categorized(self):
        # setUp's member has no email address, and the wrapper drops empty
        # recipients before it sends anything.
        self.member.email = 'member@example.com'
        self.member.save()
        self.topic.subscribers.add(self.member)
        reply = Post.objects.create(topic=self.topic, user=self.author,
                                    body='a reply')

        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            notify_topic_subscribers(reply, defer=False)

        self.assertIn('category=topic_notification', logged.output[0])

    def test_unsubscribe_removes_user(self):
        self.topic.subscribers.add(self.member)
        response = self.client.post(
            reverse('forums-unsubscribe_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.member, self.topic.subscribers.all())

    def test_subscription_status_reflects_state(self):
        self.topic.subscribers.add(self.member)
        response = self.client.get(
            reverse('forums-subscription_status', args=[self.topic.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_subscribed'])

    def test_manage_subscriptions_lists_and_deletes(self):
        self.topic.subscribers.add(self.member)

        get_resp = self.client.get(reverse('forums-manage_subscriptions'))
        self.assertEqual(get_resp.status_code, 200)

        self.client.post(reverse('forums-manage_subscriptions'),
                         {'delete_ids': [str(self.topic.id)]})
        self.assertNotIn(self.member, self.topic.subscribers.all())

    def test_manage_subscriptions_delete_all(self):
        self.topic.subscribers.add(self.member)
        self.client.post(reverse('forums-manage_subscriptions'),
                         {'delete_all': '1'})
        self.assertEqual(self.member.subscriptions.count(), 0)


class FavoriteTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.member = User.objects.create_user('member', '', 'pw')
        self.topic = make_topic(self.forum, self.author)
        self.client.login(username='member', password='pw')

    def tearDown(self):
        cache.clear()

    def test_favorite_adds_bookmark(self):
        response = self.client.post(
            reverse('forums-favorite_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.member, self.topic.bookmarkers.all())

    def test_favorite_requires_post(self):
        response = self.client.get(
            reverse('forums-favorite_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 405)

    def test_favorite_inaccessible_topic_is_forbidden(self):
        # Note: favorite returns 403 here, whereas subscribe raises 404.
        secret = Group.objects.create(name='Inner Circle')
        self.forum.category.groups.add(secret)
        response = self.client.post(
            reverse('forums-favorite_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(self.member, self.topic.bookmarkers.all())

    def test_unfavorite_removes_bookmark(self):
        self.topic.bookmarkers.add(self.member)
        response = self.client.post(
            reverse('forums-unfavorite_topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.member, self.topic.bookmarkers.all())

    def test_favorites_status_reflects_state(self):
        self.topic.bookmarkers.add(self.member)
        response = self.client.get(
            reverse('forums-favorites_status', args=[self.topic.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_favorite'])

    def test_manage_favorites_lists_and_deletes(self):
        self.topic.bookmarkers.add(self.member)

        get_resp = self.client.get(reverse('forums-manage_favorites'))
        self.assertEqual(get_resp.status_code, 200)

        self.client.post(reverse('forums-manage_favorites'),
                         {'delete_ids': [str(self.topic.id)]})
        self.assertNotIn(self.member, self.topic.bookmarkers.all())

    def test_manage_favorites_delete_all(self):
        self.topic.bookmarkers.add(self.member)
        self.client.post(reverse('forums-manage_favorites'), {'delete_all': '1'})
        self.assertEqual(self.member.favorite_topics.count(), 0)
