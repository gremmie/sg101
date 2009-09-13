"""
Models for the forums application.
"""
from django.db import models
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string


class Category(models.Model):
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


class Forum(models.Model):
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


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics')
    name = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    view_count = models.IntegerField(blank=True, default=0)
    sticky = models.BooleanField(blank=True, default=False)
    locked = models.BooleanField(blank=True, default=False)

    # denormalized fields to reduce database hits
    post_count = models.IntegerField(blank=True, default=0)
    update_date = models.DateTimeField(auto_now=True)
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


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts')
    user = models.ForeignKey(User, related_name='posts')
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    body = models.TextField()
    html = models.TextField()
    user_ip = models.IPAddressField(blank=True, default='', null=True)

    class Meta:
        ordering = ('creation_date', )

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

# TODO: A "read" table
