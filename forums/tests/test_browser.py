"""Browser tests for the forums' pages."""
import datetime
import re

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.urls import reverse
from playwright.sync_api import expect

from bio.models import STA_ACTIVE
from core.tests.browser import BrowserTestCase
from forums.models import Attachment, FlaggedPost, Forum, Post, Topic
from forums.tests.test_moderation import add_post, make_topic
from forums.views.main import POSTS_PER_PAGE
from oembed.models import Oembed
from search.models import SearchDocument


# The players' own requests, answered by the tests so nothing leaves them.
PLAYERS = re.compile(r'^https://(www\.youtube\.com|player\.vimeo\.com|w\.soundcloud\.com)/')


def add_video(page, url):
    """Attaches the video at url through the post box's video modal."""
    page.locator('.editor-video').click()
    modal = page.locator('#video-modal')
    expect(modal).to_be_visible()
    modal.locator('input[name="q"]').fill(url)
    modal.locator('#video-form-submit').click()


def boxes(page, *selectors):
    """The boxes of the elements selected, measured together, so a reflow can't
    fall between one measurement and the next."""
    return page.evaluate('''(selectors) => selectors.map((s) => {
        const r = document.querySelector(s).getBoundingClientRect();
        return {x: r.x, y: r.y, width: r.width, height: r.height};
    })''', list(selectors))


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

    def test_quiet_text_is_one_grey(self):
        self.member.profile.signature = 'Keep on surfin'
        self.member.profile.save()
        post = add_post(self.topic, self.member)
        Post.objects.filter(pk=post.pk).update(
            update_date=post.creation_date + datetime.timedelta(hours=1))
        self.page.set_viewport_size({'width': 1280, 'height': 900})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        styles = self.page.locator('.quiet').evaluate_all(
            'es => es.map(e => { const s = getComputedStyle(e);'
            ' return [e.className, s.color, s.fontSize]; })')
        # The posted date, the "Top" links, and what is about the post: the
        # author's details, the edit note and the signature.
        self.assertGreaterEqual(len(styles), 6)
        for name, colour, size in styles:
            with self.subTest(element=name):
                self.assertEqual((colour, size), ('rgb(85, 85, 85)', '14px'))

    def test_the_top_links_look_like_links(self):
        add_post(self.topic, self.member)
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        tops = self.page.locator('a[href="#top"]')
        # One under the post, one under the topic.
        self.assertEqual(tops.count(), 2)
        # A link in a card's body; the header's links are a darker shade.
        link_colour = self.page.evaluate(
            'getComputedStyle(document.querySelector('
            '".sg101-card .card-section a")).color')
        for colour, size in tops.evaluate_all(
                'es => es.map(e => { const s = getComputedStyle(e);'
                ' return [s.color, s.fontSize]; })'):
            self.assertEqual((colour, size), (link_colour, '14px'))

    def phone_avatar(self, post):
        return self.page.locator('#post-%d .forum-post-phone-avatar img' % post.id)

    def test_a_phone_shows_a_small_avatar_beside_the_name_and_date(self):
        post = add_post(self.topic, self.member)
        self.page.set_viewport_size({'width': 360, 'height': 800})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        avatar = self.phone_avatar(post)
        expect(avatar).to_be_visible()
        header = '#post-%d .medium-9 .sg101-card-divider .hide-for-medium' % post.id
        avatar_box, text_box = boxes(
            self.page, header + ' .forum-post-phone-avatar img',
            header + ' .forum-post-phone-byline')
        self.assertEqual((avatar_box['width'], avatar_box['height']), (40, 40))
        # Left of the name and date, and no taller than them, so the header
        # is the height it was without it.
        self.assertLessEqual(avatar_box['x'] + avatar_box['width'], text_box['x'])
        self.assertLessEqual(avatar_box['height'], text_box['height'])

    def test_a_phone_avatar_that_is_not_square_is_cropped_not_stretched(self):
        # An upload narrower than the limit is never cropped square.
        post = add_post(self.topic, self.member)
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())
        avatar = self.phone_avatar(post)

        avatar.evaluate('''img => new Promise((resolve) => {
            img.onload = resolve;
            img.src = 'data:image/svg+xml,' + encodeURIComponent(
                '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="60"/>');
        })''')

        box = avatar.bounding_box()
        self.assertEqual((box['width'], box['height']), (40, 40))
        self.assertEqual(avatar.evaluate('e => getComputedStyle(e).objectFit'), 'cover')

    def test_the_phone_avatar_is_not_a_second_link_to_the_profile(self):
        post = add_post(self.topic, self.member)
        self.page.set_viewport_size({'width': 360, 'height': 800})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        holder = self.page.locator('#post-%d .forum-post-phone-avatar' % post.id)
        self.assertEqual(holder.locator('a').count(), 0)
        self.assertEqual(holder.get_attribute('aria-hidden'), 'true')

    def test_the_desktop_has_only_the_author_cards_avatar(self):
        post = add_post(self.topic, self.member)
        self.page.set_viewport_size({'width': 1280, 'height': 900})

        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

        expect(self.phone_avatar(post)).to_be_hidden()
        expect(self.page.locator(
            '#post-%d .forum-post-avatar img' % post.id)).to_be_visible()


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
        # Another member's posts: a post's own author has no flag.
        self.author = User.objects.create_user('author', '', 'pw')
        self.topic = make_topic(self.forum, self.author)
        self.first = add_post(self.topic, self.author, body='the first post')
        self.second = add_post(self.topic, self.author, body='the second post')

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

    def test_tools_work_on_a_quick_reply(self):
        # A quick reply is the poster's own, so it has no flag; a moderator's
        # delete is the tool to try on it.
        self.open_topic(self.moderator)
        seen = self.answer_dialogs(accept=True)
        self.reply('delete me')
        expect(self.page.locator('#forum-topic-post-container > .row')).to_have_count(3)
        post = Post.objects.get(body='delete me')

        self.page.locator('#post-%d .post-delete' % post.id).click()

        expect(self.page.locator('#post-%d' % post.id)).to_have_count(0)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
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


