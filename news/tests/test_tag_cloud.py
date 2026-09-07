"""
Tests for the news tag cloud's font-size calculation and its query.

The font-size maths came from django-tagging, which this app no longer depends
on. The expected sizes below were captured from that implementation before it
was removed, so these tests pin the rendering the archive has always had rather
than whatever the new code happens to produce.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from news.models import Category, PendingStory, Story
from news.tag_cloud import LINEAR, LOGARITHMIC, CloudTag, calculate_cloud, tag_cloud


def sizes(tags):
    return [(t.name, t.count, t.font_size) for t in tags]


class CalculateCloudTests(TestCase):
    """Pure maths -- no database."""

    def test_a_spread_of_counts_gets_a_spread_of_sizes(self):
        tags = [CloudTag('a', 1), CloudTag('b', 2), CloudTag('c', 5),
                CloudTag('d', 20), CloudTag('e', 100)]

        self.assertEqual(sizes(calculate_cloud(tags)),
                         [('a', 1, 1), ('b', 2, 1), ('c', 5, 2),
                          ('d', 20, 3), ('e', 100, 4)])

    def test_the_linear_distribution_differs_from_the_logarithmic_one(self):
        """Not used by the site, but it is half the function and it is cheap to
        keep honest: linear leaves everything below the top at size 1."""
        pairs = [('a', 1), ('b', 2), ('c', 5), ('d', 20), ('e', 100)]

        linear = calculate_cloud([CloudTag(n, c) for n, c in pairs],
                                 distribution=LINEAR)

        self.assertEqual(sizes(linear),
                         [('a', 1, 1), ('b', 2, 1), ('c', 5, 1),
                          ('d', 20, 1), ('e', 100, 4)])

    def test_equal_counts_all_get_the_smallest_size(self):
        """Zero delta between the thresholds -- the case that would divide by
        zero if the thresholds were computed as a ratio."""
        tags = [CloudTag('a', 5), CloudTag('b', 5), CloudTag('c', 5)]

        self.assertEqual(sizes(calculate_cloud(tags)),
                         [('a', 5, 1), ('b', 5, 1), ('c', 5, 1)])

    def test_a_maximum_count_of_one_does_not_take_a_logarithm_of_one(self):
        """log(1) is 0, so the logarithmic branch would divide by zero."""
        tags = [CloudTag('a', 1), CloudTag('b', 1)]

        self.assertEqual(sizes(calculate_cloud(tags)), [('a', 1, 1), ('b', 1, 1)])

    def test_a_single_tag_is_not_a_special_case(self):
        self.assertEqual(sizes(calculate_cloud([CloudTag('a', 7)])), [('a', 7, 1)])

    def test_no_tags_returns_no_tags(self):
        """min() and max() over an empty sequence raise; the guard is the point."""
        self.assertEqual(calculate_cloud([]), [])


class TagCloudQueryTests(TestCase):
    fixtures = ['news_categories.json']

    def setUp(self):
        self.author = User.objects.create_user('author', '', 'pw')
        self.category = Category.objects.get(pk=1)

    def make(self, title, tags):
        return Story.objects.create(title=title, submitter=self.author,
                                    category=self.category, short_markup='body',
                                    tags=tags)

    def test_counts_come_from_every_story_carrying_the_tag(self):
        self.make('One', ['surf', 'reverb'])
        self.make('Two', ['surf'])
        self.make('Three', [])

        self.assertEqual([(t.name, t.count) for t in tag_cloud(Story)],
                         [('reverb', 1), ('surf', 2)])

    def test_the_cloud_is_ordered_by_tag_name(self):
        self.make('One', ['zither', 'anchor', 'moog'])

        self.assertEqual([t.name for t in tag_cloud(Story)],
                         ['anchor', 'moog', 'zither'])

    def test_pending_stories_are_not_in_the_cloud(self):
        """The cloud has always been Story-only. A pending submission's tags are
        not public until an admin approves it."""
        self.make('Published', ['surf'])
        PendingStory.objects.create(title='Submitted', submitter=self.author,
                                    category=self.category, short_markup='body',
                                    tags=['unapproved'])

        self.assertEqual([t.name for t in tag_cloud(Story)], ['surf'])

    def test_the_cloud_is_one_query(self):
        self.make('One', ['surf', 'reverb'])

        with self.assertNumQueries(1):
            list(tag_cloud(Story))
