from django.contrib import admin
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin as FlatPageAdminOld
from django.conf import settings

class FlatPageAdmin(FlatPageAdminOld):
    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']

# We have to unregister it, and then reregister
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
