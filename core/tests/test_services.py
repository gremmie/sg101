import unittest

from mock import call, patch

from core.services import get_redis_connection


class ServicesTestCase(unittest.TestCase):
    @patch('core.services.redis')
    def test_get_redis_connect_via_unix_socket(self, mock_redis):
        result = get_redis_connection(unix_socket_path='/tmp/redis.sock', db=14)

        self.assertEqual(mock_redis.mock_calls, [
            call.StrictRedis(unix_socket_path='/tmp/redis.sock', db=14),
        ])
        self.assertEqual(result, mock_redis.StrictRedis.return_value)

    @patch('core.services.redis')
    def test_get_redis_connect_via_tcp(self, mock_redis):
        result = get_redis_connection(host='localhost', port=6379, db=14,
                                      unix_socket_path=None)

        self.assertEqual(mock_redis.mock_calls, [
            call.StrictRedis(host='localhost', port=6379, db=14),
        ])
        self.assertEqual(result, mock_redis.StrictRedis.return_value)
