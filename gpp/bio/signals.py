"""
Signal handler(s) for the bio application.
"""
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from bio.models import UserProfile

def on_user_save(sender, **kwargs):
    """
    This signal handler ensures that every User has a corresonding
    UserProfile. It is called after User instance is saved. It creates
    a UserProfile for the User if the created argument is True.
    """
    created = kwargs['created']
    if created:
        user = kwargs['instance']
        profile = UserProfile()
        profile.user = user
        profile.save()


post_save.connect(on_user_save, sender=User)