class VideoAttachmentTestCase(BrowserTestCase):
    """The quick reply's video button and attachment list, in a real browser."""
    fixtures = ['forums.json']
    VIDEO_URL = 'https://www.youtube.com/watch?v=sg101test'
    # The fetch view answers from this row, and the players' requests are
    # answered by the test, so nothing leaves it.
    EMBED = ('<iframe width="480" height="270" src="https://www.youtube.com/embed/sg101test"'
             ' title="test video"></iframe>')

    def setUp(self):
        super().setUp()
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.author = User.objects.create_user('author', '', 'pw')
        self.topic = make_topic(Forum.objects.get(slug='shallow-end'), self.author)
        self.first = add_post(self.topic, self.author, body='the first post')
        self.embed = Oembed.objects.create(
            url=self.VIDEO_URL, type=Oembed.VIDEO, title='test video',
            width=480, height=270, html=self.EMBED)
        self.dialogs = []
        self.page.on('dialog', lambda dialog: (self.dialogs.append(dialog.type),
                                               dialog.dismiss()))
        self.context.route(PLAYERS, lambda route: route.fulfill(
            content_type='text/html', body='<html><body></body></html>'))

    def open_topic(self):
        self.login(self.member)
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

    def entries(self):
        return self.page.locator('form [data-attachments] .forum-attachment-entry')

    def add_video(self, url=VIDEO_URL):
        add_video(self.page, url)

    def reply(self, text):
        """Sends a quick reply; returns the request's body once it is answered.

        Waiting for the answer keeps the server's work inside the test: a
        request still running when the test's tables are flushed deadlocks
        with the flush.
        """
        self.page.locator('.v3-editor textarea').fill(text)
        with self.page.expect_response('**/forums/quick-reply/') as response:
            self.page.locator('#forums-reply-post').click()
        response.value.finished()
        return response.value.request.post_data

    def attachments_box(self):
        return self.page.locator('fieldset.forum-post-form .forum-post-attachments')

    def test_the_attachments_box_shows_only_while_it_holds_a_video(self):
        self.open_topic()
        expect(self.attachments_box()).to_be_hidden()
        self.add_video()
        expect(self.entries()).to_have_count(1)
        expect(self.attachments_box()).to_be_visible()
        self.entries().first.locator('.attachment-remove').click()
        expect(self.entries()).to_have_count(0)
        expect(self.attachments_box()).to_be_hidden()

    def test_editing_a_post_with_a_video_shows_the_attachments_box(self):
        post = add_post(self.topic, self.member, body='a post with a video')
        Attachment.objects.create(post=post, embed=self.embed, order=0)
        self.login(self.member)
        self.page.goto(self.live_server_url + reverse('forums-edit_post', kwargs={'id': post.id}))
        expect(self.entries()).to_have_count(1)
        expect(self.attachments_box()).to_be_visible()

    def test_an_added_video_is_sent_with_the_reply(self):
        self.open_topic()
        self.add_video()

        expect(self.page.locator('#video-modal')).to_be_hidden()
        expect(self.entries()).to_have_count(1)
        expect(self.entries().locator('iframe[title="test video"]')).to_be_attached()
        body = self.reply('a reply with a video')

        self.assertIn('name="attachment"\r\n\r\n%d\r\n' % self.embed.pk, body)
        rows = self.page.locator('#forum-topic-post-container > .row')
        expect(rows).to_have_count(2)
        expect(rows.last.locator('.forum-attachment iframe[title="test video"]')).to_be_attached()
        expect(self.entries()).to_have_count(0)
        post = Post.objects.get(body='a reply with a video')
        self.assertEqual(list(post.attachments.all()), [self.embed])
        self.assertEqual(self.dialogs, [])

    def test_a_removed_video_is_not_sent(self):
        self.open_topic()
        self.add_video()
        expect(self.entries()).to_have_count(1)

        self.entries().locator('.attachment-remove').click()

        expect(self.entries()).to_have_count(0)
        body = self.reply('changed my mind')
        self.assertNotIn('name="attachment"', body)

    def test_a_refused_video_says_why_in_the_modal(self):
        self.page.route('**/oembed/fetch/', lambda route: route.fulfill(
            status=400, content_type='text/plain',
            body='Sorry, we could not retrieve your video (test)'))
        self.open_topic()

        self.add_video('https://www.youtube.com/watch?v=nosuchvideo')

        status = self.page.locator('#video-status')
        expect(status).to_be_visible()
        expect(status).to_have_text('Sorry, we could not retrieve your video (test)')
        expect(self.page.locator('#video-modal')).to_be_visible()
        expect(self.page.locator('#video-modal input[name="q"]')).to_have_value(
            'https://www.youtube.com/watch?v=nosuchvideo')
        expect(self.entries()).to_have_count(0)
        self.assertEqual(self.dialogs, [])

    def test_a_refused_reply_keeps_its_videos(self):
        self.open_topic()
        self.add_video()
        expect(self.entries()).to_have_count(1)
        Topic.objects.filter(pk=self.topic.pk).update(locked=True)

        self.reply('my reply')

        expect(self.page.get_by_text("You don't have permission to post")).to_be_visible()
        expect(self.entries()).to_have_count(1)

    def width_overrun(self, iframe, box):
        """How far the iframe's right edge passes its box's content edge."""
        return iframe.evaluate(
            """(frame, box) => {
                  const inner = box.getBoundingClientRect().left + box.clientLeft
                     + box.clientWidth - parseFloat(getComputedStyle(box).paddingRight);
                  return frame.getBoundingClientRect().right - inner;
               }""", box.element_handle())

    def test_a_posted_video_fits_its_card_on_a_phone(self):
        Attachment.objects.create(post=self.first, embed=self.embed, order=0)
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.open_topic()

        card = self.page.locator('#post-%d .card-section:has(.forum-attachment)' % self.first.id)
        iframe = card.locator('.forum-attachment iframe')
        expect(iframe).to_be_attached()
        self.assertLessEqual(self.width_overrun(iframe, card), 0)

    def test_an_attached_video_fits_the_form_on_a_phone(self):
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.open_topic()
        self.add_video()

        # A fieldset is never narrower than its contents, so a video too wide
        # widens the list with it, and the page.
        iframe = self.entries().locator('iframe')
        expect(iframe).to_be_attached()
        overrun = iframe.evaluate('f => f.getBoundingClientRect().right - window.innerWidth')
        self.assertLessEqual(overrun, 0)
        self.assertLessEqual(self.page.evaluate(
            'document.documentElement.scrollWidth - window.innerWidth'), 0)

    def frame_size(self, iframe):
        """The iframe's width and height, the content width of its box, and
        the height of what holds it."""
        return iframe.evaluate("""f => {
              const box = f.closest('.card-section, [data-attachments]');
              const cs = getComputedStyle(box);
              const r = f.getBoundingClientRect();
              return {w: r.width, h: r.height, box: box.clientWidth
                 - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
                 around: f.parentElement.getBoundingClientRect().height};
           }""")

    def assertFillsAt16x9(self, iframe):
        size = self.frame_size(iframe)
        self.assertAlmostEqual(size['w'], size['box'], delta=1)
        self.assertAlmostEqual(size['w'] / size['h'], 16 / 9, delta=0.02)
        # Nothing around it holds a taller space open below it. An inline
        # iframe sits on a text line, so a few pixels of the line show.
        self.assertLess(size['around'] - size['h'], 8)

    def posted(self, html, url):
        embed = Oembed.objects.create(url=url, type=Oembed.VIDEO, title='posted',
                                      width=480, height=270, html=html)
        Attachment.objects.create(post=self.first, embed=embed, order=0)
        return self.page.locator('#post-%d .forum-attachment iframe' % self.first.id)

    def test_a_posted_video_fills_its_card_at_16_9(self):
        iframe = self.posted(self.EMBED, 'https://www.youtube.com/watch?v=posted')
        for width in (360, 1280):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width': width, 'height': 800})
                self.open_topic()
                expect(iframe).to_be_attached()
                self.assertFillsAt16x9(iframe)

    def test_a_posted_vimeo_video_is_16_9_too(self):
        iframe = self.posted(
            '<iframe src="https://player.vimeo.com/video/1" width="480" height="270"></iframe>',
            'https://vimeo.com/1')
        self.open_topic()
        expect(iframe).to_be_attached()
        self.assertFillsAt16x9(iframe)

    def test_an_added_video_and_its_reply_are_16_9(self):
        # Neither was in the page when it loaded.
        self.page.set_viewport_size({'width': 1280, 'height': 800})
        self.open_topic()
        self.add_video()
        expect(self.entries()).to_have_count(1)
        self.assertFillsAt16x9(self.entries().locator('iframe'))

        self.reply('a reply with a video')

        rows = self.page.locator('#forum-topic-post-container > .row')
        expect(rows).to_have_count(2)
        self.assertFillsAt16x9(rows.last.locator('.forum-attachment iframe'))

    def test_a_player_that_is_not_a_video_keeps_its_height(self):
        iframe = self.posted(
            '<iframe width="480" height="295" src="https://w.soundcloud.com/player/?t=1">'
            '</iframe>', 'https://soundcloud.com/a/b')
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.open_topic()
        expect(iframe).to_be_attached()
        size = self.frame_size(iframe)
        self.assertLessEqual(size['w'], size['box'])
        self.assertEqual(size['h'], 295)


