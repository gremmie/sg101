"""
This file contains the admin definitions for the donations application.
"""
from django.contrib import admin
from donations.models import Donation

class DonationAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', )

admin.site.register(Donation, DonationAdmin)
