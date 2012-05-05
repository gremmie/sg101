"""
Celery tasks for the accounts application.

"""
from celery.task import task

from accounts.stats import update_user_stats


@task
def user_stats_task(user_id):
    """
    Run the update_user_stats() function on a new task.

    """
    update_user_stats(user_id)
