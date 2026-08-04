"""
Celery tasks for the accounts application.

"""

from celery import shared_task

from accounts.stats import update_user_stats


@shared_task
def user_stats_task(user_id):
    """
    Run the update_user_stats() function on a new task.

    """
    update_user_stats(user_id)
