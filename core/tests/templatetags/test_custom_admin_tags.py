"""
Unit tests for the custom admin template tags.

"""
import re

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from mock import patch


class AdminDashboardTestCase(TestCase):
    TEMPLATE = Template(
        '{% load custom_admin_tags %}{% admin_dashboard user %}')

    def setUp(self):
        self.user = User.objects.create_user(username='pjmoto',
                                             email='member32@example.com',
                                             is_staff=True)

    def test_empty_database(self):
        rendered = self.TEMPLATE.render(Context({'user': self.user}))
        self.assertEqual(rendered.strip(), '')

    @patch('core.templatetags.custom_admin_tags.BandEntry.objects.new_entry_count')
    @patch('core.templatetags.custom_admin_tags.PmFlag.objects.count')
    @patch('core.templatetags.custom_admin_tags.ShoutFlag.objects.count')
    @patch('core.templatetags.custom_admin_tags.FlaggedLink.objects.count')
    @patch('core.templatetags.custom_admin_tags.PendingLink.objects.count')
    @patch('core.templatetags.custom_admin_tags.PendingStory.objects.count')
    @patch('core.templatetags.custom_admin_tags.Event.objects')
    @patch('core.templatetags.custom_admin_tags.FlaggedPost.objects.count')
    @patch('core.templatetags.custom_admin_tags.PendingDownload.objects.count')
    @patch('core.templatetags.custom_admin_tags.CommentFlag.objects.count')
    @patch('core.templatetags.custom_admin_tags.UserProfileFlag.objects.count')
    def test_dashboard(self, mock_profile_count, mock_comment_count,
                       mock_pending_download_count, mock_flagged_post_count,
                       mock_event_objects, mock_pending_story_count,
                       mock_pending_link_count, mock_flagged_link_count,
                       mock_shout_flag_count, mock_pm_flag_count,
                       mock_band_entry_count):

        mock_profile_count.return_value = 1
        mock_comment_count.return_value = 2
        mock_pending_download_count.return_value = 3
        mock_flagged_post_count.return_value = 4

        mock_event_objects.filter.return_value.count.return_value = 5

        mock_pending_story_count.return_value = 6
        mock_pending_link_count.return_value = 7
        mock_flagged_link_count.return_value = 8
        mock_shout_flag_count.return_value = 9
        mock_pm_flag_count.return_value = 10
        mock_band_entry_count.return_value = 11

        rendered = self.TEMPLATE.render(Context({'user': self.user}))
        self.assertIsNotNone(re.search(r'\bProfiles.*: 1', rendered))
        self.assertIsNotNone(re.search(r'\bComments.*: 2', rendered))
        self.assertIsNotNone(re.search(r'\bDownloads.*: 3', rendered))
        self.assertIsNotNone(re.search(r'\bPosts.*: 4', rendered))
        self.assertIsNotNone(re.search(r'\bCalendar.*: 5', rendered))
        self.assertIsNotNone(re.search(r'\bNews.*: 6', rendered))
        self.assertIsNotNone(re.search(r'\bNew Links.*: 7', rendered))
        self.assertIsNotNone(re.search(r'\bBroken Links.*: 8', rendered))
        self.assertIsNotNone(re.search(r'\bShouts.*: 9', rendered))
        self.assertIsNotNone(re.search(r"\bPM's.*: 10", rendered))
        self.assertIsNotNone(re.search(r"\bBand Map.*: 11", rendered))

        # Nothing is shown to non-staff users.
        eddie = User.objects.create_user(username='eddie',
                                         email='member34@example.com',
                                         is_staff=False)
        rendered = self.TEMPLATE.render(Context({'user': eddie}))
        self.assertEqual(rendered.strip(), '')
