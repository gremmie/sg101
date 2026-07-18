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
    from django.core.management import call_command

    # Cleanup old sessions

    call_command('clearsessions')

    # Execute our forum cleanup command to delete old last visit records.

    call_command('forum_cleanup')


@shared_task
def max_users():
    """
    Run the periodic task to calculate the who's online max users/visitors
    statistics.

    """
    core.whos_online.max_users()
