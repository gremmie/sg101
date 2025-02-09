"""
Tests for accounts' stats module.

"""
from django.contrib.auth.models import User
from django.test import TestCase
from mock import call, patch, Mock

import accounts.stats


class AccountStatsTestCase(TestCase):
    fixtures = ['accounts.json']

    @patch('accounts.tasks.user_stats_task')
    def test_on_user_save_created(self, task_mock):
        user = User.objects.get(pk=1)
        kwargs = {
            'created': True,
            'instance': user,
        }
        mock_sender = Mock()
        accounts.stats.on_user_save(mock_sender, **kwargs)
        self.assertEqual(task_mock.mock_calls, [
            call.delay(1),
        ])

    @patch('accounts.tasks.user_stats_task')
    def test_on_user_save_updated(self, task_mock):
        user = User.objects.get(pk=1)
        kwargs = {
            'created': False,
            'instance': user,
        }
        mock_sender = Mock()
        accounts.stats.on_user_save(mock_sender, **kwargs)
        self.assertEqual(task_mock.mock_calls, [])

    @patch('accounts.stats.get_redis_connection')
    def test_update_user_status(self, connection_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.incr.return_value = 1
        accounts.stats.update_user_stats(1)
        self.assertEqual(redis_mock.mock_calls, [
            call.incr('accounts:user_count'),
            call.set('accounts:user_count', 1),
            call.pipeline(),
            call.pipeline().lpush('accounts:new_users', u'Gremmie'),
            call.pipeline().ltrim('accounts:new_users', 0, 9),
            call.pipeline().execute(),
        ])

    @patch('accounts.stats.get_redis_connection')
    def test_get_user_count(self, connection_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.get.return_value = 42
        result = accounts.stats.get_user_count()
        self.assertEqual(result, 42)
        self.assertEqual(redis_mock.mock_calls, [
            call.get('accounts:user_count'),
        ])

    @patch('accounts.stats.get_redis_connection')
    def test_get_new_users(self, connection_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.lrange.return_value = ['Gremmie', 'pjmoto']
        result = accounts.stats.get_new_users()
        self.assertEqual(result, ['Gremmie', 'pjmoto'])
        self.assertEqual(redis_mock.mock_calls, [
            call.lrange('accounts:new_users', 0, -1),
        ])

    @patch('accounts.stats.get_redis_connection')
    def test_get_new_users(self, connection_mock):
        redis_mock = Mock()
        connection_mock.return_value = redis_mock
        redis_mock.get.return_value = 42
        redis_mock.lrange.return_value = ['Gremmie', 'pjmoto']

        result = accounts.stats.get_user_stats()

        self.assertEqual(result, (42, ['Gremmie', 'pjmoto']))
        self.assertEqual(redis_mock.mock_calls, [
            call.get('accounts:user_count'),
            call.lrange('accounts:new_users', 0, -1),
        ])
