"""
Tests for the banners application's template tags.

"""
from django.test import TestCase

from mock import call, patch, Mock

from banners.templatetags.banner_tags import banner_url


class BannersTemplateTagsTestCase(TestCase):
    def setUp(self):
        self.url = 'http://example.com/some/campaign'
        self.slug = 'slug'

    @patch('banners.templatetags.banner_tags.get_redis_connection')
    def test_banner_url_cache_hit(self, connection_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.lpop.return_value = self.url

        self.assertEqual(banner_url(self.slug), self.url)

        self.assertEqual(redis_mock.mock_calls, [
            call.lpop('banners:url:{}'.format(self.slug)),
        ])

    @patch('banners.templatetags.banner_tags.Banner')
    @patch('banners.templatetags.banner_tags.get_redis_connection')
    def test_banner_url_cache_miss(self, connection_mock, banner_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.lpop.return_value = None

        qs = [Mock(), Mock()]
        qs[0].image.configure_mock(url='url0')
        qs[1].image.configure_mock(url='url1')

        banner_mock.objects.filter.return_value = qs

        self.assertEqual(banner_url(self.slug), 'url0')

        redis_key = 'banners:url:{}'.format(self.slug)
        self.assertEqual(redis_mock.mock_calls, [
            call.lpop(redis_key),
            call.rpush(redis_key, 'url1'),
        ])
        self.assertEqual(banner_mock.objects.filter.mock_calls, [
            call(campaign__slug=self.slug),
        ])
