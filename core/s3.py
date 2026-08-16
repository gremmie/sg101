"""s3.py

This module provides Amazon S3 convenience wrappers, built on boto3.

Two callers: core/images/upload.py stores member photos, and user_photos/s3.py
deletes them. S3Bucket exists so neither has to know boto3's argument shapes,
and so the URL format written into user_photos.Photo rows is produced in one
place.

boto3's *client* is used rather than its resource layer. The batch delete below
is a client-shaped call whichever layer wraps it, and the client's flat keyword
arguments are what the tests assert against -- a chained resource call
(bucket.Object(key).put(...)) produces mock call lists that are considerably
harder to read a wrong argument out of.

"""
import boto3

# The S3 DeleteObjects API accepts at most 1000 keys per request. boto (v2)
# chunked internally; boto3's delete_objects does not, and raises instead. This
# is not a theoretical limit here: user_photos.s3.delete_photos submits two keys
# per photo (image + thumbnail), and three members have enough photos to exceed
# 1000 keys in a single delete -- the largest at 2,466. Both the admin's bulk
# action and antispam's account deactivation can reach them.
_DELETE_BATCH_SIZE = 1000


class S3Bucket(object):
    """This class abstracts an Amazon S3 bucket.

    """
    def __init__(self, access_key, secret_key, base_url, bucket_name,
                 region_name='us-west-1'):
        self.region_name = region_name
        self.client = self._get_client(access_key, secret_key)
        self.base_url = base_url
        if not base_url.endswith('/'):
            self.base_url += '/'
        self.name = bucket_name

    def _get_client(self, access_key, secret_key):
        return boto3.client('s3',
                            region_name=self.region_name,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key)

    def upload_from_file(self, key_name, fp, metadata=None, public=True):
        """Uploads data from the file object fp to a new key named
        key_name. metadata, if not None, must be a dict of metadata key / value
        pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        self._put(key_name, fp, metadata, public)
        return self._url(key_name)

    def upload_from_filename(self, key_name, filename, metadata=None,
            public=True):
        """Uploads data from the file named by filename to a new key named
        key_name. metadata, if not None, must be a dict of metadata key / value
        pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        with open(filename, 'rb') as fp:
            self._put(key_name, fp, metadata, public)
        return self._url(key_name)

    def upload_from_string(self, key_name, content, metadata=None,
            public=True):
        """Creates a new key with the given key_name, and uploads the string
        content to it. metadata, if not None, must be a dict of metadata key /
        value pairs which will be added to the key.

        If public is True, the key will be made public after the upload.

        Returns the URL to the uploaded file.

        """
        self._put(key_name, content, metadata, public)
        return self._url(key_name)

    def delete_keys(self, key_urls):
        """Deletes a set of keys, specified as a list of URLs. The URLs could
        have been returned by one or more of the upload_* methods.

        URLs that do not address this bucket are skipped; they are not this
        bucket's to delete.

        Returns the number of keys in this bucket that were successfully
        deleted.

        """
        prefix = '{}{}/'.format(self.base_url, self.name)
        prefix_len = len(prefix)

        keys = []
        for url in key_urls:
            if url.startswith(prefix):
                keys.append(url[prefix_len:])

        deleted = 0
        for i in range(0, len(keys), _DELETE_BATCH_SIZE):
            batch = keys[i:i + _DELETE_BATCH_SIZE]
            response = self.client.delete_objects(
                Bucket=self.name,
                Delete={
                    'Objects': [{'Key': key} for key in batch],
                    'Quiet': True,
                })
            deleted += len(batch) - len(response.get('Errors', []))

        return deleted

    def _put(self, key_name, body, metadata, public):
        """Private method to write one object, applying metadata and the public
        ACL if asked for.

        """
        kwargs = {'Bucket': self.name, 'Key': key_name, 'Body': body}

        if metadata:
            # S3 metadata travels as headers, so botocore requires str values
            # and rejects anything else; boto (v2) coerced them itself.
            kwargs['Metadata'] = {k: str(v) for k, v in metadata.items()}

        if public:
            # Objects already in this bucket are public-read and the site serves
            # them as plain URLs, so new ones have to match. A bucket carrying
            # Block Public Access, or object ownership set to bucket-owner
            # enforced, rejects a per-object ACL outright -- that is a property
            # of the live bucket and cannot be settled from here. The S3 smoke
            # tool is what answers it.
            kwargs['ACL'] = 'public-read'

        self.client.put_object(**kwargs)

    def _url(self, key_name):
        """Private method returning the public URL of a key in this bucket.

        This format is written into user_photos.Photo rows as an absolute URL,
        and tens of thousands of existing rows already use it, so new uploads
        have to be indistinguishable from them.

        """
        return '{}{}/{}'.format(self.base_url, self.name, key_name)
