"""
Models for the shoutbox application.
"""
from django.db import models
from django.contrib.auth.models import User


class Shout(models.Model):
    user = models.ForeignKey(User)
    shout_date = models.DateTimeField(auto_now_add=True)
    shout = models.TextField()

    @models.permalink
    def get_absolute_url(self):
        return ('shoutbox-view', [str(self.id)])

    def __unicode__(self):
        shout = self.shout[:60]
        return u'Shout from %s: %s' % (self.user.username, shout)

    class Meta:
        ordering = ('-shout_date', )


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
        return '<a href="/admin/shoutbox/shout/%s">Shout</a>' % self.shout.id
    get_shout_url.allow_tags = True

# vim: ts=4 sw=4
