"""Tests for the search document registry."""

import datetime
import re

from django.contrib.auth.models import User
from django.test import TestCase

from elsewhere.models import WebsiteProfile

from bio.models import UserProfile
from downloads.models import Category as DownloadCategory
from downloads.models import Download
from forums.models import Category as ForumCategory
from forums.models import Forum
from forums.models import Post
from forums.models import Topic
from news.models import Category as NewsCategory
from news.models import Story
from podcast.models import Channel
from podcast.models import Item
from search.documents import all_documents
from search.models import SearchDocument
from weblinks.models import Category as LinkCategory
from weblinks.models import Link
from ygroup.models import Post as YgroupPost


LEXEME_RE = re.compile(r"'((?:[^']|'')*)':(\d+[A-D]?(?:,\d+[A-D]?)*)")


def lexeme_weights(vector):
    """
    Parses a tsvector's text form into {lexeme: set of weight labels}.

    A lexeme carries one label per position, so a word appearing in both the
    title and the body comes back as {'A', 'B'}. Positions PostgreSQL leaves
    unlabelled are weight D.

    """
    weights = {}
    for lexeme, positions in LEXEME_RE.findall(vector):
        labels = set(re.findall(r'[A-D]', positions)) or {'D'}
        weights[lexeme.replace("''", "'")] = labels
    return weights


class DocumentTestCase(TestCase):
    """
    Base case building one instance of each of the eight searchable types.

    The test vocabulary is chosen so the 'english' stemmer leaves it alone:
    jaguar, reverb, kahuna, sabertooth, jeff and tank all survive stemming
    intact, which keeps the weight assertions readable.

    """
    def setUp(self):
        self.user = User.objects.create_user('kahuna', 'jeff@example.com', 'pw')
        self.user.first_name = 'Jeff'
        self.user.last_name = 'Sabertooth'
        self.user.save()

        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.location = 'Long Beach'
        self.profile.occupation = 'Promoter'
        self.profile.interests = 'Reverb tanks'
        self.profile.profile_text = 'Running surf shows since 1995.'
        self.profile.signature = 'Hang loose'
        self.profile.save()
        WebsiteProfile.objects.create(user=self.user,
                                      name='kahunasurf.example.com',
                                      url='http://kahunasurf.example.com/')

        forum = Forum.objects.create(
                category=ForumCategory.objects.create(name='Main', slug='main'),
                name='Surf Music', slug='surf-music')
        self.topic = Topic.objects.create(forum=forum, user=self.user,
                                          name='Jaguar setup')
        self.post = Post.objects.create(topic=self.topic, user=self.user,
                                        body='I dialed in the reverb tank.')

        self.story = Story.objects.create(
                title='Convention roundup',
                submitter=self.user,
                category=NewsCategory.objects.create(title='Shows', slug='shows'),
                short_markup='Bands played all afternoon.',
                long_markup='A jaguar through a blackface amp.',
                tags='surfabilly')

        self.link = Link.objects.create(
                category=LinkCategory.objects.create(title='Bands', slug='bands'),
                title='The Ventures', url='http://ventures.example.com/',
                description='Official band site.', user=self.user)

        self.download = Download.objects.create(
                category=DownloadCategory.objects.create(title='Tabs', slug='tabs'),
                title='Pipeline tab', description='Tablature for Pipeline.',
                file='downloads/pipeline.txt', user=self.user,
                ip_address='127.0.0.1')

        channel = Channel.objects.create(
                title='SG101 Podcast', link='http://example.com/', language='en',
                copyright='SG101', subtitle='Surf music', author='Brian',
                description='A surf music podcast', owner_name='Brian',
                owner_email='brian@example.com', image='podcast/cover.jpg',
                category='Music', explicit='no', keywords='surf')
        self.item = Item.objects.create(
                channel=channel, title='Episode 42', author='Brian Neal',
                subtitle='Instrumental gems', summary='A show about the reverb tank.',
                enclosure_url='http://example.com/42.mp3', enclosure_length=1000,
                enclosure_type='audio/mpeg', guid='42', duration='30:00',
                keywords='surfabilly', explicit='no')

        self.ygroup_post = YgroupPost.objects.create(
                title='Old thread', poster='wahini',
                msg='<p>Anyone have a spare <i>tank</i>?</p>',
                creation_date=datetime.datetime(2005, 3, 1, 12, 0))

        self.objects = {
            Topic: self.topic,
            Post: self.post,
            Story: self.story,
            UserProfile: self.profile,
            Link: self.link,
            Download: self.download,
            Item: self.item,
            YgroupPost: self.ygroup_post,
        }

    def weights_for(self, obj):
        """Indexes obj and returns its stored vector as {lexeme: weights}."""
        doc = SearchDocument.objects.index_object(obj)
        vector = SearchDocument.objects.filter(pk=doc.pk).values_list(
                'search_vector', flat=True)[0]
        return lexeme_weights(vector)


