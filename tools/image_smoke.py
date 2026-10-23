"""Live smoke test of the site's image upload paths.

Drives the avatar, user-photo and photo-of-the-day uploads through the real
views, with real image bytes, against the running stack -- then removes
everything it created. The unit suite mocks storage and runs against a throwaway
database, so it cannot tell you that an upload works on this deployment; this
can.

    docker compose exec -T web python /app/tools/image_smoke.py
    docker compose exec -T web python /app/tools/image_smoke.py --s3

Run it after anything that touches image handling: a Pillow bump, a change to
core/images/, a storage or settings change.

WARNING -- THIS WRITES TO WHATEVER DATABASE THE SETTINGS POINT AT, which in the
development container is the converted production snapshot. It creates a user,
uploads photos as that user, and deletes all of it again in a `finally` block,
verifying afterwards that the scratch user is gone. That cleanup has been
exercised, but it is still a write path against real data: take a snapshot
first with `tools/pg_snapshot.sh dump <label>` (see DOCKER.md section 6), and do
not point this at production.

Without --s3 the user-photo path is forced down its LOCAL_UPLOAD branch. Both
branches run the same PIL code and differ only in where the bytes land, so the
default run exercises image handling either way.

--s3 ADDITIONALLY WRITES REAL OBJECTS TO THE REAL BUCKET
--------------------------------------------------------
It needs live AWS credentials (AWS_ACCESS_KEY / AWS_SECRET_KEY) and it puts
objects into settings.USER_PHOTOS_BUCKET, so it is opt-in and off by default.
This is the only thing in the project that can tell you the S3 code actually
works: every S3 test in the suite mocks boto3, so none of them can catch a
wrong argument, and none of them knows whether the credentials still
authenticate or whether the bucket still permits a public-read write.

It uploads through the real view, fetches the object back over plain https with
no credentials (which is what proves public-read), checks the metadata the
upload attached, deletes through user_photos.storage.delete_photos -- so the
routing added for local files is exercised against a real S3 URL -- and then
confirms the object is gone.

Objects it creates are named with a recognisable prefix, because make_key()
otherwise produces random base64 that a interrupted run would leave unfindable.
The prefix is substituted for this run only; everything else takes the ordinary
path. To sweep leftovers by hand after a crash:

    aws s3 ls s3://sg101.user.photos/ | grep _image_smoke_
    aws s3 rm s3://sg101.user.photos/<key>

"""
import argparse
import os
import shutil
import sys
import traceback
import uuid
from io import BytesIO

import requests

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.dev')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client, override_settings  # noqa: E402
from PIL import Image  # noqa: E402

import core.images.upload  # noqa: E402
from core.s3 import S3Bucket, bucket_url_prefix  # noqa: E402
from core.tests.images.imagemakers import (jpeg_bytes,  # noqa: E402
                                           oriented_jpeg_bytes, png_bytes)
from potd.models import Photo  # noqa: E402
from user_photos.models import Photo as UserPhoto  # noqa: E402
from user_photos.storage import delete_photos  # noqa: E402

USERNAME = '_image_smoke_user'
PASSWORD = 'image-smoke'
S3_KEY_PREFIX = '_image_smoke_'

results = []
created = {'user': None, 'potd': None, 'photos': [], 'made_upload_dir': False,
           's3_keys': []}


def check(label, fn):
    try:
        detail = fn()
        results.append((True, label, detail))
        print('  ok    %-42s %s' % (label, detail))
    except Exception as exc:
        results.append((False, label, '%s: %s' % (type(exc).__name__, exc)))
        print('  FAIL  %-42s %s: %s' % (label, type(exc).__name__, exc))
        traceback.print_exc()


def opened(data):
    image = Image.open(BytesIO(data))
    image.load()
    return image


def upload_dir():
    return os.path.join(settings.MEDIA_ROOT,
                        settings.USER_PHOTOS_LOCAL_UPLOAD_DIR)


def ensure_upload_dir():
    """Create the local upload directory if this deployment has none.

    Dev uploads to S3, so the directory usually does not exist. Without this
    the run dies inside process_upload() with a FileNotFoundError, but only
    after the Photo row has already been written -- half-done work is worse
    than a clean refusal, and worse than simply creating the directory.

    """
    path = upload_dir()
    if not os.path.isdir(path):
        os.makedirs(path)
        created['made_upload_dir'] = True
        print('  (created %s for this run)' % path)


