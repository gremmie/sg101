"""Browser tests for the forums' pages."""
import datetime
import re

from django.contrib.auth.models import Group, User
from playwright.sync_api import expect

from bio.models import STA_ACTIVE
from core.tests.browser import BrowserTestCase
from forums.models import Forum, Post
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
