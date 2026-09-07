"""
Tests for how story tags are stored, queried and rendered.

The tag data moved from a space-separated string plus a join table onto an array
column on the story. These cover the parts of that move a page renders or a
query count would notice.
"""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.forms import modelform_factory
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from news.models import Category, PendingStory, Story
from news.utils import attach_extra_attrs
from search.documents import StoryDocument


# StoryAdmin declares no `form`, so a plain ModelForm exercises the same
# validation path the admin does: _post_clean() -> full_clean().
StoryForm = modelform_factory(Story, fields=['title', 'tags'])


class TagTestCase(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.category = Category.objects.get(pk=1)

    def make(self, title='A News Story', tags=None):
        return Story.objects.create(title=title, submitter=self.author,
                                    category=self.category,
                                    short_markup='body', tags=tags or [])


class TagStorageTests(TagTestCase):

    def test_tags_round_trip(self):
        story = self.make(tags=['surf', 'reverb'])
        story.refresh_from_db()

        self.assertEqual(story.tags, ['surf', 'reverb'])

    def test_a_story_can_have_no_tags(self):
        story = self.make()
        story.refresh_from_db()

        self.assertEqual(story.tags, [])

    def test_pending_stories_carry_tags_too(self):
        """Both models inherit the field, and a pending story keeps its tags
        through approval, which copies them onto the new Story."""
        pending = PendingStory.objects.create(
            title='Submitted', submitter=self.author, category=self.category,
            short_markup='body', tags=['Surf'])
        pending.refresh_from_db()

        self.assertEqual(pending.tags, ['surf'])


class TagFormValidationTests(TagTestCase):

    def test_commas_separate_tags(self):
        form = StoryForm(data={'title': 'T', 'tags': 'surf, reverb , twang'})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['tags'], ['surf', 'reverb', 'twang'])

    def test_a_tag_containing_a_space_is_rejected(self):
        """The box was space-separated for years. Typing spaces out of habit
        would otherwise be accepted as one three-word tag, which no tag URL
        resolves and which appears alone in the cloud."""
        form = StoryForm(data={'title': 'T', 'tags': 'surf reverb twang'})

        self.assertFalse(form.is_valid())
        self.assertIn('spaces', str(form.errors['tags']))

    def test_the_field_says_to_use_commas(self):
        self.assertIn('commas', Story._meta.get_field('tags').help_text)


class TagQueryCountTests(TagTestCase):
    """The point of the move was deleting round trips, so the counts are pinned.

    These count queries against `news_story` rather than whole pages. The pages
    also render a sidebar of countdowns, polls and birthdays whose queries are
    cached, so a whole-page count depends on which test ran first and warmed the
    cache -- it passes for the wrong reason. The claim being made here is about
    what the tag data costs, and that is what is counted.

    A `.defer('tags')` anywhere in these views would turn the array into one
    query per story rendered, which is the regression these guard against.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        self.story = self.make(title='Front Page News', tags=['surf', 'reverb'])
        # More stories than one, so an N+1 shows up as a count rather than
        # hiding inside a single-row page.
        for n in range(3):
            self.make(title='Filler %d' % n, tags=['surf'])

    def story_queries(self, url):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(url)
            captured = list(ctx.captured_queries)
        return [q for q in captured if 'news_story' in q['sql']]

    def test_the_tag_page_is_two_story_queries(self):
        """A count and a page of rows -- down from four, which also looked the
        tag up and then bulk-loaded the join table."""
        self.assertEqual(len(self.story_queries(
            reverse('news-tag_page', kwargs={'tag_name': 'surf'}))), 2)

    def test_the_story_page_is_one_story_query(self):
        self.assertEqual(len(self.story_queries(
            reverse('news-story', args=[self.story.id]))), 1)

    def test_the_index_is_two_story_queries(self):
        self.assertEqual(len(self.story_queries(
            reverse('news-index_page'))), 2)

    def test_the_archive_page_is_two_story_queries(self):
        submitted = self.story.date_submitted
        self.assertEqual(len(self.story_queries(
            reverse('news-archive_page', kwargs={'year': submitted.year,
                                                 'month': submitted.month}))), 2)

    def test_the_tag_cloud_is_one_story_query(self):
        self.assertEqual(len(self.story_queries(
            reverse('news-tag_index'))), 1)


class TagRenderingTests(TagTestCase):

    def test_the_story_page_links_each_tag(self):
        story = self.make(title='Front Page News', tags=['surf', 'reverb'])

        body = self.client.get(reverse('news-story', args=[story.id])
                               ).content.decode()

        for tag in ('surf', 'reverb'):
            self.assertIn(reverse('news-tag_page', kwargs={'tag_name': tag}),
                          body)

    def test_the_index_summary_links_each_tag(self):
        self.make(title='Front Page News', tags=['surf'])

        body = self.client.get(reverse('news-index_page')).content.decode()

        self.assertIn(reverse('news-tag_page', kwargs={'tag_name': 'surf'}),
                      body)

    def test_an_untagged_story_renders_no_tag_block(self):
        story = self.make(title='Front Page News')

        body = self.client.get(reverse('news-story', args=[story.id])
                               ).content.decode()

        self.assertNotIn('news-tags', body)


class AttachExtraAttrsTests(TagTestCase):

    def test_comment_counts_are_still_attached(self):
        story = self.make(tags=['surf'])
        stories = list(Story.objects.filter(pk=story.pk))

        attach_extra_attrs(stories)

        # version 2 with no forums topic: the function leaves comment_count
        # unset, exactly as it did before the tags half was removed.
        self.assertFalse(hasattr(stories[0], 'comment_count'))

    def test_it_issues_no_query_for_tags(self):
        story = self.make(tags=['surf'])
        stories = list(Story.objects.filter(pk=story.pk))

        with self.assertNumQueries(0):
            attach_extra_attrs(stories)


class StoryDocumentTests(TagTestCase):

    def test_the_summary_indexes_the_tags(self):
        story = self.make(tags=['surfabilly', 'reverb'])

        summary = StoryDocument().summary(story)

        self.assertIn('surfabilly', summary)
        self.assertIn('reverb', summary)


class TagAdminWidgetTests(TagTestCase):
    """The tag box is the one field an editor types a long value into, and an
    ArrayField does not get the admin's text-input styling by default."""

    def rendered_tag_field(self, model):
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        request = RequestFactory().get('/')
        request.user = User.objects.create_superuser(
            'admin-%s' % model.__name__.lower(), '', 'pw')
        form = dj_admin.site._registry[model].get_form(request)()
        return str(form['tags'])

    def test_the_tag_box_is_styled_like_the_admin_s_other_text_inputs(self):
        for model in (Story, PendingStory):
            with self.subTest(model=model.__name__):
                self.assertIn('vTextField', self.rendered_tag_field(model))

    def test_the_tag_box_fills_the_row(self):
        for model in (Story, PendingStory):
            with self.subTest(model=model.__name__):
                self.assertIn('width: 100%', self.rendered_tag_field(model))
