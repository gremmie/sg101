"""
Models for the ygroup application, which is a read-only archive of messages
from the old Yahoo Group.
"""
from django.urls import reverse
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

    def get_absolute_url(self):
        return reverse('ygroup-thread_view', args=[self.pk])


class Post(models.Model):
    thread = models.ForeignKey(
            Thread, null=True, blank=True,
            on_delete=models.SET_NULL, related_name='posts')
    title = models.CharField(max_length=255)
    creation_date = models.DateTimeField()
    poster = models.CharField(max_length=128)
    msg = models.TextField()

    # precomputed URL to this post in the parent thread for efficiency
    thread_url = models.URLField(blank=True)

    class Meta:
        ordering = ('creation_date', )
        verbose_name = 'yahoo group post'
        verbose_name_plural = 'yahoo group posts'

    def __unicode__(self):
        return u'Post %d, %s' % (self.pk, self.title)

    def get_absolute_url(self):
        return reverse('ygroup-post_view', kwargs={'pk': str(self.pk)})

    def search_title(self):
        return self.title

    def search_summary(self):
        return self.msg
