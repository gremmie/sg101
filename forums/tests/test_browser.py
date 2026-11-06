"""Browser tests for the forums' pages."""
from django.contrib.auth.models import User
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase
from forums.models import Forum
from forums.tests.test_moderation import add_post, make_topic


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
