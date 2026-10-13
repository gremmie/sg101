"""Browser tests for the news app's pages."""
import os
import re
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase


# An allowed image host with https is returned as-is, without a fetch.
HOT_LINK_URL = 'https://surfguitar101.com/static/img/test.jpg'

# The status callouts start out hidden, holding the success text, so a test
# asserts one is visible before reading what it says.

# Where the caret sits in CARET_TEXT, and what an image inserted there on its
# own line should leave around it.
CARET_TEXT = 'first\nsecond'
CARET = len('first')
IMAGE_AT_CARET = re.compile(r'^first\n!\[image\]\((\S+)\)\nsecond$')


class SubmitPostBoxTestCase(BrowserTestCase):
    """The post box on the story submission page, in a real browser.

    The page loads jQuery from ajax.googleapis.com, so these tests need
    outbound network access to Google's CDN.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.login(self.user)
        self.page.goto(self.live_server_url + reverse('news-submit'))
        self.textarea = self.page.locator('.v3-editor textarea')

    def select(self, start, end):
        self.textarea.evaluate('(t, [i, j]) => { t.focus(); t.setSelectionRange(i, j); }',
                               [start, end])

    def test_upload_button_opens_the_upload_modal(self):
        # Foundation opens every Reveal modal; if its init fails, the page
        # still renders and the modal never appears.
        self.page.locator('a.editor-upload[data-open="upload-modal"]').click()
        expect(self.page.locator('#upload-modal')).to_be_visible()

    def test_bold_wraps_the_selection(self):
        self.textarea.fill('hello world')
        self.select(6, 11)
        self.page.locator('.editor-bold').click()
        expect(self.textarea).to_have_value('hello **world**')

    def test_link_wraps_the_selection_in_the_url_given(self):
        self.textarea.fill('hello world')
        self.select(6, 11)
        self.page.once('dialog', lambda dialog: dialog.accept('https://example.com'))
        self.page.locator('.editor-link').click()
        expect(self.textarea).to_have_value('hello [world](https://example.com)')

    def test_preview_renders_the_markdown(self):
        self.textarea.fill('some **bold** text')
        self.page.locator('.editor-preview').click()
        expect(self.page.locator('#editor-preview-panel strong')).to_have_text('bold')

    def test_preview_shows_why_it_failed(self):
        """The preview is refused once the session is gone; the reason
        appears in the panel, not in an alert."""
        self.textarea.fill('some **bold** text')
        self.context.clear_cookies(name=settings.SESSION_COOKIE_NAME)
        self.page.locator('.editor-preview').click()
        expect(self.page.locator('#editor-preview-panel .alert')).to_have_text(
            'This service is only available to logged-in users.')

    def test_hot_link_into_a_box_never_clicked_goes_at_the_end(self):
        """A textarea filled by the server, here the form returned for a
        missing title, has its caret at the start until the member clicks in
        it. An image goes at the end there, as it always has."""
        self.textarea.fill(CARET_TEXT)
        # form.submit() skips the browser's own check of the required title.
        with self.page.expect_navigation():
            self.textarea.evaluate('t => t.form.submit()')
        self.textarea = self.page.locator('.v3-editor textarea')
        expect(self.textarea).to_have_value(CARET_TEXT)

        self.page.locator('.editor-hot-link').click()
        self.page.locator('#hot-link-form input[name="url"]').fill(HOT_LINK_URL)
        self.page.locator('#hot-link-form-submit').click()

        expect(self.page.locator('#hot-link-status')).to_be_visible()
        expect(self.textarea).to_have_value(
            'first\nsecond\n![image]({})'.format(HOT_LINK_URL))

    def test_hot_link_inserts_the_image_at_the_caret(self):
        self.textarea.fill(CARET_TEXT)
        self.select(CARET, CARET)
        self.page.locator('.editor-hot-link').click()
        self.page.locator('#hot-link-form input[name="url"]').fill(HOT_LINK_URL)
        self.page.locator('#hot-link-form-submit').click()

        status = self.page.locator('#hot-link-status')
        expect(status).to_be_visible()
        expect(status).to_contain_text('Success')
        expect(self.textarea).to_have_value(
            'first\n![image]({})\nsecond'.format(HOT_LINK_URL))


class SubmitUploadTestCase(BrowserTestCase):
    """Uploading from the post box on the story submission page.

    Uploads are stored locally under a temporary MEDIA_ROOT, never on S3.
    """

    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, cls.media_root)
        # Local upload copies into this directory and does not create it.
        os.makedirs(os.path.join(cls.media_root, 'user_photos'))
        cls.local_upload = override_settings(USER_PHOTOS_LOCAL_UPLOAD=True,
                                             USER_PHOTOS_LOCAL_UPLOAD_DIR='user_photos',
                                             MEDIA_ROOT=cls.media_root)
        cls.local_upload.enable()
        cls.addClassCleanup(cls.local_upload.disable)
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.login(self.user)
        self.page.goto(self.live_server_url + reverse('news-submit'))
        self.textarea = self.page.locator('.v3-editor textarea')
        self.files = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.files)

    def file(self, name, write):
        path = os.path.join(self.files, name)
        write(path)
        return path

    def upload(self, path):
        self.page.locator('.editor-upload').click()
        self.page.locator('#photo-upload-form input[name="image_file"]').set_input_files(path)
        self.page.locator('#photo-upload-submit').click()

    def test_an_upload_inserts_the_image_at_the_caret(self):
        image = self.file('red.png',
                          lambda path: Image.new('RGB', (40, 30), 'red').save(path))
        self.textarea.fill(CARET_TEXT)
        self.textarea.evaluate('(t, i) => { t.focus(); t.setSelectionRange(i, i); }', CARET)

        self.upload(image)

        status = self.page.locator('#photo-status')
        expect(status).to_be_visible()
        expect(status).to_contain_text('Success')
        expect(self.textarea).to_have_value(IMAGE_AT_CARET)

    def test_a_file_that_is_not_an_image_says_why(self):
        def write(path):
            with open(path, 'wb') as f:
                f.write(b'not an image')
        not_an_image = self.file('notes.jpg', write)
        self.textarea.fill(CARET_TEXT)

        self.upload(not_an_image)

        status = self.page.locator('#photo-status')
        expect(status).to_be_visible()
        expect(status).to_contain_text('Upload a valid image.')
        expect(self.page.locator('#photo-upload-submit')).to_be_enabled()
        expect(self.textarea).to_have_value(CARET_TEXT)
