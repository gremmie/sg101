"""
Models for the forums application.
"""
import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string


POST_EDIT_DELTA = datetime.timedelta(seconds=3)


class Category(models.Model):
    """
    Forums belong to a category, whose access may be assigned to groups.
    """
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80)
    position = models.IntegerField(blank=True, default=0)
    groups = models.ManyToManyField(Group, blank=True, null=True,
        help_text="If groups are assigned to this category, only members" \
                    " of those groups can view this category.")

    class Meta:
        ordering = ('position', )
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return self.name

    def can_access(self, user):
        """
        Checks to see if the given user has permission to access
        this category.
        If this category has no groups assigned to it, return true.
        Else, return true if the user belongs to a group that has been
        assigned to this category, and false otherwise.
        """
        if self.groups.count() == 0:
            return True
        if user.is_authenticated():
            return self.groups.filter(user__pk=user.id).count() > 0
        return False


class ForumManager(models.Manager):
    """
    The manager for the Forum model. Provides a centralized place to
    put commonly used and useful queries.
    """

    def forums_for_user(self, user):
        """
        Returns a queryset containing the forums that the given user can
        "see" due to authenticated status, superuser status and group membership.
        """
        if user.is_superuser:
            qs = self.all()
        else:
            user_groups = []
            if user.is_authenticated():
                user_groups = user.groups.all()

            qs = self.filter(Q(category__groups__isnull=True) | \
                    Q(category__groups__in=user_groups))

        return qs.select_related('category', 'last_post', 'last_post__user')


class Forum(models.Model):
    """
    A forum is a collection of topics.
    """
    category = models.ForeignKey(Category, related_name='forums')
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80)
    description = models.TextField(blank=True, default='')
    position = models.IntegerField(blank=True, default=0)
    moderators = models.ManyToManyField(Group, blank=True, null=True)

    # denormalized fields to reduce database hits
    topic_count = models.IntegerField(blank=True, default=0)
    post_count = models.IntegerField(blank=True, default=0)
    last_post = models.OneToOneField('Post', blank=True, null=True,
        related_name='parent_forum')

    objects = ForumManager()

    class Meta:
        ordering = ('position', )

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('forums-forum_index', [self.slug])

    def topic_count_update(self):
        """Call to notify the forum that its topic count has been updated."""
        self.topic_count = Topic.objects.filter(forum=self).count()

    def post_count_update(self):
        """Call to notify the forum that its post count has been updated."""
        my_posts = Post.objects.filter(topic__forum=self)
        self.post_count = my_posts.count()
        if self.post_count > 0:
            self.last_post = my_posts[self.post_count - 1]
        else:
            self.last_post = None

    def sync(self):
        """
        Call to notify the forum that it needs to recompute its
        denormalized fields.
        """
        self.topic_count_update()
        self.post_count_update()

    def last_post_pre_delete(self):
        """
        Call this function prior to deleting the last post in the forum.
        A new last post will be found, if one exists.
        This is to avoid the Django cascading delete issue.
        """
        try:
            self.last_post = \
                Post.objects.filter(topic__forum=self).exclude(pk=self.last_post.pk).latest()
        except Post.DoesNotExist:
            self.last_post = None

    def catchup(self, user, flv=None):
        """
        Call to mark this forum all caught up for the given user (i.e. mark all topics
        read for this user).
        """
        TopicLastVisit.objects.filter(user=user, topic__forum=self).delete()
        if flv is None:
            try:
                flv = ForumLastVisit.objects.get(user=user, forum=self)
            except ForumLastVisit.DoesNotExist:
                flv = ForumLastVisit(user=user, forum=self)

        now = datetime.datetime.now()
        flv.begin_date = now
        flv.end_date = now
        flv.save()


