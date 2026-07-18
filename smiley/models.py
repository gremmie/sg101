"""
Models for the smiley application.
"""
import re

from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils.html import format_html
from django.contrib.sites.models import Site
from django.utils.encoding import python_2_unicode_compatible

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

    def get_smiley_regexes(self, relative_urls=True):
        """
        Returns a list of 2-tuples of the form: (regex, repl)
        where regex is a regular expression for a smiley and
        repl is the replacement image in Markdown format.

        If relative_urls is true, the smiley images will use relative URLs. If
        False, absolute URLs will be used.

        """
        key = 'smiley_regexes_rel' if relative_urls else 'smiley_regexes_abs'
        regexes = cache.get(key)
        if regexes:
            return regexes

        regexes = [(re.compile(r"(^|\s|(?<=\s))%s(\s|$)" % re.escape(s.code)),
            r"\1%s\2" % s.markdown(relative_urls=relative_urls)) for s in self.all()]
        cache.set(key, regexes, CACHE_TIMEOUT)
        return regexes


@python_2_unicode_compatible
class Smiley(models.Model):
    image = models.ImageField(upload_to='smiley/images/')
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)
    is_extra = models.BooleanField(default=False)

    objects = SmileyManager()

    class Meta:
        verbose_name_plural = 'Smilies'
        ordering = ('title', )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.image.url

    def html(self):
        """Returns a HTML img tag representation of the smiley."""
        if self.image:
            return format_html('<img src="{}" alt="{}" title="{}" />',
                    self.get_absolute_url(), self.title, self.title)
        return u''

    def markdown(self, relative_urls=True):
        """Returns a markdown representation of the smiley.

        If relative_urls is True, relative URLs will be generated. If False,
        absolute URLs will be used.

        """
        if self.image:
            if relative_urls:
                return u'![%s](%s "%s")' % (self.title, self.image.url,
                        self.title)
            else:
                site = Site.objects.get_current()
                return (u'![%s](%s://%s%s "%s")' % (
                    self.title, settings.SITE_SCHEME, site.domain, self.image.url, self.title))
        return u''
