"""
Contains models for the bio application.
I would have picked profile for this application, but that is already taken, apparently.
"""

import os.path

from django.db import models
from django.contrib import auth
from django.conf import settings
from django.core.cache import cache

from core.markup import SiteMarkup


(STA_ACTIVE, STA_RESIGNED, STA_REMOVED, STA_SUSPENDED, STA_SPAMMER) = range(5)

USER_STATUS_CHOICES = (
    (STA_ACTIVE, "Active"),
    (STA_RESIGNED, "Resigned"),
    (STA_REMOVED, "Removed"),
    (STA_SUSPENDED, "Suspended"),
    (STA_SPAMMER, "Spammer"),
)

def avatar_file_path_for_user(username, filename):
    return os.path.join(settings.AVATAR_DIR, 'users', username, filename)

def avatar_file_path(instance, filename):
    return avatar_file_path_for_user(instance.user.username, filename)


class UserProfile(models.Model):
    """model to represent additional information about users"""

    user = models.ForeignKey(auth.models.User, unique=True)
    location = models.CharField(max_length=128, blank=True)
    birthday = models.DateField(blank=True, null=True,
            help_text='Optional; the year is not shown to others')
    occupation = models.CharField(max_length=128, blank=True)
    interests = models.CharField(max_length=255, blank=True)
    profile_text = models.TextField(blank=True)
    profile_html = models.TextField(blank=True)
    hide_email = models.BooleanField(default=True)
    signature = models.TextField(blank=True)
    signature_html = models.TextField(blank=True)
    avatar = models.ImageField(upload_to=avatar_file_path, blank=True)
    time_zone = models.CharField(max_length=64, blank=True,
            default='US/Pacific')
    use_24_time = models.BooleanField(default=False)
    forum_post_count = models.IntegerField(default=0)
    status = models.IntegerField(default=STA_ACTIVE,
            choices=USER_STATUS_CHOICES)
    status_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.user.username

    class Meta:
        ordering = ('user__username', )

    def save(self, *args, **kwargs):
        sm = SiteMarkup()
        self.profile_html = sm.convert(self.profile_text)
        self.signature_html = sm.convert(self.signature)
        super(UserProfile, self).save(*args, **kwargs)
        cache.delete('avatar_' + self.user.username)

    @models.permalink
    def get_absolute_url(self):
        return ('bio-view_profile', (), {'username': self.user.username})


class UserProfileFlag(models.Model):
    """This model represents a user flagging a profile as inappropriate."""
    user = models.ForeignKey(auth.models.User)
    profile = models.ForeignKey(UserProfile)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"%s's profile flagged by %s" % (self.profile.user.username,
                self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_profile_url(self):
        return '<a href="%s">Profile</a>' % self.profile.get_absolute_url()
    get_profile_url.allow_tags = True
