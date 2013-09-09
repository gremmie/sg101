"""s3.py

This module provides the necessary S3 upload functionality for the user_photos
application.

"""
from boto.s3.connection import S3Connection
from boto.s3.key import Key


class S3Bucket(object):
    """This class abstracts an Amazon S3 bucket.

    We currently only need upload functionality.

    """
    def __init__(self, access_key, secret_key, bucket_name):
        self.conn = S3Connection(access_key, secret_key)
        self.bucket = self.conn.get_bucket(bucket_name, validate=False)

    def upload_from_filename(self, key_name, filename, metadata=None,
            public=True):
        """Uploads data from the file named by filename to a new key named
        key_name. metadata, if not None, must be a dict of metadata key / value
        pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        """
        key = self._make_key(key_name, metadata)
        key.set_contents_from_filename(filename)
        if public:
            key.make_public()

    def upload_from_string(self, key_name, content, metadata=None,
            public=True):
        """Creates a new key with the given key_name, and uploads the string
        content to it. metadata, if not None, must be a dict of metadata key /
        value pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        """
        key = self._make_key(key_name, metadata)
        key.set_contents_from_string(content)
        if public:
            key.make_public()

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