class Topic(models.Model):
    """
    A topic is a thread of discussion, consisting of a series of posts.
    """
    forum = models.ForeignKey(Forum, related_name='topics')
    name = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    view_count = models.IntegerField(blank=True, default=0)
    sticky = models.BooleanField(blank=True, default=False)
    locked = models.BooleanField(blank=True, default=False)

    # denormalized fields to reduce database hits
    post_count = models.IntegerField(blank=True, default=0)
    update_date = models.DateTimeField()
    last_post = models.OneToOneField('Post', blank=True, null=True,
        related_name='parent_topic')

    class Meta:
        ordering = ('-sticky', '-update_date', )

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('forums-topic_index', [self.pk])

    def post_count_update(self):
        """
        Call this function to notify the topic instance that its post count
        has changed.
        """
        my_posts = Post.objects.filter(topic=self)
        self.post_count = my_posts.count()
        if self.post_count > 0:
            self.last_post = my_posts[self.post_count - 1]
            self.update_date = self.last_post.creation_date
        else:
            self.last_post = None
            self.update_date = self.creation_date

    def reply_count(self):
        """
        Returns the number of replies to a topic. The first post
        doesn't count as a reply.
        """
        if self.post_count > 1:
            return self.post_count - 1
        return 0

    def save(self, *args, **kwargs):
        if not self.id:
            now = datetime.datetime.now()
            self.creation_date = now
            self.update_date = now

        super(Topic, self).save(*args, **kwargs)

    def last_post_pre_delete(self):
        """
        Call this function prior to deleting the last post in the topic.
        A new last post will be found, if one exists.
        This is to avoid the Django cascading delete issue.
        """
        try:
            self.last_post = \
                Post.objects.filter(topic=self).exclude(pk=self.last_post.pk).latest()
        except Post.DoesNotExist:
            self.last_post = None


class Post(models.Model):
    """
    A post is an instance of a user's single contribution to a topic.
    """
    topic = models.ForeignKey(Topic, related_name='posts')
    user = models.ForeignKey(User, related_name='posts')
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(null=True)
    body = models.TextField()
    html = models.TextField()
    user_ip = models.IPAddressField(blank=True, default='', null=True)

    class Meta:
        ordering = ('creation_date', )
        get_latest_by = 'creation_date'

    @models.permalink
    def get_absolute_url(self):
        return ('forums-goto_post', [self.pk])

    def summary(self):
        LIMIT = 50
        if len(self.body) < LIMIT:
            return self.body
        return self.body[:LIMIT] + '...'

    def __unicode__(self):
        return self.summary()

    def save(self, *args, **kwargs):
        html = render_to_string('forums/post.html', {'data': self.body})
        self.html = html.strip()
        super(Post, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        first_post_id = self.topic.posts.all()[0].id
        super(Post, self).delete(*args, **kwargs)
        if self.id == first_post_id:
            self.topic.delete()

    def has_been_edited(self):
        return self.update_date is not None

    def touch(self):
        """Call this function to indicate the post has been edited."""
        self.update_date = datetime.datetime.now()


class FlaggedPost(models.Model):
    """This model represents a user flagging a post as inappropriate."""
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    flag_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'Post ID %s flagged by %s' % (self.post.id, self.user.username)

    class Meta:
        ordering = ('flag_date', )

    def get_post_url(self):
        return '<a href="%s">Post</a>' % self.post.get_absolute_url()
    get_post_url.allow_tags = True


class ForumLastVisit(models.Model):
    """
    This model records the last time a user visited a forum.
    It is used to compute if a user has unread topics in a forum.
    We keep track of a window of time, delimited by begin_date and end_date.
    Topics updated within this window are tracked, and may have TopicLastVisit
    objects.
    Marking a forum as all read sets the begin_date equal to the end_date.
    """
    user = models.ForeignKey(User)
    forum = models.ForeignKey(Forum)
    begin_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'forum')
        ordering = ('-end_date', )

    def __unicode__(self):
        return u'Forum: %d User: %d Date: %s' % (self.forum.id, self.user.id,
                self.end_date.strftime('%Y-%m-%d %H:%M:%S'))

    def is_caught_up(self):
        return self.begin_date == self.end_date


class TopicLastVisit(models.Model):
    """
    This model records the last time a user read a topic.
    Objects of this class exist for the window specified in the
    corresponding ForumLastVisit object.
    """
    user = models.ForeignKey(User)
    topic = models.ForeignKey(Topic)
    last_visit = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'topic')
        ordering = ('-last_visit', )

    def __unicode__(self):
        return u'Topic: %d User: %d Date: %s' % (self.topic.id, self.user.id,
                self.last_visit.strftime('%Y-%m-%d %H:%M:%S'))

    def save(self, *args, **kwargs):
        if self.id is one:
            self.touch()
        super(TopicLastVisit, self).save(*args, **kwargs)
        
    def touch(self):
        self.last_visit = datetime.datetime.now()
