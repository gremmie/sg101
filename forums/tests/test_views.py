"""
Tests for the views in the forums application.

"""
import datetime
import pathlib

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

from bio.models import STA_ACTIVE, STA_STRANGER
from forums.models import Attachment, Forum, Post, Topic
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
                    reverse('forums-edit_post',
                            kwargs={'id': self.topic.last_post.id}),
                    reverse('forums-mod_forum', kwargs={'slug': self.forum.slug})):
            with self.subTest(url=url):
                self.assertOldDesign(self.client.get(url))

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
        self.assertTemplateNotUsed(response, 'forums/display_post.html')
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
        # The minifier writes (even) as (2n). The selector must end at the
        # card: the divider's selector begins with the same text.
        self.assertRegex(
            css, r'#forum-topic-post-container>\.row:nth-child\(2n\) \.sg101-card[,{]')

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
        self.assertTemplateNotUsed(response, 'forums/display_post.html')
        self.assertContains(response, 'a quick reply')

    def test_edit_page_keeps_the_old_card(self):
        self.login(self.member)

        response = self.client.get(reverse(
            'forums-edit_post', kwargs={'id': self.topic.last_post.id}))

        self.assertOldDesign(response)
        self.assertTemplateUsed(response, 'forums/display_post.html')
        self.assertTemplateNotUsed(response, 'forums/display_post_v3.html')


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
