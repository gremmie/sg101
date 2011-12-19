"""
Tasks for our custom search application.

"""
from celery.task import task

from queued_search.management.commands.process_search_queue import Command


@task
def process_search_queue_task():
    """
    Celery task to run the queued_search application's process_search_queue
    command.

    """
    command = Command()
    command.execute()
