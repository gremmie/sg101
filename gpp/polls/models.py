"""
Models for the Polls application.

"""
import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class PollManager(models.Manager):
    """Manager for the Poll model"""

    def get_current_polls(self):
        now = datetime.datetime.now()
        return self.filter(
                Q(is_enabled=True),
                Q(start_date__lte=now),
                Q(end_date__isnull=True) | Q(end_date__gte=now))

    def get_old_polls(self):
        now = datetime.datetime.now()
        return self.filter(
                is_enabled=True,
                end_date__isnull=False,
                end_date__lt=now)


class Poll(models.Model):
    """Model to represent polls"""
    start_date = models.DateTimeField(db_index=True,
            help_text='Date/time the poll will be eligible for voting.',)
    end_date = models.DateTimeField(blank=True, null=True, db_index=True,
            help_text='Date/time the poll will be ineligible for voting. '
                'Leave blank for an open ended poll.')
    is_enabled = models.BooleanField(default=True, db_index=True,
            help_text='Check to allow the poll to be viewed on the site.')
    question = models.CharField(max_length=200)

    objects = PollManager()

    def __unicode__(self):
        return self.question

    class Meta:
        ordering = ('-start_date', )
        get_latest_by = 'start_date'

    @models.permalink
    def get_absolute_url(self):
        return ('polls-detail', [], {'poll_id': str(self.id)})

    def results(self):
        """
        Returns a tuple; element 0 is the total votes, element 1 is a list of
        {choice, votes, pct}
        """
        choices = []
        total_votes = 0
        for choice in self.choice_set.all():
            total_votes += choice.votes
            choices.append({'choice': choice.choice, 'votes': choice.votes, 'pct': 0.0})

        if total_votes > 0:
            for choice in choices:
                choice['pct'] = float(choice['votes']) / total_votes * 100.0

        return (total_votes, choices)

    def _total_votes(self):
        """
        Returns the number of votes cast in this poll to date.

        """
        if not hasattr(self, '_total_votes_cache'):
            self._total_votes_cache = sum(choice.votes for choice in
                                            self.choice_set.all())
        return self._total_votes_cache
    total_votes = property(_total_votes)

    def is_open(self):
        now = datetime.datetime.now()
        return self.start_date <= now and (not self.end_date or now <= self.end_date)

    def can_comment_on(self):
        return self.is_open()


class Choice(models.Model):
    """Model for poll choices"""
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    voters = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return self.choice
