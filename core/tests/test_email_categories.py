"""
Tests for the email category vocabulary.

"""
import json
import unittest

from core.email_categories import (EmailCategory, SUBJECT_REDACTED,
                                   SUBJECT_SAFE, subject_for_log)


class EmailCategoryTestCase(unittest.TestCase):
    def test_members_serialize_as_their_value(self):
        # Celery serializes task arguments to JSON. A plain Enum raises
        # TypeError here, which would break every deferred send.
        self.assertEqual(json.dumps({'category': EmailCategory.REGISTRATION}),
                         '{"category": "registration"}')

    def test_members_format_as_their_value(self):
        # A plain Enum formats as 'EmailCategory.REGISTRATION', which would
        # make the log line unreadable and uncountable.
        self.assertEqual('%s' % EmailCategory.REGISTRATION, 'registration')

    def test_member_equals_the_bare_string(self):
        # Tasks queued before this deploy carry a bare string, and in-flight
        # ones have to keep working.
        self.assertEqual(EmailCategory.REGISTRATION, 'registration')


class SubjectClassificationTestCase(unittest.TestCase):
    def test_every_category_is_classified(self):
        # The point of the enum: adding a category without deciding whether
        # its subject is safe to log fails here rather than leaking quietly.
        self.assertEqual(set(EmailCategory), SUBJECT_SAFE | SUBJECT_REDACTED)

    def test_no_category_is_both(self):
        self.assertFalse(SUBJECT_SAFE & SUBJECT_REDACTED)

    def test_subject_kept_for_a_safe_category(self):
        self.assertEqual(
            subject_for_log(EmailCategory.REGISTRATION, 'Confirm your account'),
            'Confirm your account')

    def test_subject_redacted_for_member_authored_categories(self):
        for category in (EmailCategory.PM_NOTIFICATION,
                         EmailCategory.CONTACT_FORM):
            with self.subTest(category=category):
                self.assertEqual(subject_for_log(category, 'what a member typed'),
                                 '<redacted>')

    def test_subject_redacted_for_an_unrecognized_category(self):
        # An allowlist, so anything unclassified errs toward hiding.
        self.assertEqual(subject_for_log('some_future_category', 'a subject'),
                         '<redacted>')

    def test_uncategorized_is_redacted(self):
        # An in-flight task from before the deploy has unknown provenance.
        self.assertEqual(subject_for_log(EmailCategory.UNCATEGORIZED, 'a subject'),
                         '<redacted>')
