"""Tests for the rule that decides which account keeps a shared address.

Some addresses are held by more than one account, and the migration that
installs the unique index has to clear the extras first. The rule is a pure
function over (pk, email, last_login) rows rather than a queryset walk, for two
reasons: the index it clears the way for forbids the very rows a database-level
test would need to set up, and most of the tie-breaks below do not occur in the
real data at all, so nothing else can exercise them.

Only the first case has ever been seen in production. The rest exist for a group
that turns up in some later snapshot with a shape this one did not have.

"""
import datetime
from importlib import import_module

from django.test import SimpleTestCase

plan_blanking = import_module(
    'accounts.migrations.0008_auth_user_email_lower_unique').plan_blanking


def when(year, month, day):
    return datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)


class PlanBlankingTests(SimpleTestCase):

    def test_the_later_login_keeps_the_address(self):
        rows = [
            (1, 'shared@example.com', when(2020, 1, 1)),
            (2, 'shared@example.com', when(2024, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), {1})

    def test_case_variants_are_one_group(self):
        # Folded by 0003 before this runs, but the rule must not depend on that
        # having happened -- it is what makes the LOWER(email) index buildable.
        rows = [
            (1, 'Shared@Example.com', when(2024, 1, 1)),
            (2, 'shared@example.com', when(2020, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), {2})

    def test_a_null_last_login_loses(self):
        rows = [
            (1, 'shared@example.com', None),
            (2, 'shared@example.com', when(2011, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), {1})

    def test_equal_logins_are_settled_by_lowest_pk(self):
        rows = [
            (7, 'shared@example.com', when(2024, 1, 1)),
            (3, 'shared@example.com', when(2024, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), {7})

    def test_all_null_logins_are_settled_by_lowest_pk(self):
        rows = [
            (7, 'shared@example.com', None),
            (3, 'shared@example.com', None),
        ]

        self.assertEqual(plan_blanking(rows), {7})

    def test_a_group_of_three_keeps_one(self):
        rows = [
            (1, 'shared@example.com', when(2020, 1, 1)),
            (2, 'shared@example.com', when(2024, 1, 1)),
            (3, 'shared@example.com', when(2022, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), {1, 3})

    def test_distinct_addresses_are_left_alone(self):
        rows = [
            (1, 'one@example.com', when(2020, 1, 1)),
            (2, 'two@example.com', when(2024, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), set())

    def test_blank_addresses_are_not_a_group(self):
        # Several accounts hold '', and the index exempts them. If they
        # grouped, this rule would blank accounts that are already blank and
        # claim it had done work.
        rows = [
            (1, '', when(2026, 1, 1)),
            (2, '', None),
            (3, '', when(2020, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), set())

    def test_running_against_already_resolved_rows_plans_nothing(self):
        rows = [
            (1, '', when(2020, 1, 1)),
            (2, 'shared@example.com', when(2024, 1, 1)),
        ]

        self.assertEqual(plan_blanking(rows), set())
