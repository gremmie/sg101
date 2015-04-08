"""Signal handlers for the downloads application.

We use signals to compute the denormalized category counts whenever a download
is saved.

"""
from django.db.models.signals import post_save
from django.db.models.signals import post_delete

from downloads.models import Category, Download, PendingDownload


def on_download_save(sender, **kwargs):
    """This function updates the count field for all categories.
    It is called whenever a download is saved via a signal.
    """
    if kwargs['created']:
        # we only have to update the parent category
        download = kwargs['instance']
        cat = download.category
        cat.count = Download.public_objects.filter(category=cat).count()
        cat.save()
    else:
        # update all categories just to be safe (an existing download could
        # have been moved from one category to another
        cats = Category.objects.all()
        for cat in cats:
            cat.count = Download.public_objects.filter(category=cat).count()
            cat.save()


def on_download_delete(sender, **kwargs):
    """This function updates the count field for the download's parent
    category. It is called when a download is deleted via a signal.

    We now delete the uploaded file when the download is deleted.
    """
    # update the parent category
    download = kwargs['instance']
    cat = download.category
    cat.count = Download.public_objects.filter(category=cat).count()
    cat.save()

    # delete the actual file
    if download.file:
        download.file.delete(save=False)


def on_pending_download_delete(sender, **kwargs):
    """Delete the uploaded file if it exists."""

    download = kwargs['instance']
    # delete the actual file
    if download.file:
        download.file.delete(save=False)


post_save.connect(on_download_save, sender=Download,
        dispatch_uid='downloads.receivers')
post_delete.connect(on_download_delete, sender=Download,
        dispatch_uid='downloads.receivers')
post_delete.connect(on_pending_download_delete, sender=PendingDownload,
        dispatch_uid='downloads.receivers')
