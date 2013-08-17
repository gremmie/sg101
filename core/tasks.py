"""
Celery tasks for the core application.

"""
from celery.task import task
import django.core.mail

import core.whos_online


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
    # These imports, when placed at the top of the module, caused all kinds of
    # import problems when running on the production server (Python 2.5 and
    # mod_wsgi). Moving them here worked around that problem.

    from django.contrib.sessions.management.commands import clearsessions
    from forums.management.commands import forum_cleanup

    # Cleanup old sessions

    command = clearsessions.Command()
    command.execute()

    # Execute our forum cleanup command to delete old last visit records.

    command = forum_cleanup.Command()
    command.execute()


@task
def max_users():
    """
    Run the periodic task to calculate the who's online max users/visitors
    statistics.

    """
    core.whos_online.max_users()
