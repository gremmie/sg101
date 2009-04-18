"""
Models for the comments application.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core import urlresolvers


COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

class CommentManager(models.Manager):
    """Manager for the Comment model class."""

    def for_object(self, obj, filter_public=True):
        """QuerySet for all comments for a particular model instance."""
        ct = ContentType.objects.get_for_model(obj)
        qs = self.get_query_set().filter(content_type__pk=ct.id,
                object_id=obj.id)
        if filter_public:
            qs = qs.filter(is_public=True)
        return qs


class Comment(models.Model):
    """My own version of a Comment class that can attach comments to any other model."""
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User)
    comment = models.TextField(max_length=COMMENT_MAX_LENGTH)
    html = models.TextField(blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.IPAddressField('IP Address')
    is_public = models.BooleanField(default=True, 
            help_text='Uncheck this field to make the comment invisible.')
    is_removed = models.BooleanField(default=False,
            help_text='Check this field to replace the comment with a ' \
                    '"This comment has been removed" message')

    # Attach manager
    objects = CommentManager()

    class Meta:
        ordering = ('creation_date', )

    def __unicode__(self):
        return u'%s: %s...' % (self.user.username, self.comment[:50])

    def save(self, force_insert=False, force_update=False):
        html = render_to_string('comments/markdown.html', {'data': self.comment})
        self.html = html.strip()
        super(Comment, self).save(force_insert, force_update)

    def get_absolute_url(self):
        return self.get_content_object_url() + ('#c%s' % self.id)

    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return urlresolvers.reverse(
            "comments-url-redirect",
            args=(self.content_type_id, self.object_id)
        )


class CommentFlag(models.Model):
    """This model represents a user flagging a comment as inappropriate."""
    user = models.ForeignKey(User)
    comment = models.ForeignKey(Comment)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'Comment ID %s flagged by %s' % (self.comment_id, self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_comment_url(self):
        return '<a href="/admin/comments/comment/%s">Comment</a>' % self.comment.id
    get_comment_url.allow_tags = True