class RegistryTestCase(DocumentTestCase):

    def test_registry_covers_every_searchable_type(self):
        registered = set(document.model for document in all_documents())
        self.assertEqual(registered, set(self.objects))

    def test_every_document_type_builds(self):
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                doc = SearchDocument.objects.index_object(obj)
                self.assertTrue(doc.title)
                self.assertTrue(doc.url)
                self.assertIsNotNone(doc.date)
                vector = SearchDocument.objects.filter(pk=doc.pk).values_list(
                        'search_vector', flat=True)[0]
                self.assertTrue(vector)

    def test_every_queryset_finds_its_own_objects(self):
        for document in all_documents():
            with self.subTest(model=document.model.__name__):
                obj = self.objects[document.model]
                self.assertIn(obj, document.get_queryset())

    def test_documents_point_at_their_source_object(self):
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                doc = SearchDocument.objects.index_object(obj)
                self.assertEqual(doc.content_object, obj)


class WeightTestCase(DocumentTestCase):

    def test_post_weights_title_body_and_author(self):
        weights = self.weights_for(self.post)
        self.assertIn('A', weights['jaguar'])       # the topic name
        self.assertIn('B', weights['tank'])         # the post body
        self.assertIn('C', weights['kahuna'])       # the author's username

    def test_topic_weights_name_and_author(self):
        weights = self.weights_for(self.topic)
        self.assertIn('A', weights['jaguar'])
        self.assertIn('C', weights['kahuna'])

    def test_profile_weights_username_and_full_name_as_the_title(self):
        weights = self.weights_for(self.profile)
        self.assertIn('A', weights['kahuna'])
        self.assertIn('A', weights['sabertooth'])
        self.assertIn('A', weights['jeff'])
        self.assertIn('B', weights['promot'])       # occupation
        self.assertIn('B', weights['beach'])        # location
        self.assertIn('B', weights['reverb'])       # interests
        self.assertIn('B', weights['surf'])         # profile text

    def test_profile_indexes_linked_site_names_and_urls(self):
        weights = self.weights_for(self.profile)
        self.assertIn('kahunasurf.example.com', weights)

    def test_full_names_are_absent_from_content_documents(self):
        content = [self.topic, self.post, self.story, self.link, self.download]
        for obj in content:
            with self.subTest(model=type(obj).__name__):
                weights = self.weights_for(obj)
                self.assertNotIn('sabertooth', weights)
                self.assertNotIn('jeff', weights)
                self.assertIn('kahuna', weights)


class DocumentContentTestCase(DocumentTestCase):

    def test_story_indexes_its_tags(self):
        weights = self.weights_for(self.story)
        self.assertIn('B', weights['surfabilli'])

    def test_link_indexes_its_url(self):
        weights = self.weights_for(self.link)
        self.assertIn('B', weights['ventures.example.com'])

    def test_podcast_item_indexes_subtitle_summary_and_keywords(self):
        weights = self.weights_for(self.item)
        self.assertIn('B', weights['instrument'])   # subtitle
        self.assertIn('B', weights['tank'])         # summary
        self.assertIn('B', weights['surfabilli'])   # keywords

    def test_ygroup_post_indexes_its_poster(self):
        weights = self.weights_for(self.ygroup_post)
        self.assertIn('C', weights['wahini'])

    def test_topic_has_no_body_text(self):
        doc = SearchDocument.objects.index_object(self.topic)
        self.assertEqual(doc.summary, '')

    def test_html_is_stripped_from_body_text(self):
        doc = SearchDocument.objects.index_object(self.ygroup_post)
        self.assertNotIn('<', doc.summary)
        weights = self.weights_for(self.ygroup_post)
        self.assertIn('tank', weights)
        self.assertNotIn('p', weights)

    def test_dates_come_from_each_documents_own_date_field(self):
        expected = {
            self.topic: self.topic.creation_date,
            self.post: self.post.creation_date,
            self.story: self.story.date_submitted,
            self.profile: self.user.date_joined,
            self.link: self.link.date_added,
            self.download: self.download.date_added,
            self.item: self.item.pubdate,
            self.ygroup_post: self.ygroup_post.creation_date,
        }
        for obj, date in expected.items():
            with self.subTest(model=type(obj).__name__):
                doc = SearchDocument.objects.index_object(obj)
                self.assertEqual(doc.date, date)

    def test_urls_come_from_get_absolute_url(self):
        for model, obj in self.objects.items():
            with self.subTest(model=model.__name__):
                doc = SearchDocument.objects.index_object(obj)
                self.assertEqual(doc.url, obj.get_absolute_url())
