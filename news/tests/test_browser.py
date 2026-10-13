"""Browser tests for the news app's pages."""

from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase


class SubmitPostBoxTestCase(BrowserTestCase):
    """The post box on the story submission page, in a real browser.

    The page loads jQuery from ajax.googleapis.com, so these tests need
    outbound network access to Google's CDN.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.login(self.user)

    def test_upload_button_opens_the_upload_modal(self):
        # Foundation opens every Reveal modal; if its init fails, the page
        # still renders and the modal never appears.
        self.page.goto(self.live_server_url + reverse('news-submit'))
        self.page.locator('a.editor-upload[data-open="upload-modal"]').click()
        expect(self.page.locator('#upload-modal')).to_be_visible()
