"""
Contains models for the bio application.
I would have picked profile for this application, but that is already taken, apparently.
"""
import datetime
import os.path

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string

from core.markup import SiteMarkup

# These are the secondary user status enumeration values. 
(STA_ACTIVE,        # User is a full member in good standing.
 STA_RESIGNED,      # User has voluntarily asked to be removed.
 STA_REMOVED,       # User was removed for bad behavior.
 STA_SUSPENDED,     # User is temporarily suspended; e.g. a stranger tripped
                    # the spam filter.
 STA_SPAMMER,       # User has been removed for spamming.
 STA_STRANGER,      # New member, isn't fully trusted yet. Their comments and
                    # forum posts are scanned for spam. They can have their
                    # accounts deactivated by moderators for spamming.
 ) = range(6)

USER_STATUS_CHOICES = (
    (STA_ACTIVE, "Active"),
    (STA_RESIGNED, "Resigned"),
    (STA_REMOVED, "Removed"),
    (STA_SUSPENDED, "Suspended"),
    (STA_SPAMMER, "Spammer"),
    (STA_STRANGER, "Stranger")
)


class Badge(models.Model):
    """This model represents badges that users can earn."""
    image = models.ImageField(upload_to='badges')
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    order = models.IntegerField()
    numeric_id = models.IntegerField(db_index=True)

    class Meta:
        ordering = ('order', )

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return self.image.url

    def html(self):
        """Returns a HTML img tag representation of the badge."""
        if self.image:
            return u'<img src="%s" alt="%s" title="%s" />' % (
                    self.get_absolute_url(), self.name, self.name)
        return u''
    html.allow_tags = True


def avatar_file_path_for_user(username, filename):
    return os.path.join(settings.AVATAR_DIR, 'users', username, filename)

def avatar_file_path(instance, filename):
    return avatar_file_path_for_user(instance.user.username, filename)


class UserProfile(models.Model):
    """model to represent additional information about users"""

    user = models.ForeignKey(User, unique=True)
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
    status = models.IntegerField(default=STA_STRANGER,
            choices=USER_STATUS_CHOICES)
    status_date = models.DateTimeField(auto_now_add=True)
    badges = models.ManyToManyField(Badge, through="BadgeOwnership")
    update_date = models.DateTimeField(db_index=True, blank=True)

    def __unicode__(self):
        return self.user.username

    class Meta:
        ordering = ('user__username', )

    def save(self, *args, **kwargs):
        update_date = datetime.datetime.now()
        sm = SiteMarkup()
        self.profile_html = sm.convert(self.profile_text)
        self.signature_html = sm.convert(self.signature)
        super(UserProfile, self).save(*args, **kwargs)
        cache.delete('avatar_' + self.user.username)

    @models.permalink
    def get_absolute_url(self):
        return ('bio-view_profile', (), {'username': self.user.username})

    def badge_ownership(self):
        if hasattr(self, '_badges'):
            return self._badges
        self._badges = BadgeOwnership.objects.filter(profile=self).select_related(
                "badge")
        return self._badges

    def is_stranger(self):
        """Returns True if this user profile status is STA_STRANGER."""
        return self.status == STA_STRANGER

    def user_is_active(self):
        """Returns the profile's user is_active status. This function exists
        for the admin.
        """
        return self.user.is_active
    user_is_active.boolean = True
    user_is_active.short_description = "Is Active"

    def search_title(self):
        full_name = self.user.get_full_name()
        if full_name:
            return u"%s (%s)" % (self.user.username, full_name)
        return self.user.username

    def search_summary(self):
        text = render_to_string('search/indexes/bio/userprofile_text.txt',
                {'object': self});
        return text


class UserProfileFlag(models.Model):
    """This model represents a user flagging a profile as inappropriate."""
    user = models.ForeignKey(User)
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


class BadgeOwnership(models.Model):
    """This model represents the ownership of badges by users."""
    profile = models.ForeignKey(UserProfile)
    badge = models.ForeignKey(Badge)
    count = models.IntegerField(default=1)

    class Meta:
        verbose_name_plural = "badge ownership"
        ordering = ('badge__order', )

    def __unicode__(self):
        if self.count == 1:
            return u"%s owns 1 %s" % (self.profile.user.username,
                    self.badge.name)
        else:
            return u"%s owns %d %s badges" % (self.profile.user.username,
                    self.count, self.badge.name)

    def badge_count_str(self):
        if self.count == 1:
            return u"1 %s" % self.badge.name
        return u"%d %ss" % (self.count, self.badge.name)
