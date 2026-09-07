"""
Tests for the rename_tag and merge_tags management commands.

Renaming a tag used to be a form in the admin that half-worked: the join table
followed and each story's own copy of the string did not, so the next save of
any affected story quietly put the old tag back. Merging was not possible at
all. These commands are new capability rather than restored capability, and the
tests are written against that -- particularly that a rename survives a later
save, which is the property the old form lacked.
"""
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from news.models import Category, PendingStory, Story
from news.retag import retag, tag_in_use


class RetagTestCase(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.category = Category.objects.get(pk=1)

    def story(self, title, tags, **kwargs):
        return Story.objects.create(title=title, submitter=self.author,
                                    category=self.category,
                                    short_markup='body', tags=tags, **kwargs)

    def pending(self, title, tags):
        return PendingStory.objects.create(title=title, submitter=self.author,
                                           category=self.category,
                                           short_markup='body', tags=tags)

    def run_command(self, name, *args, **opts):
        out, err = StringIO(), StringIO()
        call_command(name, *args, stdout=out, stderr=err, **opts)
        return out.getvalue()


class RenameTagTests(RetagTestCase):

    def test_it_renames_across_every_story_carrying_the_tag(self):
        a = self.story('One', ['video', 'surf'])
        b = self.story('Two', ['video'])
        c = self.story('Three', ['tremolo'])

        self.run_command('rename_tag', 'video', 'clips')

        for story in (a, b, c):
            story.refresh_from_db()
        self.assertEqual(a.tags, ['clips', 'surf'])
        self.assertEqual(b.tags, ['clips'])
        self.assertEqual(c.tags, ['tremolo'])

    def test_a_rename_survives_a_later_save(self):
        """The defect in the admin form this replaces: it renamed the shared row
        and left each story holding the old string, so the next save of any of
        them reverted that story alone."""
        story = self.story('One', ['video'])

        self.run_command('rename_tag', 'video', 'clips')

        story.refresh_from_db()
        story.save()
        story.refresh_from_db()
        self.assertEqual(story.tags, ['clips'])

    def test_pending_stories_are_renamed_too(self):
        pending = self.pending('Submitted', ['video'])

        self.run_command('rename_tag', 'video', 'clips')

        pending.refresh_from_db()
        self.assertEqual(pending.tags, ['clips'])

    def test_the_report_names_a_count_for_each_model(self):
        self.story('One', ['video'])
        self.pending('Submitted', ['video'])

        output = self.run_command('rename_tag', 'video', 'clips')

        self.assertIn('news story', output)
        self.assertIn('pending story', output)

    def test_arguments_are_lowercased(self):
        story = self.story('One', ['video'])

        self.run_command('rename_tag', 'Video', 'Clips')

        story.refresh_from_db()
        self.assertEqual(story.tags, ['clips'])

    def test_renaming_onto_a_tag_in_use_is_refused(self):
        story = self.story('One', ['video'])
        self.story('Two', ['clips'])

        with self.assertRaises(CommandError) as caught:
            self.run_command('rename_tag', 'video', 'clips')

        self.assertIn('merge_tags', str(caught.exception))
        story.refresh_from_db()
        self.assertEqual(story.tags, ['video'])

    def test_an_unknown_tag_is_refused(self):
        with self.assertRaises(CommandError) as caught:
            self.run_command('rename_tag', 'nosuchtag', 'clips')

        self.assertIn('nosuchtag', str(caught.exception))

    def test_dry_run_writes_nothing(self):
        story = self.story('One', ['video'])
        before = story.update_date

        output = self.run_command('rename_tag', 'video', 'clips', dry_run=True)

        story.refresh_from_db()
        self.assertEqual(story.tags, ['video'])
        self.assertEqual(story.update_date, before)
        self.assertIn('1', output)


class MergeTagsTests(RetagTestCase):

    def test_it_folds_the_source_into_the_destination(self):
        story = self.story('One', ['show'])
        self.story('Two', ['release'])

        self.run_command('merge_tags', 'show', 'release')

        story.refresh_from_db()
        self.assertEqual(story.tags, ['release'])

    def test_a_story_carrying_both_ends_up_with_one(self):
        """The whole reason merge is its own command."""
        story = self.story('One', ['surf', 'show', 'release', 'reverb'])

        self.run_command('merge_tags', 'show', 'release')

        story.refresh_from_db()
        self.assertEqual(story.tags, ['surf', 'release', 'reverb'])

    def test_tag_order_is_preserved(self):
        """Tags render in array order, so a merge must not resort them."""
        story = self.story('One', ['zither', 'show', 'anchor'])
        self.story('Two', ['release'])

        self.run_command('merge_tags', 'show', 'release')

        story.refresh_from_db()
        self.assertEqual(story.tags, ['zither', 'release', 'anchor'])

    def test_merging_into_an_unused_tag_is_refused(self):
        """rename_tag refuses when the target exists; merge_tags refuses when it
        does not. Between them there is exactly one right command."""
        self.story('One', ['show'])

        with self.assertRaises(CommandError) as caught:
            self.run_command('merge_tags', 'show', 'nosuchtag')

        self.assertIn('rename_tag', str(caught.exception))


class SideEffectTests(RetagTestCase):
    """The reasons this does not go through Story.save()."""

    def test_the_rendered_body_is_not_rewritten(self):
        """save() re-renders short_text from short_markup. Measured against
        production, that changes the visible text of 14 stories -- literal
        asterisks from Markdown's emphasis conformance fix. A tag rename must
        not touch the body."""
        story = self.story('One', ['video'])
        Story.objects.filter(pk=story.pk).update(
            short_text='<p>hand written HTML that markup would not produce</p>')

        self.run_command('rename_tag', 'video', 'clips')

        story.refresh_from_db()
        self.assertEqual(story.short_text,
                         '<p>hand written HTML that markup would not produce</p>')

    def test_update_date_moves(self):
        """reconcile_search finds a stale index row by comparing update_date
        against indexed_at. Leaving it alone would make this change invisible to
        the one sweep that exists to catch it."""
        story = self.story('One', ['video'])
        Story.objects.filter(pk=story.pk).update(
            update_date=timezone.now() - timezone.timedelta(days=30))
        before = Story.objects.get(pk=story.pk).update_date

        self.run_command('rename_tag', 'video', 'clips')

        story.refresh_from_db()
        self.assertGreater(story.update_date, before)

    def test_a_reindex_is_queued_for_each_story(self):
        """bulk_update fires no post_save, so nothing queues these by itself."""
        self.story('One', ['video'])
        self.story('Two', ['video'])

        with mock.patch('search.tasks.reindex_document.delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_command('rename_tag', 'video', 'clips')

        self.assertEqual(delay.call_count, 2)

    def test_no_reindex_is_queued_for_pending_stories(self):
        """PendingStory has no search document; a submission is not public."""
        self.pending('Submitted', ['video'])

        with mock.patch('search.tasks.reindex_document.delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                self.run_command('rename_tag', 'video', 'clips')

        self.assertEqual(delay.call_count, 0)

    def test_a_failure_part_way_through_changes_nothing(self):
        self.story('One', ['video'])
        self.pending('Submitted', ['video'])

        with mock.patch.object(PendingStory.objects, 'bulk_update',
                               side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                self.run_command('rename_tag', 'video', 'clips')

        self.assertTrue(tag_in_use('video'))
        self.assertFalse(tag_in_use('clips'))


class RetagHelperTests(RetagTestCase):

    def test_tag_in_use_looks_at_both_models(self):
        self.assertFalse(tag_in_use('video'))
        self.pending('Submitted', ['video'])
        self.assertTrue(tag_in_use('video'))

    def test_retag_reports_a_count_per_model(self):
        self.story('One', ['video'])
        self.story('Two', ['video'])
        self.pending('Submitted', ['video'])

        counts = retag('video', 'clips')

        self.assertEqual(counts, {Story: 2, PendingStory: 1})
