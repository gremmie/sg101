"""
Models for the news application.
"""
import datetime

from django.urls import reverse
from django.db import models
from django.contrib.auth.models import User
from tagging.fields import TagField

from core.markup import site_markup


# News App versions
NEWS_VERSION = 2


class Category(models.Model):
    """News stories belong to categories"""
    title = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    icon = models.ImageField(upload_to='news/categories/', blank=True)
    forum_slug = models.CharField(
            max_length=80,
            default='',
            blank=True,
            help_text=("Identifies the forum to create comment threads in for "
                       "stories in this category. If blank, no comment threads "
                       "will be created for stories in this category."))

    def __unicode__(self):
        return self.title

    def num_stories(self):
        return Story.objects.filter(category=self.pk).count()

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('title', )


class StoryBase(models.Model):
    """Abstract model to collect common fields."""
    title = models.CharField(max_length=255)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    short_text = models.TextField(default='', blank=True)
    long_text = models.TextField(default='', blank=True)
    date_submitted = models.DateTimeField(db_index=True)
    allow_comments = models.BooleanField(default=True)
    tags = TagField()
    front_page_expiration = models.DateField(null=True, blank=True)
    update_date = models.DateTimeField(db_index=True, blank=True)
    priority = models.IntegerField(db_index=True, default=0, blank=True)
    meta_description = models.TextField(blank=True)
    short_markup = models.TextField(default='', blank=True)
    long_markup = models.TextField(default='', blank=True)
    admin_content = models.TextField(default='', blank=True)
    version = models.SmallIntegerField(default=NEWS_VERSION)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_submitted = datetime.datetime.now()
            self.update_date = self.date_submitted
        else:
            self.update_date = datetime.datetime.now()

        if self.version >= 2:
            self.short_text = kwargs.pop('short_text', '')
            if not self.short_text and self.short_markup:
                self.short_text = site_markup(self.short_markup)

            self.long_text = kwargs.pop('long_text', '')
            if not self.long_text and self.long_markup:
                self.long_text = site_markup(self.long_markup)

        super(StoryBase, self).save(*args, **kwargs)


class PendingStory(StoryBase):
    """Stories submitted by users are held pending admin approval"""

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-date_submitted']
        verbose_name_plural = 'Pending Stories'


class Story(StoryBase):
    """Model for news stories"""
    forums_topic = models.OneToOneField('forums.Topic', blank=True, null=True,
                                        on_delete=models.SET_NULL,
                                        db_index=False,
                                        help_text="Forum topic used for comments")

    def get_absolute_url(self):
        return reverse('news-story', args=[str(self.id)])

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'news story'
        verbose_name_plural = 'news stories'

    def can_comment_on(self):
        # Only used for version 0 stories
        now = datetime.datetime.now()
        delta = now - self.date_submitted
        return self.allow_comments and delta.days < 30

    def forums_comment_count(self):
        """Returns number of comments for V2 news stories."""
        if self.forums_topic:
            return max(0, self.forums_topic.post_count - 1)
        return 0

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
