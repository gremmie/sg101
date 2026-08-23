"""
View tests for the bio application.

"""
import datetime
from io import BytesIO
import logging
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from django.core import mail
from django.utils import timezone

from PIL import Image

from accounts.models import EMAIL_CHANGE_EXPIRATION
from accounts.models import PendingEmailChange
from bio.models import UserProfile, UserProfileFlag
from forums.models import Topic

from elsewhere.models import (SocialNetworkProfile, InstantMessengerProfile,
    WebsiteProfile)


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

    def test_other_profile_differing_case(self):
        # Over half of all usernames carry uppercase, so profile URLs are
        # case-bearing; a mis-cased bookmark used to resolve and must still.
        self.client.login(username='paul', password='pw')
        url = reverse('bio-view_profile', kwargs={'username': 'EDDIE'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unknown_profile_is_404(self):
        self.client.login(username='paul', password='pw')
        url = reverse('bio-view_profile', kwargs={'username': 'nobody'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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
        # The address posted above is now pending confirmation rather than
        # applied; EmailChangeTestCase covers that flow. This assertion used to
        # read assertEqual(u.email, 'pjmoto@example.com').
        self.assertEqual(u.email, '')
        self.assertEqual(u.pending_email_change.new_email, 'pjmoto@example.com')
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
        url = reverse('bio-flag_profile', args=[eddie.profile.pk])

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


class EditElsewhereTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('paul', '', 'pw')
        self.user.save()
        self.client.login(username='paul', password='pw')
        self.url = reverse('bio-edit_elsewhere')

    def test_get_view(self):
        response = self.client.get(reverse('bio-edit_elsewhere'))
        self.assertEqual(response.status_code, 200)

    def test_add_social_network(self):
        response = self.client.post(self.url, {
            'network_id': 'catster',
            'username': 'pjmoto',
            'sn-form': 'Add Social Network',
        })
        self.assertRedirects(response, self.url)
        user_networks = self.user.social_network_profiles.all()
        self.assertEqual(user_networks.count(), 1)
        self.assertEqual(user_networks[0].network_id, 'catster')

    def test_add_instant_messenger(self):
        response = self.client.post(self.url, {
            'network_id': 'aim',
            'username': 'pjmoto',
            'im-form': 'Add Instant Messenger',
        })
        self.assertRedirects(response, self.url)
        user_networks = self.user.instant_messenger_profiles.all()
        self.assertEqual(user_networks.count(), 1)
        self.assertEqual(user_networks[0].network_id, 'aim')

    def test_add_website(self):
        response = self.client.post(self.url, {
            'name': 'pjmoto.com',
            'url': 'https://example.com/pjmoto',
            'w-form': 'Add Website',
        })
        self.assertRedirects(response, self.url)
        websites = self.user.website_profiles.all()
        self.assertEqual(websites.count(), 1)
        self.assertEqual(websites[0].name, 'pjmoto.com')
        self.assertEqual(websites[0].url, 'https://example.com/pjmoto')

    def test_delete_social_network(self):
        profile = SocialNetworkProfile(user=self.user, network_id='catster',
                                       username='pjmoto')
        profile.save()
        self.assertEqual(self.user.social_network_profiles.count(), 1)
        response = self.client.post(self.url, {
            'delete_id': profile.id,
            'delete-sn-form': 'Delete',
        })
        self.assertRedirects(response, self.url)
        self.assertEqual(self.user.social_network_profiles.count(), 0)

    def test_delete_instant_messenger(self):
        profile = InstantMessengerProfile(user=self.user, network_id='aim',
                                          username='pjmoto')
        profile.save()
        self.assertEqual(self.user.instant_messenger_profiles.count(), 1)
        response = self.client.post(self.url, {
            'delete_id': profile.id,
            'delete-im-form': 'Delete',
        })
        self.assertRedirects(response, self.url)
        self.assertEqual(self.user.instant_messenger_profiles.count(), 0)

    def test_delete_website(self):
        profile = WebsiteProfile(user=self.user, name='pjmoto.com',
                                 url='https://example.com/pjmoto')
        profile.save()
        self.assertEqual(self.user.website_profiles.count(), 1)
        response = self.client.post(self.url, {
            'delete_id': profile.id,
            'delete-w-form': 'Delete',
        })
        self.assertRedirects(response, self.url)
        self.assertEqual(self.user.website_profiles.count(), 0)


class EmailChangeTestCase(TestCase):
    """Requesting, confirming, cancelling and resending an email change.

    The property under test throughout: an address the member has not answered
    mail at never reaches User.email.

    """

    def setUp(self):
        self.user = User.objects.create_user('paul', 'paul@example.com', 'pw')
        self.url = reverse('bio-edit_profile')
        self.assertTrue(self.client.login(username='paul', password='pw'))

    def post_edit(self, email, **kwargs):
        data = {
            'first_name': 'Paul',
            'last_name': 'Johnson',
            'email': email,
            'submit_button': 'Save',
        }
        data.update(kwargs)
        return self.client.post(self.url, data, follow=True)

    def test_requested_address_does_not_reach_the_user(self):
        self.post_edit('new@example.com')

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paul@example.com')
        self.assertEqual(self.user.pending_email_change.new_email,
                         'new@example.com')

    def test_the_rest_of_the_profile_still_saves(self):
        self.post_edit('new@example.com', occupation='Surf Guitar Pioneer')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Paul')
        self.assertEqual(self.user.profile.occupation, 'Surf Guitar Pioneer')

    def test_both_addresses_are_mailed(self):
        self.post_edit('new@example.com')

        recipients = sorted(sum((m.to for m in mail.outbox), []))
        self.assertEqual(recipients, ['new@example.com', 'paul@example.com'])

    def test_the_confirmation_carries_the_link_and_the_notice_does_not(self):
        self.post_edit('new@example.com')

        change = self.user.pending_email_change
        by_recipient = {m.to[0]: m for m in mail.outbox}
        self.assertIn(change.key, by_recipient['new@example.com'].body)
        # No action link to the old address: there is no takeover path here
        # (login is by username, and a password reset mails its link to the
        # address on file), so a "this wasn't me" link would add attack surface
        # to answer a risk that does not exist. It names the contact form.
        self.assertNotIn(change.key, by_recipient['paul@example.com'].body)

    def test_the_send_is_categorized(self):
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

        with self.assertLogs('email', level='INFO') as logged:
            self.post_edit('new@example.com')

        self.assertTrue(all('category=email_change' in line
                            for line in logged.output),
                        msg=logged.output)

    def test_the_member_is_told_the_change_is_pending(self):
        """Asserted against the notice, not against the address appearing.

        Saving redirects to bio-me, which renders the pending-change notice --
        so a bare assertContains for the address passes whether or not the
        member is told anything, and would keep passing if the notice were
        removed and something else happened to print the address.

        """
        response = self.post_edit('new@example.com')

        self.assertContains(response, 'warning callout')
        self.assertContains(response, 'new@example.com')
        self.assertContains(response, reverse('bio-email_change_cancel'))

    def test_the_edit_page_shows_the_verified_address_and_a_notice(self):
        """A flash dies on the next page load; the pending state does not."""
        self.post_edit('new@example.com')

        response = self.client.get(self.url)

        self.assertEqual(response.context['pending_change'].new_email,
                         'new@example.com')
        self.assertEqual(response.context['user_form']['email'].value(),
                         'paul@example.com')
        self.assertContains(response, 'new@example.com')
        # A multi-line {# #} is not a comment token -- Django's tokenizer is
        # not DOTALL -- so one renders to the page as literal text. Asserting
        # on the address alone did not notice that.
        self.assertNotContains(response, '{#')
        self.assertNotContains(response, '{%')
        # Both buttons reach the page and point somewhere real. The cancel and
        # resend tests below post to these URLs directly, so nothing else here
        # would notice a button that went missing or lost its formaction.
        self.assertContains(response, reverse('bio-email_change_cancel'))
        self.assertContains(response, reverse('bio-email_change_resend'))

    def test_the_profile_page_shows_the_notice_too(self):
        """The edit page is not where a member spends time; the profile is."""
        self.post_edit('new@example.com')

        response = self.client.get(reverse('bio-me'))

        self.assertEqual(response.context['pending_change'].new_email,
                         'new@example.com')
        self.assertContains(response, 'warning callout')
        self.assertContains(response, reverse('bio-email_change_cancel'))
        self.assertContains(response, reverse('bio-email_change_resend'))

    def test_the_notice_never_reaches_another_members_profile(self):
        """Nobody else should learn an address its owner has not confirmed.

        Structural rather than conditional: only my_profile puts
        pending_change in the context, and view_profile redirects to bio-me
        when the subject is you. This asserts the structure holds.

        """
        self.post_edit('new@example.com')
        User.objects.create_user('eddie', 'eddie@example.com', 'pw')
        self.client.login(username='eddie', password='pw')

        response = self.client.get(reverse('bio-view_profile',
                                           kwargs={'username': 'paul'}))

        self.assertIsNone(response.context.get('pending_change'))
        self.assertNotContains(response, 'new@example.com')

    def test_the_profile_page_notice_expires_with_the_request(self):
        self.post_edit('new@example.com')
        PendingEmailChange.objects.all().update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))

        response = self.client.get(reverse('bio-me'))

        self.assertIsNone(response.context['pending_change'])

    def test_an_expired_pending_change_is_not_shown(self):
        self.post_edit('new@example.com')
        PendingEmailChange.objects.all().update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))

        response = self.client.get(self.url)

        self.assertIsNone(response.context['pending_change'])

    def test_a_second_request_replaces_the_first(self):
        self.post_edit('first@example.com')
        mail.outbox = []

        self.post_edit('second@example.com')

        self.assertEqual(PendingEmailChange.objects.count(), 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.pending_email_change.new_email,
                         'second@example.com')
        # The old address is told again: it is the only signal the member gets
        # if someone else is making these requests.
        recipients = sorted(sum((m.to for m in mail.outbox), []))
        self.assertEqual(recipients, ['paul@example.com', 'second@example.com'])

    def test_cancel_clears_the_pending_change(self):
        self.post_edit('typo@example.com')

        response = self.client.post(reverse('bio-email_change_cancel'),
                                    follow=True)

        self.assertRedirects(response, self.url)
        self.assertFalse(PendingEmailChange.objects.exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paul@example.com')

    def test_a_new_request_works_immediately_after_a_cancel(self):
        self.post_edit('typo@example.com')
        self.client.post(reverse('bio-email_change_cancel'))

        self.post_edit('right@example.com')

        self.user.refresh_from_db()
        self.assertEqual(self.user.pending_email_change.new_email,
                         'right@example.com')

    def test_cancel_and_resend_return_to_the_page_they_came_from(self):
        """The notice is on two pages, so a fixed redirect moves the member."""
        self.post_edit('new@example.com')
        me = reverse('bio-me')

        for name in ['bio-email_change_resend', 'bio-email_change_cancel']:
            with self.subTest(name=name):
                self.post_edit('new@example.com')
                response = self.client.post(reverse(name), {'next': me})
                self.assertRedirects(response, me)

    def test_an_offsite_next_is_refused(self):
        """A redirect target posted by a form is an open redirect if trusted."""
        self.post_edit('new@example.com')

        for hostile in ['https://evil.example.com/', '//evil.example.com/',
                        'http://evil.example.com/']:
            with self.subTest(next=hostile):
                self.post_edit('new@example.com')
                response = self.client.post(reverse('bio-email_change_cancel'),
                                            {'next': hostile})
                self.assertRedirects(response, reverse('bio-edit_profile'))

    def test_cancel_requires_a_post(self):
        self.post_edit('typo@example.com')

        response = self.client.get(reverse('bio-email_change_cancel'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(PendingEmailChange.objects.exists())

    def test_the_cancel_and_resend_flashes_are_actually_displayed(self):
        """Both redirect to the edit page, so that page has to render messages.

        Only four templates on the site include core/message_list.html, and
        edit_profile.html was not one of them -- so these two flashes were
        stored and then surfaced on whatever page the member happened to visit
        next. Asserting the redirect is not enough to catch that.

        """
        self.post_edit('new@example.com')

        for name, expected in [('bio-email_change_resend', 'sent again'),
                               ('bio-email_change_cancel', 'cancelled')]:
            with self.subTest(name=name):
                response = self.client.post(reverse(name), follow=True)
                self.assertContains(response, expected)

    def test_resend_mails_the_new_address_only(self):
        self.post_edit('new@example.com')
        mail.outbox = []

        response = self.client.post(reverse('bio-email_change_resend'),
                                    follow=True)

        self.assertRedirects(response, self.url)
        # The old address was told when the change was requested; a resend is
        # not a new request, so telling it again would be noise.
        self.assertEqual([m.to for m in mail.outbox], [['new@example.com']])

    def test_resend_restarts_the_expiry_window(self):
        self.post_edit('new@example.com')
        original = PendingEmailChange.objects.get()
        PendingEmailChange.objects.all().update(
            date_requested=timezone.now() - datetime.timedelta(hours=23))

        self.client.post(reverse('bio-email_change_resend'))

        current = PendingEmailChange.objects.get()
        self.assertNotEqual(current.key, original.key)
        self.assertLess(timezone.now() - current.date_requested,
                        datetime.timedelta(minutes=1))

    def test_resend_with_nothing_pending_is_harmless(self):
        response = self.client.post(reverse('bio-email_change_resend'),
                                    follow=True)

        self.assertRedirects(response, self.url)
        self.assertEqual(mail.outbox, [])

    def test_login_is_required(self):
        self.client.logout()

        for name in ['bio-email_change_cancel', 'bio-email_change_resend']:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.post(url)
                self.assertRedirects(
                    response, reverse('accounts-login') + '?next=' + url)


class UnverifiedAddressIsNotDisplayedTestCase(TestCase):
    """Criterion 7, asserted rather than assumed.

    The pending address never enters User.email, so the three templates that
    render a member's address need no edit. That is a property of the model
    decision, not of the templates, and nothing else in the suite would notice
    if a later change started writing the address at request time -- so it is
    asserted here, across all three surfaces at once. The forums fixture is
    here for the third of them.

    """
    fixtures = ['forums.json']

    def setUp(self):
        self.user = User.objects.create_user('paul', 'paul@example.com', 'pw')
        # hide_email defaults to True, which would make every assertion below
        # pass for the wrong reason.
        UserProfile.objects.filter(user=self.user).update(hide_email=False)
        self.assertTrue(self.client.login(username='paul', password='pw'))
        # follow=True so the success flash is rendered and consumed here: it
        # names the pending address, and an unconsumed message would appear on
        # whichever page each test below fetches.
        self.client.post(reverse('bio-edit_profile'), {
            'first_name': '', 'last_name': '', 'email': 'new@example.com',
            'submit_button': 'Save',
        }, follow=True)
        self.assertEqual(PendingEmailChange.objects.count(), 1)

    def assertPublishesVerifiedAddressOnly(self, response):
        """Assert on the mailto link, not on the bare string.

        "Do not display an unverified address" means do not publish it to
        other people. The owner's own pending-change notice names the pending
        address on purpose, so asserting the string is simply absent would
        fail for the right behaviour. The mailto link is the thing that
        actually hands the address out.

        """
        self.assertContains(response, 'mailto:paul@example.com')
        self.assertNotContains(response, 'mailto:new@example.com')

    def test_profile_page(self):
        response = self.client.get(reverse('bio-me'))

        self.assertPublishesVerifiedAddressOnly(response)

    def test_member_list(self):
        response = self.client.get(reverse('bio-member_list',
                                           kwargs={'type': 'user'}))

        self.assertPublishesVerifiedAddressOnly(response)

    def test_forum_post(self):
        self.client.post(
            reverse('forums-new_topic', kwargs={'slug': 'shallow-end'}),
            {'name': 'A test topic', 'body': 'testing 1, 2, 3...'})
        topic = Topic.objects.get(name='A test topic')

        response = self.client.get(reverse('forums-topic_index',
                                           kwargs={'id': str(topic.pk)}))

        self.assertPublishesVerifiedAddressOnly(response)
