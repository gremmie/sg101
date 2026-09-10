"""Tests for the downloads app signal handlers."""

import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

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


class FileDeletionTestCase(TestCase):
    """The uploaded file goes when the row that owns it does.

    Asserted against storage rather than against the field: the receivers call
    file.delete(save=False), and whether a file is still on disk afterwards is
    the property worth having. Everything is written under a temporary
    MEDIA_ROOT, so no real upload is read or removed.

    """
    fixtures = ['downloads_categories.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')
        self.category = Category.objects.get(pk=1)
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, True)

    def uploaded(self, model):
        """Save a `model` row carrying a real file; return it and the path."""
        with override_settings(MEDIA_ROOT=self.media_root):
            row = model(category=self.category,
                        title='Title',
                        description='Cool stuff',
                        user=self.user,
                        ip_address='127.0.0.1',
                        file=SimpleUploadedFile('tune.zip', b'zip bytes'))
            row.save()
            path = row.file.path

        self.assertTrue(os.path.exists(path))
        return row, path

    def delete(self, row):
        with override_settings(MEDIA_ROOT=self.media_root):
            row.delete()

    def test_the_file_goes_with_the_download(self):
        download, path = self.uploaded(Download)

        self.delete(download)

        self.assertFalse(os.path.exists(path))

    def test_the_file_goes_with_the_pending_download(self):
        pending, path = self.uploaded(PendingDownload)

        self.delete(pending)

        self.assertFalse(os.path.exists(path))
