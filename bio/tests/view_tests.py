"""
View tests for the bio application.

"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse, NoReverseMatch


class MemberSearchTest(TestCase):

    USERNAME = u'John'

    def setUp(self):
        user = User.objects.create_user(self.USERNAME, '', 'password')
        user.save()

        self.username = 'test_user'
        self.pw = 'password'
        self.user = User.objects.create_user(self.username, '', self.pw)
        self.user.save()
        self.assertTrue(self.client.login(username=self.username,
            password=self.pw))

    def tearDown(self):
        self.client.logout()

    def testValidName(self):
        """
        Test a valid username.
        """

        response = self.client.post(reverse('bio-member_search'),
                            {'username': self.USERNAME},
                            follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(response.redirect_chain[0][0],
                    'http://testserver' + reverse('bio-view_profile',
                        kwargs={'username': self.USERNAME}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

    def testInvalidName(self):
        """
        Test a invalid username.
        """

        response = self.client.post(reverse('bio-member_search'),
                            {'username': self.USERNAME + '!'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That username does not exist.")

    def testTrailingSpace(self):
        """
        Test a username with a trailing space.
        """

        try:
            response = self.client.post(reverse('bio-member_search'),
                                {'username': self.USERNAME + ' '},
                                follow=True)
        except NoReverseMatch:
            self.fail('bit by a MySQL bug?')

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(response.redirect_chain[0][0],
                    'http://testserver' + reverse('bio-view_profile',
                        kwargs={'username': self.USERNAME}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)
