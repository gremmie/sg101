"""This file contains the automatic admin site definitions for the mailer
application."""
from django.contrib import admin

from mailer.models import Message


class MessageAdmin(admin.ModelAdmin):
    list_display = ('from_address', 'to_address', 'subject', 'creation_date')
    list_display_links = ('subject', )


admin.site.register(Message, MessageAdmin)
