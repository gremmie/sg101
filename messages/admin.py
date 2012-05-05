"""
This file contains the automatic admin site definitions for the Message models.
"""
from django.contrib import admin

from messages.models import Message
from messages.models import Options


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'send_date', 'subject')
    raw_id_fields = ('sender', 'receiver')
    exclude = ('html', )
    date_hierarchy = 'send_date'
    list_display_links = ('subject', )

admin.site.register(Message, MessageAdmin)
admin.site.register(Options)