class PostingPagesBrowserTestCase(BrowserTestCase):
    """New topic, new post and edit post, and the new topic's Quick Search."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.embeds = [Oembed.objects.create(
            url='https://www.youtube.com/watch?v=%s' % name, type=Oembed.VIDEO,
            title=name, width=480, height=270,
            html='<iframe width="480" height="270" src="https://www.youtube.com/embed/%s"'
                 ' title="%s"></iframe>' % (name, name))
            for name in ('one', 'two')]
        self.context.route(PLAYERS, lambda route: route.fulfill(
            content_type='text/html', body='<html><body></body></html>'))
        self.dialogs = []
        self.accept_dialogs = False
        self.page.on('dialog', lambda dialog: (
            self.dialogs.append(dialog.type),
            dialog.accept() if self.accept_dialogs else dialog.dismiss()))
        self.requests = []
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.login(self.member)

    def goto(self, name, **kwargs):
        self.page.goto(self.live_server_url + reverse(name, kwargs=kwargs))

    def submit(self):
        with self.page.expect_navigation():
            self.page.locator('#forum-post-submit').click()

    def entries(self):
        return self.page.locator('form [data-attachments] .forum-attachment-entry')

    def test_start_a_topic_reply_with_a_quote_then_edit_the_reply(self):
        one, two = self.embeds
        self.goto('forums-new_topic', slug=self.forum.slug)
        self.page.locator('#id_name').fill('Reverb tanks')
        self.page.locator('.v3-editor textarea').fill('Which tank?')
        add_video(self.page, one.url)
        expect(self.entries()).to_have_count(1)
        self.submit()
        topic = Topic.objects.get(name='Reverb tanks')
        first = topic.posts.get()
        self.assertEqual(list(first.attachments.all()), [one])

        self.page.goto('%s%s?quote=%d' % (
            self.live_server_url,
            reverse('forums-new_post', kwargs={'topic_id': topic.id}), first.id))
        textarea = self.page.locator('.v3-editor textarea')
        expect(textarea).to_have_value(re.compile(r'> Which tank\?'))
        add_video(self.page, two.url)
        expect(self.entries()).to_have_count(1)
        self.submit()
        reply = topic.posts.exclude(pk=first.pk).get()
        self.assertEqual(list(reply.attachments.all()), [two])

        self.goto('forums-edit_post', id=reply.id)
        expect(self.entries()).to_have_count(1)
        add_video(self.page, one.url)
        expect(self.entries()).to_have_count(2)
        self.submit()
        self.assertEqual(list(reply.attachments.order_by('attachment__order')), [two, one])

        self.assertFalse([url for url in self.requests if 'fetch_' in url and 'fetch/' not in url])
        self.assertEqual(self.dialogs, [])

    def test_quick_search_shows_matches_under_the_subject(self):
        topic = make_topic(self.forum, self.member, name='Reverb tank drip')
        SearchDocument.objects.index_object(topic)
        self.goto('forums-new_topic', slug=self.forum.slug)

        self.page.locator('#id_name').fill('reverb')
        self.page.locator('#quick-search').click()

        results = self.page.locator('[data-quick-search] #quick-search-results')
        expect(results).to_be_visible()
        expect(results.get_by_role('link', name='Reverb tank drip')).to_be_visible()
        expect(self.page.locator('#quick-search')).to_be_enabled()

        results.get_by_role('button', name='Hide').click()

        expect(self.page.locator('#quick-search-results')).to_have_count(0)
        self.assertEqual(self.dialogs, [])

    def test_quick_search_is_an_icon_and_search_and_says_searching_while_busy(self):
        held = []
        self.page.route('**/search/topics/**', lambda route: held.append(route))
        self.goto('forums-new_topic', slug=self.forum.slug)
        button = self.page.locator('#quick-search')
        icon = button.locator('i.fi-magnifying-glass')
        expect(button).to_have_text('Search')
        expect(icon).to_be_visible()

        self.page.locator('#id_name').fill('reverb')
        button.click()
        expect(button).to_have_text('Searching…')
        expect(button).to_be_disabled()
        expect(icon).to_be_visible()
        while not held:
            self.page.wait_for_timeout(50)
        held[0].continue_()

        expect(self.page.locator('#quick-search-results')).to_be_visible()
        expect(button).to_have_text('Search')
        expect(button).to_be_enabled()
        expect(icon).to_be_visible()

    def test_quick_search_errors_show_in_a_callout(self):
        self.page.route('**/search/topics/**', lambda route: route.fulfill(
            status=500, content_type='text/plain', body='Search is resting'))
        self.goto('forums-new_topic', slug=self.forum.slug)

        self.page.locator('#id_name').fill('reverb')
        self.page.locator('#quick-search').click()

        expect(self.page.locator('[data-quick-search] .callout')).to_have_text(
            'Search is resting')
        expect(self.page.locator('#quick-search')).to_be_enabled()
        self.assertEqual(self.dialogs, [])

    def test_quick_search_is_beside_the_subject_on_desktop_and_under_it_on_a_phone(self):
        # Each width is a fresh load: a resize reflows the header while it is measured.
        self.page.set_viewport_size({'width': 1280, 'height': 900})
        self.goto('forums-new_topic', slug=self.forum.slug)
        field, search = boxes(self.page, '#id_name', '#quick-search')
        # On the subject's line, the same height, filling the rest of it.
        self.assertAlmostEqual(search['y'], field['y'], delta=1)
        self.assertAlmostEqual(search['height'], field['height'], delta=1)
        self.assertGreater(search['x'], field['x'] + field['width'])
        self.assertLess(search['x'] - (field['x'] + field['width']), 24)
        self.assertGreater(field['width'], 4 * search['width'])

        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.goto('forums-new_topic', slug=self.forum.slug)
        field, search = boxes(self.page, '#id_name', '#quick-search')
        self.assertGreaterEqual(search['y'], field['y'] + field['height'])
        self.assertEqual(self.page.evaluate(
            'document.documentElement.scrollWidth > window.innerWidth'), False)

    def test_quick_search_has_the_same_gap_between_icon_and_words_at_each_width(self):
        gaps = []
        for width in (1280, 360):
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.goto('forums-new_topic', slug=self.forum.slug)
            left, right = boxes(self.page, '#quick-search i', '#quick-search span')
            gaps.append(right['x'] - (left['x'] + left['width']))
        for gap in gaps:
            self.assertGreaterEqual(gap, 3)
        self.assertAlmostEqual(gaps[0], gaps[1], delta=0.5)

    def test_quick_search_without_a_subject_asks_for_one(self):
        self.goto('forums-new_topic', slug=self.forum.slug)

        self.page.locator('#quick-search').click()

        expect(self.page.locator('[data-quick-search] .callout')).to_be_visible()
        self.assertFalse([url for url in self.requests if '/search/topics/' in url])

    def test_the_edit_pages_card_tools_work(self):
        # A moderator editing another member's post has the card's flag.
        moderator = User.objects.create_user('mod', '', 'pw')
        mod_group = Group.objects.get(name='Forum Moderators')
        moderator.groups.add(mod_group)
        self.forum.moderators.add(mod_group)
        topic = make_topic(self.forum, self.member)
        post = add_post(topic, self.member, body='flag me')
        self.context.clear_cookies()
        self.login(moderator)
        self.accept_dialogs = True
        self.goto('forums-edit_post', id=post.id)

        self.page.locator('#post-%d .post-flag' % post.id).click()

        expect(self.page.locator('#post-%d .callout' % post.id)).to_contain_text(
            'The post was flagged')
        self.assertTrue(FlaggedPost.objects.filter(post=post).exists())


class ForumNavBrowserTestCase(BrowserTestCase):
    """The select boxes that take a member to a forum or a list of topics."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        self.forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.topic = make_topic(self.forum, self.member)
        add_post(self.topic, self.member)
        self.login(self.member)

    def choose_and_go(self, start, label, destination):
        self.page.goto(self.live_server_url + start)
        box = self.page.locator('[data-forum-nav]')
        box.locator('select').select_option(label=label)
        box.get_by_role('button', name='Go').click()
        expect(self.page).to_have_url(self.live_server_url + destination)

    def test_the_topic_pages_jump_box_goes_to_the_chosen_forum(self):
        self.choose_and_go(self.topic.get_absolute_url(), 'Gear',
                           reverse('forums-forum_index', kwargs={'slug': 'gear'}))

    def test_the_forum_pages_jump_box_goes_to_the_chosen_forum(self):
        self.choose_and_go(
            reverse('forums-forum_index', kwargs={'slug': self.forum.slug}),
            'Surf Videos',
            reverse('forums-forum_index', kwargs={'slug': 'surf-videos'}))

    def test_the_index_query_box_goes_to_the_chosen_list(self):
        self.choose_and_go(reverse('forums-index'), 'Show unanswered topics',
                           reverse('forums-unanswered_topics'))


