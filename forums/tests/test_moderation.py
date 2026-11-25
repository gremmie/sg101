"""
Characterization tests for forums moderator actions and spam tools.

These lock in the *effects* of the moderator-only views -- the destructive and
state-changing operations (stick/lock/move/split topics, bulk moderation, and
deactivating spammers / promoting strangers). The permission gating on these
views is covered separately in test_permissions; here a moderator (superuser)
performs the action and we assert what actually changed.
"""
import datetime
import re
from unittest import mock

import bio.models
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.urls import reverse
from django.test import TestCase
from django.utils import timezone

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
        add_post(topic, self.author, when=timezone.now() - 3 * DAY)
        reply2 = add_post(topic, self.author, when=timezone.now() - 2 * DAY)
        reply3 = add_post(topic, self.author, when=timezone.now() - 1 * DAY)

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
        add_post(topic, self.author, when=timezone.now() - 3 * DAY)
        reply2 = add_post(topic, self.author, when=timezone.now() - 2 * DAY)
        add_post(topic, self.author, when=timezone.now() - 1 * DAY)

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


class SplitAndMovePageTests(TestCase):
    """The split and move pages are V3. Split shows every post as a card with
    its date and IP, a checkbox on all but the first, and starts on the
    topic's own forum; its two selection errors still render."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        User.objects.create_superuser('admin', 'a@example.com', 'pw')
        self.topic = make_topic(self.forum, self.author, name='Original')
        self.posts = [add_post(self.topic, self.author, body='post %d' % n,
                               when=timezone.now() - (3 - n) * DAY) for n in range(3)]
        for post in self.posts:
            post.user_ip = '192.0.2.%d' % (post.id % 250)
            post.save()
        self.split_url = reverse('forums-mod_topic_split', args=[self.topic.id])
        self.move_url = reverse('forums-mod_topic_move', args=[self.topic.id])
        self.client.login(username='admin', password='pw')

    def assertV3(self, response, title):
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateNotUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
        self.assertContains(response, '<h2>%s: Original</h2>' % title, html=True)

    def test_both_pages_are_v3(self):
        self.assertV3(self.client.get(self.split_url), 'Split Topic')
        self.assertV3(self.client.get(self.move_url), 'Move Topic')

    def test_split_shows_each_post_as_a_card_with_its_ip(self):
        response = self.client.get(self.split_url)
        html = response.content.decode('utf-8')
        self.assertEqual(html.count('class="sg101-card forum-split-post"'), 3)
        for post in self.posts:
            with self.subTest(post=post.id):
                self.assertContains(response, 'IP: %s' % post.user_ip)
                self.assertContains(response, 'post %d' % self.posts.index(post))

    def test_every_post_but_the_first_has_a_checkbox(self):
        html = self.client.get(self.split_url).content.decode('utf-8')
        values = re.findall(r'<input type="checkbox" name="post_ids" value="(\d+)"', html)
        self.assertEqual(values, [str(p.id) for p in self.posts[1:]])

    def test_the_split_buttons_come_before_and_after_the_posts(self):
        html = self.client.get(self.split_url).content.decode('utf-8')
        first_card = html.index('forum-split-post')
        last_card = html.rindex('forum-split-post')
        for name in ('split-selected', 'split-at'):
            with self.subTest(button=name):
                places = [m.start() for m in re.finditer(r'name="%s"' % name, html)]
                self.assertEqual(len(places), 2)
                self.assertLess(places[0], first_card)
                self.assertGreater(places[1], last_card)

    def test_split_starts_on_the_topics_forum(self):
        html = self.client.get(self.split_url).content.decode('utf-8')
        self.assertRegex(html, r'<option value="%d" selected>' % self.forum.id)

    def test_splitting_nothing_explains_and_splits_nothing(self):
        response = self.client.post(self.split_url, {'name': 'New', 'forums': self.forum.id,
                                                     'split-selected': '1'})
        self.assertContains(response, 'Please select some posts')
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertEqual(Topic.objects.get(pk=self.topic.id).post_count, 3)

    def test_splitting_at_two_posts_explains_and_splits_nothing(self):
        response = self.client.post(self.split_url, {
            'name': 'New', 'forums': self.forum.id, 'split-at': '1',
            'post_ids': [str(self.posts[1].id), str(self.posts[2].id)]})
        self.assertContains(response, 'Please select only one post to split the topic at')
        self.assertEqual(Topic.objects.get(pk=self.topic.id).post_count, 3)

    def test_move_is_refused_to_a_member(self):
        self.client.logout()
        User.objects.create_user('member', '', 'pw')
        self.client.login(username='member', password='pw')
        self.assertEqual(self.client.get(self.move_url).status_code, 403)


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
        for markup in ['<tr', '<th', '<td', '<label']:
            self.assertNotIn(markup, controls)
        # Only the template's own input group: none from rendering the field.
        self.assertEqual(controls.count('<div'), 2)

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
        return html[start:html.index('</form>', start)]


class ModForumPageTests(TestCase):
    """The moderate-forum page is V3, its checkboxes are found by
    check_all.js, and a bulk action returns to the page it was taken on."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        author = User.objects.create_user('author', '', 'pw')
        User.objects.create_superuser('admin', 'a@example.com', 'pw')
        self.topics = []
        for n in range(5):
            topic = make_topic(self.forum, author, name='t%d' % n)
            add_post(topic, author)
            self.topics.append(topic)
        self.url = reverse('forums-mod_forum', kwargs={'slug': self.forum.slug})
        self.client.login(username='admin', password='pw')

    def test_the_page_is_v3(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateNotUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'core/v3/pagination.html')
        self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
        self.assertTemplateUsed(response, 'forums/v3/last_post_info.html')
        self.assertNotIn('page_nav', response.context)
        self.assertContains(response, '<h2>Moderate Forum: %s</h2>' % self.forum.name,
                            html=True)

    def test_check_all_replaces_forums_mod(self):
        response = self.client.get(self.url)
        self.assertContains(response, '/static/js/v3/forums/check_all.js')
        self.assertNotContains(response, 'forums_mod.js')
        self.assertIsNone(finders.find('js/forums_mod.js'))

    def test_the_checkboxes_and_buttons_carry_their_checks(self):
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        self.assertEqual(html.count('data-check-all'), 1)
        self.assertEqual(html.count('data-check-item'), len(self.topics))
        self.assertContains(response, 'data-none-checked="Please select some topics."')
        self.assertEqual(html.count('data-confirm='), 1)
        self.assertRegex(html, r'<button[^>]*class="alert button" name="delete"[^>]*'
                               r'data-confirm="Are you sure you want to delete the selected '
                               r'topics\?"><i class="fi-trash" aria-hidden="true"></i>Delete</button>')

    def test_sticky_and_lock_carry_their_icons(self):
        html = self.client.get(self.url).content.decode('utf-8')
        for name, icon, label in (('sticky', 'fi-asterisk', 'Toggle Sticky'),
                                  ('lock', 'fi-lock', 'Toggle Lock')):
            with self.subTest(button=name):
                self.assertRegex(html, r'<button type="submit" class="button" name="%s"'
                                       r' value="1" formnovalidate><i class="%s"'
                                       r' aria-hidden="true"></i>%s</button>'
                                       % (name, icon, label))

    def test_move_joins_its_select(self):
        response = self.client.get(self.url)
        self.assertRegex(response.content.decode('utf-8'),
            r'(?s)<div class="input-group">\s*'
            r'<div class="input-group-button">\s*<input type="submit" class="button"'
            r' value="Move To:" name="move" />\s*</div>\s*'
            r'<select name="forums" class="input-group-field" aria-label="Move to forum"')

    @mock.patch('forums.views.main.TOPICS_PER_PAGE', 2)
    def test_the_form_posts_back_to_its_page(self):
        response = self.client.get(self.url + '?page=2')
        self.assertContains(response, 'action="?page=2"')
        self.assertNotContains(response, 'name="page"')

    @mock.patch('forums.views.main.TOPICS_PER_PAGE', 2)
    def test_a_bulk_action_returns_to_its_page(self):
        response = self.client.post(self.url + '?page=2',
                                    {'topic_ids': [str(self.topics[0].id)], 'lock': '1'})
        self.assertRedirects(response, self.url + '?page=2')

    @mock.patch('forums.views.main.TOPICS_PER_PAGE', 2)
    def test_emptying_the_last_page_returns_to_the_new_last_page(self):
        # Five topics, two a page: page 3 holds one topic.
        last = self.client.get(self.url + '?page=3').context['page'].object_list
        self.assertEqual(len(last), 1)
        response = self.client.post(self.url + '?page=3',
                                    {'topic_ids': [str(last[0].id)], 'delete': '1'})
        self.assertRedirects(response, self.url + '?page=2')


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
