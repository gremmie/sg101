"""
Models for the gcalendar application.
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from core.markup import site_markup


class PendingEventManager(models.Manager):
    """A manager for pending events."""

    def get_query_set(self):
        """Returns a queryset of events that have been approved to update
        the Google calendar."""
        return super(PendingEventManager, self).get_query_set().filter(
                Q(status=Event.NEW_APRV) | \
                Q(status=Event.EDIT_APRV) | \
                Q(status=Event.DEL_APRV)
            )


class Event(models.Model):
    """Model to represent calendar events."""

    # Event status codes:
    (NEW, NEW_APRV, EDIT_REQ, EDIT_APRV, DEL_REQ, DEL_APRV, ON_CAL) = range(7)

    STATUS_CHOICES = (
        (NEW, 'New'),
        (NEW_APRV, 'New Approved'),
        (EDIT_REQ, 'Edit Request'),
        (EDIT_APRV, 'Edit Approved'),
        (DEL_REQ, 'Delete Request'),
        (DEL_APRV, 'Delete Approved'),
        (ON_CAL, 'On Calendar'),
    )

    REPEAT_CHOICES = (
        ('none', 'Does not repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    )

    user = models.ForeignKey(User)
    what = models.CharField(max_length=255)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField()
    end_time = models.TimeField(null=True, blank=True)
    time_zone = models.CharField(max_length=64, blank=True)
    all_day = models.BooleanField(default=False)
    repeat = models.CharField(max_length=7, choices=REPEAT_CHOICES)
    repeat_interval = models.IntegerField(null=True, blank=True,
        help_text='Only valid for repeating events.')
    until_date = models.DateField(null=True, blank=True,
        help_text='Only valid for repeating events; leave blank for no end date.')
    weekly_sun = models.BooleanField(default=False, verbose_name='Weekly on Sun',
        help_text='Only valid for weekly repeats.')
    weekly_mon = models.BooleanField(default=False, verbose_name='Weekly on Mon',
        help_text='Only valid for weekly repeats.')
    weekly_tue = models.BooleanField(default=False, verbose_name='Weekly on Tue',
        help_text='Only valid for weekly repeats.')
    weekly_wed = models.BooleanField(default=False, verbose_name='Weekly on Wed',
        help_text='Only valid for weekly repeats.')
    weekly_thu = models.BooleanField(default=False, verbose_name='Weekly on Thu',
        help_text='Only valid for weekly repeats.')
    weekly_fri = models.BooleanField(default=False, verbose_name='Weekly on Fri',
        help_text='Only valid for weekly repeats.')
    weekly_sat = models.BooleanField(default=False, verbose_name='Weekly on Sat',
        help_text='Only valid for weekly repeats.')
    monthly_by_day = models.BooleanField(default=False,
        help_text='Only valid for monthly repeats; Checked: By day of the month, Unchecked: By day of the week.')
    where = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    html = models.TextField(blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    google_id = models.CharField(max_length=255, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=NEW, db_index=True)

    objects = models.Manager()
    pending_events = PendingEventManager()

    def __unicode__(self):
        return self.what

    class Meta:
        ordering = ('-date_submitted', )

    def save(self, *args, **kwargs):
        self.html = site_markup(self.description)
        super(Event, self).save(*args, **kwargs)

    def is_approved(self):
        return self.status not in (self.NEW, self.EDIT_REQ, self.DEL_REQ)
    is_approved.boolean = True

