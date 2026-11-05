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


class HeaderAlignmentTestCase(BrowserTestCase):
    """The header's blocks end where the page's content does."""

    RIGHT_EDGES = '''() => {
        const right = sel => document.querySelector(sel).getBoundingClientRect().right;
        const content = document.querySelector('.small-12.medium-9.columns');
        return {
            content: right('.small-12.medium-9.columns') -
                parseFloat(getComputedStyle(content).paddingRight),
            search: right('#top-search button'),
            banner: right('#logo-row img[alt="SG101 Banner"]'),
            menu: right('#main-menu'),
        };
    }'''

    def test_the_header_lines_up_with_the_content(self):
        # The page's row is 1200 px wide at most: at 1190 it fills the window,
        # at 1280 it's a little narrower, at 1920 much narrower.
        for width in (1190, 1280, 1920):
            self.page.set_viewport_size({'width': width, 'height': 900})
            self.page.goto(self.live_server_url + reverse('polls-main'))
            edges = self.page.evaluate(self.RIGHT_EDGES)
            for name in ('search', 'banner', 'menu'):
                with self.subTest(width=width, block=name):
                    self.assertAlmostEqual(edges[name], edges['content'], delta=1)
