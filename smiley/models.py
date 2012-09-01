"""
Models for the smiley application.
"""
import re

from django.db import models
from django.core.cache import cache
from django.contrib.sites.models import Site

CACHE_TIMEOUT = 60 * 60      # seconds


class SmileyManager(models.Manager):

    def get_smiley_map(self):
        """
        Returns a dictionary, the keys are smiley codes.
        The values are the HTML representations of the keys.
        The dictionary is cached.
        """
        map = cache.get('smiley_map')
        if map:
            return map

        map = dict((s.code, s.html()) for s in self.all())
        cache.set('smiley_map', map, CACHE_TIMEOUT)
        return map

    def get_smilies(self, extra=False):
        """
        Returns smiley model instances filtered by the extra flag.
        """
        key = 'smileys' if not extra else 'smileys_extra'
        smilies = cache.get(key)
        if smilies:
            return smilies

        smilies = self.filter(is_extra=extra)
        cache.set(key, smilies, CACHE_TIMEOUT)
        return smilies

    def get_smiley_regexes(self):
        """
        Returns a list of 2-tuples of the form: (regex, repl)
        where regex is a regular expression for a smiley and
        repl is the replacement image in Markdown format.
        """
        regexes = cache.get('smiley_regexes')
        if regexes:
            return regexes

        regexes = [(re.compile(r"(^|\s|(?<=\s))%s(\s|$)" % re.escape(s.code)),
            r"\1%s\2" % s.markdown()) for s in self.all()]
        cache.set('smiley_regexes', regexes, CACHE_TIMEOUT)
        return regexes


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
        """Returns a HTML img tag representation of the smiley."""
        if self.image:
            site = Site.objects.get_current()
            return (u'<img src="http://%s%s" alt="%s" title="%s" />' %
                    (site.domain, self.get_absolute_url(), self.title, self.title))
        return u''
    html.allow_tags = True

    def markdown(self):
        """Returns a markdown representation of the smiley."""
        if self.image:
            site = Site.objects.get_current()
            return (u'![%s](http://%s%s "%s")' % 
                    (self.title, site.domain, self.get_absolute_url(), self.title))
        return u''