class PostListBrowserTestCase(BrowserTestCase):
    """A member's posts are listed as cards, each as tall as its post."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        topic = make_topic(forum, self.member)
        add_post(topic, self.member, body='A short post.')
        add_post(topic, self.member, body='Another short post.')
        self.login(self.member)

    def test_each_card_is_as_tall_as_its_post(self):
        self.page.goto(self.live_server_url + reverse('forums-my_posts'))
        cards = self.page.evaluate('''() => Array.from(
            document.querySelectorAll('.sg101-card'), (card) => {
                const r = card.getBoundingClientRect();
                const body = card.querySelector('.card-section p').getBoundingClientRect();
                return {top: r.top, bottom: r.bottom, bodyBottom: body.bottom};
            })''')

        self.assertEqual(len(cards), 2)
        for card in cards:
            # The card ends below its one line of text by no more than its padding.
            self.assertLess(card['bottom'] - card['bodyBottom'], 50)
        # The second card follows the first with only the gap between them.
        self.assertLess(cards[1]['top'] - cards[0]['bottom'], 50)


class ManageTopicsBrowserTestCase(BrowserTestCase):
    """The favorites page's master checkbox, and the warning and question
    asked before anything is removed."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.topics = []
        for name in ('First topic', 'Second topic', 'Third topic'):
            topic = make_topic(forum, self.member, name=name)
            add_post(topic, self.member)
            self.member.favorite_topics.add(topic)
            self.topics.append(topic)
        self.login(self.member)
        self.page.goto(self.live_server_url + reverse('forums-manage_favorites'))
        self.master = self.page.locator('[data-check-all]')
        self.boxes = self.page.locator('[data-check-item]')

        self.posts = []
        self.page.on('request', lambda request: request.method == 'POST'
                     and self.posts.append(request.url))

    def answer_dialogs(self, accept):
        """Accept or dismiss every dialog; return what each said."""
        seen = []

        def handle(dialog):
            seen.append((dialog.type, dialog.message))
            if accept:
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.on('dialog', handle)
        return seen

    def tick(self, *names):
        for name in names:
            self.page.get_by_role('checkbox', name='Select %s' % name).check()

    def submit(self):
        self.page.get_by_role('button', name='Delete Selected').click()

    def favorites(self):
        return set(self.member.favorite_topics.values_list('name', flat=True))

    def test_the_master_checks_and_unchecks_every_box(self):
        self.assertEqual(self.boxes.count(), 3)
        self.master.check()
        for i in range(3):
            expect(self.boxes.nth(i)).to_be_checked()
        self.master.uncheck()
        for i in range(3):
            expect(self.boxes.nth(i)).not_to_be_checked()

    def test_unticking_one_box_unticks_the_master(self):
        self.master.check()
        self.boxes.nth(1).uncheck()
        expect(self.master).not_to_be_checked()
        expect(self.boxes.nth(0)).to_be_checked()
        expect(self.boxes.nth(2)).to_be_checked()

    def test_nothing_ticked_warns_and_posts_nothing(self):
        seen = self.answer_dialogs(accept=True)
        self.submit()
        self.assertEqual(seen, [('alert', 'Please select some topics to remove.')])
        self.assertEqual(self.posts, [])
        self.assertEqual(len(self.favorites()), 3)

    def test_dismissing_the_question_removes_nothing(self):
        seen = self.answer_dialogs(accept=False)
        self.tick('First topic', 'Third topic')
        self.submit()
        self.assertEqual(seen, [(
            'confirm', 'Are you sure you wish to remove the selected topics from your list?')])
        self.assertEqual(self.posts, [])
        self.assertEqual(len(self.favorites()), 3)

    def test_accepting_the_question_removes_exactly_the_ticked_topics(self):
        seen = self.answer_dialogs(accept=True)
        self.tick('First topic', 'Third topic')
        self.submit()
        expect(self.boxes).to_have_count(1)
        self.assertEqual([kind for kind, _ in seen], ['confirm'])
        self.assertEqual(self.favorites(), {'Second topic'})

    def test_on_a_phone_the_checkboxes_take_only_their_own_width(self):
        self.page.set_viewport_size({'width': 360, 'height': 800})
        self.page.reload()
        check, topic = (self.page.locator('tbody tr').first.locator('td').nth(i)
                        .evaluate('e => e.getBoundingClientRect().width')
                        for i in (0, 1))
        self.assertLess(check, 50)
        self.assertGreater(topic, 200)



