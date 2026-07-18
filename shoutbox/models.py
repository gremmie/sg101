"""
Models for the shoutbox application.
"""
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import escape, urlize, format_html
from django.utils.encoding import python_2_unicode_compatible

from smiley.utils import smilify_html


@python_2_unicode_compatible
class Shout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shout_date = models.DateTimeField(blank=True)
    shout = models.TextField()
    html = models.TextField()

    class Meta:
        ordering = ('-shout_date', )

    def __str__(self):
        if len(self.shout) > 60:
            return self.shout[:60] + "..."
        return self.shout

    def get_absolute_url(self):
        return reverse('shoutbox-view', args=[str(self.pk)])

    def save(self, *args, **kwargs):
        if not self.id:
            self.shout_date = datetime.datetime.now()
        self.html = urlize(smilify_html(escape(self.shout)), trim_url_limit=15,
                nofollow=True)
        super(Shout, self).save(*args, **kwargs)


@python_2_unicode_compatible
class ShoutFlag(models.Model):
    """This model represents a user flagging a shout as inappropriate."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shout = models.ForeignKey(Shout, on_delete=models.CASCADE)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return u'Shout ID %s flagged by %s' % (self.shout_id, self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_shout_url(self):
        return format_html('<a href="/admin/shoutbox/shout/{id}">Shout #{id}</a>',
                id=self.shout.id)
    get_shout_url.short_description = 'Link to Shout'

