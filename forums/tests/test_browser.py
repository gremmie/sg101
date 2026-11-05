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
        user = User.objects.create_user('pjmoto', '', 'pw')
        topic = make_topic(Forum.objects.get(slug='shallow-end'), user)
        add_post(topic, user)
        self.login(user)
        self.page.goto(self.live_server_url + topic.get_absolute_url())

    def test_the_reply_box_is_the_working_post_box(self):
        # A module that fails to load raises no page error, only a console
        # one, so this uses the post box to show it loaded.
        textarea = self.page.locator('.v3-editor textarea')
        textarea.fill('hello world')
        textarea.evaluate('t => { t.focus(); t.setSelectionRange(6, 11); }')
        self.page.locator('.editor-bold').click()
        expect(textarea).to_have_value('hello **world**')
