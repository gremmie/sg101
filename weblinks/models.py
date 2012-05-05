"""
This module contains the models for the weblinks application.
"""
import datetime

from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Links belong to categories"""
    title = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    description = models.TextField(blank=True)
    count = models.IntegerField(default=0)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('title', )


class PublicLinkManager(models.Manager):
    """The manager for all public links."""
    def get_query_set(self):
        return super(PublicLinkManager, self).get_query_set().filter(
                is_public=True).select_related()


class LinkBase(models.Model):
    """Abstract model to aggregate common fields of a web link."""
    category = models.ForeignKey(Category)
    title = models.CharField(max_length=128)
    url = models.URLField(db_index=True)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User)
    date_added = models.DateTimeField(db_index=True)
    update_date = models.DateTimeField(db_index=True, blank=True)

    class Meta:
        abstract = True


class Link(LinkBase):
    """Model to represent a web link"""
    hits = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False, db_index=True)

    # Managers:
    objects = models.Manager()
    public_objects = PublicLinkManager()

    class Meta:
        ordering = ('title', )

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.date_added:
                self.date_added = datetime.datetime.now()
            self.update_date = self.date_added
        else:
            self.update_date = datetime.datetime.now()

        super(Link, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('weblinks-link_detail', [str(self.id)])

    def search_title(self):
        return self.title

    def search_summary(self):
        return self.description


class PendingLink(LinkBase):
    """This model represents links that users submit. They must be approved by
    an admin before they become visible on the site.
    """
    class Meta:
        ordering = ('date_added', )

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            self.date_added = datetime.datetime.now()
            self.update_date = self.date_added
        else:
            self.update_date = datetime.datetime.now()

        super(PendingLink, self).save(*args, **kwargs)


class FlaggedLinkManager(models.Manager):

    def create(self, link, user):
        flagged_link = FlaggedLink(link = link, user = user, approved = False)
        flagged_link.save()


class FlaggedLink(models.Model):
    """Model to represent links that have been flagged as broken by users"""
    link = models.ForeignKey(Link)
    user = models.ForeignKey(User)
    date_flagged = models.DateField(auto_now_add = True)
    approved = models.BooleanField(default = False, 
        help_text = 'Check this and save to remove the referenced link from the database')

    objects = FlaggedLinkManager()

    def save(self, *args, **kwargs):
        if self.approved:
            self.link.delete()
            self.delete()
        else:
            super(FlaggedLink, self).save(*args, **kwargs)

    def url(self):
        return self.link.url

    def get_link_url(self):
        return '<a href="%s">Link #%d</a>' % (self.link.get_absolute_url(),
                self.link.id)
    get_link_url.allow_tags = True
    get_link_url.short_description = "View Link on Site"

    def __unicode__(self):
        return self.link.title

    class Meta:
        ordering = ('-date_flagged', )
