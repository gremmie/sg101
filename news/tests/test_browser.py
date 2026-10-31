"""Browser tests for the news app's pages."""
import io
import os
import re
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from playwright.sync_api import expect

from core.services import get_redis_connection
from core.tests.browser import BrowserTestCase
from smiley.models import Smiley


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
    """The post box on the story submission page, in a real browser."""

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

    def test_an_open_modal_is_not_hidden_from_assistive_technology(self):
        # Chrome logs its "Blocked aria-hidden" messages only once something
        # asks for the accessibility tree, which a headless test never does,
        # so the attributes are checked rather than the console.
        self.page.locator('a.editor-upload[data-open="upload-modal"]').click()
        modal = self.page.locator('#upload-modal')
        expect(modal).to_be_visible()

        hidden = modal.evaluate('''m => {
            const hidden = [];
            for (let e = m; e; e = e.parentElement) {
                if (e.getAttribute('aria-hidden') === 'true') hidden.push(e.tagName);
            }
            return hidden;
        }''')
        self.assertEqual(hidden, [])

    def test_cancel_comes_before_the_primary_action(self):
        """The primary action is the last button in the row, on the right."""
        for modal, primary in (('#hot-link-modal', 'Hot-Link'),
                               ('#upload-modal', 'Upload')):
            with self.subTest(modal=modal):
                row = self.page.locator(modal).locator('.columns.text-right')
                labels = row.locator('.button').evaluate_all(
                    'buttons => buttons.map(b => (b.value || b.textContent).trim())')
                self.assertEqual(labels, ['Cancel', primary])

    def test_closing_a_modal_leaves_body_as_it_was(self):
        body = self.page.locator('body')
        before = body.get_attribute('aria-hidden')
        self.page.locator('a.editor-upload[data-open="upload-modal"]').click()
        modal = self.page.locator('#upload-modal')
        expect(modal).to_be_visible()
        modal.locator('.close-button').click()
        expect(modal).to_be_hidden()
        self.assertEqual(body.get_attribute('aria-hidden'), before)

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

    def test_enter_in_the_address_hot_links(self):
        """Enter submits through the form's first submit button. Cancel comes
        first in the row, but is a plain button, so it is not that."""
        self.page.locator('.editor-hot-link').click()
        address = self.page.locator('#hot-link-form input[name="url"]')
        address.fill(HOT_LINK_URL)
        address.press('Enter')

        expect(self.page.locator('#hot-link-modal')).to_be_visible()
        status = self.page.locator('#hot-link-status')
        expect(status).to_be_visible()
        expect(status).to_contain_text('Success')
        expect(self.textarea).to_have_value('![image]({})'.format(HOT_LINK_URL))


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
        # Each upload counts against the real rate limit, whose counter lives
        # a day in the test redis. Start each test at zero and leave nothing.
        conn = get_redis_connection()
        quota_key = 'user_photos:counts:pjmoto'
        conn.delete(quota_key)
        self.addCleanup(conn.delete, quota_key)
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


def png(name, color='red'):
    """A small PNG for set_input_files, made in memory."""
    out = io.BytesIO()
    Image.new('RGB', (40, 30), color).save(out, 'PNG')
    return {'name': name, 'mimeType': 'image/png', 'buffer': out.getvalue()}


# Records every object URL the page makes and releases.
RECORD_OBJECT_URLS = """
    window.objectURLs = {created: [], revoked: []};
    const create = URL.createObjectURL, revoke = URL.revokeObjectURL;
    URL.createObjectURL = (f) => {
        const url = create(f);
        window.objectURLs.created.push(url);
        return url;
    };
    URL.revokeObjectURL = (url) => {
        window.objectURLs.revoked.push(url);
        revoke(url);
    };
"""


