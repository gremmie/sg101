"""
Models for the news application.
"""

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
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


class PendingStory(models.Model):
    """Stories submitted by users are held pending admin approval"""
    title = models.CharField(max_length=255)
    submitter = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    short_text = models.TextField()
    long_text = models.TextField(blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True, db_index=True)
    allow_comments = models.BooleanField(default=True)
    approved = models.BooleanField(default=False)
    tags = TagField()

    def save(self, force_insert = False, force_update = False):
        if self.approved:
            Story.objects.create(title=self.title,
                    submitter=self.submitter,
                    category=self.category,
                    short_text=self.short_text,
                    long_text=self.long_text,
                    allow_comments=self.allow_comments,
                    date_published=datetime.datetime.now(),
                    tags=self.tags)
            self.delete()
            cache.delete('home_news')
        else:
            super(PendingStory, self).save(force_insert, force_update)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-date_submitted', )
        verbose_name_plural = 'Pending Stories'


class Story(models.Model):
    """Model for news stories"""
    title = models.CharField(max_length=255)
    submitter = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    short_text = models.TextField()
    long_text = models.TextField(blank=True)
    allow_comments = models.BooleanField(default=True)
    date_published = models.DateTimeField(db_index=True)
    tags = TagField()

    @models.permalink
    def get_absolute_url(self):
        return ('news.views.story', [str(self.id)])

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-date_published', )
        verbose_name_plural = 'Stories'

    def can_comment_on(self):
        now = datetime.datetime.now()
        delta = now - self.date_published
        return delta.days < 30

    def save(self, force_insert=False, force_update=False):
        super(Story, self).save(force_insert, force_update)
        cache.delete('home_news')

