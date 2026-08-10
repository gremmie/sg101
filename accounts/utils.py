import logging

from django.contrib.auth.models import User
from django.utils import timezone


logger = logging.getLogger('auth')


def create_new_user(pending_user, ip=None, admin_activation=False):
    """
    This function contains the code to create a new user from a
    pending user. The pending user is deleted and the new user
    is saved. A log message is produced. If admin_activation is false,
    then ip should be the user's IP they confirmed from, if available.

    """
    new_user = User()

    new_user.username = pending_user.username
    new_user.first_name = ''
    new_user.last_name = ''
    new_user.email = pending_user.email
    new_user.password = pending_user.password     # already been hashed
    new_user.is_staff = False
    new_user.is_active = True
    new_user.is_superuser = False
    new_user.last_login = timezone.now()
    new_user.date_joined = new_user.last_login

    new_user.save()
    pending_user.delete()

    if admin_activation:
        msg = 'Accounts registration confirmed by ADMIN for %s' % new_user.username
    else:
        msg = 'Accounts registration confirmed by USER for %s from %s' % (
                new_user.username, ip)

    logger.info(msg)
