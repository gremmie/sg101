"""
Celery tasks for the messages application.

"""
from celery.task import task


@task
def purge_messages():
    """
    Task to purge messages that have been deleted by both sender & receiver.

    """
    from messages.management.commands.purge_messages import Command

    command = Command()
    command.execute()
