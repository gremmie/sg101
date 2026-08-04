"""
Celery tasks for the messages application.

"""

from celery import shared_task


@shared_task
def purge_messages():
    """
    Task to purge messages that have been deleted by both sender & receiver.

    """
    from django.core.management import call_command

    call_command('purge_messages')
