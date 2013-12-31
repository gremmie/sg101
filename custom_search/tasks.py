"""
Tasks for our custom search application.

"""
from __future__ import absolute_import

from celery import shared_task
from django.conf import settings

from queued_search.management.commands.process_search_queue import Command


@shared_task
def process_search_queue_task():
    """
    Celery task to run the queued_search application's process_search_queue
    command.

    """
    if settings.SEARCH_QUEUE_ENABLED:
        command = Command()
        command.execute()
    else:
        logger = process_search_queue_task.get_logger()
        logger.warning("Search queue disabled; skipping processing")
