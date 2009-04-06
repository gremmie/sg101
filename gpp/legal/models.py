"""models for the legal module"""

from django.db import models

class Policy(models.Model):
   policy_type = models.SlugField(help_text = 'A slug for database lookups')
   title = models.CharField(max_length = 64)
   text = models.TextField()
   revised_date = models.DateField()

   def __unicode__(self):
      return self.title

   class Meta:
      verbose_name_plural = 'Policies'
