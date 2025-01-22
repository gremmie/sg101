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
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from core.markup import SiteMarkup
import bio.flags
from bio.signals import notify_profile_content_update


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


def avatar_file_path(instance, filename):
    # The avatar's name is the username plus the current time plus the file
    # extension. The time is used to bust browser caches.
    # Get extension, if it exists:
    ext = os.path.splitext(filename)[1]
    if not ext:
        ext = '.jpg'
    avatar_name = "{}{}{}".format(instance.user.username,
            datetime.datetime.utcnow().strftime('%S%f'), ext)
    return os.path.join(settings.AVATAR_DIR, 'users', avatar_name)


class UserProfile(models.Model):
    """model to represent additional information about users"""

    user = models.OneToOneField(User, related_name='profile',
                                on_delete=models.CASCADE)
    location = models.CharField(max_length=128, blank=True)
    country = models.CharField(max_length=2, blank=True, default='',
            choices=bio.flags.FLAG_CHOICES,
            help_text='Optional')
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
    auto_favorite = models.BooleanField(default=False)
    auto_subscribe = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user.username

    class Meta:
        ordering = ('user__username', )

    def save(self, *args, **kwargs):
        """
        Custom profile save() function.
        If content_update is True (default), then it is assumed that major
        fields are being updated and that the profile_content_update signal
        should be signalled. When content_update is False, the update_date is
        not updated, expensive markup conversions are not performed, and the
        signal is not signalled. This is useful for updating the
        forum_post_count, for example.

        """
        content_update = kwargs.pop('content_update', True)

        if content_update:
            self.update_date = datetime.datetime.now()
            sm = SiteMarkup()
            self.profile_html = sm.convert(self.profile_text)
            self.signature_html = sm.convert(self.signature)
            cache.delete('avatar_' + self.user.username)

        super(UserProfile, self).save(*args, **kwargs)

        if content_update:
            notify_profile_content_update(self)

    def get_absolute_url(self):
        return reverse('bio-view_profile', kwargs={'username': self.user.username})

    def badge_ownership(self):
        return BadgeOwnership.objects.filter(profile=self).select_related('badge')

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

    def reset(self):
        """
        Reset profile fields to empty defaults.
        This function is useful when a spammer is identified.

        """
        self.location = ''
        self.country = ''
        self.birthday = None
        self.occupation = ''
        self.interests = ''
        self.profile_text = ''
        self.signature = ''

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
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
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
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
