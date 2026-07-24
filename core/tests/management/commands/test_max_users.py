"""Test for the max_user management command."""
from io import StringIO
import unittest

from django.core.management import call_command
from mock import patch


class MaxUsersTestCase(unittest.TestCase):
    @patch('core.management.commands.max_users.max_users')
    def test_max_users(self, mock_max_users):
        out = StringIO()
        call_command('max_users', stdout=out)
        self.assertEqual(out.getvalue(), '')
        out.close()
        mock_max_users.assert_called_once()
