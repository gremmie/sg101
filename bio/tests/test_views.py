"""
View tests for the bio application.

"""
from io import BytesIO
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core import mail

from PIL import Image

from bio.models import UserProfile, UserProfileFlag


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

        response = self.client.get(reverse('bio-member_search'),
                            {'username': self.USERNAME},
                            follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse(
                        'bio-view_profile',
                        kwargs={'username': self.USERNAME}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)

    def testInvalidName(self):
        """
        Test a invalid username.
        """

        response = self.client.get(reverse('bio-member_search'),
                            {'username': self.USERNAME + '!'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That username does not exist.")

    def testTrailingSpace(self):
        """
        Test a username with a trailing space.
        """

        try:
            response = self.client.get(reverse('bio-member_search'),
                                {'username': self.USERNAME + ' '},
                                follow=True)
        except NoReverseMatch:
            self.fail('bit by a MySQL bug?')

        self.assertEqual(len(response.redirect_chain), 1)
        if response.redirect_chain:
            self.assertEqual(
                    response.redirect_chain[0][0],
                    reverse(
                        'bio-view_profile',
                        kwargs={'username': self.USERNAME}))
            self.assertEqual(response.redirect_chain[0][1], 302)

        self.assertEqual(response.status_code, 200)


class AnonMemberListTest(TestCase):

    def _test_login_required(self, list_by):

        member_list_url = reverse('bio-member_list', kwargs={'type': list_by})
        response = self.client.get(member_list_url, follow=True)
        login_url = reverse('accounts-login') + '?next=' + member_list_url
        self.assertRedirects(response, login_url)

    def test_login_required(self):
        self._test_login_required('user')
        self._test_login_required('date')


class MemberListTest(TestCase):

    def setUp(self):
        u1 = User.objects.create_user('paul', '', 'pw')
        u1.save()
        u2 = User.objects.create_user('eddie', '', 'pw')
        u2.save()

        self.user = u1
        self.client.login(username=u1.username, password='pw')

    def _test_get(self, list_by, page=None, code=200):

        member_list_url = reverse('bio-member_list', kwargs={'type': list_by})
        if page is not None:
            member_list_url += '?page=%d' % page
        response = self.client.get(member_list_url)
        self.assertEqual(response.status_code, code)

    def test_get(self):
        self._test_get('user')
        self._test_get('date')
        self._test_get('user', page=1)
        self._test_get('date', page=1)

    def test_invalid_page(self):
        self._test_get('user', page=99, code=404)
        self._test_get('date', page=99, code=404)


class ProfileTest(TestCase):

    def setUp(self):
        u1 = User.objects.create_user('paul', '', 'pw')
        u1.save()
        u2 = User.objects.create_user('eddie', '', 'pw')
        u2.save()

    def tearDown(self):
        profile = UserProfile.objects.get(user__username='paul')
        if profile.avatar:
            os.remove(profile.avatar.path)

    def test_anon_my_profile(self):
        my_url = reverse('bio-me')
        response = self.client.get(my_url)
        login_url = reverse('accounts-login') + '?next=' + my_url
        self.assertRedirects(response, login_url)

    def test_authenticated_my_profile(self):
        self.client.login(username='paul', password='pw')
        response = self.client.get(reverse('bio-me'))
        self.assertEqual(response.status_code, 200)

    def test_anon_other_profile(self):
        url = reverse('bio-view_profile', kwargs={'username': 'eddie'})
        response = self.client.get(url)
        login_url = reverse('accounts-login') + '?next=' + url
        self.assertRedirects(response, login_url)

    def test_authenticated_other_profile(self):
        self.client.login(username='paul', password='pw')
        url = reverse('bio-view_profile', kwargs={'username': 'eddie'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_profile_as_me_redirects(self):
        self.client.login(username='paul', password='pw')
        url = reverse('bio-view_profile', kwargs={'username': 'paul'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('bio-me'))

    def test_edit_anon(self):
        url = reverse('bio-edit_profile')
        response = self.client.get(url)
        login_url = reverse('accounts-login') + '?next=' + url
        self.assertRedirects(response, login_url)

    def test_edit_profile(self):
        self.client.login(username='paul', password='pw')
        url = reverse('bio-edit_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Save some new data. We don't exhaustively test every field.
        response = self.client.post(url, {
            'first_name': 'Paul',
            'last_name': 'Johnson',
            'email': 'pjmoto@example.com',
            'occupation': 'Surf Guitar Pioneer',
            'profile_text': 'Wrote Mr. Moto at age 15.',
            'submit_button': 'Save',
        })
        self.assertRedirects(response, reverse('bio-me'))

        u = User.objects.get(username='paul')
        self.assertEqual(u.first_name, 'Paul')
        self.assertEqual(u.last_name, 'Johnson')
        self.assertEqual(u.email, 'pjmoto@example.com')
        profile = u.profile
        self.assertEqual(profile.occupation, 'Surf Guitar Pioneer')
        self.assertEqual(profile.profile_text, 'Wrote Mr. Moto at age 15.')

    def test_avatar_change(self):
        self.client.login(username='paul', password='pw')
        url = reverse('bio-change_avatar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Create an in-memory image for a dummy avatar
        file_obj = BytesIO()
        image = Image.new('RGBA', size=(100, 100))
        image.save(file_obj, 'png')
        file_obj.name = 'avatar.png'
        file_obj.seek(0)

        response = self.client.post(url, {'avatar_file': file_obj}, follow=True)
        self.assertRedirects(response, reverse('bio-me'))

        profile = UserProfile.objects.get(user__username='paul')
        self.assertTrue(profile.avatar.path)
        self.assertTrue(profile.avatar.name)
        self.assertTrue(os.path.exists(profile.avatar.path))

    def test_flag_profile_get(self):
        paul = User.objects.get(username='paul')
        eddie = User.objects.get(username='eddie')
        url = reverse('bio-flag_profile', args=[eddie.pk])

        # not logged in, wrong request method:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # logged in, wrong request method
        self.client.login(username='paul', password='pw')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # logged out, right request method
        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfileFlag.objects.all().count(), 0)

        # logged in, right request method
        self.client.login(username='paul', password='pw')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfileFlag.objects.all().count(), 1)

        flag = UserProfileFlag.objects.first()
        self.assertEqual(flag.user, paul)
        self.assertEqual(flag.profile, eddie.profile)

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('A Profile Has Been Flagged' in mail.outbox[0].subject)
