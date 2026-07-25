"""
Form tests for the bio application.

"""
from django.contrib.auth.models import User
from django.test import TestCase

from bio.forms import EditUserProfileForm
from bio.forms import SearchUsersForm


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


class SearchUsersFormTestCase(TestCase):

    def setUp(self):
        User.objects.create_user('BrianNeal', 'brianneal@example.com', 'pw')

    def test_exact_username(self):
        form = SearchUsersForm({'username': 'BrianNeal'})
        self.assertTrue(form.is_valid())

    def test_username_differing_case(self):
        # Members type a name into this box; matching it case-sensitively
        # would turn a found member into "does not exist".
        form = SearchUsersForm({'username': 'brianneal'})
        self.assertTrue(form.is_valid())

    def test_unknown_username(self):
        form = SearchUsersForm({'username': 'nobody'})
        self.assertFalse(form.is_valid())
