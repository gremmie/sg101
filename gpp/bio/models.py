"""
Contains models for the bio application.
I would have picked profile for this application, but that is already taken, apparently.
"""

import os.path

from django.db import models
from django.contrib import auth
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache


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

    def __unicode__(self):
        return self.user.username

    class Meta:
        ordering = ('user__username', )

    def save(self, *args, **kwargs):
        html = render_to_string('bio/markdown.html', {'data': self.profile_text})
        self.profile_html = html.strip()
        html = render_to_string('bio/markdown.html', {'data': self.signature})
        self.signature_html = html.strip()
        super(UserProfile, self).save(*args, **kwargs)
        cache.delete('avatar_' + self.user.username)

