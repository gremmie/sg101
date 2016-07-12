from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active']
    ordering = ['-event_date']
