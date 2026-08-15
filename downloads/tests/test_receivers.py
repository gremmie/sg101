"""Tests for the downloads app signal handlers."""

from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import Mock

from downloads.models import Category
from downloads.models import Download
from downloads.models import PendingDownload


class ReceiverTestCase(TestCase):

    fixtures = ['downloads_categories.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

    def test_download_signal_handlers(self):

        category = Category.objects.get(pk=1)
        dl = Download(category=category,
                      title='Title',
                      description='Cool stuff',
                      is_public=True,
                      user=self.user,
                      ip_address='127.0.0.1')
        dl.save()

        category = Category.objects.get(pk=1)
        self.assertEqual(1, category.count)

        category2 = Category.objects.get(pk=4)
        dl.category = category2
        dl.save()

        category = Category.objects.get(pk=1)
        self.assertEqual(0, category.count)
        category2 = Category.objects.get(pk=4)
        self.assertEqual(1, category2.count)

        dl.delete()
        category2 = Category.objects.get(pk=4)
        self.assertEqual(0, category2.count)

    def test_pending_download_signal_handlers(self):

        category = Category.objects.get(pk=1)
        dl = PendingDownload(
                category=category,
                title='Title',
                description='Cool stuff',
                user=self.user,
                ip_address='127.0.0.1')
        dl.save()

        dl.file = Mock()
        dl.delete()

        dl.file.delete.assert_called_with(save=False)

