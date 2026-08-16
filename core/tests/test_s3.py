"""Unit tests for the S3Bucket wrapper.

These mock boto3 and assert on the calls made to it, so they prove we call the
API the way we intend to -- not that the calls succeed against a real bucket.
Nothing here can catch a wrong argument name that boto3 would reject at runtime;
that is what the S3 mode of tools/image_smoke.py is for.

"""
import unittest

from unittest.mock import call, patch, mock_open, Mock

from core.s3 import S3Bucket


class S3BucketTestCase(unittest.TestCase):

    def _bucket(self, mock_boto3):
        """Build an S3Bucket against the patched boto3 and return it together
        with the client mock its calls land on.

        """
        bucket = S3Bucket('access', 'secret', 'base_url', 'bucket_name')
        return bucket, mock_boto3.client.return_value

    @patch('core.s3.boto3')
    def test_client_is_built_for_the_region(self, mock_boto3):
        bucket, _ = self._bucket(mock_boto3)

        self.assertEqual(bucket.region_name, 'us-west-1')
        self.assertEqual(mock_boto3.client.mock_calls, [
            call('s3',
                 region_name='us-west-1',
                 aws_access_key_id='access',
                 aws_secret_access_key='secret'),
        ])
        self.assertEqual(bucket.base_url, 'base_url/')
        self.assertEqual(bucket.name, 'bucket_name')

    @patch('core.s3.boto3')
    def test_upload_from_file(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        mock_fp = Mock()
        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        url = bucket.upload_from_file('key_name', mock_fp, metadata)

        self.assertEqual(client.mock_calls, [
            call.put_object(Bucket='bucket_name',
                            Key='key_name',
                            Body=mock_fp,
                            Metadata={'user': '1234', 'date': '6/24/2025'},
                            ACL='public-read'),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.boto3')
    def test_upload_from_filename(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        opener = mock_open(read_data=b'image bytes')
        with patch('core.s3.open', opener, create=True):
            url = bucket.upload_from_filename('key_name', 'filename', metadata)

        opener.assert_called_once_with('filename', 'rb')
        self.assertEqual(client.mock_calls, [
            call.put_object(Bucket='bucket_name',
                            Key='key_name',
                            Body=opener.return_value,
                            Metadata={'user': '1234', 'date': '6/24/2025'},
                            ACL='public-read'),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.boto3')
    def test_upload_from_string(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        metadata = {
            'user': 1234,
            'date': '6/24/2025',
        }
        url = bucket.upload_from_string('key_name', 'content', metadata)

        self.assertEqual(client.mock_calls, [
            call.put_object(Bucket='bucket_name',
                            Key='key_name',
                            Body='content',
                            Metadata={'user': '1234', 'date': '6/24/2025'},
                            ACL='public-read'),
        ])
        self.assertEqual(url, 'base_url/bucket_name/key_name')

    @patch('core.s3.boto3')
    def test_upload_without_metadata_or_acl(self, mock_boto3):
        """Both are optional, and neither key should be sent when not asked
        for -- an unwanted ACL='public-read' is rejected outright by a bucket
        with public access blocked.

        """
        bucket, client = self._bucket(mock_boto3)

        bucket.upload_from_string('key_name', 'content', public=False)

        self.assertEqual(client.mock_calls, [
            call.put_object(Bucket='bucket_name',
                            Key='key_name',
                            Body='content'),
        ])

    @patch('core.s3.boto3')
    def test_delete_zero_keys(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        result = bucket.delete_keys([])

        self.assertEqual(result, 0)
        self.assertEqual(client.mock_calls, [])

    @patch('core.s3.boto3')
    def test_delete_keys(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        urls = [
            'base_url/bucket_name/foo',
            'base_url/bucket_name/bar',
            'baz',
        ]
        client.delete_objects.return_value = {}

        result = bucket.delete_keys(urls)

        # Two of the three URLs address this bucket. The third is somewhere
        # else and is not this bucket's to delete, so it is not counted as
        # deleted -- the boto v2 implementation returned 3 here.
        self.assertEqual(result, 2)
        self.assertEqual(client.mock_calls, [
            call.delete_objects(
                Bucket='bucket_name',
                Delete={'Objects': [{'Key': 'foo'}, {'Key': 'bar'}],
                        'Quiet': True}),
        ])

    @patch('core.s3.boto3')
    def test_delete_keys_counts_errors_against_the_total(self, mock_boto3):
        bucket, client = self._bucket(mock_boto3)

        urls = [
            'base_url/bucket_name/foo',
            'base_url/bucket_name/bar',
        ]
        client.delete_objects.return_value = {
            'Errors': [{'Key': 'bar', 'Code': 'AccessDenied'}],
        }

        self.assertEqual(bucket.delete_keys(urls), 1)

    @patch('core.s3.boto3')
    def test_delete_keys_no_url_addresses_this_bucket(self, mock_boto3):
        """Nothing to delete means no request at all; delete_objects rejects an
        empty Objects list.

        """
        bucket, client = self._bucket(mock_boto3)

        result = bucket.delete_keys(['somewhere/else/foo', 'baz'])

        self.assertEqual(result, 0)
        self.assertEqual(client.mock_calls, [])

    @patch('core.s3.boto3')
    def test_delete_keys_batches_at_the_api_limit(self, mock_boto3):
        """S3's DeleteObjects takes at most 1000 keys per request and boto3 does
        not chunk for us. Three members own enough photos to exceed that in one
        delete, reachable from the admin action and from antispam deactivation.

        """
        bucket, client = self._bucket(mock_boto3)

        urls = ['base_url/bucket_name/key%d' % i for i in range(2500)]
        client.delete_objects.return_value = {}

        result = bucket.delete_keys(urls)

        self.assertEqual(result, 2500)
        self.assertEqual(client.delete_objects.call_count, 3)

        sizes = [len(c.kwargs['Delete']['Objects'])
                 for c in client.delete_objects.call_args_list]
        self.assertEqual(sizes, [1000, 1000, 500])

        # Every key is sent exactly once, in order, across the batches.
        sent = [obj['Key']
                for c in client.delete_objects.call_args_list
                for obj in c.kwargs['Delete']['Objects']]
        self.assertEqual(sent, ['key%d' % i for i in range(2500)])

    @patch('core.s3.boto3')
    def test_base_url_already_ending_in_slash_is_not_doubled(self, mock_boto3):
        bucket = S3Bucket('access', 'secret', 'base_url/', 'bucket_name')

        self.assertEqual(bucket.base_url, 'base_url/')
        self.assertEqual(bucket.upload_from_string('key_name', 'content'),
                         'base_url/bucket_name/key_name')
