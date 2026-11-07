"""Browser tests for the forums' pages."""
import datetime
import re

from django.contrib.auth.models import Group, User
from playwright.sync_api import expect

from bio.models import STA_ACTIVE
from core.tests.browser import BrowserTestCase
from forums.models import FlaggedPost, Forum, Post, Topic
from forums.tests.test_moderation import add_post, make_topic
from forums.views.main import POSTS_PER_PAGE


class TopicPageTestCase(BrowserTestCase):
    """The topic page's reply box, in a real browser."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.topic = make_topic(Forum.objects.get(slug='shallow-end'), self.user)
        add_post(self.topic, self.user)
        self.login(self.user)
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

    def horizontal_scroll(self):
        return self.page.evaluate(
            'document.documentElement.scrollWidth - window.innerWidth')

    def test_the_reply_box_is_the_working_post_box(self):
        # A module that fails to load raises no page error, only a console
        # one, so this uses the post box to show it loaded.
        textarea = self.page.locator('.v3-editor textarea')
        textarea.fill('hello world')
        textarea.evaluate('t => { t.focus(); t.setSelectionRange(6, 11); }')
        self.page.locator('.editor-bold').click()
        expect(textarea).to_have_value('hello **world**')

    def test_the_reply_box_fits_a_phone(self):
        # A fieldset is never narrower than its contents, so a toolbar too
        # wide for the screen widens the whole page.
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.page.reload()
        expect(self.page.locator('.v3-editor')).to_be_visible()
        self.assertLessEqual(self.horizontal_scroll(), 0)

    def test_a_long_link_in_a_post_is_not_cut_off(self):
        # No hyphens: a browser can break a line at one. The card hides what
        # overflows it, so the page doesn't scroll; the end of the link is
        # simply cut off.
        add_post(self.topic, self.user,
                 body='https://example.com/' + 'alongpathsegment' * 10)
        self.context.clear_cookies()
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.page.reload()
        body = self.page.locator('.card-section', has_text='alongpathsegment')
        expect(body).to_be_visible()
        overrun = body.evaluate('e => e.scrollWidth - e.clientWidth')
        self.assertLessEqual(overrun, 0)


class PostCardTestCase(BrowserTestCase):
    """The post card's anchor and its stranger highlight, in a real browser."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.member.profile.status = STA_ACTIVE
        self.member.profile.save(content_update=False)
        self.topic = make_topic(Forum.objects.get(slug='shallow-end'), self.member)

    def test_a_permalink_lands_on_its_post(self):
        posts = [add_post(self.topic, self.member, body='post %d' % n)
                 for n in range(2 * POSTS_PER_PAGE)]
        last = posts[-1]

        self.page.goto(self.live_server_url + last.get_absolute_url())

        expect(self.page).to_have_url(re.compile(r'page=2#p%d$' % last.id))
        expect(self.page.locator('#post-%d' % last.id)).to_be_in_viewport()

    def test_a_strangers_post_is_highlighted_on_either_card_colour(self):
        stranger = User.objects.create_user('newbie', '', 'pw')
        authors = [self.member, self.member, stranger, stranger]
        posts = [add_post(self.topic, author) for author in authors]

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        def background(post):
            # The post's header bar, above its body.
            divider = self.page.locator(
                '#post-%d .medium-9 .sg101-card-divider' % post.id).first
            return divider.evaluate('e => getComputedStyle(e).backgroundColor')

        odd, even, stranger_odd, stranger_even = map(background, posts)
        self.assertNotEqual(stranger_odd, odd)
        self.assertNotEqual(stranger_even, even)
        self.assertEqual(stranger_odd, stranger_even)

    def test_the_tools_sit_on_the_bottom_of_a_short_post(self):
        # The author card is the taller here, and the post card is stretched
        # to match; the spare height belongs above the tools, not below them.
        self.member.profile.location = 'Huntington Beach, California'
        self.member.profile.country = 'us'
        self.member.profile.save(content_update=False)
        post = add_post(self.topic, self.member, body='Short.')
        self.page.set_viewport_size({'width': 1280, 'height': 900})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        card = self.page.locator('#post-%d .medium-9 .sg101-card' % post.id)
        tools = card.locator('.forum-post-tools')
        card_box, tools_box = card.bounding_box(), tools.bounding_box()
        gap = (card_box['y'] + card_box['height']) - (tools_box['y'] + tools_box['height'])
        # Within a pixel: the card's bottom border.
        self.assertLessEqual(gap, 1)

    def test_the_tools_sit_right_with_the_stranger_tools_below(self):
        moderator = User.objects.create_user('mod', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        moderator.groups.add(mod_group)
        self.topic.forum.moderators.add(mod_group)
        stranger = User.objects.create_user('newbie', '', 'pw')
        post = add_post(self.topic, stranger)
        self.login(moderator)
        self.page.set_viewport_size({'width': 1280, 'height': 900})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        tools = self.page.locator('#post-%d .forum-post-tools' % post.id)
        right = tools.evaluate(
            'e => e.getBoundingClientRect().right - parseFloat(getComputedStyle(e).paddingRight)')
        icons = tools.locator('.forum-post-tool-icons').bounding_box()
        stranger_tools = tools.locator('.forum-post-stranger-tools').bounding_box()
        # Each line of tools ends at the section's right edge, and the
        # stranger tools start below the others.
        for box in (icons, stranger_tools):
            self.assertLessEqual(abs(right - (box['x'] + box['width'])), 1)
        self.assertGreaterEqual(stranger_tools['y'], icons['y'] + icons['height'])

    def test_what_is_about_the_post_steps_back_from_it(self):
        self.member.profile.signature = 'Keep on surfin'
        self.member.profile.save()
        post = add_post(self.topic, self.member, body='The post itself.')
        Post.objects.filter(pk=post.pk).update(
            update_date=post.creation_date + datetime.timedelta(hours=1))
        self.page.set_viewport_size({'width': 1280, 'height': 900})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        section = self.page.locator('#post-%d .medium-9 .card-section' % post.id).first
        style = ('e => { const s = getComputedStyle(e);'
                 ' return [parseFloat(s.fontSize), s.color]; }')
        body_size, body_colour = section.locator('p', has_text='The post itself.').evaluate(style)
        details = self.page.locator('#post-%d .forum-post-author-details' % post.id)
        parts = {
            'signature': section.locator('.forum-post-signature'),
            'edit note': section.locator('.forum-post-edited'),
            'author details': details,
        }
        for part, locator in parts.items():
            with self.subTest(part=part):
                size, colour = locator.evaluate(style)
                self.assertLess(size, body_size)
                self.assertNotEqual(colour, body_colour)
        rule = section.locator('.forum-post-signature hr').bounding_box()
        self.assertLess(rule['width'], section.bounding_box()['width'] / 2)


class TopicScriptTestCase(BrowserTestCase):
    """The topic page's script: quick reply, flag and delete, in place."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.moderator = User.objects.create_user('mod', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        self.moderator.groups.add(mod_group)
        self.forum.moderators.add(mod_group)
        self.topic = make_topic(self.forum, self.member)
        self.first = add_post(self.topic, self.member, body='the first post')
        self.second = add_post(self.topic, self.member, body='the second post')

    def open_topic(self, user):
        self.login(user)
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

    def answer_dialogs(self, accept):
        """Accept or dismiss every dialog; return the list of their types."""
        seen = []

        def handle(dialog):
            seen.append(dialog.type)
            if accept:
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.on('dialog', handle)
        return seen

    def card_colour(self, row):
        return row.locator('.medium-9 .sg101-card').evaluate(
            'e => getComputedStyle(e).backgroundColor')

    def assertFlagReplyShown(self, post):
        # In the post's own card, under the post, not in the author's card.
        callout = self.page.locator('#post-%d .medium-9 .callout' % post.id)
        expect(callout).to_be_visible()
        expect(callout).to_contain_text('The post was flagged')

    def reply(self, text):
        self.page.locator('.v3-editor textarea').fill(text)
        self.page.locator('#forums-reply-post').click()

    def test_quick_reply_appends_the_post_and_clears_the_box(self):
        self.open_topic(self.member)
        seen = self.answer_dialogs(accept=True)
        self.page.evaluate('window.notReloaded = true')

        self.reply('a quick reply')

        rows = self.page.locator('#forum-topic-post-container > .row')
        expect(rows).to_have_count(3)
        expect(rows.last).to_contain_text('a quick reply')
        self.assertNotEqual(self.card_colour(rows.last), self.card_colour(rows.nth(1)))
        expect(self.page.locator('.v3-editor textarea')).to_have_value('')
        expect(self.page.locator('#forums-reply-post')).to_be_enabled()
        self.assertTrue(self.page.evaluate('window.notReloaded === true'))
        self.assertTrue(Post.objects.filter(body='a quick reply').exists())
        self.assertNotIn('alert', seen)

    def test_a_refused_reply_keeps_its_text(self):
        self.open_topic(self.member)
        seen = self.answer_dialogs(accept=True)
        Topic.objects.filter(pk=self.topic.pk).update(locked=True)

        self.reply('my carefully written reply')

        expect(self.page.get_by_text("You don't have permission to post")).to_be_visible()
        expect(self.page.locator('.v3-editor textarea')).to_have_value(
            'my carefully written reply')
        expect(self.page.locator('#forums-reply-post')).to_be_enabled()
        expect(self.page.locator('#forum-topic-post-container > .row')).to_have_count(2)
        self.assertNotIn('alert', seen)

    def test_flag_shows_the_servers_reply_on_the_post(self):
        self.open_topic(self.member)
        seen = self.answer_dialogs(accept=True)

        self.page.locator('#post-%d .post-flag' % self.first.id).click()

        self.assertFlagReplyShown(self.first)
        self.assertTrue(FlaggedPost.objects.filter(post=self.first).exists())
        self.assertEqual(seen, ['confirm'])

    def test_flag_shows_its_reply_on_a_phone(self):
        # The author card is hidden there, so a reply put in it is never seen.
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.open_topic(self.member)
        self.answer_dialogs(accept=True)

        self.page.locator('#post-%d .post-flag' % self.first.id).click()

        self.assertFlagReplyShown(self.first)

    def test_a_cancelled_flag_does_nothing(self):
        self.open_topic(self.member)
        seen = self.answer_dialogs(accept=False)

        self.page.locator('#post-%d .post-flag' % self.first.id).click()
        self.page.wait_for_timeout(500)

        self.assertEqual(seen, ['confirm'])
        self.assertFalse(FlaggedPost.objects.exists())
        expect(self.page.locator('#post-%d .callout' % self.first.id)).to_have_count(0)

    def test_a_moderator_deletes_a_post(self):
        self.open_topic(self.moderator)
        seen = self.answer_dialogs(accept=True)

        self.page.locator('#post-%d .post-delete' % self.second.id).click()

        expect(self.page.locator('#post-%d' % self.second.id)).to_have_count(0)
        expect(self.page.locator('#post-%d' % self.first.id)).to_be_visible()
        self.assertFalse(Post.objects.filter(pk=self.second.pk).exists())
        self.assertEqual(seen, ['confirm'])

    def test_flag_works_on_a_quick_reply(self):
        self.open_topic(self.member)
        seen = self.answer_dialogs(accept=True)
        self.reply('flag me')
        expect(self.page.locator('#forum-topic-post-container > .row')).to_have_count(3)
        post = Post.objects.get(body='flag me')

        self.page.locator('#post-%d .post-flag' % post.id).click()

        self.assertFlagReplyShown(post)
        self.assertTrue(FlaggedPost.objects.filter(post=post).exists())
        self.assertNotIn('alert', seen)

    def test_a_cancelled_topic_delete_keeps_the_topic(self):
        self.open_topic(self.moderator)
        url = self.page.url
        seen = self.answer_dialogs(accept=False)

        self.page.locator('#forum-mod-del-topic').click()
        self.page.wait_for_timeout(500)

        self.assertEqual(seen, ['confirm'])
        self.assertEqual(self.page.url, url)
        self.assertTrue(Topic.objects.filter(pk=self.topic.pk).exists())