class PaginationBrowserTestCase(BrowserTestCase):
    """Pagination on a phone: First, Previous, the page, Next and Last, as blue
    icon buttons on one line; on a wider screen, Previous, the numbers and
    Next, each button an icon and a word."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        forum = Forum.objects.get(slug='shallow-end')
        member = User.objects.create_user('pjmoto', '', 'pw')
        self.topic = make_topic(forum, member)
        for n in range(2 * POSTS_PER_PAGE + 5):
            add_post(self.topic, member, body='Post %d' % n)
        self.login(member)
        self.pagination = self.page.locator('ul.pagination').first

    def open(self, width, page):
        self.page.set_viewport_size({'width': width, 'height': 800})
        self.page.goto('%s%s?page=%d' % (self.live_server_url,
                                         self.topic.get_absolute_url(), page))

    def button(self, label):
        return self.pagination.get_by_role('link', name=label)

    def test_a_phone_gets_first_previous_the_page_next_and_last_on_one_line(self):
        # 320 px, the narrowest phone in common use.
        self.open(320, 2)
        labels = ('First page', 'Previous page', 'Next page', 'Last page')
        for label in labels:
            expect(self.button(label)).to_be_visible()
        status = self.pagination.locator('li', has_text='2 of 3')
        expect(status).to_be_visible()
        expect(self.pagination.get_by_role('link', name='Page 1')).to_be_hidden()
        expect(self.pagination.get_by_text('Previous', exact=True)).to_be_hidden()
        # Each icon is a glyph from the icon font, not an empty box.
        for icon in self.pagination.locator('.button i').all():
            self.assertNotIn(icon.evaluate(
                "e => getComputedStyle(e, '::before').content"), ('none', 'normal', ''))
        # The text item sits a pixel or two lower than the buttons; a wrapped
        # item would be a whole line lower.
        tops = [self.button(label).bounding_box()['y'] for label in labels]
        tops.append(status.bounding_box()['y'])
        self.assertLess(max(tops) - min(tops), 10)
        # The pagination itself, not the page: at 320 the signed-in header's
        # Logout button is wider than the screen on its own.
        right, scroll, client = self.pagination.evaluate(
            'u => [u.getBoundingClientRect().right, u.scrollWidth, u.clientWidth]')
        self.assertLessEqual(right, 320)
        self.assertLessEqual(scroll, client)

    def test_a_wider_screen_gets_previous_the_numbers_and_next(self):
        self.open(1280, 2)
        expect(self.button('Previous page')).to_have_text('Previous')
        expect(self.button('Next page')).to_have_text('Next')
        expect(self.pagination.get_by_text('Previous', exact=True)).to_be_visible()
        expect(self.pagination.get_by_text('Next', exact=True)).to_be_visible()
        expect(self.pagination.get_by_role('link', name='Page 1')).to_be_visible()
        expect(self.pagination.get_by_role('link', name='Page 3')).to_be_visible()
        expect(self.button('First page')).to_be_hidden()
        expect(self.button('Last page')).to_be_hidden()
        expect(self.pagination.locator('li', has_text='2 of 3')).to_be_hidden()

    def test_the_buttons_look_like_the_pages_other_buttons(self):
        self.open(1280, 2)
        colours = 'e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).color]'
        expected = self.page.locator('a.button', has_text='New Reply').first.evaluate(colours)
        for label in ('Previous page', 'Next page'):
            with self.subTest(button=label):
                self.assertEqual(self.button(label).evaluate(colours), expected)

    def test_on_a_phone_the_icon_buttons_are_the_same_width(self):
        self.open(360, 2)
        widths = [self.button(label).bounding_box()['width']
                  for label in ('First page', 'Previous page', 'Next page', 'Last page')]
        # The glyphs differ by a pixel or so; a hidden word's gap would add more.
        self.assertLess(max(widths) - min(widths), 2)

    def test_an_icon_does_not_make_its_button_taller(self):
        # On a wider screen, where the button keeps its word without the icon.
        self.open(1280, 2)
        button = self.button('Next page')
        with_icon = button.bounding_box()['height']
        button.locator('i').evaluate("e => e.style.display = 'none'")
        self.assertLess(with_icon - button.bounding_box()['height'], 2)

    def test_last_goes_to_the_last_page_and_greys_out_there(self):
        self.open(360, 1)
        self.button('Last page').click()
        expect(self.pagination.locator('li', has_text='3 of 3')).to_be_visible()
        self.assertEqual(self.button('Next page').count(), 0)
        self.assertEqual(self.button('Last page').count(), 0)


class ForumDensityBrowserTestCase(BrowserTestCase):
    """On wider screens the forum tables and a thread's post chrome are tighter
    than Foundation's defaults; phones keep the defaults. The exact sizes are
    the stylesheet's; these check the breakpoint, the one rule that changes
    behaviour, and that the rebuilt stylesheet is the one served."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        cache.clear()
        self.forum = Forum.objects.get(slug='shallow-end')
        member = User.objects.create_user('pjmoto', '', 'pw')
        self.topic = make_topic(self.forum, member, name='A sticky topic', sticky=True)
        add_post(self.topic, member)
        add_post(self.topic, member)
        self.forum_url = reverse('forums-forum_index', kwargs={'slug': self.forum.slug})
        self.post = '#forum-topic-post-container > .row'

    def open(self, width, url):
        self.page.set_viewport_size({'width': width, 'height': 900})
        self.page.goto(self.live_server_url + url)

    def style(self, selector, prop):
        return self.page.locator(selector).first.evaluate(
            '(e, p) => getComputedStyle(e)[p]', prop)

    def test_phones_keep_todays_spacing(self):
        self.open(360, reverse('forums-index'))
        self.assertEqual(self.style('h3.forum-category', 'fontSize'), '19px')
        self.assertEqual(self.style('table.forum-table td', 'padding'), '8px 10px 10px')
        self.assertEqual(self.style('table.forum-table td p', 'marginBottom'), '16px')

        self.open(360, self.forum_url)
        self.assertEqual(self.style('table.forum-table td i.fi-asterisk', 'fontSize'), '36px')

        self.open(360, self.topic.get_absolute_url())
        self.assertEqual(self.style(self.post + ' .medium-9 .sg101-card-divider', 'paddingTop'),
                         '16px')
        self.assertEqual(self.style(self.post + ' .forum-post-tools', 'paddingTop'), '16px')

    def test_the_last_posts_date_stays_on_one_line_only_on_wider_screens(self):
        time = 'table.forum-table .forum-last-post-time'
        self.open(1280, self.forum_url)
        self.assertEqual(self.style(time, 'whiteSpace'), 'nowrap')
        # One box per link and one for the space between: on one line, they
        # share a top.
        tops = self.page.locator(time).first.evaluate(
            'e => Array.from(e.getClientRects(), (r) => Math.round(r.top))')
        self.assertEqual(len(set(tops)), 1)
        # On a phone the Last Post column is 10rem wide, and the date must wrap.
        self.open(360, self.forum_url)
        self.assertEqual(self.style(time, 'whiteSpace'), 'normal')

    def test_wider_screens_get_the_tighter_layout(self):
        self.open(1280, reverse('forums-index'))
        self.assertEqual(self.style('table.forum-table td', 'padding'), '6px 10px')
        self.open(1280, self.topic.get_absolute_url())
        self.assertEqual(self.style(self.post + ' .medium-9 .sg101-card-divider', 'paddingTop'),
                         '8px')


