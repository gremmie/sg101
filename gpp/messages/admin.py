"""
This file contains the automatic admin site definitions for the Message models.
"""

from django.contrib import admin
from messages.models import Message
from messages.models import Options

admin.site.register(Message)
admin.site.register(Options)
