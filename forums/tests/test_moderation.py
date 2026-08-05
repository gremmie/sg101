"""
Characterization tests for forums moderator actions and spam tools.

These lock in the *effects* of the moderator-only views -- the destructive and
state-changing operations (stick/lock/move/split topics, bulk moderation, and
deactivating spammers / promoting strangers). The permission gating on these
views is covered separately in test_permissions; here a moderator (superuser)
performs the action and we assert what actually changed.
"""
import datetime

import bio.models
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from forums.models import Forum, Post, Topic


DAY = datetime.timedelta(days=1)


def make_topic(forum, user, name='a topic', locked=False, sticky=False):
    topic = Topic.objects.create(forum=forum, name=name, user=user,
                                 locked=locked, sticky=sticky)
    return topic


def add_post(topic, user, when=None, body='a post'):
    post = Post.objects.create(topic=topic, user=user, body=body)
    if when is not None:
        post.creation_date = when
        post.update_date = when
        post.save()
    topic.post_count_update()
    topic.save()
    topic.forum.post_count_update()
    topic.forum.save()
    return Post.objects.get(pk=post.pk)


class ModTopicActionTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.other_forum = Forum.objects.get(slug='gear')
        self.author = User.objects.create_user('author', '', 'pw')
        self.admin = User.objects.create_superuser('admin', 'a@example.com', 'pw')
        self.assertTrue(self.client.login(username='admin', password='pw'))

    def test_stick_toggles_sticky(self):
        topic = make_topic(self.forum, self.author)
        add_post(topic, self.author)
        self.assertFalse(topic.sticky)

        response = self.client.get(reverse('forums-mod_topic_stick', args=[topic.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.get(pk=topic.id).sticky)

    def test_move_topic_changes_forum(self):
        topic = make_topic(self.forum, self.author)
        add_post(topic, self.author)

        # The form page renders...
        get_resp = self.client.get(reverse('forums-mod_topic_move', args=[topic.id]))
        self.assertEqual(get_resp.status_code, 200)

        # ...and moving re-parents the topic.
        response = self.client.post(reverse('forums-mod_topic_move', args=[topic.id]),
                                    {'forums': self.other_forum.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Topic.objects.get(pk=topic.id).forum, self.other_forum)

    def test_split_selected_posts_to_new_topic(self):
        topic = make_topic(self.forum, self.author, name='Original')
        add_post(topic, self.author, when=datetime.datetime.now() - 3 * DAY)
        reply2 = add_post(topic, self.author, when=datetime.datetime.now() - 2 * DAY)
        reply3 = add_post(topic, self.author, when=datetime.datetime.now() - 1 * DAY)

        response = self.client.post(
            reverse('forums-mod_topic_split', args=[topic.id]),
            {'name': 'Split Off', 'forums': self.forum.id,
             'post_ids': [str(reply2.id), str(reply3.id)]})
        self.assertEqual(response.status_code, 302)

        new_topic = Topic.objects.get(name='Split Off')
        self.assertEqual(new_topic.post_count, 2)
        self.assertEqual(Topic.objects.get(pk=topic.id).post_count, 1)
        self.assertEqual(Post.objects.get(pk=reply2.id).topic, new_topic)

    def test_split_at_moves_post_and_following(self):
        topic = make_topic(self.forum, self.author, name='Original')
        add_post(topic, self.author, when=datetime.datetime.now() - 3 * DAY)
        reply2 = add_post(topic, self.author, when=datetime.datetime.now() - 2 * DAY)
        add_post(topic, self.author, when=datetime.datetime.now() - 1 * DAY)

        response = self.client.post(
            reverse('forums-mod_topic_split', args=[topic.id]),
            {'name': 'Tail', 'forums': self.forum.id,
             'post_ids': [str(reply2.id)], 'split-at': 'on'})
        self.assertEqual(response.status_code, 302)

        # reply2 and everything created at/after it moved to the new topic.
        new_topic = Topic.objects.get(name='Tail')
        self.assertEqual(new_topic.post_count, 2)
        self.assertEqual(Topic.objects.get(pk=topic.id).post_count, 1)

    def test_split_by_non_moderator_redirects_without_splitting(self):
        # Unlike most mod views (which 403), mod_topic_split redirects a
        # non-moderator back to the topic and does nothing.
        topic = make_topic(self.forum, self.author, name='Original')
        add_post(topic, self.author)
        reply = add_post(topic, self.author)
        User.objects.create_user('member', '', 'pw')
        self.client.logout()
        self.client.login(username='member', password='pw')

        response = self.client.post(
            reverse('forums-mod_topic_split', args=[topic.id]),
            {'name': 'Nope', 'forums': self.forum.id,
             'post_ids': [str(reply.id)]})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Topic.objects.filter(name='Nope').exists())


class ModForumBulkTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.other_forum = Forum.objects.get(slug='gear')
        self.author = User.objects.create_user('author', '', 'pw')
        self.admin = User.objects.create_superuser('admin', 'a@example.com', 'pw')
        self.t1 = make_topic(self.forum, self.author, name='t1')
        add_post(self.t1, self.author)
        self.t2 = make_topic(self.forum, self.author, name='t2')
        add_post(self.t2, self.author)
        self.url = reverse('forums-mod_forum', kwargs={'slug': self.forum.slug})

    def test_non_moderator_is_forbidden(self):
        User.objects.create_user('member', '', 'pw')
        self.client.login(username='member', password='pw')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_moderator_page_renders(self):
        self.client.login(username='admin', password='pw')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_bulk_sticky(self):
        self.client.login(username='admin', password='pw')
        self.client.post(self.url, {'topic_ids': [str(self.t1.id), str(self.t2.id)],
                                    'sticky': '1'})
        self.assertTrue(Topic.objects.get(pk=self.t1.id).sticky)
        self.assertTrue(Topic.objects.get(pk=self.t2.id).sticky)

    def test_bulk_lock(self):
        self.client.login(username='admin', password='pw')
        self.client.post(self.url, {'topic_ids': [str(self.t1.id), str(self.t2.id)],
                                    'lock': '1'})
        self.assertTrue(Topic.objects.get(pk=self.t1.id).locked)
        self.assertTrue(Topic.objects.get(pk=self.t2.id).locked)

    def test_bulk_delete(self):
        self.client.login(username='admin', password='pw')
        self.client.post(self.url, {'topic_ids': [str(self.t1.id), str(self.t2.id)],
                                    'delete': '1'})
        self.assertFalse(Topic.objects.filter(pk__in=[self.t1.id, self.t2.id]).exists())

    def test_bulk_move(self):
        self.client.login(username='admin', password='pw')
        self.client.post(self.url, {'topic_ids': [str(self.t1.id)],
                                    'move': '1', 'forums': str(self.other_forum.id)})
        self.assertEqual(Topic.objects.get(pk=self.t1.id).forum, self.other_forum)

    def test_the_move_control_is_a_bare_select(self):
        """
        The control bar renders the destination field and nothing that belongs
        to a table, since the bar is a <div>. Whole-form rendering would supply
        the wrapper, and which wrapper it supplies changes between releases.

        """
        self.client.login(username='admin', password='pw')
        controls = self._controls(self.client.get(self.url))
        self.assertIn('<select name="forums"', controls)
        for markup in ['<tr', '<th', '<td', '<div', '<label']:
            self.assertNotIn(markup, controls)

    def test_a_move_with_no_destination_shows_the_error(self):
        """The field error has to survive rendering the field on its own."""
        self.client.login(username='admin', password='pw')
        response = self.client.post(self.url, {'topic_ids': [str(self.t1.id)],
                                               'move': '1'})
        self.assertEqual(response.status_code, 200)
        controls = self._controls(response)
        self.assertIn('errorlist', controls)
        self.assertIn('This field is required.', controls)
        self.assertEqual(Topic.objects.get(pk=self.t1.id).forum, self.forum)

    def _controls(self, response):
        """Returns the markup inside the moderator control bar."""
        html = response.content.decode('utf-8')
        opening = '<div class="forum-mod-controls">'
        start = html.index(opening) + len(opening)
        return html[start:html.index('</div>', start)]


class SpammerToolTests(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        # A freshly created user's profile defaults to STA_STRANGER.
        self.stranger = User.objects.create_user('stranger', 's@example.com', 'pw')
        self.admin = User.objects.create_superuser('admin', 'a@example.com', 'pw')
        self.topic = make_topic(self.forum, self.stranger)
        self.post = add_post(self.topic, self.stranger, body='spammy content')

    def test_spammer_page_renders_for_moderator(self):
        self.client.login(username='admin', password='pw')
        response = self.client.get(reverse('forums-spammer', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_moderate'])
        self.assertTrue(response.context['can_deactivate'])

    def test_moderator_deactivates_stranger_spammer(self):
        self.client.login(username='admin', password='pw')
        response = self.client.post(reverse('forums-spammer', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)

        poster = User.objects.get(pk=self.stranger.id)
        self.assertFalse(poster.is_active)
        self.assertEqual(poster.profile.status, bio.models.STA_SPAMMER)
        # Their posts are removed as part of deactivation.
        self.assertFalse(Post.objects.filter(user=poster).exists())

    def test_cannot_deactivate_a_non_stranger(self):
        # Promote the poster out of stranger status first.
        profile = self.stranger.profile
        profile.status = bio.models.STA_ACTIVE
        profile.save()

        self.client.login(username='admin', password='pw')
        response = self.client.post(reverse('forums-spammer', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)   # re-renders, no redirect
        self.assertTrue(User.objects.get(pk=self.stranger.id).is_active)

    def test_non_moderator_cannot_deactivate(self):
        User.objects.create_user('member', 'm@example.com', 'pw')
        self.client.login(username='member', password='pw')
        self.client.post(reverse('forums-spammer', args=[self.post.id]))
        self.assertTrue(User.objects.get(pk=self.stranger.id).is_active)

    def test_spammer_nailed_confirms_success_after_deactivation(self):
        self.client.login(username='admin', password='pw')
        self.client.post(reverse('forums-spammer', args=[self.post.id]))

        response = self.client.get(
            reverse('forums-spammer_nailed', args=[self.stranger.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['success'])

    def test_moderator_promotes_stranger(self):
        self.client.login(username='admin', password='pw')
        response = self.client.post(reverse('forums-stranger', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.get(pk=self.stranger.id).profile.status,
                         bio.models.STA_ACTIVE)
