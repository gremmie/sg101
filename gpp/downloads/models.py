"""
Models for the downloads application.
"""
import os

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template.defaultfilters import filesizeformat


class Category(models.Model):
    """Downloads belong to categories."""
    title = models.CharField(max_length=64)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('title', )

    def __unicode__(self):
        return self.title

    def num_downloads(self):
        return Download.public_objects.filter(category=self.pk).count()


def download_path(instance, filename):
    """
    Creates a path for a download. Uses the current date to avoid filename
    clashes. Uses the current microsecond also to make the directory name
    harder to guess.
    """
    now = datetime.datetime.now()
    parts = ['downloads']
    parts.extend([str(p) for p in (now.year, now.month, now.day, now.microsecond)])
    parts.append(filename)
    return os.path.join(*parts)


class PublicDownloadManager(models.Manager):
    """The manager for all public downloads."""
    def get_query_set(self):
        return super(PublicDownloadManager, self).get_query_set().filter(is_public=True)


class Download(models.Model):
    """Model to represent a download."""
    title = models.CharField(max_length=128)
    category = models.ForeignKey(Category)
    description = models.TextField()
    html = models.TextField(blank=True)
    file = models.FileField(upload_to=download_path)
    user = models.ForeignKey(User)
    date_added = models.DateTimeField(auto_now_add=True)
    ip_address = models.IPAddressField('IP Address')
    hits = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    total_votes = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False, db_index=True)

    # Managers:
    objects = models.Manager()
    public_objects = PublicDownloadManager()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('downloads-download', [str(self.id)])

    def save(self, force_insert=False, force_update=False):
        html = render_to_string('downloads/markdown.html', {'data': self.description})
        self.html = html.strip()
        super(Download, self).save(force_insert, force_update)

    def vote(self, vote_value):
        """receives a vote_value and updates internal score accordingly"""
        total_score = self.average_score * self.total_votes
        total_score += vote_value
        self.total_votes += 1
        self.average_score = total_score / self.total_votes
        return self.average_score

    def size(self):
        return filesizeformat(self.file.size)


class AllowedExtensionManager(models.Manager):
    def get_extension_list(self):
        return self.values_list('extension', flat=True)


class AllowedExtension(models.Model):
    """Model to represent the list of allowed file extensions."""
    extension = models.CharField(max_length=8)

    objects = AllowedExtensionManager()

    def __unicode__(self):
        return self.extension

    class Meta:
        ordering = ('extension', )


class VoteRecord(models.Model):
    """Model to record the date that a user voted on a download."""
    download = models.ForeignKey(Download)
    user = models.ForeignKey(User)
    vote_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s voted on '%s' on %s" % (
                self.user.username, 
                self.download.title, 
                self.vote_date.strftime('%b %d, %Y %H:%M:%S'))

    class Meta:
        ordering = ('-vote_date', )