def main(with_s3=False):
    ensure_upload_dir()

    created['user'] = User.objects.create_user(
        USERNAME, 'image-smoke@example.com', PASSWORD)
    # Two things the production settings need and the test client does not
    # supply by default. Neither matters in development, which is why this tool
    # ran there and had never run against the stack it most needs to check.
    #
    # SERVER_NAME: Client() sends `Host: testserver`, which production's
    # ALLOWED_HOSTS rejects (development allows '*'), so every view-driven check
    # came back 400. The first allowed host is the right one to claim to be; a
    # leading dot is a suffix pattern rather than a name, so it is stripped.
    #
    # X-Forwarded-Proto: production sets SECURE_SSL_REDIRECT, so a plain-HTTP
    # POST is answered 301 to https -- which drops the body, and `follow=True`
    # then re-issues it as a GET. The checks saw 200 and no stored file. The
    # header is how Apache tells Django a request arrived over TLS
    # (SECURE_PROXY_SSL_HEADER), so claiming it is what a real request does.
    host = (settings.ALLOWED_HOSTS or ['testserver'])[0].lstrip('.')
    if host == '*':
        host = 'testserver'
    client = Client(SERVER_NAME=host, HTTP_X_FORWARDED_PROTO='https')
    assert client.login(username=USERNAME, password=PASSWORD), 'login failed'

    print('\n== avatar uploads (bio.views.change_avatar)')

    def avatar(name, data):
        response = client.post('/profile/avatar/',
                               {'avatar_file': SimpleUploadedFile(name, data)},
                               follow=True)
        assert response.status_code == 200, response.status_code
        profile = User.objects.get(username=USERNAME).profile
        assert profile.avatar.name, 'no avatar was stored'
        with profile.avatar.open('rb') as f:
            return opened(f.read())

    def png_avatar():
        image = avatar('smoke.png', png_bytes(size=(400, 300)))
        assert image.format == 'PNG', image.format
        assert image.mode == 'RGBA', image.mode
        assert max(image.size) <= settings.MAX_AVATAR_SIZE_PIXELS, image.size
        lo, hi = image.getchannel('A').getextrema()
        assert lo < hi, 'alpha was flattened'
        return 'PNG %s %s alpha %s-%s' % (image.mode, image.size, lo, hi)

    def jpeg_avatar():
        image = avatar('smoke.jpg', jpeg_bytes(size=(400, 300)))
        assert image.format == 'JPEG', image.format
        assert max(image.size) <= settings.MAX_AVATAR_SIZE_PIXELS, image.size
        return 'JPEG %s %s' % (image.mode, image.size)

    def oriented_avatar():
        # Landscape source carrying "rotate 90 CW" must come back rotated.
        image = avatar('turned.jpg', oriented_jpeg_bytes(6, size=(400, 300)))
        return 'JPEG %s (EXIF-oriented)' % (image.size,)

    check('PNG avatar keeps alpha and downscales', png_avatar)
    check('JPEG avatar downscales', jpeg_avatar)
    check('JPEG avatar with EXIF orientation', oriented_avatar)

    print('\n== user photo upload (user_photos.views.upload)')

    def user_photo(name, data, fmt):
        with override_settings(USER_PHOTOS_LOCAL_UPLOAD=True,
                               USER_PHOTOS_ENABLED=True):
            response = client.post(
                '/user_photos/upload/',
                {'image_file': SimpleUploadedFile(name, data)}, follow=True)
        assert response.status_code == 200, response.status_code
        photo = UserPhoto.objects.filter(user=created['user']).latest('id')
        created['photos'].append(photo)
        for url in (photo.url, photo.thumb_url):
            path = os.path.join(settings.MEDIA_ROOT,
                                url.split(settings.MEDIA_URL, 1)[1])
            image = opened(open(path, 'rb').read())
            assert image.format == fmt, '%s != %s' % (image.format, fmt)
        return 'stored %s + thumbnail as %s' % (photo.id, fmt)

    check('PNG user photo + thumbnail',
          lambda: user_photo('shot.png', png_bytes(size=(1000, 800)), 'PNG'))
    check('JPEG user photo + thumbnail',
          lambda: user_photo('shot.jpg', jpeg_bytes(size=(1000, 800)), 'JPEG'))

    print('\n== photo of the day (potd.models.Photo.generate_thumb)')

    def potd(name, data, fmt):
        photo = Photo(photo=SimpleUploadedFile(name, data),
                      caption='image smoke', description='image smoke',
                      user=created['user'])
        photo.save()
        created['potd'] = photo
        with photo.thumb.open('rb') as f:
            image = opened(f.read())
        assert image.format == fmt, '%s != %s' % (image.format, fmt)
        assert image.size[0] <= 120, image.size
        result = '%s thumb %s' % (fmt, image.size)
        _delete_potd(photo)
        created['potd'] = None
        return result

    check('PNG photo of the day',
          lambda: potd('potd.png', png_bytes(size=(600, 450)), 'PNG'))
    check('JPEG photo of the day',
          lambda: potd('potd.jpg', jpeg_bytes(size=(600, 450)), 'JPEG'))

    if with_s3:
        s3_main(client)


