"""
Models for the smiley application.
"""
from django.db import models


class SmileyManager(models.Manager):
    smiley_map = None
    smilies = None

    def get_smiley_map(self):
        if self.smiley_map is None:
            smilies = self.all()
            self.smiley_map = {}
            for s in smilies:
                self.smiley_map[s.code] = s.html()
        return self.smiley_map

    def get_smilies(self):
        if self.smilies is None:
            self.smilies = self.all()
        return self.smilies

    def clear_cache(self):
        self.smiley_map = None
        self.smilies = None


class Smiley(models.Model):
    image = models.ImageField(upload_to='smiley/images/')
    title = models.CharField(max_length=32)
    code = models.CharField(max_length=32)

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
            return u'<img src="%s" alt="%s" title="%s" />' % \
                    (self.get_absolute_url(), self.title, self.title)
        return u''
    html.allow_tags = True

