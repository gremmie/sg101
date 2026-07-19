import unittest

from mock import call, patch, Mock

from core.s3 import S3Bucket


@unittest.skip("S3/boto is disabled on Python 3 until the Cloudflare R2 / boto3 "
               "step; S3Bucket raises NotImplementedError meanwhile.")
class S3BucketTestCase(unittest.TestCase):
    @patch('core.s3.OrdinaryCallingFormat')
    @patch('core.s3.connect_to_region')
    @patch('core.s3.Key')
    def test_upload_from_file(self, mock_key, mock_connect, mock_call_format):

        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')

        self.assertEqual(bucket.region_name, 'us-west-1')
        self.assertEqual(mock_connect.mock_calls, [
            call('us-west-1', aws_access_key_id='access',
                 aws_secret_access_key='secret',
                 calling_format=mock_call_format()),
            call().get_bucket('bucket_name', validate=False),

        ])
        self.assertEqual(bucket.base_url, 'base_url/')
        self.assertEqual(bucket.name, 'bucket_name')

        mock_fp = Mock()
        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        url = bucket.upload_from_file('key_name', mock_fp, metadata)

        self.assertEqual(mock_key.mock_calls, [
            call(bucket.bucket),
            call().set_metadata('date', '6/24/2025'),
            call().set_metadata('user', 1234),
            call().set_contents_from_file(mock_fp),
            call().make_public(),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.OrdinaryCallingFormat')
    @patch('core.s3.connect_to_region')
    @patch('core.s3.Key')
    def test_upload_from_filename(self, mock_key, mock_connect,
                                  mock_call_format):

        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')

        self.assertEqual(bucket.region_name, 'us-west-1')
        self.assertEqual(mock_connect.mock_calls, [
            call('us-west-1', aws_access_key_id='access',
                 aws_secret_access_key='secret',
                 calling_format=mock_call_format()),
            call().get_bucket('bucket_name', validate=False),

        ])
        self.assertEqual(bucket.base_url, 'base_url/')
        self.assertEqual(bucket.name, 'bucket_name')

        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        url = bucket.upload_from_filename('key_name', 'filename', metadata)

        self.assertEqual(mock_key.mock_calls, [
            call(bucket.bucket),
            call().set_metadata('date', '6/24/2025'),
            call().set_metadata('user', 1234),
            call().set_contents_from_filename('filename'),
            call().make_public(),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.OrdinaryCallingFormat')
    @patch('core.s3.connect_to_region')
    @patch('core.s3.Key')
    def test_upload_from_string(self, mock_key, mock_connect, mock_call_format):

        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')

        self.assertEqual(bucket.region_name, 'us-west-1')
        self.assertEqual(mock_connect.mock_calls, [
            call('us-west-1', aws_access_key_id='access',
                 aws_secret_access_key='secret',
                 calling_format=mock_call_format()),
            call().get_bucket('bucket_name', validate=False),

        ])
        self.assertEqual(bucket.base_url, 'base_url/')
        self.assertEqual(bucket.name, 'bucket_name')

        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        url = bucket.upload_from_string('key_name', 'content', metadata)

        self.assertEqual(mock_key.mock_calls, [
            call(bucket.bucket),
            call().set_metadata('date', '6/24/2025'),
            call().set_metadata('user', 1234),
            call().set_contents_from_string('content'),
            call().make_public(),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.OrdinaryCallingFormat')
    @patch('core.s3.connect_to_region')
    @patch('core.s3.Key')
    def test_delete_zero_keys(self, mock_key, mock_connect, mock_call_format):

        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')

        result = bucket.delete_keys([])

        self.assertEqual(result, 0)

    @patch('core.s3.OrdinaryCallingFormat')
    @patch('core.s3.connect_to_region')
    @patch('core.s3.Key')
    def test_delete_keys(self, mock_key, mock_connect, mock_call_format):

        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')

        urls = [
            'base_url/bucket_name/foo',
            'base_url/bucket_name/bar',
            'baz',
        ]
        mock_connect.return_value.get_bucket.return_value.delete_keys\
                .return_value.errors = []

        result = bucket.delete_keys(urls)

        self.assertEqual(result, 3)

        self.assertEqual(mock_connect.return_value.get_bucket.return_value.
                         mock_calls, [
            call.delete_keys(['foo', 'bar'], quiet=True),
        ])
