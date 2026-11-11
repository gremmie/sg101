"""Browser tests for the forums' pages."""
import datetime
import re

from django.contrib.auth.models import Group, User
from playwright.sync_api import expect

from bio.models import STA_ACTIVE
from core.tests.browser import BrowserTestCase
from forums.models import Attachment, FlaggedPost, Forum, Post, Topic
from forums.tests.test_moderation import add_post, make_topic
from forums.views.main import POSTS_PER_PAGE
from oembed.models import Oembed


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
        link_colour = self.page.evaluate(
            'getComputedStyle(document.querySelector(".sg101-card a")).color')
        for colour, size in tops.evaluate_all(
                'es => es.map(e => { const s = getComputedStyle(e);'
                ' return [s.color, s.fontSize]; })'):
            self.assertEqual((colour, size), (link_colour, '14px'))


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
    PLAYERS = re.compile(r'^https://(www\.youtube\.com|player\.vimeo\.com|w\.soundcloud\.com)/')

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
        self.context.route(self.PLAYERS, lambda route: route.fulfill(
            content_type='text/html', body='<html><body></body></html>'))

    def open_topic(self):
        self.login(self.member)
        self.page.goto(self.live_server_url + self.topic.get_absolute_url())

    def entries(self):
        return self.page.locator('form [data-attachments] .forum-attachment-entry')

    def add_video(self, url=VIDEO_URL):
        self.page.locator('.editor-video').click()
        modal = self.page.locator('#video-modal')
        expect(modal).to_be_visible()
        modal.locator('input[name="q"]').fill(url)
        modal.locator('#video-form-submit').click()

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
