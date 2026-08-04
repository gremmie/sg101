# Celery integration: these lines ensures the celery app is always imported when
# Django starts so that shared_task can find the app.
from .celery import app as celery_app
