"""Give stored photos the content type their key calls for (GitHub #40).

A photo labelled as octet-stream downloads when opened directly rather than
showing. Uploads now set the type; this repairs photos already in the bucket.
Thumbnails are left alone: all of them are mislabelled, and they are shown in
<img> tags, where the label does not matter.

    docker compose exec -T web python /app/tools/fix_s3_content_types.py
    docker compose exec -T web python /app/tools/fix_s3_content_types.py --apply --limit 3
    docker compose exec -T web python /app/tools/fix_s3_content_types.py --apply

The first form is a dry run, and writes nothing. It takes a minute or two, since
a listing does not carry content types and every photo has to be asked.

--apply WRITES TO THE PRODUCTION BUCKET
---------------------------------------
S3 changes an object's type only by copying it onto itself, and that copy
resets the object's ACL and replaces its metadata, so this sets both again. A
photo that is not public is left alone, because the copy would publish it. After
each copy the object is read back, with credentials and then over plain https
without them, and the first one that is not as expected stops the run.

The copy changes the object's Last-Modified. Nothing here can be undone other
than by copying again, but a repaired photo is no longer selected, so a run that
stopped can simply be run again.

"""
import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import boto3
import requests
from botocore.config import Config

sys.path.insert(0, '/app')

from core.s3 import bucket_url_prefix, content_type_for  # noqa: E402

OCTET_STREAM = ('binary/octet-stream', 'application/octet-stream')

# A photo's key is a 22 or 32 character id and its extension; its thumbnail's
# adds a "t". Every key in the bucket was one or the other when this was written.
PHOTO_STEM_LENGTHS = (22, 32)

ALL_USERS = 'http://acs.amazonaws.com/groups/global/AllUsers'

# What a copy with MetadataDirective=REPLACE drops unless it is passed again.
PRESERVED_HEADERS = ('CacheControl', 'ContentDisposition', 'ContentEncoding',
                     'ContentLanguage', 'Expires', 'StorageClass')


class RepairFailed(Exception):
    pass


def is_photo_key(key):
    return len(os.path.splitext(key)[0]) in PHOTO_STEM_LENGTHS


def repair_type(key, head):
    """The type to give this object, or None if it should be left as it is."""
    if not is_photo_key(key) or head.get('ContentType') not in OCTET_STREAM:
        return None
    return content_type_for(key)


def is_public(client, bucket, key):
    grants = client.get_object_acl(Bucket=bucket, Key=key)['Grants']
    return any(grant['Permission'] == 'READ' and
               grant['Grantee'].get('URI') == ALL_USERS for grant in grants)


def copy_with_type(client, bucket, key, head, content_type):
    kwargs = {header: head[header] for header in PRESERVED_HEADERS if header in head}
    client.copy_object(Bucket=bucket,
                       Key=key,
                       CopySource={'Bucket': bucket, 'Key': key},
                       # Not if the object changed since it was read.
                       CopySourceIfMatch=head['ETag'],
                       MetadataDirective='REPLACE',
                       Metadata=head.get('Metadata', {}),
                       ContentType=content_type,
                       ACL='public-read',
                       **kwargs)


def verify(client, bucket, key, head, content_type, public_url):
    """Raises RepairFailed unless the object is what it was, with the new type,
    and the public can read it."""
    after = client.head_object(Bucket=bucket, Key=key)
    for field, expected in (('ContentType', content_type),
                            ('ETag', head['ETag']),
                            ('ContentLength', head['ContentLength']),
                            ('Metadata', head.get('Metadata', {}))):
        if after.get(field) != expected:
            raise RepairFailed('{}: {} is {!r}, expected {!r}'.format(
                key, field, after.get(field), expected))
    response = requests.head(public_url, timeout=30)
    served = response.headers.get('Content-Type')
    if response.status_code != 200 or served != content_type:
        raise RepairFailed('{}: over https, status {} and type {!r}'.format(
            key, response.status_code, served))


def find_repairs(client, bucket):
    """Returns (repairs, unknown): (key, head, type) for each photo to repair,
    and the mislabelled photos whose key names no type."""
    keys = []
    for page in client.get_paginator('list_objects_v2').paginate(Bucket=bucket):
        keys += [obj['Key'] for obj in page.get('Contents', [])]
    photos = [key for key in keys if is_photo_key(key)]
    print('{} objects, {} of them photos'.format(len(keys), len(photos)))

    with ThreadPoolExecutor(16) as executor:
        heads = list(executor.map(
            lambda key: client.head_object(Bucket=bucket, Key=key), photos))

    repairs, unknown = [], []
    for key, head in zip(photos, heads):
        content_type = repair_type(key, head)
        if content_type:
            repairs.append((key, head, content_type))
        elif head.get('ContentType') in OCTET_STREAM:
            unknown.append(key)
    return repairs, unknown


def run(client, bucket, base_url, apply, limit):
    """Returns the number repaired, or would-be repaired."""
    repairs, unknown = find_repairs(client, bucket)
    print('{} to repair; {} mislabelled with no type from the key, left alone'.format(
        len(repairs), len(unknown)))

    public, private = [], []
    for repair in repairs:
        (public if is_public(client, bucket, repair[0]) else private).append(repair)
    for key, _, _ in private:
        print('not public, left alone: {}'.format(key))
    print('{} public, {} not'.format(len(public), len(private)))

    chosen = public[:limit] if limit else public
    prefix = bucket_url_prefix(base_url, bucket)
    for key, head, content_type in chosen:
        url = prefix + quote(key)
        if apply:
            copy_with_type(client, bucket, key, head, content_type)
            verify(client, bucket, key, head, content_type, url)
            print('repaired {} -> {}  {}'.format(head['ContentType'], content_type, url))
        else:
            print('would set {} -> {}  {}'.format(head['ContentType'], content_type, url))
    print('{} {}'.format('repaired' if apply else 'would repair', len(chosen)))
    return len(chosen)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--apply', action='store_true',
                        help='copy the objects; without this nothing is written')
    parser.add_argument('--limit', type=int, default=0,
                        help='handle only this many, to try it on a few first')
    args = parser.parse_args()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.dev')
    import django
    django.setup()
    from django.conf import settings

    # The dev settings log botocore at DEBUG, and that includes the access key ID
    # in every request's signature.
    logging.disable(logging.CRITICAL)

    client = boto3.client('s3',
                          region_name=settings.USER_PHOTOS_REGION,
                          aws_access_key_id=settings.USER_PHOTOS_ACCESS_KEY,
                          aws_secret_access_key=settings.USER_PHOTOS_SECRET_KEY,
                          config=Config(max_pool_connections=16))
    try:
        run(client, settings.USER_PHOTOS_BUCKET, settings.USER_PHOTOS_BASE_URL,
            args.apply, args.limit)
    except RepairFailed as exc:
        print('STOPPED: {}'.format(exc))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
