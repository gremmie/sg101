"""Models for the messages application."""

import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from core.markup import site_markup


class MessageManager(models.Manager):
    """The manager for the Message model. Provides convenience functions."""

    def inbox(self, user):
        return self.filter(receiver=user,
            receiver_delete_date__isnull=True).select_related('sender')

    def outbox(self, user):
        return self.filter(sender=user,
            sender_delete_date__isnull=True).select_related('receiver')

    def trash(self, user):
        return self.filter(
            Q(sender=user, sender_delete_date__isnull=False) |
            Q(receiver=user, receiver_delete_date__isnull=False)
        ).select_related()

    def unread_count(self, user):
        return self.filter(receiver=user, read_date__isnull=True).count()


class Message(models.Model):
    """The Message is a model for a private message between users."""
    sender = models.ForeignKey(User, related_name='sender')
    receiver = models.ForeignKey(User, related_name='receiver')
    send_date = models.DateTimeField('Date Sent', null=True, blank=True)
    read_date = models.DateTimeField('Date Received', null=True, blank=True)
    reply_date = models.DateTimeField('Date Replied', null=True, blank=True)
    subject = models.CharField(max_length=120)
    message = models.TextField()
    html = models.TextField()
    sender_delete_date = models.DateTimeField(null=True, blank=True)
    receiver_delete_date = models.DateTimeField(null=True, blank=True)
    signature_attached = models.BooleanField(default=False)

    objects = MessageManager()

    def unread(self):
        """returns True if the message has not been read yet"""
        return self.read_date is None

    def replied_to(self):
        """returns True if the message has been replied to"""
        return self.reply_date is not None

    def is_deleted(self, user):
        """returns True if the message has been deleted by the user"""
        if (user == self.sender and self.sender_delete_date is not None) or (
            user == self.receiver and self.receiver_delete_date is not None):
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.id:
            self.send_date = datetime.datetime.now()
        self.html = site_markup(self.message)
        super(Message, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('messages.views.view', [str(self.id)])

    def __unicode__(self):
        return self.subject

    class Meta:
        ordering = ('-send_date', )


class OptionsManager(models.Manager):
    """Manager class for Options model."""

    def for_user(self, user):
        try:
            opts = self.get(user=user)
        except Options.DoesNotExist:
            opts = Options(user=user)
            opts.save()
        return opts


class Options(models.Model):
    """Options is a model for user private message options."""
    user = models.ForeignKey(User, editable=False)
    attach_signature = models.BooleanField("Always attach signature?", default=True)
    notify_email = models.BooleanField("Notify me of new messages via email?", default=False)

    objects = OptionsManager()

    def __unicode__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = "Options"


