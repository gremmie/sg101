"""
Signal handlers & signals for the bio application.

"""
from django.db.models.signals import post_save
from django.contrib.auth.models import User

import bio.badges
from bio.models import UserProfile

from donations.models import Donation
from weblinks.models import Link
from downloads.models import Download
from news.models import Story
from potd.models import Photo


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


def on_donation_save(sender, **kwargs):
    """
    This function is called after a Donation is saved.
    If the Donation was newly created and not anonymous,
    award the user a contributor pin.

    """
    if kwargs['created']:
        donation = kwargs['instance']
        if not donation.is_anonymous and donation.user:
            bio.badges.award_badge(bio.badges.CONTRIBUTOR_PIN, donation.user)


def on_link_save(sender, **kwargs):
    """
    This function is called after a Link is saved. If the Link was newly
    created, award the user a link pin.

    """
    if kwargs['created']:
        link = kwargs['instance']
        bio.badges.award_badge(bio.badges.LINK_PIN, link.user)


def on_download_save(sender, **kwargs):
    """
    This function is called after a Download is saved. If the Download was
    newly created, award the user a download pin.

    """
    if kwargs['created']:
        download = kwargs['instance']
        bio.badges.award_badge(bio.badges.DOWNLOAD_PIN, download.user)


def on_story_save(sender, **kwargs):
    """
    This function is called after a Story is saved. If the Story was
    newly created, award the user a news pin.

    """
    if kwargs['created']:
        story = kwargs['instance']
        bio.badges.award_badge(bio.badges.NEWS_PIN, story.submitter)


def on_photo_save(sender, **kwargs):
    """
    This function is called after a Photo is saved. If the Photo was
    newly created, award the user a POTD pin.

    """
    if kwargs['created']:
        photo = kwargs['instance']
        bio.badges.award_badge(bio.badges.POTD_PIN, photo.user)


post_save.connect(on_user_save, sender=User, dispatch_uid='bio.receivers')
post_save.connect(on_donation_save, sender=Donation, dispatch_uid='bio.receivers')
post_save.connect(on_link_save, sender=Link, dispatch_uid='bio.receivers')
post_save.connect(on_download_save, sender=Download, dispatch_uid='bio.receivers')
post_save.connect(on_story_save, sender=Story, dispatch_uid='bio.receivers')
post_save.connect(on_photo_save, sender=Photo, dispatch_uid='bio.receivers')
