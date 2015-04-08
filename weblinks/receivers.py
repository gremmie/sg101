"""Signal handlers for the weblinks application.

We use signals to compute the denormalized category counts whenever a weblink
is saved.
"""
from django.db.models.signals import post_save
from django.db.models.signals import post_delete

from weblinks.models import Category, Link


def on_link_save(sender, **kwargs):
    """This function updates the count field for all categories.
    It is called whenever a link is saved via a signal.
    """
    if kwargs['created']:
        # we only have to update the parent category
        link = kwargs['instance']
        cat = link.category
        cat.count = Link.public_objects.filter(category=cat).count()
        cat.save()
    else:
        # update all categories just to be safe (an existing link could
        # have been moved from one category to another
        cats = Category.objects.all()
        for cat in cats:
            cat.count = Link.public_objects.filter(category=cat).count()
            cat.save()


def on_link_delete(sender, **kwargs):
    """This function updates the count field for the link's parent
    category. It is called when a link is deleted via a signal.
    """
    # update the parent category
    link = kwargs['instance']
    cat = link.category
    cat.count = Link.public_objects.filter(category=cat).count()
    cat.save()


post_save.connect(on_link_save, sender=Link, dispatch_uid='weblinks.receivers')
post_delete.connect(on_link_delete, sender=Link, dispatch_uid='weblinks.receivers')
