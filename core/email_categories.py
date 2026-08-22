"""The vocabulary of email categories recorded in email.log.

Every message the site sends through core.functions.send_mail carries one of
these, so the log can be counted by purpose without parsing subject lines --
which would break the first time a subject is reworded.

StrEnum rather than Enum: Celery serializes task arguments to JSON, where a
plain Enum raises TypeError, and '%s' on one yields 'EmailCategory.REGISTRATION'
rather than the value. Being a str subclass also means a category compares equal
to its bare string, so tasks serialized before a deploy keep working.

Django's error mail does not appear here. AdminEmailHandler sends outside this
wrapper, so crash reports are not logged; see the email handler in the settings
for what that omits.
"""
from enum import StrEnum


class EmailCategory(StrEnum):
    """Why the site sent a message."""

    REGISTRATION = 'registration'
    PASSWORD_RESET = 'password_reset'
    FORGOT_USERNAME = 'forgot_username'
    TOPIC_NOTIFICATION = 'topic_notification'
    PM_NOTIFICATION = 'pm_notification'
    CONTACT_FORM = 'contact_form'
    # Flags, spam trips, pending downloads and links -- the email_admins and
    # email_managers family.
    ADMIN_NOTIFICATION = 'admin_notification'
    # A task queued before the category existed, or a caller that forgot one.
    UNCATEGORIZED = 'uncategorized'


# Adding a category? Put it in exactly one of the two sets below.
# test_every_category_is_classified fails until you do, which is the point of
# using an enum here -- a category cannot reach the log unclassified.
#
# Subjects are logged only for categories known to carry no member-authored
# text. This is an allowlist rather than a list of things to hide, so a
# category nobody has classified is redacted instead of exposed.
SUBJECT_SAFE = frozenset({
    EmailCategory.REGISTRATION,
    EmailCategory.PASSWORD_RESET,
    EmailCategory.FORGOT_USERNAME,
    EmailCategory.TOPIC_NOTIFICATION,
    EmailCategory.ADMIN_NOTIFICATION,
})

# A private message's subject line and a contact form's are written by members,
# which is the same reason the body is never logged. UNCATEGORIZED is here
# because its provenance is unknown by definition.
#
# Nothing reads this set at runtime -- subject_for_log() asks SUBJECT_SAFE and
# redacts anything else, so an unrecognized category is hidden without help from
# here. It is not dead code: it is the declaration that lets the tests prove
# every category was classified deliberately. Keep it in step with the enum.
SUBJECT_REDACTED = frozenset({
    EmailCategory.PM_NOTIFICATION,
    EmailCategory.CONTACT_FORM,
    EmailCategory.UNCATEGORIZED,
})

REDACTED = '<redacted>'


def subject_for_log(category, subject):
    """Return the subject to log, or a placeholder if it is member-authored."""
    return subject if category in SUBJECT_SAFE else REDACTED
