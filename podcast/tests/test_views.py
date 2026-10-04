"""
Tests for the podcast application's views.

"""
import datetime
import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.test import TestCase, override_settings
from django.urls import reverse

from podcast.models import Channel, Item


class FilesOnlyStaticFilesStorage(StaticFilesStorage):
    """Refuses a static name that is not a file, as production's storage does.

    Production serves static files through ManifestStaticFilesStorage, whose
    manifest lists only the files collectstatic copied. Asked for anything else
    -- a directory, say -- it raises ValueError, and the page is a 500. The test
    settings use the plain storage, which only prefixes STATIC_URL and so
    accepts any name at all. This raises where production does, without a
    collectstatic run.
    """
    def url(self, name):
        path = finders.find(name)
        if not path or not os.path.isfile(path):
            raise ValueError(
                "Missing staticfiles manifest entry for '{}'".format(name))
        return super().url(name)


@override_settings(STORAGES={
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'podcast.tests.test_views.FilesOnlyStaticFilesStorage',
    },
})
class DetailTestCase(TestCase):

    def setUp(self):
        channel = Channel.objects.create(
                title='Surfguitar101.com\'s Podcast',
                link='https://surfguitar101.com/podcast/',
                language='en',
                copyright='(C) Copyright Brian Neal',
                subtitle='Surf music',
                author='SurfGuitar101.com Podcasters',
                description='Surf music and interviews.',
                owner_name='Brian Neal',
                owner_email='podcast@surfguitar101.com',
                image='podcast/podcast_logo.jpg',
                category='Music',
                explicit='no',
                keywords='surf')
        self.item = Item.objects.create(
                channel=channel,
                title='Episode 13',
                author='SurfGuitar101.com Podcasters',
                subtitle='Thirteen',
                summary='An episode.',
                enclosure_url='https://example.com/podcast/sg101-13.mp3',
                enclosure_length=1000,
                enclosure_type='audio/mpeg',
                guid='sg101-13',
                pubdate=datetime.datetime(2010, 7, 23,
                                          tzinfo=datetime.timezone.utc),
                duration='01:00:00',
                keywords='surf',
                explicit='no')

    def test_detail_renders(self):
        response = self.client.get(
                reverse('podcast-detail', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Episode 13')

    def test_no_flash_fallback(self):
        # The player is HTML5 only: no Flash solution, and so no swfPath for
        # jPlayer to load a .swf from.
        response = self.client.get(
                reverse('podcast-detail', args=[self.item.pk]))
        self.assertContains(response, 'solution: "html"')
        self.assertNotContains(response, 'swfPath')
        self.assertNotContains(response, 'Flash')
