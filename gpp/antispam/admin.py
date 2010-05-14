"""Admin definitions for the antispam application."""

from django.contrib import admin

from antispam.models import SpamPhrase


class SpamPhraseAdmin(admin.ModelAdmin):
    search_fields = ('phrase', )


admin.site.register(SpamPhrase, SpamPhraseAdmin)
