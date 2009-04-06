"""This file contains the automatic admin site definitions for the legal models"""

from django.contrib import admin
from legal.models import Policy

class PolicyAdmin(admin.ModelAdmin):
   list_display = ('title', 'policy_type')

admin.site.register(Policy, PolicyAdmin)
