"""
Tests for the views in the forums application.

"""
import datetime
import pathlib
import re

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.staticfiles import finders
from django.http import QueryDict
from django.core.cache import cache
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bio.models import STA_ACTIVE, STA_STRANGER
from core.services import get_redis_connection
from forums.forms import NewTopicForm, PostForm
from forums.latest import UPDATED_TOPICS_SET_KEY
from forums.models import Attachment, Forum, ForumLastVisit, Post, Topic
from forums.tests.test_moderation import add_post, make_topic
from forums.views.main import POSTS_PER_PAGE, TOPICS_PER_PAGE
from oembed.models import Oembed


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
    """The forum pages render on the V3 design, with the V3 fragments."""
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
        self.assertNotIn('page_nav', response.context)

    def test_v3_pages_get_the_v3_fragments(self):
        self.login(self.member)

        response = self.client.get(self.forum_url)
        for name in ('topic_icons_tag', 'last_post_info', 'navigation_tag'):
            with self.subTest(fragment=name):
                self.assertTemplateUsed(response, 'forums/v3/%s.html' % name)
        self.assertContains(response, 'fi-asterisk')
        self.assertContains(response, 'class="breadcrumbs"')

        response = self.client.get(self.index_url)
        self.assertTemplateUsed(response, 'forums/v3/forum_query.html')
        self.assertTemplateUsed(response, 'forums/v3/last_post_info.html')

    def topic_url(self):
        return reverse('forums-topic_index', kwargs={'id': self.topic.id})

    def add_replies(self, *bodies):
        for body in bodies:
            add_post(self.topic, self.member, body=body)

    def test_topic_page_is_v3_with_every_post_for_each_role(self):
        self.add_replies('second reply', 'third reply')
        for user in (None, self.member, self.moderator):
            with self.subTest(user=user and user.username):
                self.client.logout()
                if user:
                    self.login(user)
                response = self.client.get(self.topic_url())
                self.assertV3(response)
                for body in ('a post', 'second reply', 'third reply'):
                    self.assertContains(response, body)
                self.assertTemplateUsed(response, 'core/v3/pagination.html')
                self.assertNotIn('page_nav', response.context)

    def test_topic_cards_share_one_class_and_alternate_by_css(self):
        self.add_replies('second reply', 'third reply')

        response = self.client.get(self.topic_url())

        used = [t.name for t in response.templates]
        self.assertEqual(used.count('forums/display_post_v3.html'), 3)
        # The author card, shown from medium up, and the post body.
        self.assertContains(response, 'class="sg101-card show-for-medium"',
                            count=3)
        self.assertContains(response, 'class="sg101-card"', count=3)
        self.assertNotContains(response, 'sg101-card1')
        self.assertNotContains(response, 'sg101-card2')

        source = get_template('forums/topic.html').template.source
        self.assertNotIn('{% cycle', source)
        css = (pathlib.Path(settings.PROJECT_PATH) / 'static' / 'css' / 'v3' /
               'main.min.css').read_text()
        # Posts cycle through three colours. The selector must end at the
        # card: the divider's selector begins with the same text.
        for position in ('3n+1', '3n+2', '3n+0'):
            with self.subTest(position=position):
                self.assertRegex(
                    css, r'#forum-topic-post-container>\.row:nth-child\(%s\) '
                    r'\.sg101-card[,{]' % re.escape(position))

    def test_topic_reply_box_is_the_post_box_module(self):
        self.login(self.member)

        response = self.client.get(self.topic_url())

        self.assertContains(
            response,
            '<script type="module" src="/static/js/v3/post_box/post_box.js">',
            count=1)
        used = [t.name for t in response.templates]
        self.assertEqual(used.count('core/v3/post_box_modals.html'), 1)
        for script in ('js/forums.js', 'jquery.form', 'js/v3/post_box.js',
                       'jquery-ui'):
            with self.subTest(script=script):
                self.assertNotContains(response, script)
        # The Embedding Videos help topic is out of date, so nothing links to it.
        self.assertNotContains(response, '/forums/topic/18843/')

    def test_every_topic_page_loads_the_topic_script(self):
        # Flag and delete are on every page, not only the last, which is
        # the only one with the reply box.
        for n in range(POSTS_PER_PAGE):
            add_post(self.topic, self.member)
        script = '<script type="module" src="/static/js/v3/forums/topic.js">'
        for user in (None, self.member):
            with self.subTest(user=user and user.username):
                self.client.logout()
                if user:
                    self.login(user)
                response = self.client.get(self.topic_url(), {'page': 1})
                self.assertContains(response, script, count=1)

    def test_anonymous_topic_page_has_no_post_box(self):
        response = self.client.get(self.topic_url())

        self.assertNotContains(response, 'post_box/post_box.js')
        self.assertTemplateNotUsed(response, 'core/v3/post_box_modals.html')

    def test_quick_reply_renders_the_v3_card(self):
        self.login(self.member)

        response = self.client.post(reverse('forums-quick_reply'), {
            'body': 'a quick reply',
            'topic_id': self.topic.id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forums/display_post_v3.html')
        self.assertContains(response, 'a quick reply')


class ConfirmationPagesTestCase(TestCase):
    """The pages a member lands on after starting a topic, or after adding it
    to or removing it from their favorites or subscriptions, are V3."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('member', '', 'pw')
        self.topic = make_topic(self.forum, self.member, name='A topic')
        add_post(self.topic, self.member)
        self.assertTrue(self.client.login(username='member', password='pw'))

    def post(self, name, topic):
        return self.client.post(reverse(name, args=[topic.id]), follow=True)

    def assertConfirmation(self, response, topic, *texts):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
        self.assertContains(
            response, '<a href="%s">%s</a>' % (topic.get_absolute_url(), topic.name))
        for text in texts:
            self.assertContains(response, text)

    def test_a_new_topic_lands_on_the_v3_thanks_page(self):
        response = self.client.post(
            reverse('forums-new_topic', kwargs={'slug': self.forum.slug}),
            {'name': 'A new topic', 'body': 'testing 1, 2, 3...'}, follow=True)

        topic = Topic.objects.get(name='A new topic')
        self.assertConfirmation(
            response, topic,
            '&quot;<a href="%s">A new topic</a>&quot;.' % topic.get_absolute_url())

    def test_favorite_and_unfavorite_land_on_the_v3_status_page(self):
        self.assertConfirmation(
            self.post('forums-favorite_topic', self.topic), self.topic,
            'has been added to your')
        self.assertConfirmation(
            self.post('forums-unfavorite_topic', self.topic), self.topic,
            'has been removed from your')

    def test_subscribe_and_unsubscribe_land_on_the_v3_status_page(self):
        self.assertConfirmation(
            self.post('forums-subscribe_topic', self.topic), self.topic,
            'You are now subscribed to the forum topic')
        self.assertConfirmation(
            self.post('forums-unsubscribe_topic', self.topic), self.topic,
            'You have successfully unsubscribed from the forum topic')


class ForumNavTestCase(TestCase):
    """The V3 forum pages' select boxes are driven by the nav.js module, not by
    inline jQuery; the old pages keep their inline script for now."""
    fixtures = ['forums.json']
    NAV = '<script type="module" src="/static/js/v3/forums/nav.js"></script>'

    def setUp(self):
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('member', '', 'pw')
        self.topic = make_topic(self.forum, self.member, name='A topic')
        add_post(self.topic, self.member)
        self.assertTrue(self.client.login(username='member', password='pw'))

    def test_v3_pages_load_nav_and_no_inline_navigation_script(self):
        for url in (reverse('forums-index'),
                    reverse('forums-forum_index', kwargs={'slug': self.forum.slug}),
                    self.topic.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, self.NAV, count=1)
                self.assertContains(response, 'data-forum-nav', count=1)
                self.assertNotContains(response, 'forum-jumpbox-select')
                self.assertNotContains(response, 'forum-query-select')
                self.assertNotContains(response, 'window.location = dest')

    def test_the_jump_box_script_is_gone(self):
        with self.assertRaises(TemplateDoesNotExist):
            get_template('forums/jump_box.js')

    def test_the_forum_query_script_and_its_old_box_are_gone(self):
        for name in ('forums/forum_query.js', 'forums/forum_query.html'):
            with self.subTest(template=name):
                with self.assertRaises(TemplateDoesNotExist):
                    get_template(name)


class TopicListsTestCase(TestCase):
    """The unread, unanswered and active topic lists are V3: each topic names
    its forum under its title, unread titles jump to the first unread post,
    and only the unread list offers to mark everything read."""
    fixtures = ['forums.json']
    NAV = '<script type="module" src="/static/js/v3/forums/nav.js"></script>'

    def setUp(self):
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.member = User.objects.create_user('member', '', 'pw')

        # Unanswered: a single post. Unread for the member: posted after the
        # member's window for the forum closed.
        self.topic = make_topic(self.forum, self.author, name='Reverb tank question')
        add_post(self.topic, self.author)
        now = timezone.now()
        ForumLastVisit.objects.create(user=self.member, forum=self.forum,
                                      begin_date=now - datetime.timedelta(days=1),
                                      end_date=now - datetime.timedelta(days=1))

        # The active list reads its topic ids from forums.latest's Redis set.
        conn = get_redis_connection()
        conn.delete(UPDATED_TOPICS_SET_KEY)
        conn.zadd(UPDATED_TOPICS_SET_KEY, {self.topic.id: 1})
        self.addCleanup(conn.delete, UPDATED_TOPICS_SET_KEY)

        self.unread_url = reverse('forums-unread_topics')
        self.unanswered_url = reverse('forums-unanswered_topics')
        self.active_url = reverse('forums-active_topics', args=[30])
        self.titles = {
            self.unread_url: 'Topics With Unread Posts',
            self.unanswered_url: 'Unanswered Topics',
            self.active_url: 'Last 30 Active Topics',
        }

    def login(self):
        self.assertTrue(self.client.login(username='member', password='pw'))

    def title_link(self, url):
        return '<a href="%s">%s</a>' % (url, self.topic.name)

    def assertV3List(self, response, title):
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forums/topic_list.html')
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
        self.assertTemplateUsed(response, 'forums/v3/forum_query.html')
        self.assertContains(response, self.NAV, count=1)
        self.assertContains(response, 'data-forum-nav', count=1)
        self.assertContains(response, '<h2>%s</h2>' % title, html=True)

    def test_each_list_is_v3_for_a_member(self):
        self.login()
        for url, title in self.titles.items():
            with self.subTest(url=url):
                self.assertV3List(self.client.get(url), title)

    def test_anonymous_visitors_get_the_open_lists_and_a_login_for_unread(self):
        for url in (self.unanswered_url, self.active_url):
            with self.subTest(url=url):
                self.assertV3List(self.client.get(url), self.titles[url])

        response = self.client.get(self.unread_url)
        self.assertRedirects(
            response, '%s?next=%s' % (reverse(settings.LOGIN_URL), self.unread_url),
            fetch_redirect_response=False)

    def test_each_topic_names_its_forum_under_the_title(self):
        self.login()
        forum_link = 'in <a href="%s">%s</a>' % (self.forum.get_absolute_url(),
                                                  self.forum.name)
        for url in self.titles:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, forum_link, count=1)
                self.assertNotContains(response, '<th class="col-0">Forum</th>')

    def test_unread_titles_jump_to_the_first_unread_post(self):
        self.login()
        unread = reverse('forums-topic_unread', kwargs={'id': self.topic.id})

        response = self.client.get(self.unread_url)
        self.assertContains(response, self.title_link(unread), count=1)
        self.assertNotContains(response, self.title_link(self.topic.get_absolute_url()))

        for url in (self.unanswered_url, self.active_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(
                    response, self.title_link(self.topic.get_absolute_url()), count=1)
                self.assertNotContains(response, self.title_link(unread))

    def test_only_a_non_empty_unread_list_offers_to_mark_all_read(self):
        self.login()
        catchup = 'action="%s"' % reverse('forums-catchup_all')

        response = self.client.get(self.unread_url)
        self.assertContains(response, catchup, count=1)
        self.assertContains(response, 'value="Mark All Forums Read"', count=1)

        for url in (self.unanswered_url, self.active_url):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), catchup)

        self.client.post(reverse('forums-catchup_all'))
        response = self.client.get(self.unread_url)
        self.assertContains(response, 'No topics meet your search criteria.')
        self.assertNotContains(response, catchup)

    def test_pagination_is_v3_above_and_below_the_table(self):
        for n in range(TOPICS_PER_PAGE):
            add_post(make_topic(self.forum, self.author, name='Topic %d' % n),
                     self.author)

        response = self.client.get(self.unanswered_url, {'page': 2})

        self.assertEqual(len(response.context['page'].object_list), 1)
        self.assertTemplateUsed(response, 'core/v3/pagination.html', count=2)
        self.assertNotIn('page_nav', response.context)
        self.assertContains(response, '<ul class="pagination', count=2)
        self.assertContains(response, 'href="./?page=1"')

    def test_an_empty_list_says_so(self):
        Topic.objects.filter(pk=self.topic.pk).update(post_count=2)
        response = self.client.get(self.unanswered_url)
        self.assertContains(response, 'No topics meet your search criteria.')


class PostListsTestCase(TestCase):
    """A member's posts, theirs or another member's, are listed on the V3 design
    as plain cards, newest first, each headed by where the post lives."""
    fixtures = ['forums.json']
    NAV = '<script type="module" src="/static/js/v3/forums/nav.js"></script>'
    CARD = '<div class="sg101-card">'

    def setUp(self):
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = User.objects.create_user('author', '', 'pw')
        self.reader = User.objects.create_user('reader', '', 'pw')
        self.topic = make_topic(self.forum, self.author, name='Reverb tank question')
        now = timezone.now()
        self.older = add_post(self.topic, self.author, body='The older post',
                              when=now - datetime.timedelta(days=1))
        self.newer = add_post(self.topic, self.author, body='The newer post', when=now)

        self.my_posts = reverse('forums-my_posts')
        self.authors_posts = reverse('forums-posts_for_user',
                                     kwargs={'username': 'author'})

    def login(self, username):
        self.assertTrue(self.client.login(username=username, password='pw'))

    def assertV3List(self, response, title):
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forums/post_list.html')
        self.assertTemplateUsed(response, 'v3/base.html')
        self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
        self.assertTemplateUsed(response, 'forums/v3/forum_query.html')
        self.assertContains(response, self.NAV, count=1)
        self.assertContains(response, 'data-forum-nav', count=1)
        self.assertContains(response, '<h2>%s</h2>' % title, html=True)

    def test_both_lists_are_v3(self):
        self.login('author')
        self.assertV3List(self.client.get(self.my_posts), 'My Posts')
        self.login('reader')
        self.assertV3List(self.client.get(self.authors_posts), 'Posts by author')

    def test_one_card_per_post_newest_first(self):
        self.login('reader')
        content = self.client.get(self.authors_posts).content.decode()
        self.assertEqual(content.count(self.CARD), 2)
        self.assertLess(content.index('The newer post'), content.index('The older post'))

    def test_each_card_links_its_forum_topic_and_post(self):
        self.login('reader')
        response = self.client.get(self.authors_posts)
        self.assertContains(response, '<a href="%s">%s</a>' % (
            self.forum.get_absolute_url(), self.forum.name), count=2)
        self.assertContains(response, '<a href="%s">%s</a>' % (
            self.topic.get_absolute_url(), self.topic.name), count=2)
        for post in (self.older, self.newer):
            with self.subTest(post=post.body):
                self.assertContains(response, 'href="%s"' % post.get_absolute_url(),
                                    count=1)

    def test_a_card_shows_the_body_only(self):
        embed = Oembed.objects.create(
            url='https://example.com/video', type=Oembed.VIDEO, width=480,
            height=360, html='<iframe class="an-attached-video"></iframe>')
        Attachment.objects.create(post=self.newer, embed=embed, order=0)
        self.login('reader')
        response = self.client.get(self.authors_posts)
        self.assertContains(response, self.newer.html, count=1)
        self.assertNotContains(response, 'an-attached-video')

    def test_a_member_with_no_posts_is_told_so(self):
        self.login('reader')
        response = self.client.get(self.my_posts)
        self.assertV3List(response, 'My Posts')
        self.assertContains(response, 'No posts found.')
        self.assertNotContains(response, self.CARD)

    def test_posts_in_a_forum_the_reader_cannot_see_are_left_out(self):
        gear = Forum.objects.get(slug='gear')
        hidden = make_topic(gear, self.author, name='A private topic')
        add_post(hidden, self.author, body='A private post')
        gear.category.groups.add(Group.objects.create(name='Inner Circle'))
        cache.clear()

        self.login('reader')
        response = self.client.get(self.authors_posts)
        self.assertContains(response, self.CARD, count=2)
        self.assertNotContains(response, 'A private post')

    def test_pagination_is_v3_above_and_below_the_list(self):
        for n in range(POSTS_PER_PAGE - 1):
            add_post(self.topic, self.author, body='Post %d' % n)

        self.login('reader')
        response = self.client.get(self.authors_posts, {'page': 2})

        self.assertEqual(len(response.context['page'].object_list), 1)
        self.assertTemplateUsed(response, 'core/v3/pagination.html', count=2)
        self.assertNotIn('page_nav', response.context)
        self.assertContains(response, '<ul class="pagination', count=2)

    def test_anonymous_visitors_are_sent_to_log_in(self):
        for url in (self.my_posts, self.authors_posts):
            with self.subTest(url=url):
                self.assertRedirects(
                    self.client.get(url),
                    '%s?next=%s' % (reverse(settings.LOGIN_URL), url),
                    fetch_redirect_response=False)


class ManageTopicsTestCase(TestCase):
    """A member's favorite and subscribed topics are listed on the V3 design,
    with a checkbox per topic, a master checkbox, and the warning and question
    the check_all module asks before removing anything."""
    fixtures = ['forums.json']
    NAV = '<script type="module" src="/static/js/v3/forums/nav.js"></script>'
    CHECK_ALL = '<script type="module" src="/static/js/v3/forums/check_all.js"></script>'
    NONE_CHECKED = 'Please select some topics to remove.'
    CONFIRM = 'Are you sure you wish to remove the selected topics from your list?'

    def setUp(self):
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('member', '', 'pw')
        self.topic = make_topic(self.forum, self.member, name='Reverb tank question')
        add_post(self.topic, self.member)
        self.member.favorite_topics.add(self.topic)
        self.member.subscriptions.add(self.topic)
        self.assertTrue(self.client.login(username='member', password='pw'))
        self.pages = {
            reverse('forums-manage_favorites'): 'Favorite Topics',
            reverse('forums-manage_subscriptions'): 'Topic Subscriptions',
        }

    def test_both_pages_are_v3(self):
        for url, title in self.pages.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'forums/manage_topics.html')
                self.assertTemplateUsed(response, 'v3/base.html')
                self.assertTemplateUsed(response, 'forums/v3/navigation_tag.html')
                self.assertTemplateUsed(response, 'forums/v3/forum_query.html')
                self.assertContains(response, self.NAV, count=1)
                self.assertContains(response, self.CHECK_ALL, count=1)
                self.assertNotContains(response, '$(document).ready')
                self.assertContains(response, '<h2>%s</h2>' % title, html=True)

    def test_each_row_has_a_checkbox_the_topic_and_its_forum(self):
        for url in self.pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(
                    response, '<input type="checkbox" name="delete_ids" value="%d" '
                    'data-check-item aria-label="Select %s">' % (self.topic.id, self.topic.name),
                    count=1, html=True)
                self.assertContains(response, '<a href="%s">%s</a>' % (
                    self.topic.get_absolute_url(), self.topic.name), count=1)
                self.assertContains(response, 'in <a href="%s">%s</a>' % (
                    self.forum.get_absolute_url(), self.forum.name), count=1)

    def test_the_header_has_the_master_checkbox(self):
        for url in self.pages:
            with self.subTest(url=url):
                self.assertContains(
                    self.client.get(url),
                    '<input type="checkbox" data-check-all aria-label="Select all">',
                    count=1, html=True)

    def test_the_form_carries_the_warning_and_the_question(self):
        for url in self.pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'data-none-checked="%s"' % self.NONE_CHECKED,
                                    count=1)
                self.assertContains(response, 'data-confirm="%s"' % self.CONFIRM, count=1)
                self.assertNotContains(response, 'name="page"')

    def test_pagination_is_v3_above_and_below_the_table(self):
        for n in range(20):
            topic = make_topic(self.forum, self.member, name='Topic %d' % n)
            add_post(topic, self.member)
            self.member.favorite_topics.add(topic)

        response = self.client.get(reverse('forums-manage_favorites'), {'page': 2})

        self.assertEqual(len(response.context['page'].object_list), 1)
        self.assertTemplateUsed(response, 'core/v3/pagination.html', count=2)
        self.assertContains(response, '<ul class="pagination', count=2)

    def test_an_empty_list_says_so_and_offers_nothing_to_delete(self):
        self.member.favorite_topics.clear()
        response = self.client.get(reverse('forums-manage_favorites'))
        self.assertContains(response, 'No topics found')
        self.assertNotContains(response, 'Delete Selected')
        self.assertNotContains(response, 'data-check-item')


class PostCardTestCase(TestCase):
    """Each part of the V3 post card, shown to the viewers who may use it and
    to no one else."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.author = self.make_user('author', STA_ACTIVE)
        self.member = self.make_user('member', STA_ACTIVE)
        self.moderator = self.make_user('moderator', STA_ACTIVE)
        mod_group = Group.objects.get(name='Forum Moderators')
        self.moderator.groups.add(mod_group)
        self.forum.moderators.add(mod_group)
        self.stranger = self.make_user('stranger', STA_STRANGER)

        self.topic = make_topic(self.forum, self.author)
        self.post = add_post(self.topic, self.author)

    def make_user(self, username, status):
        # A new profile is a stranger's with the email hidden; set both.
        user = User.objects.create_user(username, username + '@example.com', 'pw')
        user.profile.status = status
        user.profile.hide_email = False
        user.profile.save(content_update=False)
        return user

    def view(self, viewer, topic=None):
        """The topic page as viewer sees it; None is an anonymous visitor."""
        self.client.logout()
        if viewer is not None:
            self.assertTrue(self.client.login(username=viewer.username,
                                              password='pw'))
        topic = topic or self.topic
        response = self.client.get(
            reverse('forums-topic_index', kwargs={'id': topic.id}))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def stranger_post(self):
        topic = make_topic(self.forum, self.stranger, name='a stranger topic')
        return topic, add_post(topic, self.stranger, body='a stranger post')

    def button(self, name, post):
        return (r'<button type="button"[^>]*class="[^"]*\b%s\b[^"]*"'
                r'[^>]*data-post-id="%d"' % (name, post.id))

    def assertShownTo(self, needle, shown, hidden, topic=None):
        for viewer in shown:
            with self.subTest(needle=needle, viewer=viewer and viewer.username):
                self.assertIn(needle, self.view(viewer, topic))
        for viewer in hidden:
            with self.subTest(needle=needle, absent_for=viewer and viewer.username):
                self.assertNotIn(needle, self.view(viewer, topic))

    def assertButtonShownTo(self, name, post, shown, hidden, topic=None):
        pattern = self.button(name, post)
        for viewer in shown:
            with self.subTest(button=name, viewer=viewer and viewer.username):
                self.assertRegex(self.view(viewer, topic), pattern)
        for viewer in hidden:
            with self.subTest(button=name, absent_for=viewer and viewer.username):
                self.assertNotRegex(self.view(viewer, topic), pattern)

    def test_every_post_has_both_anchors(self):
        # p<id> is where goto_post sends a permalink; post-<id> is the post's
        # element, which the page's script removes on delete.
        second = add_post(self.topic, self.member)
        page = self.view(None)
        for post in (self.post, second):
            with self.subTest(post=post.id):
                self.assertIn('id="p%d"' % post.id, page)
                self.assertIn('id="post-%d"' % post.id, page)

    def test_quote_reply_for_those_who_can_reply(self):
        url = (reverse('forums-new_post', kwargs={'topic_id': self.topic.id}) +
               '?quote=%d' % self.post.id)
        self.assertShownTo(url, shown=[self.member, self.moderator],
                           hidden=[None])

    def test_edit_for_the_author_and_moderators(self):
        url = reverse('forums-edit_post', kwargs={'id': self.post.id})
        self.assertShownTo(url, shown=[self.author, self.moderator],
                           hidden=[self.member, None])

    def test_flag_for_signed_in_viewers_but_not_the_author(self):
        self.assertButtonShownTo('post-flag', self.post,
                                 shown=[self.member, self.moderator],
                                 hidden=[self.author, None])

    def test_delete_for_moderators(self):
        self.assertButtonShownTo('post-delete', self.post,
                                 shown=[self.moderator],
                                 hidden=[self.author, self.member, None])

    def test_ip_link_for_moderators(self):
        url = reverse('forums-post_ip_info', kwargs={'post_id': self.post.id})
        self.assertShownTo(url, shown=[self.moderator],
                           hidden=[self.author, self.member, None])

    def test_stranger_tools_for_moderators_on_a_strangers_post(self):
        topic, post = self.stranger_post()
        for name in ('forums-stranger', 'forums-spammer'):
            url = reverse(name, kwargs={'post_id': post.id})
            self.assertShownTo(url, shown=[self.moderator],
                               hidden=[self.member, self.stranger, None],
                               topic=topic)

    def test_no_stranger_tools_on_a_members_post(self):
        url = reverse('forums-stranger', kwargs={'post_id': self.post.id})
        self.assertShownTo(url, shown=[], hidden=[self.moderator])

    def test_no_stranger_tools_on_a_moderators_own_post(self):
        # A new moderator account is still a stranger.
        self.moderator.profile.status = STA_STRANGER
        self.moderator.profile.save(content_update=False)
        post = add_post(self.topic, self.moderator, body='a moderator post')
        url = reverse('forums-stranger', kwargs={'post_id': post.id})
        self.assertShownTo(url, shown=[], hidden=[self.moderator])

    def test_pm_link_for_signed_in_viewers_but_not_the_author(self):
        url = reverse('messages-compose') + '?to=author'
        self.assertShownTo(url, shown=[self.member, self.moderator],
                           hidden=[self.author, None])

    def test_email_link_for_signed_in_viewers_but_not_the_author(self):
        self.assertShownTo('mailto:author@example.com',
                           shown=[self.member, self.moderator],
                           hidden=[self.author, None])

    def test_no_email_link_when_the_author_hides_it(self):
        self.author.profile.hide_email = True
        self.author.profile.save(content_update=False)
        self.assertShownTo('mailto:author@example.com', shown=[],
                           hidden=[self.member, self.moderator])

    def test_signature(self):
        self.author.profile.signature = 'Keep on surfin'
        self.author.profile.save()
        self.assertShownTo('Keep on surfin', shown=[None, self.member], hidden=[])

    def test_the_authors_name_is_bold(self):
        # Once in the author card, once in the phone's header.
        link = '<strong><a href="%s"' % reverse(
            'bio-view_profile', kwargs={'username': 'author'})
        self.assertEqual(self.view(None).count(link), 2)

    def test_a_rule_then_the_signature_after_the_edit_note(self):
        self.author.profile.signature = 'Keep on surfin'
        self.author.profile.save()
        Post.objects.filter(pk=self.post.pk).update(
            update_date=self.post.creation_date + datetime.timedelta(hours=1))

        page = self.view(None)

        self.assertRegex(page, r'class="forum-post-signature[^"]*">\s*<hr />\s*<p>Keep on surfin')
        self.assertLess(page.index('Last edited'), page.index('forum-post-signature'))

    def test_last_edited_only_once_edited(self):
        self.assertShownTo('Last edited', shown=[], hidden=[None, self.member])
        Post.objects.filter(pk=self.post.pk).update(
            update_date=self.post.creation_date + datetime.timedelta(hours=1))
        self.assertShownTo('Last edited', shown=[None, self.member], hidden=[])

    def test_last_edited_is_in_the_viewers_time_zone(self):
        # 03:00 UTC is 2 PM in Sydney in January (AEDT, +11), and 9 PM the
        # day before in Chicago, the site's zone. Posted an hour earlier.
        edited = datetime.datetime(2026, 1, 15, 3, 0, tzinfo=datetime.timezone.utc)
        Post.objects.filter(pk=self.post.pk).update(
            creation_date=edited - datetime.timedelta(hours=1), update_date=edited)
        self.member.profile.time_zone = 'Australia/Sydney'
        self.member.profile.use_24_time = False
        self.member.profile.save(content_update=False)

        page = self.view(self.member)

        self.assertIn('Last edited: Jan 15 2026 02:00 PM', page)
        self.assertNotIn('Jan 14', page)

    def test_attachments(self):
        embed = Oembed.objects.create(
            url='https://example.com/video', type=Oembed.VIDEO, width=480,
            height=360, html='<iframe class="an-attached-video"></iframe>')
        Attachment.objects.create(post=self.post, embed=embed, order=0)
        self.assertShownTo('an-attached-video', shown=[None, self.member],
                           hidden=[])

    def test_stranger_highlight(self):
        topic, post = self.stranger_post()
        self.assertIn('sg101-card-divider stranger', self.view(None, topic))
        self.assertNotIn('sg101-card-divider stranger', self.view(None))

    def test_quick_reply_returns_the_complete_card(self):
        self.assertTrue(self.client.login(username='moderator', password='pw'))

        response = self.client.post(reverse('forums-quick_reply'), {
            'body': 'a moderator reply',
            'topic_id': self.topic.id,
        })

        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='a moderator reply')
        page = response.content.decode()
        self.assertIn('id="post-%d"' % post.id, page)
        self.assertIn(reverse('forums-edit_post', kwargs={'id': post.id}), page)
        self.assertIn(
            reverse('forums-post_ip_info', kwargs={'post_id': post.id}), page)
        self.assertRegex(page, self.button('post-delete', post))
        # The reply is the moderator's own: nothing to flag, PM or email.
        self.assertNotRegex(page, self.button('post-flag', post))
        self.assertNotIn(reverse('messages-compose') + '?to=moderator', page)
        self.assertNotIn('mailto:moderator@example.com', page)


class PostingPagesTestCase(TestCase):
    """New topic, new post and edit post, on the V3 design with the post box,
    its video button and the attachment list."""
    fixtures = ['forums.json']

    def setUp(self):
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('member', '', 'pw')
        self.moderator = User.objects.create_user('moderator', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        self.moderator.groups.add(mod_group)
        self.forum.moderators.add(mod_group)
        self.topic = make_topic(self.forum, self.member, name='Fender Twins')
        self.first = add_post(self.topic, self.member, body='the first post')
        self.reply = add_post(self.topic, self.member, body='a reply')
        # Created a then b: b's id is higher, so an order that follows the
        # ids is not the order asked for.
        self.a = self.make_embed('first')
        self.b = self.make_embed('second')

    def make_embed(self, name):
        return Oembed.objects.create(
            url='https://www.youtube.com/watch?v=%s' % name, type=Oembed.VIDEO,
            title=name, width=480, height=270,
            html='<iframe width="480" height="270" title="%s"></iframe>' % name)

    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password='pw'))

    def urls(self):
        return {
            'new topic': reverse('forums-new_topic', kwargs={'slug': self.forum.slug}),
            'new post': reverse('forums-new_post', kwargs={'topic_id': self.topic.id}),
            'edit post': reverse('forums-edit_post', kwargs={'id': self.reply.id}),
        }

    def attachment_ids(self, response):
        """The attachment ids the page's form would send, in page order."""
        return [int(pk) for pk in re.findall(
            r'<input type="hidden" name="attachment" value="(\d+)"',
            response.content.decode())]

    def test_each_page_is_v3_with_the_video_post_box(self):
        self.login(self.member)
        for name, url in self.urls().items():
            with self.subTest(page=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'v3/base.html')
                self.assertContains(response, 'class="editor-video"', count=1)
                self.assertContains(response, 'id="video-modal"', count=1)
                self.assertContains(response, 'data-attachments', count=1)
                self.assertContains(
                    response,
                    '<script type="module" src="/static/js/v3/post_box/post_box.js">',
                    count=1)
                for old in ('js/forums.js', 'jquery.form', 'markitup', 'jquery-ui',
                            'forums/show_form.html'):
                    self.assertNotContains(response, old)
                self.assertNotContains(response, '/forums/topic/18843/')

    def test_new_topic_has_the_subject_and_quick_search(self):
        self.login(self.member)
        response = self.client.get(self.urls()['new topic'])
        self.assertContains(response, 'name="name"', count=1)
        self.assertContains(response, 'id="quick-search"', count=1)
        self.assertContains(
            response,
            '<script type="module" src="/static/js/v3/forums/quick_search.js">',
            count=1)
        self.assertNotContains(response, 'name="sticky"')
        self.assertNotContains(response, 'name="locked"')

    def test_a_moderator_can_start_a_topic_sticky_or_locked(self):
        self.login(self.moderator)
        response = self.client.get(self.urls()['new topic'])
        self.assertContains(response, 'name="sticky"', count=1)
        self.assertContains(response, 'name="locked"', count=1)

    def test_new_post_has_no_subject_or_quick_search(self):
        self.login(self.member)
        response = self.client.get(self.urls()['new post'])
        self.assertNotContains(response, 'name="name"')
        self.assertNotContains(response, 'quick-search')

    def test_quote_fills_the_body(self):
        self.login(self.member)
        response = self.client.get(self.urls()['new post'], {'quote': self.first.id})
        self.assertEqual(response.context['form']['body'].value(),
                         '*member wrote:*\n\n> the first post\n\n')
        self.assertContains(response, '&gt; the first post')

    def test_new_post_to_a_locked_topic_says_so(self):
        Topic.objects.filter(pk=self.topic.pk).update(locked=True)
        self.login(self.member)
        response = self.client.get(self.urls()['new post'])
        self.assertContains(response, 'This topic is locked.')
        self.assertNotContains(response, 'data-post-box')
        self.assertNotContains(response, '<textarea')

    def test_edit_post_shows_the_post_on_the_v3_card(self):
        self.login(self.member)
        response = self.client.get(self.urls()['edit post'])
        self.assertTemplateUsed(response, 'forums/display_post_v3.html')
        self.assertContains(response, 'id="post-%d"' % self.reply.id, count=1)
        self.assertNotContains(response, 'name="name"')

    def test_editing_the_first_post_edits_the_subject(self):
        self.login(self.member)
        response = self.client.get(
            reverse('forums-edit_post', kwargs={'id': self.first.id}))
        self.assertContains(response, 'name="name"', count=1)
        self.assertContains(response, 'value="Fender Twins"')

    def test_edit_post_lists_its_saved_videos_once_in_order(self):
        Attachment.objects.create(post=self.reply, embed=self.a, order=1)
        Attachment.objects.create(post=self.reply, embed=self.b, order=0)
        self.login(self.member)
        response = self.client.get(self.urls()['edit post'])
        self.assertEqual(self.attachment_ids(response), [self.b.pk, self.a.pk])
        self.assertContains(response, 'title="second"', count=2)  # the card, the list
        self.assertNotContains(response, 'name="post_id"')
        self.assertNotContains(response, 'fetch_attachments')

    def test_a_new_topic_with_an_error_keeps_its_video_once(self):
        self.login(self.member)
        response = self.client.post(self.urls()['new topic'], {
            'name': '', 'body': 'no subject', 'attachment': [str(self.b.pk), str(self.a.pk)]})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['name'])
        self.assertEqual(self.attachment_ids(response), [self.b.pk, self.a.pk])

    def test_a_new_post_with_an_error_keeps_its_video(self):
        self.login(self.member)
        response = self.client.post(self.urls()['new post'], {
            'body': '![image](http://example.com/a.jpg)', 'attachment': str(self.b.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['body'])
        self.assertEqual(self.attachment_ids(response), [self.b.pk])

    def test_an_edit_with_an_error_keeps_what_was_posted(self):
        Attachment.objects.create(post=self.reply, embed=self.a, order=0)
        self.login(self.member)
        response = self.client.post(self.urls()['edit post'], {
            'body': '![image](http://example.com/a.jpg)', 'attachment': str(self.b.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.attachment_ids(response), [self.b.pk])

    def test_an_unknown_attachment_id_is_skipped(self):
        self.login(self.member)
        response = self.client.post(self.urls()['new post'], {
            'body': 'with videos',
            'attachment': [str(self.b.pk), '999999', str(self.a.pk)]})
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(body='with videos')
        self.assertEqual(list(post.attachments.order_by('attachment__order')),
                         [self.b, self.a])

    def test_the_forms_carry_no_hidden_attachment_fields(self):
        # The attachment list carries the ids; a hidden field as well would
        # send each one twice, from any template that renders every field.
        Attachment.objects.create(post=self.reply, embed=self.a, order=0)
        data = QueryDict(mutable=True)
        data.update({'name': '', 'body': 'x', 'attachment': str(self.a.pk)})
        forms = {
            'new topic': NewTopicForm(self.member, self.forum, data),
            'edit post': PostForm(instance=self.reply),
            'edit post, posted': PostForm(data, instance=self.reply),
        }
        for name, form in forms.items():
            with self.subTest(form=name):
                self.assertEqual(set(form.fields) - {'name', 'body'}, set())

    def test_the_old_attachment_endpoints_are_gone(self):
        self.login(self.member)
        for url in ('/forums/fetch_attachments/?pid=%d' % self.reply.id,
                    '/oembed/fetch_saved/?embeds=%d' % self.a.pk):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
        self.assertIsNone(finders.find('js/forums.js'))
        for name in ('forums/show_form.html', 'forums/display_post.html',
                     'forums/post_edit_button.html', 'user_photos/image_forms.html'):
            with self.subTest(template=name):
                with self.assertRaises(TemplateDoesNotExist):
                    get_template(name)