class PostFormDensityBrowserTestCase(BrowserTestCase):
    """The forum's posting forms, the reply box and the new topic, new post and
    edit post pages, have a tighter box than Foundation's fieldset; other
    fieldsets keep its default."""
    fixtures = ['forums.json']

    def setUp(self):
        super().setUp()
        forum = Forum.objects.get(slug='shallow-end')
        self.member = User.objects.create_user('pjmoto', '', 'pw')
        self.topic = make_topic(forum, self.member)
        add_post(self.topic, self.member)
        self.login(self.member)

    def style(self, selector, prop):
        return self.page.locator(selector).first.evaluate(
            '(e, p) => getComputedStyle(e)[p]', prop)

    def assertTight(self, submit):
        form = 'fieldset.fieldset:has(%s)' % submit
        self.assertEqual(self.style(form, 'padding'), '12px')
        self.assertEqual(self.style(form + ' .forum-post-attachments', 'paddingTop'), '4px')
        self.assertEqual(self.style(submit, 'marginBottom'), '0px')

    def test_the_reply_box_and_the_posting_pages_are_tighter(self):
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())
        self.assertTight('#forums-reply-post')
        self.page.goto(self.live_server_url + reverse(
            'forums-new_post', kwargs={'topic_id': self.topic.id}))
        self.assertTight('#forum-post-submit')

    def test_other_fieldsets_keep_foundations_padding(self):
        self.page.goto(self.live_server_url + reverse('search'))
        self.assertEqual(self.style('fieldset.fieldset', 'padding'), '20px')
