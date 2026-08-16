"""Deleting the stored files behind member photo uploads.

A photo lives in one of two places, decided by USER_PHOTOS_LOCAL_UPLOAD at the
moment it was uploaded: the S3 bucket, or this server's own disk under
MEDIA_ROOT. Each row stores an absolute URL, so the row itself records which one
-- there is no flag to consult, and a queryset can hold a mixture.

Both have to work here, because every delete path in the site arrives through
this module: a member removing their own photos, the admin's bulk action, and
antispam deactivating an account.

"""
import logging
import os
from urllib.parse import urlsplit

from django.conf import settings

from core.s3 import S3Bucket, bucket_url_prefix


logger = logging.getLogger(__name__)


def _local_url_prefix():
    """The URL path shared by every locally-stored photo.

    core.images.upload._user_photo_url() builds
    {scheme}://{domain}{MEDIA_URL}{USER_PHOTOS_LOCAL_UPLOAD_DIR}/{name}.

    """
    return '{}{}/'.format(settings.MEDIA_URL,
                          settings.USER_PHOTOS_LOCAL_UPLOAD_DIR)


def _local_path(url):
    """Return the on-disk path for a locally-stored photo URL, or None if the
    URL does not name one.

    Matching is on the URL *path*, never the scheme or the host, because both of
    those are environment-dependent: _user_photo_url() builds the scheme from
    SITE_SCHEME, which is 'https' in production and 'http' in base.py, and the
    host from the current Site row. A photo uploaded in a dev container is
    therefore http:// on whatever domain that install uses, while production's
    are https:// on surfguitar101.com -- the same rows, matched by the same
    code.

    (Measured 2026-08-16: every one of the 52,662 stored URLs is https, on one
    of two hosts. The mixed-scheme case is a dev/production difference, not
    something the archive contains.)

    The result is confined to the upload directory regardless. Nothing
    user-supplied reaches Photo.url today -- only UploadForm writes it, always
    from process_upload() -- but a delete driven by a database column should not
    depend on that continuing to be true.

    """
    prefix = _local_url_prefix()
    path = urlsplit(url).path
    if not path.startswith(prefix):
        return None

    name = path[len(prefix):]
    if not name:
        return None

    root = os.path.realpath(os.path.join(settings.MEDIA_ROOT,
                                         settings.USER_PHOTOS_LOCAL_UPLOAD_DIR))
    candidate = os.path.realpath(os.path.join(root, name))
    if candidate != root and not candidate.startswith(root + os.sep):
        logger.error("Refusing to delete %s: it resolves to %s, outside %s",
                     url, candidate, root)
        return None

    return candidate


def _delete_local(paths):
    """Unlink local photo files. Returns how many are gone afterwards.

    A file that is already missing counts as deleted: the row is going away
    either way, and one absent file must not abort the batch or leave a member
    unable to remove a photo.

    """
    deleted = 0
    for path in paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            logger.info("Local photo file was already gone: %s", path)
            deleted += 1
        except OSError:
            logger.exception("Could not delete local photo file: %s", path)
        else:
            deleted += 1
    return deleted


def delete_photos(qs):
    """Delete the stored files for the given Photo queryset.

    Returns the number of stored files actually deleted, across both backends.
    The rows are not touched; callers delete those.

    """
    s3_prefix = bucket_url_prefix(settings.USER_PHOTOS_BASE_URL,
                                  settings.USER_PHOTOS_BUCKET)

    s3_urls = []
    local_paths = []
    unknown = 0

    photo_count = 0
    for photo in qs:
        photo_count += 1
        for url in (photo.url, photo.thumb_url):
            if not url:
                continue
            path = _local_path(url)
            if path is not None:
                local_paths.append(path)
            elif url.startswith(s3_prefix):
                s3_urls.append(url)
            else:
                unknown += 1
                logger.warning(
                    "Not deleting %s: it is neither in %s nor under %s",
                    url, s3_prefix, _local_url_prefix())

    requested = len(s3_urls) + len(local_paths)
    logger.info(
        "Deleting %d stored file(s) for %d photo(s): %d in S3, %d local, "
        "%d unrecognised", requested, photo_count, len(s3_urls),
        len(local_paths), unknown)

    # Only build the bucket if there is something in it to delete -- a member
    # whose photos are all on local disk should not need working credentials.
    s3_deleted = 0
    if s3_urls:
        bucket = S3Bucket(settings.USER_PHOTOS_ACCESS_KEY,
                          settings.USER_PHOTOS_SECRET_KEY,
                          settings.USER_PHOTOS_BASE_URL,
                          settings.USER_PHOTOS_BUCKET,
                          region_name=settings.USER_PHOTOS_REGION)
        s3_deleted = bucket.delete_keys(s3_urls)

    local_deleted = _delete_local(local_paths)
    deleted = s3_deleted + local_deleted

    if deleted == requested:
        logger.info("Deleted %d stored file(s)", deleted)
    else:
        logger.warning(
            "Deleted %d of %d stored file(s): S3 %d/%d, local %d/%d",
            deleted, requested, s3_deleted, len(s3_urls),
            local_deleted, len(local_paths))

    return deleted
