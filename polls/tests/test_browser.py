"""Browser tests for the polls app's pages."""
import datetime

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from core.tests.browser import BrowserTestCase
from polls.models import Poll


class PollCommentTestCase(BrowserTestCase):
    """Posting a comment on an open poll, which comments.js adds without a reload."""

    def setUp(self):
        super().setUp()
        now = timezone.now()
        poll = Poll.objects.create(start_date=now - datetime.timedelta(7),
                                   end_date=now + datetime.timedelta(7),
                                   question='Favorite reverb?')
        self.login(User.objects.create_user('pjmoto', '', 'pw'))
        self.page.goto(self.live_server_url + reverse('polls-detail', args=[poll.pk]))

    def test_a_posted_comment_is_numbered_and_counted(self):
        self.page.locator('#id_comment').fill('Fender, always')
        self.page.locator('#comment-form-post').click()
        comment = self.page.locator('#comment-container > div').last
        expect(comment).to_contain_text('Fender, always')
        expect(comment.locator('.comment-list')).to_have_text('1.')
        expect(self.page.locator('#comment-count')).to_have_text('1')
