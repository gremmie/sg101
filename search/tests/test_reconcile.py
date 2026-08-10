"""
Tests for the index reconcile sweep.

Every one of these seeds a condition the incremental path is supposed to make
impossible and then asserts the sweep notices. That is the only way to have any
confidence in a monitoring job: a sweep that reports clean is indistinguishable
from a sweep that cannot see, right up until the day it matters.

The drift is created behind the signals -- direct queryset writes, not model
saves -- because a save would queue a reindex and repair the very thing the
test is about.

"""
import datetime

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

from bio.models import UserProfile
from downloads.models import Download
from forums.models import Post
from forums.models import Topic
from search.models import SearchDocument
from search.reconcile import reconcile
from search.tests.test_documents import DocumentTestCase
from ygroup.models import Post as YgroupPost


def rows_for(model):
    """The index rows for one source model."""
    return SearchDocument.objects.filter(
            content_type=ContentType.objects.get_for_model(model))


class ReconcileTestCase(DocumentTestCase):
    """
    Runs against the one-of-each-type fixture, indexed by the bulk command, so
    a sweep here covers all eight document types.

    """
    def setUp(self):
        super().setUp()
        call_command('reindex_search', verbosity=0)

    def report_for(self, model):
        """The sweep's findings for one document type."""
        key = '%s.%s' % (model._meta.app_label, model._meta.model_name)
        return next(report for report in reconcile().types
                    if report.key == key)

    # -- a clean index ---------------------------------------------------

    def test_a_clean_index_reports_clean(self):
        report = reconcile()

        self.assertTrue(report.clean)
        self.assertEqual(report.private, 0)
        for type_report in report.types:
            with self.subTest(key=type_report.key):
                self.assertTrue(type_report.clean)
                self.assertEqual(type_report.missing.count, 0)
                self.assertEqual(type_report.orphaned.count, 0)
                self.assertEqual(type_report.stale.count, 0)

    def test_every_document_type_is_swept(self):
        # A type missing from the report is a type nothing is watching, which
        # would look exactly like a type that never drifts.
        keys = set(report.key for report in reconcile().types)

        self.assertEqual(keys, set('%s.%s' % (model._meta.app_label,
                                              model._meta.model_name)
                                   for model in self.objects))

    # -- missing ---------------------------------------------------------

    def test_a_deleted_index_row_is_reported_missing(self):
        rows_for(Post).delete()

        report = self.report_for(Post)

        self.assertEqual(report.missing.count, 1)
        self.assertEqual(report.missing.sample, [self.post.pk])
        self.assertFalse(report.clean)
        # The row is gone, not wrong: nothing is orphaned or stale.
        self.assertEqual(report.orphaned.count, 0)
        self.assertEqual(report.stale.count, 0)

    def test_missing_is_counted_per_type(self):
        rows_for(Post).delete()
        rows_for(Topic).delete()

        report = reconcile()

        self.assertEqual(self.report_for(Post).missing.count, 1)
        self.assertEqual(self.report_for(Topic).missing.count, 1)
        self.assertFalse(report.clean)

    # -- orphaned --------------------------------------------------------

    def test_a_row_whose_source_is_gone_is_reported_orphaned(self):
        # Deleted through the queryset, so post_delete never fires and the row
        # it would have removed stays behind.
        pk = self.ygroup_post.pk
        YgroupPost.objects.filter(pk=pk).delete()

        report = self.report_for(YgroupPost)

        self.assertEqual(report.orphaned.count, 1)
        self.assertEqual(report.orphaned.sample, [pk])
        # Gone from the table entirely, which is what deleted separates out.
        self.assertEqual(report.deleted.count, 1)

    def test_a_row_whose_source_is_no_longer_indexable_is_orphaned(self):
        # The download still exists; withdrawing approval takes it out of the
        # indexable set, and its row should have gone with it.
        Download.objects.filter(pk=self.download.pk).update(is_public=False)

        report = self.report_for(Download)

        self.assertEqual(report.orphaned.count, 1)
        # Still in the table, so it is an orphan but not a deletion. This is
        # the shape of the defect the backfill found: rows for unapproved
        # downloads produce search hits that 404 on click.
        self.assertEqual(report.deleted.count, 0)

    def test_a_deactivated_member_leaves_an_orphaned_profile_row(self):
        self.user.is_active = False
        self.user.save()

        report = self.report_for(UserProfile)

        self.assertEqual(report.orphaned.count, 1)
        self.assertEqual(report.deleted.count, 0)

    # -- stale -----------------------------------------------------------

    def test_a_source_edited_after_indexing_is_reported_stale(self):
        # update() rather than save(), so no reindex is queued -- the state a
        # worker outage leaves behind.
        later = timezone.now() + datetime.timedelta(hours=1)
        Post.objects.filter(pk=self.post.pk).update(
                body='Rewritten while the worker was down.', update_date=later)

        report = self.report_for(Post)

        self.assertEqual(report.stale.count, 1)
        self.assertEqual(report.stale.sample, [self.post.pk])
        self.assertFalse(report.clean)
        # It is indexed and indexable; only its contents are behind.
        self.assertEqual(report.missing.count, 0)
        self.assertEqual(report.orphaned.count, 0)

    def test_a_source_edited_before_indexing_is_not_stale(self):
        earlier = timezone.now() - datetime.timedelta(hours=1)
        Post.objects.filter(pk=self.post.pk).update(update_date=earlier)

        self.assertEqual(self.report_for(Post).stale.count, 0)

    def test_the_yahoo_archive_has_no_staleness_to_report(self):
        # ygroup.Post carries no update_date -- it is a frozen import with no
        # edit path -- so the sweep must skip the check rather than fail on it.
        report = self.report_for(YgroupPost)

        self.assertEqual(report.stale.count, 0)
        self.assertTrue(report.clean)

    # -- private categories ----------------------------------------------

    def test_private_category_rows_are_reported_separately(self):
        # Assigning a group makes the category members-only. Done through the
        # m2m manager, whose signal the test's transaction never commits, so
        # the rows the handler would have removed stay behind -- which is the
        # state being tested for.
        category = self.topic.forum.category
        category.groups.add(Group.objects.create(name='Kahunas'))

        report = reconcile()
        topics = self.report_for(Topic)
        posts = self.report_for(Post)

        self.assertEqual(topics.private.count, 1)
        self.assertEqual(posts.private.count, 1)
        self.assertEqual(report.private, 2)
        self.assertFalse(report.clean)

    def test_private_rows_are_also_orphans_but_counted_apart(self):
        # A private row is orphaned too -- the document stops yielding it -- so
        # the private count has to be its own number rather than a slice of a
        # total that would otherwise hide it among unapproved downloads.
        self.topic.forum.category.groups.add(Group.objects.create(name='Kahunas'))

        report = self.report_for(Topic)

        self.assertEqual(report.orphaned.count, 1)
        self.assertEqual(report.deleted.count, 0)
        self.assertEqual(report.private.count, 1)

    def test_a_public_category_reports_no_private_rows(self):
        self.assertEqual(reconcile().private, 0)

    def test_types_without_categories_report_no_private_rows(self):
        # Only forum content has a category to be private; the rest must report
        # zero rather than raising on a category_path that is None.
        for model in (Download, UserProfile, YgroupPost):
            with self.subTest(model=model.__name__):
                self.assertEqual(self.report_for(model).private.count, 0)

    # -- the report-only guarantee ---------------------------------------

    def test_the_sweep_writes_nothing(self):
        rows_for(Post).delete()
        Download.objects.filter(pk=self.download.pk).update(is_public=False)
        YgroupPost.objects.filter(pk=self.ygroup_post.pk).delete()
        self.topic.forum.category.groups.add(Group.objects.create(name='Kahunas'))
        later = timezone.now() + datetime.timedelta(hours=1)
        Topic.objects.filter(pk=self.topic.pk).update(update_date=later)

        before = set(SearchDocument.objects.values_list('pk', 'indexed_at'))
        report = reconcile()
        after = set(SearchDocument.objects.values_list('pk', 'indexed_at'))

        # Drift of every kind, and all of it still there afterwards.
        self.assertFalse(report.clean)
        self.assertEqual(before, after)

    def test_the_sweep_issues_no_write_statements(self):
        # The assertion above compares state, which a write that happened to
        # restore it would survive. This one watches the statements themselves.
        rows_for(Post).delete()

        with CaptureQueriesContext(connection) as queries:
            reconcile()

        for query in queries:
            sql = query['sql'].lstrip().upper()
            self.assertFalse(sql.startswith(('INSERT', 'UPDATE', 'DELETE')),
                             'the sweep wrote: %s' % query['sql'][:120])

    # -- cost ------------------------------------------------------------

    def test_a_clean_sweep_costs_one_query_per_check(self):
        # A clean check fetches no rows: the count answers it. Eight types at
        # three checks each, less the staleness ygroup.Post does not have, plus
        # the two private-category checks and the content types they look up.
        with CaptureQueriesContext(connection) as queries:
            reconcile()

        selects = [q for q in queries if 'search_searchdocument' in q['sql']]
        self.assertEqual(len(selects), 8 * 3 + 7 + 2)

    # -- the management command ------------------------------------------

    def test_the_command_reports_a_clean_index(self):
        call_command('reconcile_search', verbosity=0)

    def test_the_command_exits_non_zero_on_drift(self):
        rows_for(Post).delete()

        with self.assertRaises(SystemExit) as caught:
            call_command('reconcile_search', verbosity=0)

        self.assertEqual(caught.exception.code, 1)
