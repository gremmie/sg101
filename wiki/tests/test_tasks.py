"""
Tests for the wiki application tasks.

"""
from django.test import TestCase
from mock import call, patch, ANY, Mock

from wiki.tasks import expire_cookies


class ExpireCookiesTaskTestCase(TestCase):
    @patch('wiki.tasks.get_redis_connection')
    def test_expire_cookies_task(self, connection_mock):
        redis = Mock()
        redis.zcard.return_value = 42
        redis.zremrangebyscore.return_value = 4
        connection_mock.return_value = redis

        task = expire_cookies.s().apply()

        self.assertEqual(redis.mock_calls, [
            call.zcard('wiki_cookie_keys'),
            call.zremrangebyscore('wiki_cookie_keys', 0.0, ANY),
        ])
