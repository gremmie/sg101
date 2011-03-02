"""This file contains the automatic admin site definitions for the accounts Models"""

from django.contrib import admin
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail
from accounts.models import PendingUser
from accounts import create_new_user


class PendingUserAdmin(admin.ModelAdmin):
   list_display = ('username', 'email', 'date_joined')
   actions = ('activate_account', )

   def activate_account(self, request, qs):
       """
       Activate the accounts of the selected pending users.

       """
       for pending_user in qs:
           create_new_user(pending_user, admin_activation=True)

   activate_account.short_description = "Activate accounts for selected users"


admin.site.register(IllegalUsername)
admin.site.register(IllegalEmail)
admin.site.register(PendingUser, PendingUserAdmin)
