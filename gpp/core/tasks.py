"""
Celery tasks for the core application.

"""
from celery.task import task
import django.core.mail


@task
def add(x, y):
    return x + y

@task
def send_mail(subject, message, from_email, recipient_list, **kwargs):
    django.core.mail.send_mail(subject, message, from_email, recipient_list,
            **kwargs)
