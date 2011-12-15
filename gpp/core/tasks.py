"""
Celery tasks for the core application.

"""
from celery.task import task
import django.core.mail
from django.core.management.commands.cleanup import Command as CleanupCommand
from forums.management.commands.forum_cleanup import Command as ForumCleanup


@task
def add(x, y):
    """
    It is useful to have a test task laying around. This is it.

    """
    return x + y


@task
def send_mail(subject, message, from_email, recipient_list, **kwargs):
    """
    A task to send mail via Django.

    """
    django.core.mail.send_mail(subject, message, from_email, recipient_list,
            **kwargs)


@task
def cleanup():
    """
    A task to perform site-wide cleanup actions.

    """
    # Execute Django's cleanup command (deletes old sessions).

    command = CleanupCommand()
    command.execute()

    # Execute our forum cleanup command to delete old last visit records.

    command = ForumCleanup()
    command.execute()
