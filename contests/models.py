"""
Models for the contest application.

"""
import random
import datetime

from django.db import models
from django.contrib.auth.models import User


class PublicContestManager(models.Manager):
    """
    The manager for all public contests.

    """
    def get_queryset(self):
        return super(PublicContestManager, self).get_queryset().filter(is_public=True)


class Contest(models.Model):
    """
    A model to represent contests where users sign up to win something.

    """
    title = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    description = models.TextField()
    is_public = models.BooleanField(db_index=True)
    creation_date = models.DateTimeField(blank=True)
    end_date = models.DateTimeField()
    contestants = models.ManyToManyField(User, related_name='contests',
            null=True, blank=True)
    winner = models.ForeignKey(User, null=True, blank=True,
            related_name='winning_contests')
    win_date = models.DateTimeField(null=True, blank=True)
    meta_description = models.TextField()

    objects = models.Manager()
    public_objects = PublicContestManager()

    class Meta:
        ordering = ['-creation_date']

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('contests-contest', [], {'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.pk and not self.creation_date:
            self.creation_date = datetime.datetime.now()

        super(Contest, self).save(*args, **kwargs)

    def is_active(self):
        """
        Returns True if the contest is still active.

        """
        now = datetime.datetime.now()
        return self.creation_date <= now < self.end_date

    def can_enter(self):
        """
        Returns True if the contest is still active and does not have a winner.

        """
        return not self.winner and self.is_active()

    def pick_winner(self):
        """
        This function randomly picks a winner from all the contestants.

        """
        user_ids = self.contestants.values_list('id', flat=True)
        winner_id = random.choice(user_ids)
        self.winner = User.objects.get(id=winner_id)
        self.win_date = datetime.datetime.now()

    def ogp_tags(self):
        """
        Returns a dict of Open Graph Protocol meta tags.

        """
        return {
            'og:title': self.title,
            'og:type': 'article',
            'og:url': self.get_absolute_url(),
            'og:description': self.meta_description,
        }
