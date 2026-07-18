"""Models for the antispam application."""
from django.db import models
from django.core.cache import cache
from django.utils.encoding import python_2_unicode_compatible

from antispam import SPAM_PHRASE_KEY


@python_2_unicode_compatible
class SpamPhrase(models.Model):
    """A SpamPhrase is a string that is checked for in user input. User input
    containing a SpamPhrase should be blocked and flagged.
    """
    phrase = models.CharField(max_length=64)

    class Meta:
        ordering = ('phrase', )

    def __str__(self):
        return self.phrase

    def save(self, *args, **kwargs):
        cache.delete(SPAM_PHRASE_KEY)
        self.phrase = self.phrase.lower()
        super(SpamPhrase, self).save(*args, **kwargs)
