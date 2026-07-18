from django.db import models
from django.utils.encoding import python_2_unicode_compatible


class ActiveEventManager(models.Manager):
    """Manager for all active events."""
    def get_queryset(self):
        return super(ActiveEventManager, self).get_queryset().filter(
                is_active=True)


@python_2_unicode_compatible
class Event(models.Model):
    """Model for events we are counting down for."""
    name = models.CharField(max_length=64)
    url = models.URLField(max_length=200)
    event_date = models.DateTimeField()
    is_active = models.BooleanField(db_index=True)

    objects = models.Manager()
    active_objects = ActiveEventManager()

    def __str__(self):
        return u"{} on {}".format(
            self.name, self.event_date.strftime('%m/%d/%Y'))

    class Meta:
        ordering = ['event_date']