class SubmitUploadListTestCase(BrowserTestCase):
    """The upload modal's list of chosen files, before anything is uploaded."""

    def setUp(self):
        super().setUp()
        self.context.add_init_script(RECORD_OBJECT_URLS)
        self.login(User.objects.create_user('pjmoto', '', 'pw'))
        self.page.goto(self.live_server_url + reverse('news-submit'))
        self.modal = self.page.locator('#upload-modal')
        self.input = self.modal.locator('input[name="image_file"]')
        self.entries = self.modal.locator('#photo-upload-list li')
        self.open_modal()

    def open_modal(self):
        self.page.locator('a.editor-upload').click()
        expect(self.modal).to_be_visible()

    def choose(self, *files):
        self.input.set_input_files(list(files))

    def names(self):
        return self.entries.locator('.upload-name').all_text_contents()

    def object_urls(self):
        return self.page.evaluate('window.objectURLs')

    def test_the_input_takes_several_images_of_the_formats_that_work(self):
        # Safari converts a HEIC to JPEG when the list leaves HEIC out.
        self.assertEqual(self.input.get_attribute('accept'),
                         'image/jpeg,image/png,image/gif,image/webp')
        self.assertIsNotNone(self.input.get_attribute('multiple'))

    def test_choices_add_up(self):
        self.choose(png('a.png'), png('b.png'))
        self.choose(png('c.png'), png('d.png'), png('e.png'))

        self.assertEqual(self.names(), ['a.png', 'b.png', 'c.png', 'd.png', 'e.png'])
        # Cleared, so a file removed from the list can be chosen again.
        self.assertEqual(self.input.evaluate('i => i.files.length'), 0)

    def test_each_entry_shows_its_thumbnail(self):
        self.choose(png('a.png'))

        thumb = self.entries.first.locator('img.upload-thumb')
        expect(thumb).to_have_attribute('src', re.compile(r'^blob:'))
        expect(thumb).to_have_js_property('complete', True)
        self.assertGreater(thumb.evaluate('img => img.naturalWidth'), 0)

    def test_the_cap_keeps_the_first_ten_and_says_how_many_were_left_out(self):
        self.choose(*[png('{:02}.png'.format(n)) for n in range(1, 13)])

        self.assertEqual(self.names(), ['{:02}.png'.format(n) for n in range(1, 11)])
        status = self.page.locator('#photo-status')
        expect(status).to_be_visible()
        expect(status).to_have_text(
            'You can upload up to 10 images at a time; 2 were left out.')

    def test_the_cap_counts_what_is_already_listed(self):
        self.choose(*[png('{:02}.png'.format(n)) for n in range(1, 10)])
        self.choose(png('10.png'), png('11.png'))

        self.assertEqual(len(self.names()), 10)
        expect(self.page.locator('#photo-status')).to_have_text(
            'You can upload up to 10 images at a time; 1 was left out.')

    def test_remove_takes_out_that_file_and_releases_its_thumbnail(self):
        self.choose(png('a.png'), png('b.png'), png('c.png'))
        thumb_url = self.entries.nth(1).locator('img').get_attribute('src')

        self.modal.get_by_role('button', name='Remove b.png').click()

        # The button is gone from the page by the time its click reaches
        # Reveal, which must not take that for a click outside the modal.
        expect(self.modal).to_be_visible()
        self.assertEqual(self.names(), ['a.png', 'c.png'])
        self.assertEqual(self.object_urls()['revoked'], [thumb_url])

    def on_disk(self, *names):
        """Real files, which keep their name, size and modified time from one
        choice to the next, as a member's do."""
        files = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, files)
        paths = []
        for name in names:
            path = os.path.join(files, name)
            with open(path, 'wb') as f:
                f.write(png(name)['buffer'])
            paths.append(path)
        return paths

    def test_a_file_already_listed_is_skipped_and_named(self):
        a, b, c = self.on_disk('a.png', 'b.png', 'c.png')
        self.choose(a, b)
        self.choose(b, c)

        self.assertEqual(self.names(), ['a.png', 'b.png', 'c.png'])
        expect(self.page.locator('#photo-status')).to_have_text(
            'b.png is already in the list.')

    def test_several_files_already_listed_are_named_together(self):
        a, b, c = self.on_disk('a.png', 'b.png', 'c.png')
        self.choose(a, b, c)
        self.choose(a, b, c)

        self.assertEqual(self.names(), ['a.png', 'b.png', 'c.png'])
        expect(self.page.locator('#photo-status')).to_have_text(
            'a.png, b.png and c.png are already in the list.')

    def test_a_file_already_listed_does_not_count_against_the_cap(self):
        paths = self.on_disk(*['{:02}.png'.format(n) for n in range(1, 11)])
        self.choose(*paths[:9])
        self.choose(paths[0], paths[9])

        self.assertEqual(len(self.names()), 10)
        expect(self.page.locator('#photo-status')).to_have_text(
            '01.png is already in the list.')

    def test_a_skipped_file_and_the_cap_are_both_reported(self):
        paths = self.on_disk(*['{:02}.png'.format(n) for n in range(1, 12)])
        self.choose(*paths[:9])
        self.choose(paths[0], paths[9], paths[10])

        self.assertEqual(len(self.names()), 10)
        expect(self.page.locator('#photo-status')).to_have_text(
            '01.png is already in the list. '
            'You can upload up to 10 images at a time; 1 was left out.')

    def test_different_files_with_one_name_are_both_listed(self):
        """Two cameras, or two folders, can both make an IMG_0001."""
        (first,) = self.on_disk('IMG_0001.png')
        other = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other)
        second = os.path.join(other, 'IMG_0001.png')
        Image.new('RGB', (80, 60), 'blue').save(second)
        self.choose(first)
        self.choose(second)

        self.assertEqual(self.names(), ['IMG_0001.png', 'IMG_0001.png'])
        expect(self.page.locator('#photo-status')).to_be_hidden()

    def test_a_file_removed_can_be_chosen_again(self):
        a, b = self.on_disk('a.png', 'b.png')
        self.choose(a, b)
        self.modal.get_by_role('button', name='Remove a.png').click()
        self.choose(a)

        self.assertEqual(self.names(), ['b.png', 'a.png'])
        expect(self.page.locator('#photo-status')).to_be_hidden()

    def test_a_file_that_cannot_be_drawn_shows_a_placeholder(self):
        self.choose({'name': 'notes.txt', 'mimeType': 'text/plain',
                     'buffer': b'not an image'})

        entry = self.entries.first
        expect(entry.locator('.upload-placeholder')).to_be_visible()
        expect(entry.locator('.upload-placeholder')).to_have_text('No preview')
        expect(entry.locator('img')).to_have_count(0)
        self.assertEqual(self.names(), ['notes.txt'])

    def test_reopening_the_modal_empties_the_list_and_releases_every_thumbnail(self):
        self.choose(png('a.png'), png('b.png'))
        created = self.object_urls()['created']
        self.assertEqual(len(created), 2)

        self.modal.locator('.close-button').click()
        expect(self.modal).to_be_hidden()
        self.open_modal()

        expect(self.entries).to_have_count(0)
        self.assertEqual(sorted(self.object_urls()['revoked']), sorted(created))


