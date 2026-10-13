"""
A base class for tests that drive a real browser against the live server.

Subclasses are tagged `browser`, so `--exclude-tag browser` leaves them out of a
quick run and `--tag browser` runs only them.

"""
import os

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, tag
from playwright.sync_api import sync_playwright


ASYNC_UNSAFE = 'DJANGO_ALLOW_ASYNC_UNSAFE'


@tag('browser')
class BrowserTestCase(StaticLiveServerTestCase):
    """One headless Chromium per class; a fresh context and page per test.

    A test fails if the page raised an uncaught JavaScript error, even when
    everything it asserted held.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Playwright's sync API runs an asyncio event loop in this thread, and
        # Django refuses ORM calls from a thread with a running loop. Allowed
        # for these classes only, and put back afterwards, so the guard stays
        # on for every other test.
        cls._saved_async_unsafe = os.environ.get(ASYNC_UNSAFE)
        os.environ[ASYNC_UNSAFE] = 'true'
        cls.addClassCleanup(cls._restore_async_unsafe)

        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    @classmethod
    def _restore_async_unsafe(cls):
        if cls._saved_async_unsafe is None:
            os.environ.pop(ASYNC_UNSAFE, None)
        else:
            os.environ[ASYNC_UNSAFE] = cls._saved_async_unsafe

    def setUp(self):
        super().setUp()
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.addCleanup(self.page.close)

        self.page_errors = []
        self.page.on('pageerror', lambda error: self.page_errors.append(error))
        # Registered last so it runs first, while the page is still open.
        self.addCleanup(self._fail_on_page_errors)

    def _fail_on_page_errors(self):
        if self.page_errors:
            self.fail('Uncaught errors on the page:\n' +
                      '\n'.join(str(error) for error in self.page_errors))

    def login(self, user):
        """Log the browser in as user, through a session the server shares."""
        client = Client()
        client.force_login(user)
        cookie = client.cookies[settings.SESSION_COOKIE_NAME]
        self.context.add_cookies([{
            'name': settings.SESSION_COOKIE_NAME,
            'value': cookie.value,
            'url': self.live_server_url,
        }])
