"""
This module contains custom search indexes to tailor the Haystack search
application to our needs.

"""
from queued_search.indexes import QueuedSearchIndex


class CondQueuedSearchIndex(QueuedSearchIndex):
    """
    This customized version of QueuedSearchIndex conditionally enqueues items
    to be indexed by calling the can_index() method.

    """
    def can_index(self, instance):
        """
        The default is to index all instances. Override this method to
        customize the behavior. This will be called on all update operations.

        """
        return True

    def enqueue(self, action, instance):
        """
        This method enqueues the instance only if the can_index() method
        returns True.

        """
        if (action == 'update' and self.can_index(instance) or
                action == 'delete'):
            super(CondQueuedSearchIndex, self).enqueue(action, instance)


class PublicQueuedSearchIndex(QueuedSearchIndex):
    """QueuedSearchIndex for models with is_public attributes."""

    def enqueue(self, action, instance):
        """Conditionally enqueue actions as follows.

        For update actions: if is_public is True, enqueue the update. If
        is_public is False, enqueue a delete action.

        Delete actions are always enqueued.

        """
        if action == 'update' and instance.is_public:
            super(PublicQueuedSearchIndex, self).enqueue(action, instance)
        elif (action == 'update' and not instance.is_public) or action == 'delete':
            super(PublicQueuedSearchIndex, self).enqueue('delete', instance)