class SubmitJQueryTestCase(BrowserTestCase):
    """The V3 pages run the site's own copy of jQuery, not Google's."""

    def setUp(self):
        super().setUp()
        self.requests = []
        self.page.on('request', lambda request: self.requests.append(request.url))
        self.login(User.objects.create_user('pjmoto', '', 'pw'))
        self.page.goto(self.live_server_url + reverse('news-submit'))

    def test_page_runs_jquery_3_7_1(self):
        self.assertEqual(self.page.evaluate('jQuery.fn.jquery'), '3.7.1')

    def test_page_requests_nothing_from_googles_cdn(self):
        google = [url for url in self.requests if 'ajax.googleapis.com' in url]
        self.assertEqual(google, [])


class SubmitSmileyPickerTestCase(BrowserTestCase):
    """The post box's smiley button opens a modal of every smiley."""
    fixtures = ['smilies.json']

    def setUp(self):
        super().setUp()
        # The picker reads smileys through get_smilies, which caches them.
        cache.clear()
        self.addCleanup(cache.clear)
        self.login(User.objects.create_user('pjmoto', '', 'pw'))
        self.page.goto(self.live_server_url + reverse('news-submit'))
        self.textarea = self.page.locator('.v3-editor textarea')
        self.modal = self.page.locator('#smiley-modal')

    def open_picker(self):
        self.page.locator('a.editor-smiley').click()
        expect(self.modal).to_be_visible()

    def smiley(self, code):
        return self.modal.locator('button[data-code="{}"]'.format(code))

    def place_caret(self, text, caret):
        self.textarea.fill(text)
        self.textarea.evaluate('(t, i) => { t.focus(); t.setSelectionRange(i, i); }', caret)

    def drag_title(self, dx, dy):
        handle = self.modal.locator('.smiley-modal-title').bounding_box()
        x, y = handle['x'] + 20, handle['y'] + handle['height'] / 2
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.move(x + dx, y + dy, steps=5)
        self.page.mouse.up()

    def test_smiley_button_opens_every_smiley_and_done_closes_it(self):
        self.page.locator('a.editor-smiley[data-open="smiley-modal"]').click()
        modal = self.page.locator('#smiley-modal')
        expect(modal).to_be_visible()
        expect(modal.locator('button[data-code]')).to_have_count(Smiley.objects.count())
        modal.get_by_role('button', name='Done').click()
        expect(modal).to_be_hidden()

    def test_a_smiley_goes_in_at_the_caret_with_one_space_each_side(self):
        # The same results core's SmileyPaddingTestCase renders as images.
        cases = [
            ('abcd', 2, 'ab :-) cd'),
            ('abc', 3, 'abc :-)'),
            ('abc', 0, ':-) abc'),
            ('a  b', 2, 'a :-) b'),
            ('', 0, ':-)'),
        ]
        self.open_picker()
        for text, caret, expected in cases:
            with self.subTest(text=text, caret=caret):
                self.place_caret(text, caret)
                self.smiley(':-)').click()
                expect(self.textarea).to_have_value(expected)

    def test_a_second_smiley_follows_the_first_with_one_space(self):
        self.place_caret('abcd', 2)
        self.open_picker()
        self.smiley(':-)').click()
        self.smiley(':D').click()
        expect(self.textarea).to_have_value('ab :-) :D cd')

    def test_the_same_smiley_twice_is_spaced_once(self):
        self.place_caret('abcd', 2)
        self.open_picker()
        self.smiley(':-)').click()
        self.smiley(':-)').click()
        expect(self.textarea).to_have_value('ab :-) :-) cd')

    def test_the_picker_stays_open_after_a_smiley_is_clicked(self):
        self.open_picker()
        self.smiley(':-)').click()
        expect(self.textarea).to_have_value(':-)')
        expect(self.modal).to_be_visible()

    def test_the_post_can_be_clicked_into_while_the_picker_is_open(self):
        self.open_picker()
        overlay = self.modal.evaluate("m => !!m.closest('.reveal-overlay')")
        self.assertFalse(overlay)
        # The picker sits over the middle of the page; the post's right edge is clear.
        box = self.textarea.bounding_box()
        self.textarea.click(position={'x': box['width'] - 10, 'y': 10})
        expect(self.textarea).to_be_focused()
        expect(self.modal).to_be_visible()

    def test_the_picker_can_be_dragged_by_its_title(self):
        self.open_picker()
        expect(self.modal.locator('.smiley-modal-grip')).to_be_visible()
        before = self.modal.bounding_box()
        self.drag_title(-150, 60)
        after = self.modal.bounding_box()
        self.assertAlmostEqual(after['x'], before['x'] - 150, delta=2)
        self.assertAlmostEqual(after['y'], before['y'] + 60, delta=2)

    def test_the_title_cannot_be_dragged_off_screen(self):
        self.open_picker()
        title = self.modal.locator('.smiley-modal-title')
        self.drag_title(-3000, -3000)
        box = title.bounding_box()
        self.assertGreaterEqual(box['y'], 0)
        self.assertGreaterEqual(box['x'] + box['width'], 100)

        self.drag_title(6000, 6000)
        box = title.bounding_box()
        viewport = self.page.viewport_size
        self.assertLessEqual(box['y'] + box['height'], viewport['height'])
        self.assertLessEqual(box['x'], viewport['width'] - 100)

    def test_the_picker_is_not_dragged_on_a_phone(self):
        self.page.set_viewport_size({'width': 375, 'height': 812})
        self.page.reload()
        self.open_picker()
        expect(self.modal.locator('.smiley-modal-grip')).to_be_hidden()
        before = self.modal.bounding_box()
        self.drag_title(-100, 60)
        self.assertEqual(self.modal.bounding_box(), before)

    def test_the_close_button_in_the_title_bar_closes_the_picker(self):
        # The button sits on the drag handle; pressing it must not start a drag.
        self.open_picker()
        self.modal.locator('.smiley-modal-title .close-button').click()
        expect(self.modal).to_be_hidden()

    def test_the_title_bar_stays_at_the_top_as_the_picker_scrolls(self):
        # Short enough that the picker overflows even though the test server
        # serves no media, so the smiley images take no room.
        self.page.set_viewport_size({'width': 1280, 'height': 300})
        self.open_picker()
        heights = self.modal.evaluate('m => [m.clientHeight, m.scrollHeight]')
        scrolled = self.modal.evaluate('m => { m.scrollTop = m.scrollHeight; return m.scrollTop; }')
        self.assertGreater(scrolled, 0, heights)
        modal = self.modal.bounding_box()
        title = self.modal.locator('.smiley-modal-title').bounding_box()
        self.assertAlmostEqual(title['y'], modal['y'], delta=2)
