"""
Models for the gcalendar application.

"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.html import format_html

from core.markup import site_markup
import forums.tools


GIG_FORUM_SLUG = "gigs"

class PendingEventManager(models.Manager):
    """A manager for pending events."""

    def get_queryset(self):
        """Returns a queryset of events that have been approved to update
        the Google calendar."""
        return super(PendingEventManager, self).get_queryset().filter(
                Q(status=Event.NEW_APRV) |
                Q(status=Event.EDIT_APRV) |
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    what = models.CharField(max_length=255)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField()
    end_time = models.TimeField(null=True, blank=True)
    time_zone = models.CharField(max_length=64, blank=True)
    all_day = models.BooleanField(default=False)
    where = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    html = models.TextField(blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    google_id = models.CharField(max_length=255, blank=True)
    google_url = models.URLField(max_length=255, blank=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=NEW,
            db_index=True)
    create_forum_thread = models.BooleanField(default=False)

    objects = models.Manager()
    pending_events = PendingEventManager()

    def __str__(self):
        return self.what

    class Meta:
        ordering = ('-date_submitted', )

    def save(self, *args, **kwargs):
        self.html = kwargs.pop('html', '')
        if not self.html and self.description:
            self.html = site_markup(self.description, relative_urls=False)
        super(Event, self).save(*args, **kwargs)

    def is_approved(self):
        return self.status not in (self.NEW, self.EDIT_REQ, self.DEL_REQ)
    is_approved.boolean = True

    def google_html(self):
        """Returns a HTML <a> tag to the event if it exits."""
        if self.google_url:
            return format_html('<a href="{}">On Google</a>', self.google_url)
        return u''
    google_html.short_description = 'Google Link'

    def notify_on_calendar(self):
        """
        This function should be called when the event has been added to the
        Google calendar for the first time. This gives us a chance to perform
        any first-time processing, like creating a forum thread.
        """
        if self.create_forum_thread:
            topic_name = '%s: %s' % (self.start_date.strftime('%m/%d/%Y'),
                    self.what)
            post_body = "%s\n\n[Link to event on Google Calendar](%s)" % (
                    self.description, self.google_url)

            forums.tools.create_topic(
                forum_slug=GIG_FORUM_SLUG,
                user=self.user,
                topic_name=topic_name,
                post_body=post_body)

            self.create_forum_thread = False
            self.save()
