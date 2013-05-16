"""
This file contains the admin definitions for the bio application.
"""
import datetime

from django.contrib import admin

import django.contrib.auth.models
import django.contrib.auth.admin

import bio.models
import bio.badges
from antispam.utils import deactivate_spammer


class BadgeOwnerInline(admin.TabularInline):
    model = bio.models.BadgeOwnership
    extra = 1


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'user__first_name', 'user__last_name',
            'user__email']
    exclude = ['profile_html', 'signature_html']
    list_display = ['__unicode__', 'user_is_active', 'get_status_display', 'status_date']
    readonly_fields = ['status', 'status_date', 'update_date']
    list_filter = ['status', ]
    date_hierarchy = 'status_date'
    inlines = [BadgeOwnerInline, ]
    actions = [
        'mark_active',
        'mark_resigned',
        'mark_removed',
        'mark_suspended',
        'mark_spammer',
        'mark_stranger',
        'unsubscribe_forums',
    ]

    def get_status_display(self, obj):
        return obj.get_status_display()
    get_status_display.short_description = 'Status'

    def mark_user_status(self, request, qs, status):
        """
        Common code for the admin actions. Updates the status field in the
        profiles to 'status'. Updates the status_date.  Sets the is_active
        field to True if the status is STA_ACTIVE and False otherwise.
        """
        now = datetime.datetime.now()
        for profile in qs:
            profile.user.is_active = (status == bio.models.STA_ACTIVE or
                    status == bio.models.STA_STRANGER)
            profile.user.save()
            profile.status = status
            profile.status_date = now
            profile.save(content_update=False)

        count = len(qs)
        msg = "1 user" if count == 1 else "%d users" % count
        self.message_user(request, "%s successfully marked as %s." % (msg,
            bio.models.USER_STATUS_CHOICES[status][1]))

    def mark_active(self, request, qs):
        """
        Marks users as active. Updates their profile status to STA_ACTIVE.
        """
        self.mark_user_status(request, qs, bio.models.STA_ACTIVE)
    mark_active.short_description = "Mark selected users as active"

    def mark_resigned(self, request, qs):
        """
        Marks users as inactive. Updates their profile status to STA_RESIGNED.
        """
        self.mark_user_status(request, qs, bio.models.STA_RESIGNED)
    mark_resigned.short_description = "Mark selected users as resigned"

    def mark_removed(self, request, qs):
        """
        Marks users as inactive. Updates their profile status to STA_REMOVED.
        """
        self.mark_user_status(request, qs, bio.models.STA_REMOVED)
    mark_removed.short_description = "Mark selected users as removed"

    def mark_suspended(self, request, qs):
        """
        Marks users as inactive. Updates their profile status to STA_SUSPENDED.
        """
        self.mark_user_status(request, qs, bio.models.STA_SUSPENDED)
    mark_suspended.short_description = "Mark selected users as suspended"

    def mark_spammer(self, request, qs):
        """
        Calls deactivate_spammer() on each user in the profile queryset.

        """
        count = qs.count()
        for profile in qs:
            deactivate_spammer(profile.user)

        self.message_user(request,
                "%s profile(s) successfully marked as spammers." % count)

    mark_spammer.short_description = "Mark selected users as spammers"

    def mark_stranger(self, request, qs):
        """
        Marks users as strangers. Updates their profile status to STA_STRANGER.
        """
        self.mark_user_status(request, qs, bio.models.STA_STRANGER)
    mark_stranger.short_description = "Mark selected users as strangers"

    def unsubscribe_forums(self, request, qs):
        """Delete users forum topic subscriptions."""
        for profile in qs:
            profile.user.subscriptions.clear()

        self.message_user(request, "%s subscription(s) deleted." % qs.count())

    unsubscribe_forums.short_description = "Delete users' forum subscriptions"


class UserProfileFlagAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'flag_date', 'get_profile_url']
    actions = ['accept_flags']
    raw_id_fields = ['user', 'profile']

    def accept_flags(self, request, qs):
        """
        This action awards a security pin to the user that reported the
        profile, deletes the flags, then deactivates the spammers.
        """
        count = qs.count()
        for flag in qs:
            deactivate_spammer(flag.profile.user)
            bio.badges.award_badge(bio.badges.SECURITY_PIN, flag.user)
            flag.delete()

        self.message_user(request,
                "%s profile(s) successfully marked as spammers." % count)

    accept_flags.short_description = "Mark selected profiles as spammers"


class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'html', 'order', 'numeric_id', 'description')
    list_editable = ('order', 'numeric_id')


# We like the User admin but would like a date hierarcy on date_joined.
class UserAdmin(django.contrib.auth.admin.UserAdmin):
    date_hierarchy = 'date_joined'


admin.site.register(bio.models.UserProfile, UserProfileAdmin)
admin.site.register(bio.models.UserProfileFlag, UserProfileFlagAdmin)
admin.site.register(bio.models.Badge, BadgeAdmin)

# Unregister existing ModelAdmin for User, then register ours
admin.site.unregister(django.contrib.auth.models.User)
admin.site.register(django.contrib.auth.models.User, UserAdmin)
