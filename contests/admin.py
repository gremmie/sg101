"""
Admin definitions for the contest application.

"""
from django.contrib import admin
from django.conf import settings

from contests.models import Contest


class ContestAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_public', 'creation_date', 'end_date',
            'contestant_count', 'winner']
    list_editable = ['is_public']
    date_hierarchy = 'creation_date'
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ['title']}
    raw_id_fields = ['winner', 'contestants']
    actions = ['pick_winner']

    class Media:
        js = (['js/contests/contests_admin.js'] +
                settings.GPP_THIRD_PARTY_JS['tiny_mce'])

    def contestant_count(self, obj):
        return obj.contestants.count()
    contestant_count.short_description = '# Entries'

    def pick_winner(self, request, qs):
        """
        Picks a winner on the contests selected by the admin. Note that for
        safety reasons, we only update those contests that don't have winners
        already.

        """
        count = 0
        for contest in qs:
            if not contest.winner:
                contest.pick_winner()
                contest.save()
                count += 1

        self.message_user(request, "%d of %d winners picked" % (count,
            qs.count()))

    pick_winner.short_description = "Pick winners for selected contests"



admin.site.register(Contest, ContestAdmin)
