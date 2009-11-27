"""
This file contains the admin definitions for the bio application.
"""

from django.contrib import admin
from bio.models import UserProfile
from bio.models import UserProfileFlag

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
            'user__email')
    exclude = ('profile_html', 'signature_html')


class UserProfileFlagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'flag_date', 'get_profile_url')


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserProfileFlag, UserProfileFlagAdmin)
