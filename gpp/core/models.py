"""
This file contains the core Models used in gpp
"""
from django.db import models
from django.contrib import auth


class UserLastVisit(models.Model):
    """
    This model represents timestamps indicating a user's last visit to the
    site.
    """
    user = models.ForeignKey(auth.models.User, unique=True)
    last_visit = models.DateTimeField(db_index=True)


class AnonLastVisit(models.Model):
    """
    This model represents timestamps for the last visit from non-authenticated
    users.
    """
    ip = models.CharField(max_length=16, db_index=True, unique=True)
    last_visit = models.DateTimeField(db_index=True)

