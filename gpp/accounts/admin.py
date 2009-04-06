"""This file contains the automatic admin site definitions for the accounts Models"""

from django.contrib import admin
from accounts.models import IllegalUsername
from accounts.models import IllegalEmail
from accounts.models import PendingUser

class PendingUserAdmin(admin.ModelAdmin):
   list_display = ('username', 'email', 'date_joined')

admin.site.register(IllegalUsername)
admin.site.register(IllegalEmail)
admin.site.register(PendingUser, PendingUserAdmin)
