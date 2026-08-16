"""Module for all S3 related operations for the user_photos application."""

import logging

from django.conf import settings

from core.s3 import S3Bucket


logger = logging.getLogger(__name__)


def delete_photos(qs):
    """Delete the photos stored on S3 for the given Photo queryset.

    Returns the number of photos actually deleted.

    """

    bucket = S3Bucket(settings.USER_PHOTOS_ACCESS_KEY,
                      settings.USER_PHOTOS_SECRET_KEY,
                      settings.USER_PHOTOS_BASE_URL,
                      settings.USER_PHOTOS_BUCKET,
                      region_name=settings.USER_PHOTOS_REGION)

    key_urls = []
    for photo in qs:
        key_urls.append(photo.url)
        key_urls.append(photo.thumb_url)
    req_cnt = len(key_urls)

    logger.info("Requesting deletion of %d user photo(s) from S3", req_cnt)

    act_cnt = bucket.delete_keys(key_urls)

    if act_cnt == req_cnt:
        logger.info("Deleted %d user photo(s) from S3", act_cnt)
    else:
        logger.warning("Deleted %d user photo(s) out of %d", act_cnt, req_cnt)

    return act_cnt
