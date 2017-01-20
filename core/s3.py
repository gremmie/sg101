"""s3.py

This module provides Amazon S3 convenience wrappers.

"""
from boto.s3 import connect_to_region
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.key import Key


class S3Bucket(object):
    """This class abstracts an Amazon S3 bucket.

    """
    def __init__(self, access_key, secret_key, base_url, bucket_name,
                 region_name='us-west-1'):
        self.region_name = region_name
        self.conn = self._get_connection(access_key, secret_key)
        self.bucket = self.conn.get_bucket(bucket_name, validate=False)
        self.base_url = base_url
        if not base_url.endswith('/'):
            self.base_url += '/'
        self.name = bucket_name

    def _get_connection(self, access_key, secret_key):
        conn = connect_to_region(
                    self.region_name,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    calling_format=OrdinaryCallingFormat())
        return conn

    def upload_from_file(self, key_name, fp, metadata=None, public=True):
        """Uploads data from the file object fp to a new key named
        key_name. metadata, if not None, must be a dict of metadata key / value
        pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        key = self._make_key(key_name, metadata)
        key.set_contents_from_file(fp)
        if public:
            key.make_public()
        return '{}{}/{}'.format(self.base_url, self.name, key_name)

    def upload_from_filename(self, key_name, filename, metadata=None,
            public=True):
        """Uploads data from the file named by filename to a new key named
        key_name. metadata, if not None, must be a dict of metadata key / value
        pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        key = self._make_key(key_name, metadata)
        key.set_contents_from_filename(filename)
        if public:
            key.make_public()
        return '{}{}/{}'.format(self.base_url, self.name, key_name)

    def upload_from_string(self, key_name, content, metadata=None,
            public=True):
        """Creates a new key with the given key_name, and uploads the string
        content to it. metadata, if not None, must be a dict of metadata key /
        value pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        key = self._make_key(key_name, metadata)
        key.set_contents_from_string(content)
        if public:
            key.make_public()
        return '{}{}/{}'.format(self.base_url, self.name, key_name)

    def delete_keys(self, key_urls):
        """Deletes a set of keys, specified as a list of URLs. The URLs could
        have been returned by one or more of the upload_* methods.

        Returns the number of keys that were successfully deleted.

        """
        if len(key_urls) == 0:
            return 0

        prefix = '{}{}/'.format(self.base_url, self.name)
        prefix_len = len(prefix)

        keys = []
        for url in key_urls:
            if url.startswith(prefix):
                key = url[prefix_len:]
                keys.append(key)

        response = self.bucket.delete_keys(keys, quiet=True)
        return len(key_urls) - len(response.errors)

    def _make_key(self, key_name, metadata):
        """Private method to create a key and optionally apply metadata to
        it.

        """
        key = Key(self.bucket)
        key.key = key_name
        if metadata:
            for k, v in metadata.iteritems():
                key.set_metadata(k, v)
        return key
