"""
This file contains the admin definitions for the donations application.

"""
from django.contrib import admin
from donations.models import Donation

class DonationAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']
    date_hierarchy = 'payment_date'
    list_display = ['__unicode__', 'payer_email', 'payment_date', 'memo']

admin.site.register(Donation, DonationAdmin)
