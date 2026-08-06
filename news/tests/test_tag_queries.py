"""
Tests for the vendored tagging app's tag-usage queries, exercised through the
one model on the site that carries a TagField.

These queries are the only place in the project that reaches into Django's SQL
compiler and builds a statement by hand, so they are the part of the fork most
exposed to Django's internals moving underneath it -- twice now, in ways nothing
else here would notice: an unfiltered queryset's WHERE clause stopped compiling
to empty SQL and started raising instead, and `Query.add_filter()` went from
taking one (lookup, value) tuple to taking two arguments.

"""
from django.contrib.auth.models import User
from django.test import TestCase

from tagging.models import Tag

from news.models import Category, Story


class TagUsageQueryTests(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.category = Category.objects.get(pk=1)
        self.published = Story.objects.create(
            title='Published Story', submitter=self.author,
            category=self.category, short_markup='body')
        self.other = Story.objects.create(
            title='Other Story', submitter=self.author,
            category=self.category, short_markup='body')
        Tag.objects.update_tags(self.published, 'reverb')
        Tag.objects.update_tags(self.other, 'tremolo')

    def test_usage_over_every_row_counts_all_tags(self):
        """No filters means no extra criteria -- every tag in use is returned."""
        tags = Tag.objects.usage_for_model(Story, counts=True)

        self.assertEqual({tag.name: tag.count for tag in tags},
                         {'reverb': 1, 'tremolo': 1})

    def test_usage_can_be_narrowed_by_a_filter_on_the_model(self):
        """A filter reaches the hand-built SQL as an extra WHERE criterion."""
        tags = Tag.objects.usage_for_model(
            Story, counts=True, filters={'title': 'Published Story'})

        self.assertEqual({tag.name: tag.count for tag in tags}, {'reverb': 1})

    def test_a_tag_cloud_over_every_row_gets_font_sizes(self):
        """cloud_for_model() is what the news tag index renders."""
        cloud = Tag.objects.cloud_for_model(Story)

        self.assertEqual(sorted(tag.name for tag in cloud),
                         ['reverb', 'tremolo'])
        for tag in cloud:
            self.assertTrue(hasattr(tag, 'font_size'))
