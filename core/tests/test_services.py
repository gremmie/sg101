import unittest

from unittest.mock import call, patch

from core.services import get_redis_connection


class ServicesTestCase(unittest.TestCase):
    @patch('core.services.redis')
    def test_get_redis_connect_via_tcp(self, mock_redis):
        result = get_redis_connection(host='localhost', port=6379, db=14)

        self.assertEqual(mock_redis.mock_calls, [
            call.StrictRedis(host='localhost', port=6379, db=14, decode_responses=True),
        ])
        self.assertEqual(result, mock_redis.StrictRedis.return_value)
