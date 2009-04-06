'''
This module contains the models for the weblinks application.
'''

from django.db import models
from django.contrib import auth


class Category(models.Model):
    '''Links belong to categories'''
    title = models.CharField(max_length = 64)
    description = models.TextField(blank = True)

    def __unicode__(self):
        return self.title

    def num_links(self):
        return Link.public_objects.filter(category = self.pk).count()

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('title', )


class PublicLinkManager(models.Manager):
    """The manager for all public links."""
    def get_query_set(self):
        return super(PublicLinkManager, self).get_query_set().filter(is_public=True)


class Link(models.Model):
    '''Model to represent a web link'''
    category = models.ForeignKey(Category)
    title = models.CharField(max_length=128)
    url = models.URLField(verify_exists=False, db_index=True)
    description = models.TextField(blank=True)
    user = models.ForeignKey(auth.models.User)
    date_added = models.DateField(auto_now_add=True)
    hits = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False, db_index=True)

    # Managers:
    objects = models.Manager()
    public_objects = PublicLinkManager()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title', )


class FlaggedLinkManager(models.Manager):

    def create(self, link, user):
        flagged_link = FlaggedLink(link = link, user = user, approved = False)
        flagged_link.save()


class FlaggedLink(models.Model):
    '''Model to represent links that have been flagged as broken by users'''
    link = models.ForeignKey(Link)
    user = models.ForeignKey(auth.models.User)
    date_flagged = models.DateField(auto_now_add = True)
    approved = models.BooleanField(default = False, 
        help_text = 'Check this and save to remove the referenced link from the database')

    objects = FlaggedLinkManager()

    def save(self, force_insert = False, force_update = False):
        if self.approved:
            self.link.delete()
            self.delete()
        else:
            super(FlaggedLink, self).save(force_insert, force_update)

    def url(self):
        return self.link.url

    def __unicode__(self):
        return self.link.title

    class Meta:
        ordering = ('-date_flagged', )
