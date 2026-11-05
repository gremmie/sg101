"""Browser tests for what every page wearing `v3/base.html` shares."""
from django.urls import reverse
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase


PHONE = {'width': 375, 'height': 812}


class PhoneMenuTestCase(BrowserTestCase):
    """Below medium width the main menu hides behind a menu icon."""

    def setUp(self):
        super().setUp()
        self.page.set_viewport_size(PHONE)
        self.page.goto(self.live_server_url + reverse('polls-main'))
        self.icon = self.page.locator('#small-menu .menu-icon')
        # The menu's own box has no height (its children float), so the test
        # watches one of its top-level links instead.
        self.forums = self.page.locator('#medium-menu a', has_text='Forums').first
        expect(self.forums).to_be_hidden()

    def test_tapping_the_menu_icon_opens_the_menu(self):
        self.icon.click()
        expect(self.forums).to_be_visible()

    def test_an_empty_data_toggle_raises_no_error(self):
        # Foundation 6.2.0's docs show the icon with no value, and jQuery 3
        # rejects the '#' selector it built from one.
        self.page.evaluate("""() => {
            const toggle = document.createElement('span');
            toggle.id = 'empty-toggle';
            toggle.setAttribute('data-toggle', '');
            toggle.textContent = 'toggle';
            document.body.prepend(toggle);
        }""")
        self.page.locator('#empty-toggle').click()

    def test_the_menu_icon_opens_the_menu_from_the_keyboard(self):
        self.icon.focus()
        expect(self.icon).to_be_focused()
        self.page.keyboard.press('Enter')
        expect(self.forums).to_be_visible()
