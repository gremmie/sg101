"""
Unit tests for the bio flag utility.

"""
from django.test import TestCase


class FlagsTestCase(TestCase):
    def test_flag_loading(self):
        import bio.flags

        # Just make sure we have data and didn't blow up.
        self.assertNotEqual(len(bio.flags.FLAG_DATA), 0)
        self.assertNotEqual(len(bio.flags.FLAG_CHOICES), 0)
        self.assertEqual(len(bio.flags.FLAG_DATA), len(bio.flags.FLAG_CHOICES))

