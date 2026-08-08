import datetime
import unittest

from mock import patch, call, mock_open, Mock
from core.images.upload import process_upload

class ProcessUploadTestCase(unittest.TestCase):

    @patch('core.images.upload.Site.objects.get_current')
    @patch('core.images.upload.os.chmod')
    @patch('core.images.upload.uuid')
    @patch('core.images.upload.shutil')
    @patch('core.images.upload.BytesIO')
    @patch('core.images.upload.orient_image')
    @patch('core.images.upload.Image')
    @patch('core.images.upload.settings.SITE_SCHEME', new='https')
    @patch('core.images.upload.settings.USER_PHOTOS_LOCAL_UPLOAD', new=True)
    @patch('core.images.upload.settings.MEDIA_ROOT', new='/media')
    @patch('core.images.upload.settings.USER_PHOTOS_LOCAL_UPLOAD_DIR', new='user_upload')
    def test_local_upload(self, image_mock, orient_mock, bytes_mock,
                          shutil_mock, uuid_mock, chmod_mock, current_mock):
        filename = 'image.jpg'
        orient_mock.return_value = (True, image_mock.open)

        image = Mock()
        image.size = (2000, 2000)
        image_mock.open.return_value = image

        uuid_mock.uuid4().hex = 'deadbeef'

        site_mock = Mock()
        site_mock.configure_mock(name='Site', domain='site.com')
        current_mock.return_value = site_mock

        open_mock = mock_open()
        with patch('builtins.open', open_mock):
            result = process_upload(None, filename)

        self.assertEqual(image_mock.open.mock_calls, [
            call(filename),
            call.save(filename),
            call(filename),
            call().thumbnail((660, 720), image_mock.Resampling.LANCZOS),
            call().save(filename),
            call(filename),
            call().thumbnail((120, 120), image_mock.Resampling.LANCZOS),
            call().save(bytes_mock(), format=image.format),
        ])
        orient_mock.assert_called_with(image_mock.open())

        expected_path = '/media/user_upload/deadbeef.jpg'
        expected_thumb_path = '/media/user_upload/deadbeeft.jpg'
        shutil_mock.copy.assert_called_once_with(filename, expected_path)
        self.assertEqual(chmod_mock.mock_calls, [
            call(expected_path, 0o644),
            call(expected_thumb_path, 0o644),
        ])

        bytes_mock().seek.assert_called_once_with(0)
        self.assertEqual(open_mock.mock_calls, [
            call(expected_thumb_path, 'wb'),
            call().__enter__(),
            call().write(bytes_mock().getvalue()),
            call().__exit__(None, None, None),
        ])
        self.assertEqual(result,
                         ('https://site.com/media/user_upload/deadbeef.jpg',
                          'https://site.com/media/user_upload/deadbeeft.jpg'))

    @patch('core.images.upload.BytesIO')
    @patch('core.images.upload.S3Bucket')
    @patch('core.images.upload.datetime')
    @patch('core.images.upload.uuid')
    @patch('core.images.upload.orient_image')
    @patch('core.images.upload.Image')
    @patch('core.images.upload.settings.USER_PHOTOS_LOCAL_UPLOAD', new=False)
    @patch('core.images.upload.settings.USER_PHOTOS_BUCKET', new='bucket-name')
    @patch('core.images.upload.settings.USER_PHOTOS_BASE_URL', new='base-url')
    @patch('core.images.upload.settings.USER_PHOTOS_SECRET_KEY', new='secret-key')
    @patch('core.images.upload.settings.USER_PHOTOS_ACCESS_KEY', new='access-key')
    def test_s3_upload(self, image_mock, orient_mock, uuid_mock, now_mock,
                       bucket_mock, bytes_mock):
        now_mock.datetime.now.return_value = datetime.datetime(2025, 4, 20)
        uuid_mock.uuid4().bytes = b'deadbeef'

        filename = 'image.jpg'
        orient_mock.return_value = (True, image_mock.open)

        image = Mock()
        image.size = (2000, 2000)
        image_mock.open.return_value = image

        uuid_mock.uuid4().hex = 'deadbeef'

        bucket = Mock()
        bucket_mock.return_value = bucket
        bucket.upload_from_filename.return_value = 'image-url'
        bucket.upload_from_string.return_value = 'thumb-url'

        user = Mock(username='pjmoto')
        open_mock = mock_open()
        with patch('builtins.open', open_mock):
            result = process_upload(user, filename)


        self.assertEqual(image_mock.open.mock_calls, [
            call(filename),
            call.save(filename),
            call(filename),
            call().thumbnail((660, 720), image_mock.Resampling.LANCZOS),
            call().save(filename),
            call(filename),
            call().thumbnail((120, 120), image_mock.Resampling.LANCZOS),
            call().save(bytes_mock(), format=image.format),
        ])
        orient_mock.assert_called_with(image_mock.open())

        expected_metadata = {
            'user': 'pjmoto',
            'date': '2025-04-20 00:00:00',
        }

        self.assertEqual(bucket_mock.mock_calls, [
            call(access_key='access-key',
                 secret_key='secret-key',
                 base_url='base-url',
                 bucket_name='bucket-name'),
            call().upload_from_filename('ZGVhZGJlZWY.jpg', filename,
                                        expected_metadata),
            call().upload_from_string('ZGVhZGJlZWYt.jpg',
                                      bytes_mock().getvalue(),
                                      expected_metadata),
        ])

        self.assertEqual(result, ('image-url', 'thumb-url'))

