"""Live smoke test of the site's image upload paths.

Drives the avatar, user-photo and photo-of-the-day uploads through the real
views, with real image bytes, against the running stack -- then removes
everything it created. The unit suite mocks storage and runs against a throwaway
database, so it cannot tell you that an upload works on this deployment; this
can.

    docker compose exec -T web python /app/tools/image_smoke.py

Run it after anything that touches image handling: a Pillow bump, a change to
core/images/, a storage or settings change.

WARNING -- THIS WRITES TO WHATEVER DATABASE THE SETTINGS POINT AT, which in the
development container is the converted production snapshot. It creates a user,
uploads photos as that user, and deletes all of it again in a `finally` block,
verifying afterwards that the scratch user is gone. That cleanup has been
exercised, but it is still a write path against real data: take a snapshot
first with `tools/pg_snapshot.sh dump <label>` (see DOCKER.md section 8), and do
not point this at production.

The user-photo path is forced down its LOCAL_UPLOAD branch, because the S3
branch needs live credentials and would put objects in a real bucket. Both
branches run the same PIL code and differ only in where the bytes land, so this
exercises the image handling either way -- but it is not a test of the S3 code.
"""
import os
import shutil
import sys
import traceback
from io import BytesIO

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sg101.settings.docker')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client, override_settings  # noqa: E402
from PIL import Image  # noqa: E402

from core.tests.images.imagemakers import (jpeg_bytes,  # noqa: E402
                                           oriented_jpeg_bytes, png_bytes)
from potd.models import Photo  # noqa: E402
from user_photos.models import Photo as UserPhoto  # noqa: E402

USERNAME = '_image_smoke_user'
PASSWORD = 'image-smoke'

results = []
created = {'user': None, 'potd': None, 'photos': [], 'made_upload_dir': False}


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


def main():
    ensure_upload_dir()

    created['user'] = User.objects.create_user(
        USERNAME, 'image-smoke@example.com', PASSWORD)
    client = Client()
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
            path = os.path.join(settings.MEDIA_ROOT,
                                url.split(settings.MEDIA_URL, 1)[1])
            if os.path.exists(path):
                os.remove(path)
        UserPhoto.objects.filter(pk=photo.pk).delete()

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
    try:
        main()
    finally:
        cleanup()
    failed = [r for r in results if not r[0]]
    print('\n%d/%d checks passed' % (len(results) - len(failed), len(results)))
    sys.exit(1 if failed else 0)