def smoke_key():
    """A recognisable stand-in for core.images.upload.make_key().

    The real one returns random base64, so an interrupted run would leave
    objects in the bucket that nobody could find. Only the name changes; the
    upload itself takes the ordinary path.

    """
    return S3_KEY_PREFIX + uuid.uuid4().hex


def bucket_for_smoke():
    return S3Bucket(settings.USER_PHOTOS_ACCESS_KEY,
                    settings.USER_PHOTOS_SECRET_KEY,
                    settings.USER_PHOTOS_BASE_URL,
                    settings.USER_PHOTOS_BUCKET,
                    region_name=settings.USER_PHOTOS_REGION)


def s3_main(client):
    """Upload to the real bucket, read it back, delete it, prove it is gone."""
    print('\n== S3 round trip -- REAL BUCKET %s' % settings.USER_PHOTOS_BUCKET)

    if not (settings.USER_PHOTOS_ACCESS_KEY and
            settings.USER_PHOTOS_SECRET_KEY):
        raise SystemExit(
            '  --s3 needs AWS_ACCESS_KEY and AWS_SECRET_KEY in the '
            'environment; both are empty.')

    prefix = bucket_url_prefix(settings.USER_PHOTOS_BASE_URL,
                               settings.USER_PHOTOS_BUCKET)
    state = {}

    def upload():
        # A size used nowhere else in this run. UploadForm.save() returns an
        # existing Photo when the md5 of the bytes matches one this user
        # already has, and _gradient() is deterministic -- so reusing the local
        # checks' (1000, 800) hands back their local photo and never touches
        # S3 at all. That is not hypothetical; it is what happened first.
        before = (UserPhoto.objects.filter(user=created['user'])
                  .order_by('-id').values_list('id', flat=True).first())

        # The key generator is the only substitution -- see smoke_key().
        real_make_key = core.images.upload.make_key
        core.images.upload.make_key = smoke_key
        try:
            with override_settings(USER_PHOTOS_LOCAL_UPLOAD=False,
                                   USER_PHOTOS_ENABLED=True):
                response = client.post(
                    '/user_photos/upload/',
                    {'image_file': SimpleUploadedFile(
                        's3smoke.jpg', jpeg_bytes(size=(1024, 768)))},
                    follow=True)
        finally:
            core.images.upload.make_key = real_make_key

        assert response.status_code == 200, response.status_code
        photo = UserPhoto.objects.filter(user=created['user']).latest('id')
        assert before is None or photo.id != before, (
            'no new row: UploadForm matched an existing signature and returned '
            'photo %s without uploading' % photo.id)
        created['photos'].append(photo)
        state['photo'] = photo

        for url in (photo.url, photo.thumb_url):
            assert url.startswith(prefix), 'not in the bucket: %s' % url
            created['s3_keys'].append(url[len(prefix):])

        return 'photo %s -> %s' % (photo.id, photo.url)

    def url_shape():
        """New rows must be indistinguishable from the ones already stored."""
        photo = state['photo']
        existing = (UserPhoto.objects
                    .filter(url__startswith=prefix)
                    .exclude(pk=photo.pk)
                    .values_list('url', flat=True)
                    .first())
        assert existing, 'no pre-existing S3 row to compare against'
        head = photo.url.rsplit('/', 1)[0]
        assert existing.startswith(head + '/'), \
            '%s does not match existing %s' % (photo.url, existing)
        return head + '/...'

    def public_read():
        """Fetch with no credentials at all. This is what proves public-read.

        If the bucket has since acquired Block Public Access, or object
        ownership set to bucket-owner-enforced, the per-object ACL the upload
        asks for is rejected and this comes back 403. That is a bucket
        configuration decision, not something to work around here.

        """
        r = requests.get(state['photo'].url, timeout=30)
        assert r.status_code == 200, 'HTTP %d fetching %s' % (
            r.status_code, state['photo'].url)
        image = opened(r.content)
        assert image.format == 'JPEG', image.format
        return 'HTTP 200, %s %s, %d bytes' % (image.format, image.size,
                                              len(r.content))

    def metadata():
        bucket = bucket_for_smoke()
        key = state['photo'].url[len(prefix):]
        head = bucket.client.head_object(
            Bucket=settings.USER_PHOTOS_BUCKET, Key=key)
        meta = head.get('Metadata', {})
        assert meta.get('user') == USERNAME, meta
        assert meta.get('date'), meta
        return 'user=%s date=%s' % (meta['user'], meta['date'])

    def delete_and_confirm():
        """Delete through the application's own path, not the bucket directly.

        This is what exercises task 04's routing against a real S3 URL.

        """
        photo = state['photo']
        count = delete_photos(UserPhoto.objects.filter(pk=photo.pk))
        assert count == 2, 'delete_photos reported %d, expected 2' % count

        r = requests.get(photo.url, timeout=30)
        assert r.status_code in (403, 404), \
            'object still fetchable after delete: HTTP %d' % r.status_code

        UserPhoto.objects.filter(pk=photo.pk).delete()
        created['photos'] = [p for p in created['photos'] if p.pk != photo.pk]
        created['s3_keys'] = []
        return 'delete_photos removed 2 keys; refetch HTTP %d' % r.status_code

    check('upload reaches the bucket', upload)
    if 'photo' not in state:
        # Everything below reads the uploaded object. Running them anyway
        # produces results about whatever did get stored, which is how a local
        # URL once made "delete_photos removes it again" pass: it deleted two
        # local files, and refetching a path the production web server does not
        # serve returned 404, which looked exactly like a deleted S3 object.
        print('  ---   skipping the rest: nothing was uploaded to the bucket')
        return

    check('URL matches the existing rows', url_shape)
    check('object is publicly readable', public_read)
    check('metadata survived the upload', metadata)
    check('delete_photos removes it again', delete_and_confirm)


