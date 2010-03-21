"""Models for the mailer application."""
import datetime

from django.db import models


MAX_SUBJECT = 120

class Message(models.Model):
    """The model to represent stored emails in the database."""
    from_address = models.EmailField()
    to_address = models.EmailField()
    subject = models.CharField(max_length=MAX_SUBJECT)
    body = models.TextField()
    creation_date = models.DateTimeField()

    class Meta:
        ordering = ('creation_date', )

    def __unicode__(self):
        return u'From: %s, To: %s, Subj: %s' % (
            self.from_address, self.to_address, self.subject)

    def save(self, *args, **kwargs):
        if self.id is None:
            self.creation_date = datetime.datetime.now()
        super(Message, self).save(*args, **kwargs)
