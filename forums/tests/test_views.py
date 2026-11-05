"""
Tests for the views in the forums application.

"""
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from forums.models import Forum, Topic
from forums.tests.test_moderation import add_post, make_topic
from forums.views.main import TOPICS_PER_PAGE


class ForumPostTestCase(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username,
            password=self.pw))

    def tearDown(self):
        self.client.logout()

    def testBasicForumsTest(self):

        forum_slug = 'shallow-end'
        topic_name = 'A test topic'
        topic_body = 'testing 1, 2, 3...'

        response = self.client.post(
                reverse('forums-new_topic', kwargs={'slug': forum_slug}),
                {'name': topic_name, 'body': topic_body},
                follow=True)

        self.assertEqual(len(response.redirect_chain), 1)

        forum = Forum.objects.get(slug=forum_slug)
        try:
            topic = Topic.objects.get(name=topic_name)
        except Topic.DoesNotExist:
            self.fail("topic doesn't exist")

        if response.redirect_chain:
            self.assertEqual(
                response.redirect_chain[0][0],
                reverse('forums-new_topic_thanks',
                        kwargs={'tid': str(topic.pk)}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(topic.forum.pk, forum.pk)
        self.assertEqual(topic.user.pk, self.user.pk)
        self.assertEqual(topic.name, topic_name)
        self.assertEqual(topic.post_count, 1)

        post = topic.last_post
        self.assertFalse(post is None)

        if post:
            self.assertEqual(post.body, topic_body)
            self.assertEqual(post.user.pk, self.user.pk)

        # post to the thread
        response = self.client.get(
                reverse('forums-topic_index', kwargs={'id': str(topic.pk)}))
        self.assertEqual(response.status_code, 200)

        post2_body = 'test quick post'
        response = self.client.post(
                reverse('forums-quick_reply'),
                {'body': post2_body, 'topic_id': topic.pk})
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()

        post = topic.last_post
        self.assertFalse(post is None)
        if post:
            self.assertEqual(post.body, post2_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 2)

        # quote last post
        quoted_post = topic.last_post
        response = self.client.get(
                reverse('forums-new_post', kwargs={'topic_id': topic.pk}),
                {'quote_id': quoted_post.pk})
        self.assertEqual(response.status_code, 200)

        post3_body = 'new post 3 content'
        response = self.client.post(
                reverse('forums-new_post', kwargs={'topic_id': topic.pk}),
                {'body': post3_body, 'post_id': quoted_post.pk},
                follow=True)
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()

        post = topic.last_post
        self.assertFalse(post is None)
        if post:
            self.assertEqual(post.body, post3_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 3)

        # edit last post
        post3 = topic.last_post
        response = self.client.get(
                reverse('forums-edit_post', kwargs={'id': post3.pk}))
        self.assertEqual(response.status_code, 200)

        post3_body = 'edited post 3 content'
        response = self.client.post(
                reverse('forums-edit_post', kwargs={'id': post3.pk}),
                {'body': post3_body},
                follow=True)
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()

        post = topic.last_post
        self.assertFalse(post is None)
        if post:
            self.assertEqual(post.body, post3_body)
            self.assertEqual(post.user.pk, self.user.pk)
        self.assertEqual(topic.post_count, 3)

        # our cached copy of the profile is out of date; need to refetch from
        # the database
        user = User.objects.get(username=self.username)
        profile = user.profile
        self.assertEqual(profile.forum_post_count, 3)


class PostsForUserTestCase(TestCase):
    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('MixedCase', '', 'pw')
        self.assertTrue(self.client.login(username='MixedCase', password='pw'))

    def test_posts_for_user(self):
        response = self.client.get(reverse('forums-posts_for_user',
                                           kwargs={'username': 'MixedCase'}))
        self.assertEqual(response.status_code, 200)

    def test_posts_for_user_differing_case(self):
        response = self.client.get(reverse('forums-posts_for_user',
                                           kwargs={'username': 'mixedcase'}))
        self.assertEqual(response.status_code, 200)

    def test_posts_for_unknown_user_is_404(self):
        response = self.client.get(reverse('forums-posts_for_user',
                                           kwargs={'username': 'nobody'}))
        self.assertEqual(response.status_code, 404)


class V3PagesTestCase(TestCase):
    """The forums index and a forum's topic list render on the V3 design; the
    pages not yet converted keep the old design and the old fragments."""
    fixtures = ['forums.json']

    def setUp(self):
        # The index caches two of its blocks; a block served from the cache
        # renders no template, so the template assertions would depend on test
        # order.
        cache.clear()

        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('member', '', 'pw')
        self.moderator = User.objects.create_user('moderator', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        self.moderator.groups.add(mod_group)
        self.forum.moderators.add(mod_group)

        self.topic = make_topic(self.forum, self.member, name='A sticky topic',
                                sticky=True)
        add_post(self.topic, self.member)

        self.index_url = reverse('forums-index')
        self.forum_url = reverse('forums-forum_index',
                                 kwargs={'slug': self.forum.slug})

    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password='pw'))

    def assertV3(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateNotUsed(response, 'base.html')
        self.assertIs(response.context.get('V3_DESIGN'), True)

    def assertOldDesign(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateNotUsed(response, 'v3/base.html')

    def test_both_pages_are_v3_for_each_role(self):
        for user in (None, self.member, self.moderator):
            with self.subTest(user=user and user.username):
                self.client.logout()
                if user:
                    self.login(user)
                self.assertV3(self.client.get(self.index_url))
                self.assertV3(self.client.get(self.forum_url))

    def test_only_a_moderator_gets_the_moderate_link(self):
        mod_url = reverse('forums-mod_forum', kwargs={'slug': self.forum.slug})

        self.login(self.member)
        self.assertNotContains(self.client.get(self.forum_url), mod_url)

        self.login(self.moderator)
        self.assertContains(self.client.get(self.forum_url), mod_url)

    def test_index_renders_its_stats_fragments(self):
        response = self.client.get(self.index_url)

        for name in ('accounts/user_stats_tag.html',
                     'core/max_users_tag.html',
                     'core/whos_online_tag.html',
                     'forums/forum_stats_tag.html'):
            self.assertTemplateUsed(response, name)
        self.assertContains(response, 'around the world:')
        self.assertContains(response, 'online:')

    def test_forum_pagination_comes_from_the_v3_fragment(self):
        for n in range(TOPICS_PER_PAGE):
            add_post(make_topic(self.forum, self.member, name='t%d' % n),
                     self.member)

        response = self.client.get(self.forum_url, {'page': 2})

        self.assertV3(response)
        self.assertTemplateUsed(response, 'core/v3/pagination.html')
        self.assertTemplateNotUsed(response, 'forums/pagination.html')
        self.assertNotIn('page_nav', response.context)

    def test_v3_pages_get_the_v3_fragments(self):
        self.login(self.member)

        response = self.client.get(self.forum_url)
        for name in ('topic_icons_tag', 'last_post_info', 'navigation_tag'):
            with self.subTest(fragment=name):
                self.assertTemplateUsed(response, 'forums/v3/%s.html' % name)
                self.assertTemplateNotUsed(response, 'forums/%s.html' % name)
        self.assertContains(response, 'fi-asterisk')
        self.assertContains(response, 'class="breadcrumbs"')

        response = self.client.get(self.index_url)
        self.assertTemplateUsed(response, 'forums/v3/forum_query.html')
        self.assertTemplateNotUsed(response, 'forums/forum_query.html')
        self.assertTemplateUsed(response, 'forums/v3/last_post_info.html')

    def test_old_pages_keep_the_old_fragments(self):
        self.login(self.member)

        response = self.client.get(reverse('forums-unanswered_topics'))
        self.assertOldDesign(response)
        for name in ('topic_icons_tag', 'last_post_info', 'forum_query'):
            with self.subTest(fragment=name):
                self.assertTemplateUsed(response, 'forums/%s.html' % name)
                self.assertTemplateNotUsed(response, 'forums/v3/%s.html' % name)
        self.assertContains(response, 'icons/asterisk_orange.png')
        self.assertContains(response, 'icons/note_go.png')

        response = self.client.get(reverse('forums-new_topic',
                                           kwargs={'slug': self.forum.slug}))
        self.assertOldDesign(response)
        self.assertTemplateUsed(response, 'forums/navigation_tag.html')
        self.assertTemplateNotUsed(response, 'forums/v3/navigation_tag.html')
        self.assertContains(response, 'class="forum-nav"')

    def test_unconverted_pages_stay_on_the_old_design(self):
        self.login(self.moderator)
        for url in (reverse('forums-unanswered_topics'),
                    reverse('forums-new_topic', kwargs={'slug': self.forum.slug}),
                    reverse('forums-topic_index', kwargs={'id': self.topic.id}),
                    reverse('forums-mod_forum', kwargs={'slug': self.forum.slug})):
            with self.subTest(url=url):
                self.assertOldDesign(self.client.get(url))
