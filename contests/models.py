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

    def get_current_contests(self):
        now = datetime.datetime.now()
        return self.filter(creation_date__lte=now, win_date__isnull=True)


class Contest(models.Model):
    """
    A model to represent contests where users sign up to win something.

    """
    title = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    description = models.TextField()
    is_public = models.BooleanField(default=False, db_index=True)
    creation_date = models.DateTimeField(blank=True)
    end_date = models.DateTimeField()
    contestants = models.ManyToManyField(User, related_name='contests',
            blank=True)
    winners = models.ManyToManyField(User, blank=True,
            related_name='winning_contests')
    win_date = models.DateTimeField(null=True, blank=True)
    meta_description = models.TextField()
    num_winners = models.IntegerField(default=1,
            verbose_name='Number of winners')

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
        Returns True if the contest is still active and does not have any
        winners.

        """
        return not self.win_date and self.is_active()

    def can_comment_on(self):
        return self.is_active()

    def pick_winners(self):
        """
        This function randomly picks winners from all the contestants.

        """
        user_ids = list(self.contestants.values_list('id', flat=True))

        winner_count = min(len(user_ids), self.num_winners)
        if winner_count == 0:
            return

        winner_ids = []
        for n in xrange(winner_count):
            winner = random.choice(user_ids)
            winner_ids.append(winner)
            user_ids.remove(winner)

        winners = list(User.objects.filter(pk__in=winner_ids))
        self.winners.add(*winners)
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
