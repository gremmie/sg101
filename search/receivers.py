"""
Signal handlers for the search application.

These keep the index current from ordinary site activity: saving a searchable
object queues a task to rebuild its row, deleting one queues a task to drop it,
and changing a forum category's groups queues a rebuild of everything that
category holds.

Every one of them queues on transaction.on_commit and never calls delay()
outright. A task published before its transaction commits can reach a worker
first, read a row that does not exist yet, and index nothing -- an intermittent
failure that depends on load and leaves no trace. Queueing on commit also gets
rollback right for free: the transaction rolls back, the callback never runs.

Content is indexed on post_save rather than on the forums' own
topic_content_update / post_content_update signals, which the search stack this
replaces listened to so that saves changing no text did not reindex. Those are
sent from a handful of call sites by hand; one that someone forgets to add is an
index that goes quietly stale, and post_save cannot be bypassed. A save that
changes nothing searchable costs one task and one UPDATE, and the forums take
about 134 posts a month.

Three of the senders below are not searchable models themselves. A forum
category decides whether its topics and posts may be indexed at all; a User
carries the full name and the active flag that its profile document is built
from; and a member's website links are part of that document while living in
their own model. In each case the searchable object is never saved when the
thing that changed is, so post_save on the document's own model cannot see it.

"""
from functools import partial

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_delete
from django.db.models.signals import post_save

from elsewhere.models import WebsiteProfile

from bio.models import UserProfile
from forums.models import Category
from search.documents import all_documents
from search.tasks import reindex_category
from search.tasks import reindex_document
from search.tasks import remove_document


UID = 'search.receivers'


def queue_reindex(sender, instance, **kwargs):
    """Rebuilds this object's index row once its transaction commits."""
    queue(reindex_document, sender, instance.pk)


def queue_removal(sender, instance, **kwargs):
    """Drops this object's index row once its transaction commits."""
    # instance.pk is read now rather than inside the callback: the collector
    # sets it to None once the delete finishes, which is before the commit
    # that runs the callback.
    queue(remove_document, sender, instance.pk)


def queue_category_reindex(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Rebuilds a forum category's content when its groups change.

    Assigning a group makes the category members-only and its topics and posts
    have to leave the index; removing the last one makes it public again and
    they have to come back. The task handles both, so this only has to say
    which categories were touched.

    """
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    if reverse:
        # A group gained or lost categories, rather than the other way about.
        # post_clear cannot be served here -- Django has already forgotten
        # which categories the group held -- but nothing in the admin clears
        # from this side; forums.Category is what the admin edits.
        category_ids = sorted(pk_set or ())
    else:
        category_ids = [instance.pk]

    for category_id in category_ids:
        transaction.on_commit(partial(reindex_category.delay, category_id))


def queue_user_reindex(sender, instance, created, **kwargs):
    """
    Rebuilds a member's profile row when their user record changes.

    A profile document holds the user's full name at weight A and is indexed
    only while the account is active, and both of those live on User, which the
    admin can edit on its own. The site's own edit-profile view saves the
    profile too, so this is the admin's path rather than a member's.

    """
    # A new user's profile does not exist yet: bio's own receiver creates it,
    # and creating it queues its own reindex.
    if created:
        return

    # Every login saves the user to stamp last_login. Nothing indexed changes.
    if kwargs.get('update_fields') == frozenset(['last_login']):
        return

    queue_profile_reindex(instance.pk)


def queue_website_reindex(sender, instance, **kwargs):
    """
    Rebuilds a member's profile row when their website links change.

    The links a member lists are part of the profile document -- name and url,
    at weight B, as they were in the old index template -- but they live in
    their own model, so adding or removing one never saves the profile it
    belongs to and post_save on UserProfile cannot see it.

    """
    queue_profile_reindex(instance.user_id)


def queue_profile_reindex(user_id):
    """Queues a rebuild of one member's profile row, if they have one."""
    profile_id = UserProfile.objects.filter(user_id=user_id).values_list(
            'pk', flat=True).first()
    if profile_id is not None:
        queue(reindex_document, UserProfile, profile_id)


def queue(task, model, object_id):
    """Queues task for one object, to run once the transaction commits."""
    content_type_id = ContentType.objects.get_for_model(model).pk
    transaction.on_commit(partial(task.delay, content_type_id, object_id))


# The registry decides which models are searchable, so it is also what decides
# which ones need watching.
for document in all_documents():
    post_save.connect(queue_reindex, sender=document.model, dispatch_uid=UID)
    post_delete.connect(queue_removal, sender=document.model, dispatch_uid=UID)

# Deleting a category cascades through its forums to its topics and posts,
# each of which fires its own post_delete, so only the groups need watching.
m2m_changed.connect(queue_category_reindex, sender=Category.groups.through,
                    dispatch_uid=UID)

# Two models that are not searchable themselves but hold text a profile
# document indexes, and that a profile's own post_save never sees change.
post_save.connect(queue_user_reindex, sender=User, dispatch_uid=UID)
post_save.connect(queue_website_reindex, sender=WebsiteProfile,
                  dispatch_uid=UID)
post_delete.connect(queue_website_reindex, sender=WebsiteProfile,
                    dispatch_uid=UID)
