"""
Models for the comments application.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.urls import reverse

from core.markup import site_markup


COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

class CommentManager(models.Manager):
    """Manager for the Comment model class."""

    def for_object(self, obj, filter_public=True):
        """QuerySet for all comments for a particular model instance."""
        ct = ContentType.objects.get_for_model(obj)
        qs = self.get_queryset().filter(content_type__pk=ct.id,
                object_id=obj.id)
        if filter_public:
            qs = qs.filter(is_public=True)
        return qs


class Comment(models.Model):
    """My own version of a Comment class that can attach comments to any other model."""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(max_length=COMMENT_MAX_LENGTH)
    html = models.TextField(blank=True)
    creation_date = models.DateTimeField()
    ip_address = models.GenericIPAddressField('IP Address')
    is_public = models.BooleanField(default=True,
            help_text='Uncheck this field to make the comment invisible.')
    is_removed = models.BooleanField(default=False,
            help_text='Check this field to replace the comment with a ' \
                    '"This comment has been removed" message')

    # Attach manager
    objects = CommentManager()

    class Meta:
        ordering = ('creation_date', )

    def __str__(self):
        return u'%s: %s...' % (self.user.username, self.comment[:50])

    def save(self, *args, **kwargs):
        if not self.id:
            self.creation_date = timezone.now()

        self.html = kwargs.pop('html', None)
        if self.html is None:
            self.html = site_markup(self.comment)
        super(Comment, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.get_content_object_url() + ('#c%s' % self.id)

    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return reverse(
            "comments-url-redirect",
            args=(self.content_type_id, self.object_id)
        )

    def not_removed(self):
        """
        Returns not self.is_removed. Used on the admin display for
        "green board" display purposes.
        """
        return not self.is_removed
    not_removed.boolean = True


class CommentFlag(models.Model):
    """This model represents a user flagging a comment as inappropriate."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return u'Comment ID %s flagged by %s' % (self.comment.id, self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_comment_url(self):
        return format_html('<a href="/admin/comments/comment/{}">Comment</a>',
                self.comment.id)

