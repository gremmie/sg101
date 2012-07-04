"""
This file contains the core Models used in gpp
"""
from django.db import models


class Statistic(models.Model):
    """
    This model keeps track of site statistics. Currently, the only statistic
    is the maximum number of users online. This stat is computed by a mgmt.
    command that is run on a cron job to peek at the previous two models.
    """
    max_users = models.IntegerField()
    max_users_date = models.DateTimeField()
    max_anon_users = models.IntegerField()
    max_anon_users_date = models.DateTimeField()

    def __unicode__(self):
        return u'%d users on %s' % (self.max_users,
                self.max_users_date.strftime('%Y-%m-%d %H:%M:%S'))

