"""
This file contains the admin definitions for the bio application.
"""

from django.contrib import admin
from bio.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    exclude = ('profile_html', 'signature_html')

admin.site.register(UserProfile, UserProfileAdmin)


# vim: ts=4 sw=4
