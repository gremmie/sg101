"""
Models for the ygroup application, which is a read-only archive of messages
from the old Yahoo Group.
"""
from django.db import models


class Thread(models.Model):
    title = models.CharField(max_length=255)
    creation_date = models.DateTimeField()

    # denormalized fields to reduce database hits
    poster = models.CharField(max_length=128)
    post_count = models.IntegerField(blank=True, default=0)
    page = models.IntegerField(blank=True, default=1)

    class Meta:
        ordering = ('creation_date', )

    def __unicode__(self):
        return u'Thread %d, %s' % (self.pk, self.title)

    @models.permalink
    def get_absolute_url(self):
        return ('ygroup-thread_view', [self.id])


class Post(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True,
            on_delete=models.SET_NULL, related_name='posts')
    title = models.CharField(max_length=255)
    creation_date = models.DateTimeField()
    poster = models.CharField(max_length=128)
    msg = models.TextField()

    # precomputed URL to this post in the parent thread for efficiency
    thread_url = models.URLField(verify_exists=False, blank=True)

    class Meta:
        ordering = ('creation_date', )
        verbose_name = 'yahoo group post'
        verbose_name_plural = 'yahoo group posts'

    def __unicode__(self):
        return u'Post %d, %s' % (self.pk, self.title)

    @models.permalink
    def get_absolute_url(self):
        return ('ygroup-post_view', [], {'pk': self.id})

    def search_title(self):
        return self.title

    def search_summary(self):
        return self.msg
