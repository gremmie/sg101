"""
Admin definitions for the contest application.

"""
from django.contrib import admin
from django.conf import settings

from contests.models import Contest
from core.admin import PlainTextFieldsMixin


class ContestAdmin(PlainTextFieldsMixin, admin.ModelAdmin):
    plain_text_fields = ['meta_description']
    list_display = ['title', 'is_public', 'creation_date', 'end_date',
            'contestant_count', 'winner_count']
    list_editable = ['is_public']
    date_hierarchy = 'creation_date'
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ['title']}
    raw_id_fields = ['contestants', 'winners']
    actions = ['pick_winners']

    class Media:
        js = settings.GPP_THIRD_PARTY_JS['tiny_mce']

    def contestant_count(self, obj):
        return obj.contestants.count()
    contestant_count.short_description = '# Entries'

    def winner_count(self, obj):
        return obj.winners.count()
    winner_count.short_description = '# Winners'

    def pick_winners(self, request, qs):
        """
        Picks a winner on the contests selected by the admin. Note that for
        safety reasons, we only update those contests that don't have winners
        already.

        """
        count = 0
        for contest in qs:
            if not contest.win_date:
                contest.pick_winners()
                contest.save()
                count += 1

        self.message_user(request, "%d of %d winners picked" % (count,
            qs.count()))

    pick_winners.short_description = "Pick winners for selected contests"



admin.site.register(Contest, ContestAdmin)
