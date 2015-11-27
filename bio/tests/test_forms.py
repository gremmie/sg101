"""
Form tests for the bio application.

"""
from django.test import TestCase

from bio.forms import EditUserProfileForm


class EditUserProfileFormTestCase(TestCase):

    def test_valid_timezone(self):

        post_data = {'time_zone': 'US/Central'}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_invalid_timezone(self):

        post_data = {'time_zone': u'Am\xe9rica/Argentina_/_Buenos_Aires'}
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())

    def test_blank_timezone(self):

        form = EditUserProfileForm({})
        self.assertTrue(form.is_valid())

    def test_profile_text_good(self):
        post_data = {'profile_text': "This is my profile, no images."}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_profile_text_bad_image(self):
        post_data = {
            'profile_text': "I'm cool. ![image](http://example.com/test.jpg)",
        }
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())

    def test_signature_good(self):
        post_data = {'signature': "This is my signature, no images."}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_signature_bad_image(self):
        post_data = {
            'signature': "I'm cool. ![image](http://example.com/test.jpg)",
        }
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())
