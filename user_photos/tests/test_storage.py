"""Tests for user_photos.storage.delete_photos.

These call the real function. The three view tests in test_upload_views.py mock
it out, which is right for testing the view's contract but meant nothing had
ever executed this code -- it raised on every delete path for six steps without
turning the suite red.

The S3 half is mocked at S3Bucket, since core/tests/test_s3.py already covers
what that class does with boto3. The local half is not mocked at all: it writes
real files into a temporary MEDIA_ROOT and checks whether they are still there.

"""
import os
import shutil
import tempfile

from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from user_photos.models import Photo
from user_photos.storage import delete_photos


BASE_URL = 'https://s3-us-west-1.amazonaws.com'
BUCKET = 'sg101.user.photos'
S3_PREFIX = '{}/{}/'.format(BASE_URL, BUCKET)


@override_settings(USER_PHOTOS_BASE_URL=BASE_URL,
                   USER_PHOTOS_BUCKET=BUCKET,
                   USER_PHOTOS_REGION='us-west-1',
                   USER_PHOTOS_LOCAL_UPLOAD_DIR='user_photos',
                   MEDIA_URL='/media/')
class DeletePhotosTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('deleter', 'd@example.com', 'pw')
        self.media_root = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.media_root, 'user_photos')
        os.makedirs(self.upload_dir)
        self.addCleanup(shutil.rmtree, self.media_root, True)

        patcher = mock.patch('user_photos.storage.S3Bucket')
        self.bucket_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.bucket = self.bucket_cls.return_value
        # Stand in for the real thing: report every URL addressed to us.
        self.bucket.delete_keys.side_effect = lambda urls: len(urls)

    def _local_file(self, name):
        path = os.path.join(self.upload_dir, name)
        with open(path, 'wb') as f:
            f.write(b'image bytes')
        return path

    def _photo(self, url, thumb_url=''):
        return Photo.objects.create(user=self.user, url=url,
                                    thumb_url=thumb_url)

    def _local_photo(self, name, thumb_name):
        self._local_file(name)
        self._local_file(thumb_name)
        return self._photo(
            'https://surfguitar101.com/media/user_photos/' + name,
            'https://surfguitar101.com/media/user_photos/' + thumb_name)

    def _s3_photo(self, key, thumb_key):
        return self._photo(S3_PREFIX + key, S3_PREFIX + thumb_key)

    def _run(self, qs=None):
        with override_settings(MEDIA_ROOT=self.media_root):
            return delete_photos(qs if qs is not None
                                 else Photo.objects.all())

    def test_s3_photo_is_deleted_from_the_bucket(self):
        self._s3_photo('a.jpg', 'at.jpg')

        self.assertEqual(self._run(), 2)
        self.bucket.delete_keys.assert_called_once_with(
            [S3_PREFIX + 'a.jpg', S3_PREFIX + 'at.jpg'])

    def test_local_photo_files_are_removed_from_disk(self):
        self._local_photo('b.jpg', 'bt.jpg')

        self.assertEqual(self._run(), 2)
        self.assertFalse(os.path.exists(os.path.join(self.upload_dir, 'b.jpg')))
        self.assertFalse(os.path.exists(os.path.join(self.upload_dir,
                                                     'bt.jpg')))

    def test_a_local_only_delete_never_builds_a_bucket(self):
        """Removing local photos must not require working credentials."""
        self._local_photo('c.jpg', 'ct.jpg')

        self.assertEqual(self._run(), 2)
        self.assertFalse(self.bucket_cls.called)

    def test_mixed_queryset_routes_each_row_to_its_own_backend(self):
        self._s3_photo('d.jpg', 'dt.jpg')
        self._local_photo('e.jpg', 'et.jpg')

        self.assertEqual(self._run(), 4)
        self.bucket.delete_keys.assert_called_once_with(
            [S3_PREFIX + 'd.jpg', S3_PREFIX + 'dt.jpg'])
        self.assertFalse(os.path.exists(os.path.join(self.upload_dir, 'e.jpg')))

    def test_a_missing_local_file_is_not_a_failure(self):
        photo = self._local_photo('f.jpg', 'ft.jpg')
        os.remove(os.path.join(self.upload_dir, 'f.jpg'))

        # Still 2: the row is going away either way, and one absent file must
        # not abort the batch or block the member.
        self.assertEqual(self._run(Photo.objects.filter(pk=photo.pk)), 2)
        self.assertFalse(os.path.exists(os.path.join(self.upload_dir,
                                                     'ft.jpg')))

    def test_a_url_outside_the_upload_directory_is_refused(self):
        """A path that escapes MEDIA_ROOT/user_photos must not be unlinked."""
        outside = os.path.join(self.media_root, 'secret.txt')
        with open(outside, 'wb') as f:
            f.write(b'do not delete me')

        self._photo('https://surfguitar101.com/media/user_photos/'
                    '../secret.txt')

        self.assertEqual(self._run(), 0)
        self.assertTrue(os.path.exists(outside))

    def test_an_unrecognised_url_is_skipped_and_not_counted(self):
        self._photo('https://example.com/somewhere/else.jpg')

        self.assertEqual(self._run(), 0)
        self.assertFalse(self.bucket_cls.called)

    def test_unrecognised_urls_do_not_stop_the_rest(self):
        self._local_photo('g.jpg', 'gt.jpg')
        self._photo('https://example.com/somewhere/else.jpg')

        self.assertEqual(self._run(), 2)
        self.assertFalse(os.path.exists(os.path.join(self.upload_dir, 'g.jpg')))

    def test_blank_thumb_url_is_ignored(self):
        """A blank thumb_url is nothing to delete, not something unrecognised.

        Both readings produce the same count, so this asserts on the log: an
        empty column must not be reported as a URL we failed to place.
        """
        self._local_file('h.jpg')
        self._photo('https://surfguitar101.com/media/user_photos/h.jpg', '')

        # The suite disables logging globally (settings/test.py), so assertLogs
        # sees nothing; the calls still reach the logger object.
        with mock.patch('user_photos.storage.logger') as log:
            self.assertEqual(self._run(), 1)

        self.assertEqual(log.warning.call_args_list, [])
        summary = log.info.call_args_list[0]
        self.assertEqual(summary.args[-1], 0)  # unrecognised count

    def test_a_url_naming_no_file_is_refused(self):
        """A URL ending at the prefix resolves to the upload directory itself.

        os.remove() on a directory raises IsADirectoryError, which is an
        OSError and would be caught and logged -- leaving the count and the
        directory unchanged either way. So this asserts the attempt is never
        made: the URL names no file, and is classified as unrecognised before
        any delete is tried.
        """
        self._local_file('keep.jpg')
        self._photo('https://surfguitar101.com/media/user_photos/')

        with mock.patch('user_photos.storage.os.remove') as remove:
            with mock.patch('user_photos.storage.logger') as log:
                self.assertEqual(self._run(), 0)

        self.assertEqual(remove.call_args_list, [])
        self.assertEqual(log.exception.call_args_list, [])
        self.assertTrue(os.path.isdir(self.upload_dir))
        self.assertTrue(os.path.exists(os.path.join(self.upload_dir,
                                                    'keep.jpg')))

    def test_the_count_reflects_what_s3_reported(self):
        """A partial S3 failure must not be reported as a full success."""
        self._s3_photo('i.jpg', 'it.jpg')
        self._local_photo('j.jpg', 'jt.jpg')
        self.bucket.delete_keys.side_effect = lambda urls: len(urls) - 1

        # 1 of 2 in S3, 2 of 2 local.
        self.assertEqual(self._run(), 3)

    def test_scheme_and_host_do_not_decide_locality(self):
        """The path identifies a local photo; scheme and host are ignored.

        Not because the archive is mixed -- measured 2026-08-16, all 52,662
        stored URLs are https on one of two hosts -- but because both are
        environment-dependent. _user_photo_url() takes the scheme from
        SITE_SCHEME ('https' in production, 'http' in base.py) and the host from
        the Site row, so a photo uploaded in a dev container is http:// on a
        different domain than production's. The www form is covered here as
        tolerance, not because such rows exist.
        """
        for i, url in enumerate([
            'http://surfguitar101.com/media/user_photos/k%d.jpg',
            'https://www.surfguitar101.com/media/user_photos/k%d.jpg',
        ]):
            name = 'k%d.jpg' % i
            self._local_file(name)
            self._photo(url % i)

        self.assertEqual(self._run(), 2)
        self.assertEqual(os.listdir(self.upload_dir), [])
