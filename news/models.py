"""
Models for the news application.
"""

from django.urls import reverse
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from core.markup import site_markup


# News App versions
NEWS_VERSION = 2

def validate_tags(tags):
    """Reject a tag containing a space.

    Tags are entered as one comma-separated string, so a space means the editor
    typed the old separator: "surf reverb twang" is otherwise accepted as a
    single tag, which no tag URL resolves and which appears alone in the cloud.
    This validates the whole list rather than each item, because Django's
    per-item wrapper reports only "Item 1 in the array did not validate:" and
    drops the reason.

    """
    spaced = [tag for tag in tags if ' ' in tag]
    if spaced:
        raise ValidationError(
                'Tags cannot contain spaces; separate them with commas. '
                'Did you mean "%(fixed)s"?',
                code='tag_with_space',
                params={'fixed': ', '.join(' '.join(tags).split())})


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

    def __str__(self):
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
    tags = ArrayField(
            models.CharField(max_length=50),
            default=list,
            blank=True,
            validators=[validate_tags],
            help_text="Separate tags with commas, e.g. surf, reverb, twang.")
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
            self.date_submitted = timezone.now()
            self.update_date = self.date_submitted
        else:
            self.update_date = timezone.now()

        # The tag page lowercases the name it looks up, so a tag stored with a
        # capital in it would have no reachable page.
        self.tags = [tag.lower() for tag in self.tags]

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

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_submitted']
        verbose_name_plural = 'Pending Stories'
        indexes = [GinIndex(fields=['tags'], name='news_pendingstory_tags_gin')]


class Story(StoryBase):
    """Model for news stories"""
    forums_topic = models.OneToOneField('forums.Topic', blank=True, null=True,
                                        on_delete=models.SET_NULL,
                                        db_index=False,
                                        help_text="Forum topic used for comments")

    def get_absolute_url(self):
        return reverse('news-story', args=[str(self.id)])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'news story'
        verbose_name_plural = 'news stories'
        indexes = [GinIndex(fields=['tags'], name='news_story_tags_gin')]

    def can_comment_on(self):
        # Only used for version 0 stories
        now = timezone.now()
        delta = now - self.date_submitted
        return self.allow_comments and delta.days < 30

    def forums_comment_count(self):
        """Returns number of comments for V2 news stories."""
        if self.forums_topic:
            return max(0, self.forums_topic.post_count - 1)
        return 0

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
