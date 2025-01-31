"""
Tests for the account application tasks.

"""
from django.test import TestCase
from mock import call, patch, Mock

import accounts.stats
from accounts.tasks import user_stats_task


class UserStatsTaskTestCase(TestCase):
    fixtures = ['accounts.json']

    @patch('accounts.stats.get_redis_connection')
    def test_user_stats_task(self, connection_mock):
        redis_mock = Mock()
        redis_mock.incr.return_value = 1
        connection_mock.return_value = redis_mock

        task = user_stats_task.s(1).apply()

        self.assertEquals(redis_mock.mock_calls, [
            call.incr('accounts:user_count'),
            call.set('accounts:user_count', 1),
            call.pipeline(),
            call.pipeline().lpush('accounts:new_users', u'Gremmie'),
            call.pipeline().ltrim('accounts:new_users', 0, 9),
            call.pipeline().execute(),
        ])
