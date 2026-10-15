"""Browser tests for the bio app's pages."""
from django.contrib.auth.models import User
from django.urls import reverse
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase


# An allowed image host with https is returned as-is, without a fetch.
HOT_LINK_URL = 'https://surfguitar101.com/static/img/test.jpg'

CARET_TEXT = 'first\nsecond'
CARET = len('first')
IMAGE_AT_CARET = 'first\n![image]({})\nsecond'.format(HOT_LINK_URL)


class EditProfilePostBoxTestCase(BrowserTestCase):
    """The profile edit page has two post boxes sharing one set of modals.

    The page loads jQuery from ajax.googleapis.com, so these tests need
    outbound network access to Google's CDN.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.login(self.user)
        self.page.goto(self.live_server_url + reverse('bio-edit_profile'))
        self.profile_text = self.page.locator('#id_profile_text')
        self.signature = self.page.locator('#id_signature')
        self.profile_text.fill(CARET_TEXT)
        self.signature.fill(CARET_TEXT)

    def hot_link_into(self, textarea):
        textarea.evaluate('(t, i) => { t.focus(); t.setSelectionRange(i, i); }', CARET)
        editor = self.page.locator('.v3-editor', has=textarea)
        editor.locator('.editor-hot-link').click()
        self.page.locator('#hot-link-form input[name="url"]').fill(HOT_LINK_URL)
        self.page.locator('#hot-link-form-submit').click()
        # The callout starts out hidden, already holding the success text.
        expect(self.page.locator('#hot-link-status')).to_be_visible()

    def test_hot_link_goes_into_the_second_box_when_its_button_is_used(self):
        self.hot_link_into(self.signature)
        expect(self.signature).to_have_value(IMAGE_AT_CARET)
        expect(self.profile_text).to_have_value(CARET_TEXT)

    def test_hot_link_goes_into_the_first_box_when_its_button_is_used(self):
        self.hot_link_into(self.profile_text)
        expect(self.profile_text).to_have_value(IMAGE_AT_CARET)
        expect(self.signature).to_have_value(CARET_TEXT)
