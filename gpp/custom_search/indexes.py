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
