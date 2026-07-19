from django.contrib import admin

from elsewhere.models import (SocialNetworkProfile, WebsiteProfile,
        InstantMessengerProfile)


class ProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']

class SocialNetworkProfileAdmin(ProfileAdmin):
    list_display = ['user', 'network_id', 'username', 'date_added']

class InstantMessengerProfileAdmin(ProfileAdmin):
    list_display = ['user', 'network_id', 'username', 'date_added']

class WebsiteProfileAdmin(ProfileAdmin):
    list_display = ['user', 'name', 'url']


admin.site.register(SocialNetworkProfile, SocialNetworkProfileAdmin)
admin.site.register(WebsiteProfile, WebsiteProfileAdmin)
admin.site.register(InstantMessengerProfile, InstantMessengerProfileAdmin)
