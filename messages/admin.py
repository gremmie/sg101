"""
This file contains the automatic admin site definitions for the Message models.
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from messages.models import Flag, Message, Options
import bio.badges


class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'send_date', 'subject']
    raw_id_fields = ['sender', 'receiver']
    exclude = ['html']
    date_hierarchy = 'send_date'
    list_display_links = ['subject']


class FlagAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'flag_date', 'message_link']
    date_hierarchy = 'flag_date'
    list_select_related = True
    readonly_fields = ['message', 'flag_date', 'comments', 'message_text']
    actions = ['accept_flags']

    def message_link(self, obj):
        return format_html('<a href="{}">Message</a>',
                reverse('admin:messages_message_change', args=[obj.message.id]))
    message_link.short_description = 'Message'

    def message_text(self, obj):
        return mark_safe(obj.message.html)
    message_text.short_description = 'Message text'

    def accept_flags(self, request, qs):
        """This admin action awards a security pin to the user who reported the
        message and then deletes the flag object.

        """
        count = qs.count()
        for flag in qs:
            bio.badges.award_badge(bio.badges.SECURITY_PIN, flag.message.receiver)
            flag.delete()

        self.message_user(request,
            "%s flag(s) acknowledged. You may want to mark users as spammers now." % count)

    accept_flags.short_description = "Accept selected flags"

admin.site.register(Flag, FlagAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Options)
