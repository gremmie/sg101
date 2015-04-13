"""
Models for the shoutbox application.
"""
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.html import escape, urlize

from smiley.utils import smilify_html


class Shout(models.Model):
    user = models.ForeignKey(User)
    shout_date = models.DateTimeField(blank=True)
    shout = models.TextField()
    html = models.TextField()

    class Meta:
        ordering = ('-shout_date', )

    def __unicode__(self):
        if len(self.shout) > 60:
            return self.shout[:60] + "..."
        return self.shout

    @models.permalink
    def get_absolute_url(self):
        return ('shoutbox-view', [str(self.id)])

    def save(self, *args, **kwargs):
        if not self.id:
            self.shout_date = datetime.datetime.now()
        self.html = urlize(smilify_html(escape(self.shout)), trim_url_limit=15,
                nofollow=True)
        super(Shout, self).save(*args, **kwargs)


class ShoutFlag(models.Model):
    """This model represents a user flagging a shout as inappropriate."""
    user = models.ForeignKey(User)
    shout = models.ForeignKey(Shout)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'Shout ID %s flagged by %s' % (self.shout_id, self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_shout_url(self):
        return '<a href="/admin/shoutbox/shout/%(id)d">Shout #%(id)d</a>' % (
                {'id': self.shout.id})
    get_shout_url.allow_tags = True
    get_shout_url.short_description = 'Link to Shout'

