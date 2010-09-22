"""
Signal handlers for the membermap application.
We want to detect changes to the UserProfile model. If that person is on
the map, re-save her MapEntry so that any avatar changes get picked up.
"""
from django.db.models.signals import post_save
from bio.models import UserProfile
from membermap.models import MapEntry


def on_profile_save(sender, **kwargs):
    if 'instance' in kwargs:
        profile = kwargs['instance']
        try:
            map_entry = MapEntry.objects.get(user=profile.user)
        except MapEntry.DoesNotExist:
            # Not on the map, no harm, no foul
            return
        if map_entry is not None:
            map_entry.save()


post_save.connect(on_profile_save,
        sender=UserProfile,
        dispatch_uid='membermap.signals')
