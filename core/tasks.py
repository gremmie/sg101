"""
Celery tasks for the core application.

"""
from __future__ import absolute_import

import django.core.mail
from celery import shared_task

import core.whos_online


@shared_task
def send_mail(**kwargs):
    """
    A task to send mail via Django.

    kwargs must be a dict of keyword arguments for an EmailMessage.

    """
    msg = django.core.mail.EmailMessage(**kwargs)
    msg.send()


@shared_task
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


@shared_task
def max_users():
    """
    Run the periodic task to calculate the who's online max users/visitors
    statistics.

    """
    core.whos_online.max_users()