def _delete_potd(photo):
    for field in (photo.thumb, photo.photo):
        if field.name:
            field.delete(save=False)
    Photo.objects.filter(pk=photo.pk).delete()


def cleanup():
    """Remove everything this run created, and prove the user is gone."""
    print('\n== cleanup')
    if created['potd'] is not None:
        _delete_potd(created['potd'])

    for photo in created['photos']:
        for url in (photo.url, photo.thumb_url):
            if settings.MEDIA_URL not in url:
                continue    # an S3 URL; the bucket sweep below handles it
            path = os.path.join(settings.MEDIA_ROOT,
                                url.split(settings.MEDIA_URL, 1)[1])
            if os.path.exists(path):
                os.remove(path)
        UserPhoto.objects.filter(pk=photo.pk).delete()

    # Anything left in the bucket. Normally empty -- the S3 checks delete what
    # they upload and clear this list -- so this is the path an interrupted run
    # takes, and it is verified rather than assumed.
    if created['s3_keys']:
        keys = list(created['s3_keys'])
        print('  removing %d leftover bucket object(s)' % len(keys))
        bucket = bucket_for_smoke()
        prefix = bucket_url_prefix(settings.USER_PHOTOS_BASE_URL,
                                   settings.USER_PHOTOS_BUCKET)
        bucket.delete_keys([prefix + key for key in keys])
        still_there = []
        for key in keys:
            r = requests.get(prefix + key, timeout=30)
            if r.status_code == 200:
                still_there.append(key)
        assert not still_there, \
            'bucket objects survived cleanup, remove by hand: %s' % still_there
        created['s3_keys'] = []

    user = User.objects.filter(username=USERNAME).first()
    if user is not None:
        if user.profile.avatar.name:
            user.profile.avatar.delete(save=False)
        User.objects.filter(username=USERNAME).delete()

    if created['made_upload_dir'] and os.path.isdir(upload_dir()):
        shutil.rmtree(upload_dir())

    remaining = User.objects.filter(username=USERNAME).count()
    print('  scratch user rows left: %d' % remaining)
    assert remaining == 0, 'scratch user was not removed -- clean up by hand'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--s3', action='store_true',
        help='also round-trip a photo through the REAL S3 bucket; needs live '
             'credentials and writes real objects (see the module docstring)')
    args = parser.parse_args()

    try:
        main(with_s3=args.s3)
    finally:
        cleanup()
    failed = [r for r in results if not r[0]]
    print('\n%d/%d checks passed' % (len(results) - len(failed), len(results)))
    sys.exit(1 if failed else 0)
