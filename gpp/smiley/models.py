"""
Models for the smiley application.
"""
from django.db import models
from django.core.cache import cache

CACHE_TIMEOUT = 60 * 5      # seconds


class SmileyManager(models.Manager):

    def get_smiley_map(self):
        map = cache.get('smiley_map')
        if map:
            return map

        map = dict((s.code, s.html()) for s in self.all())
        cache.set('smiley_map', map, CACHE_TIMEOUT)
        return map

    def get_smilies(self, extra=False):
        key = 'smileys' if not extra else 'smileys_extra'
        smilies = cache.get(key)
        if smilies:
            return smilies

        smilies = self.filter(is_extra=extra)
        cache.set(key, smilies, CACHE_TIMEOUT)
        return smilies


class Smiley(models.Model):
    image = models.ImageField(upload_to='smiley/images/')
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
    is_extra = models.BooleanField()

    objects = SmileyManager()

    class Meta:
        verbose_name_plural = 'Smilies'
        ordering = ('title', )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.image.url

    def html(self):
        if self.image:
            return (u'<img src="%s" alt="%s" title="%s" />' %
                    (self.get_absolute_url(), self.title, self.title))
        return u''
    html.allow_tags = True

