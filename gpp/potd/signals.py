"""
Signal handlers for the potd application.

"""
from django.db.models.signals import post_save, post_delete

from potd.models import Photo, Sequence


def on_photo_save(sender, **kwargs):
    """
    This function is executed when a Photo is saved. It inserts the photo into
    the current sequence.

    """
    photo = kwargs['instance']
    Sequence.objects.insert_photo(photo.pk)


def on_photo_delete(sender, **kwargs):
    """
    This function is executed when a Photo is deleted. It removes the photo from
    the current sequence of photos.

    """
    photo = kwargs['instance']
    Sequence.objects.remove_photo(photo.pk)


post_save.connect(on_photo_save, sender=Photo, dispatch_uid='potd.signals')
post_delete.connect(on_photo_delete, sender=Photo, dispatch_uid='potd.signals')
