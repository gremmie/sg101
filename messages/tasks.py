"""
Celery tasks for the messages application.

"""
from __future__ import absolute_import

from celery import shared_task


@shared_task
def purge_messages():
    """
    Task to purge messages that have been deleted by both sender & receiver.

    """
    from messages.management.commands.purge_messages import Command

    command = Command()
    command.execute()
