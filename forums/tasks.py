"""
Celery tasks for the forums application.

"""

from celery import shared_task

import forums.latest


@shared_task
def new_post_task(post_id):
    """
    This task performs new post processing on a Celery task.

    """
    forums.latest.process_new_post(post_id)


@shared_task
def updated_post_task(post_id):
    """
    This task performs updated post processing on a Celery task.

    """
    forums.latest.process_updated_post(post_id)


@shared_task
def new_topic_task(topic_id):
    """
    This task performs new topic processing on a Celery task.

    """
    forums.latest.process_new_topic(topic_id)


@shared_task
def updated_topic_task(topic_id):
    """
    This task performs updated topic processing on a Celery task.

    """
    forums.latest.process_updated_topic(topic_id)
