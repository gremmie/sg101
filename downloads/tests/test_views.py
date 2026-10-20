"""
Characterization tests for the downloads views.

The downloads section (backing tracks, samples, etc.) is login-gated. These
cover the browse/detail journeys, the AJAX rate + request (hit-count) endpoints,
and the add form. Uploading a real file is validated against AllowedExtension
records, so the add view is exercised at the GET level only.
"""
import json

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from downloads.models import Category, Download, VoteRecord


def make_download(user, category, title='A Track', public=True):
    return Download.objects.create(
        title=title, category=category, description='a description',
        file='downloads/track.mp3', user=user, ip_address='127.0.0.1',
        is_public=public)


class DownloadBrowseTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Backing Tracks',
                                                slug='backing-tracks')
        self.download = make_download(self.user, self.category, title='Pipeline')
        self.client.login(username='member', password='pw')

    def test_index_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('downloads-index'))
        self.assertEqual(response.status_code, 302)

    def test_index_renders(self):
        response = self.client.get(reverse('downloads-index'))
        self.assertEqual(response.status_code, 200)

    def test_category_lists_downloads(self):
        response = self.client.get(reverse('downloads-category',
            kwargs={'slug': self.category.slug, 'sort': 'title'}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pipeline', response.content.decode())

    def test_category_accepts_each_sort(self):
        for sort in ('title', 'date', 'rating', 'hits'):
            response = self.client.get(reverse('downloads-category',
                kwargs={'slug': self.category.slug, 'sort': sort}))
            self.assertEqual(response.status_code, 200, msg='sort=%s' % sort)

    def test_unknown_category_is_404(self):
        response = self.client.get(reverse('downloads-category',
            kwargs={'slug': 'nope', 'sort': 'title'}))
        self.assertEqual(response.status_code, 404)

    def test_new_popular_rating_render(self):
        for name in ('downloads-new', 'downloads-popular', 'downloads-rating'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, msg=name)

    def test_details_renders_for_public(self):
        response = self.client.get(reverse('downloads-details', args=[self.download.id]))
        self.assertEqual(response.status_code, 200)

    def test_details_has_one_of_each_post_box_modal(self):
        # The comment form brings its own modals; a second copy repeats their ids.
        response = self.client.get(reverse('downloads-details', args=[self.download.id]))
        for modal in ('hot-link-modal', 'upload-modal', 'preview-modal', 'help-modal',
                      'smiley-modal'):
            with self.subTest(modal=modal):
                self.assertContains(response, 'id="{}"'.format(modal), count=1)

    def test_details_404_for_non_public(self):
        hidden = make_download(self.user, self.category, title='Hidden', public=False)
        response = self.client.get(reverse('downloads-details', args=[hidden.id]))
        self.assertEqual(response.status_code, 404)

    def test_add_form_renders(self):
        response = self.client.get(reverse('downloads-add'))
        self.assertEqual(response.status_code, 200)

    def test_thanks_renders(self):
        response = self.client.get(reverse('downloads-add_thanks'))
        self.assertEqual(response.status_code, 200)


class DownloadRateTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Tracks', slug='tracks')
        self.download = make_download(self.user, self.category)
        self.url = reverse('downloads-rate')

    def test_rate_requires_login(self):
        response = self.client.post(self.url, {'id': self.download.id, 'rating': '3'})
        self.assertEqual(response.status_code, 403)

    def test_rate_missing_params_is_bad_request(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url, {'id': self.download.id})
        self.assertEqual(response.status_code, 400)

    def test_rate_invalid_rating_is_bad_request(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url, {'id': self.download.id, 'rating': 'x'})
        self.assertEqual(response.status_code, 400)

    def test_rate_records_vote(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url, {'id': self.download.id, 'rating': '4'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(VoteRecord.objects.filter(
            download=self.download, user=self.user).exists())

    def test_duplicate_vote_returns_minus_one(self):
        self.client.login(username='member', password='pw')
        self.client.post(self.url, {'id': self.download.id, 'rating': '4'})
        response = self.client.post(self.url, {'id': self.download.id, 'rating': '2'})
        self.assertEqual(response.content.decode(), '-1')
        self.assertEqual(VoteRecord.objects.filter(download=self.download).count(), 1)


class DownloadRequestTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('member', '', 'pw')
        self.category = Category.objects.create(title='Tracks', slug='tracks')
        self.download = make_download(self.user, self.category)
        self.url = reverse('downloads-request_download')

    def test_request_requires_login(self):
        response = self.client.post(self.url, {'id': self.download.id})
        self.assertEqual(response.status_code, 403)

    def test_request_increments_hits_and_returns_url(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url, {'id': self.download.id})
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(int(payload['id']), self.download.id)
        self.assertEqual(Download.objects.get(pk=self.download.id).hits, 1)

    def test_request_unknown_download_is_404(self):
        self.client.login(username='member', password='pw')
        response = self.client.post(self.url, {'id': 999999})
        self.assertEqual(response.status_code, 404)
