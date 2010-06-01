"""
Models for the news application.
"""

import datetime
from django.db import models
from django.contrib.auth.models import User
from tagging.fields import TagField


class Category(models.Model):
    """News stories belong to categories"""
    title = models.CharField(max_length = 64)
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

    class Meta:
        abstract = True


class PendingStory(StoryBase):
    """Stories submitted by users are held pending admin approval"""

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_submitted = datetime.datetime.now()

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
        verbose_name_plural = 'Stories'

    def can_comment_on(self):
        now = datetime.datetime.now()
        delta = now - self.date_submitted
        return self.allow_comments and delta.days < 30
