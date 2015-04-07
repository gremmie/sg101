"""
Signals for the bio application
"""
import django.dispatch

#
# This signal is sent whenever a profile has had its textual content updated.
# The provided arguments to the receiver function are:
#   - sender - the profile model instance

profile_content_update = django.dispatch.Signal(providing_args=[])


def notify_profile_content_update(profile):
    """
    Convenience function to send the profile content update signal.

    """
    profile_content_update.send_robust(profile)
