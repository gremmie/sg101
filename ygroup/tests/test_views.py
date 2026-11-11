"""Tests for the Yahoo group archive's views."""
from django.test import TestCase
from django.utils import timezone

from ygroup.models import Post, Thread


class ThreadViewTestCase(TestCase):

    def setUp(self):
        now = timezone.now()
        self.thread = Thread.objects.create(
            title='Reverb tanks', creation_date=now, poster='a member')
        Post.objects.create(thread=self.thread, title='Reverb tanks',
                            creation_date=now, poster='a member', msg='Drip.')

    def test_the_top_link_is_quiet_but_still_a_link(self):
        response = self.client.get(self.thread.get_absolute_url())

        # The class is on the paragraph, so the link keeps the link colour.
        self.assertContains(
            response,
            '<p class="quiet"><a href="#top" title="Goto top of page">Top</a></p>',
            html=True)
