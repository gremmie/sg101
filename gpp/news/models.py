"""
Models for the news application.
"""

import datetime
from django.db import models
from django.contrib.auth.models import User
from tagging.fields import TagField


class Category(models.Model):
    """News stories belong to categories"""
    title = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    icon = models.ImageField(upload_to='news/categories/', blank=True)

    def __unicode__(self):
        return self.title

    def num_stories(self):
        return News.objects.filter(category = self.pk).count()

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('title', )


class StoryBase(models.Model):
    """Abstract model to collect common fields."""
    title = models.CharField(max_length=255)
    submitter = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    short_text = models.TextField()
    long_text = models.TextField(blank=True)
    date_submitted = models.DateTimeField(db_index=True)
    allow_comments = models.BooleanField(default=True)
    tags = TagField()
    front_page_expiration = models.DateField(null=True, blank=True)
    update_date = models.DateTimeField(db_index=True, blank=True)
    priority = models.IntegerField(db_index=True, default=0, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        abstract = True


class PendingStory(StoryBase):
    """Stories submitted by users are held pending admin approval"""

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.date_submitted:
                self.date_submitted = datetime.datetime.now()
            self.update_date = self.date_submitted
        else:
            self.update_date = datetime.datetime.now()

        super(PendingStory, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-date_submitted', )
        verbose_name_plural = 'Pending Stories'


class Story(StoryBase):
    """Model for news stories"""

    @models.permalink
    def get_absolute_url(self):
        return ('news.views.story', [str(self.id)])

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-date_submitted', )
        verbose_name = 'news story'
        verbose_name_plural = 'news stories'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_submitted = datetime.datetime.now()
            self.update_date = self.date_submitted
        else:
            self.update_date = datetime.datetime.now()

        super(Story, self).save(*args, **kwargs)

    def can_comment_on(self):
        now = datetime.datetime.now()
        delta = now - self.date_submitted
        return self.allow_comments and delta.days < 30

    def search_title(self):
        return self.title

    def search_summary(self):
        return u"\n".join((self.short_text, self.long_text))

    def ogp_tags(self):
        """
        Returns a dict of Open Graph Protocol meta tags.

        """
        desc = self.meta_description.strip()
        if not desc:
            desc = 'News article submitted by %s on %s.' % (
                    self.submitter.username,
                    self.date_submitted.strftime('%B %d, %Y'))

        return {
            'og:title': self.title,
            'og:type': 'article',
            'og:url': self.get_absolute_url(),
            'og:image': self.category.icon.url,
            'og:description': desc,
        }
