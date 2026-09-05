"""
Form tests for the bio application.

"""
import datetime
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from accounts.models import EMAIL_CHANGE_EXPIRATION
from accounts.models import PendingEmailChange
from bio.forms import EditUserForm
from bio.forms import EditUserProfileForm
from bio.forms import SearchUsersForm
from bio.forms import UploadAvatarForm
from core.tests.images.imagemakers import jpeg_bytes, png_bytes


def _suspend_email_uniqueness():
    """Drop the LOWER(email) unique index for the rest of this transaction.

    A TestCase rolls back, which restores it; nothing outside the test sees it
    gone.

    """
    if connection.vendor == 'mysql':
        return

    with connection.cursor() as cursor:
        cursor.execute('DROP INDEX IF EXISTS auth_user_email_lower_uniq')


class EditUserProfileFormTestCase(TestCase):

    def test_valid_timezone(self):

        post_data = {'time_zone': 'US/Central'}
        form = EditUserProfileForm(post_data)
        self.assertTrue(form.is_valid())

    def test_invalid_timezone(self):

        post_data = {'time_zone': u'Am\xe9rica/Argentina_/_Buenos_Aires'}
        form = EditUserProfileForm(post_data)
        self.assertFalse(form.is_valid())

    def test_path_shaped_timezone_is_a_validation_error(self):
        """ZoneInfo answers path-shaped input with ValueError, not
        ZoneInfoNotFoundError. Catching only the latter would turn each of
        these into a 500 on a field anyone can post to."""

        for tz in ['../etc/passwd', '/etc/passwd', '..', 'a/../../b']:
            with self.subTest(tz=tz):
                form = EditUserProfileForm({'time_zone': tz})
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


class UploadAvatarFormTestCase(TestCase):
    """Avatar downscaling against real image bytes.

    clean_avatar_file() stashes self.file_type = image.format while the image
    is still the one it opened, because save() then scales through
    downscale_image_square(), whose crop()/resize() hand back new images with
    .format of None. Move that capture into save() and there is nothing left to
    read the format from, so these tests fail -- which is the point of them.

    """

    def _saved(self, name, data):
        upload = SimpleUploadedFile(name, data)
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertTrue(form.is_valid(), form.errors)

        filename, content = form.save()
        image = Image.open(BytesIO(content.read()))
        image.load()
        return filename, image

    def test_downscales_a_jpeg_avatar(self):
        filename, image = self._saved('avatar.jpg', jpeg_bytes(size=(400, 300)))

        self.assertEqual(filename, 'avatar.jpg')
        self.assertEqual(image.format, 'JPEG')
        self.assertEqual(image.size, (100, 100))

    def test_downscales_a_png_avatar_and_keeps_its_alpha(self):
        filename, image = self._saved('avatar.png', png_bytes(size=(400, 300)))

        self.assertEqual(filename, 'avatar.png')
        self.assertEqual(image.format, 'PNG')
        self.assertEqual(image.size, (100, 100))
        self.assertEqual(image.mode, 'RGBA')
        alpha = image.getchannel('A').getextrema()
        self.assertLess(alpha[0], alpha[1])

    def test_rejects_a_file_that_is_not_an_image(self):
        upload = SimpleUploadedFile('avatar.png', b'not an image')
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertFalse(form.is_valid())

    def test_small_avatar_is_returned_unchanged(self):
        data = png_bytes(size=(50, 50))
        upload = SimpleUploadedFile('small.png', data)
        form = UploadAvatarForm({}, {'avatar_file': upload})

        self.assertTrue(form.is_valid(), form.errors)
        filename, content = form.save()

        self.assertEqual(filename, 'small.png')
        self.assertIs(content, upload)


class EditUserFormTestCase(TestCase):
    """Validation on the email field of the profile edit form.

    The constraint that shapes every test here: some addresses in the
    production database were held by more than one account. A uniqueness check
    that ran on every submission would lock every member in that position out of
    saving any profile edit at all, forever, including edits that never touch
    the email field. So the check must fire only when the address actually
    changes.

    Those pairs have since been cleared and a unique index keeps new ones from
    forming, so the state is no longer reachable through the site -- but the
    guard is still the right shape, and the test below builds the state by hand
    to prove it.

    """

    def setUp(self):
        self.user = User.objects.create_user('paul', 'paul@example.com', 'pw')
        self.other = User.objects.create_user('eddie', 'eddie@example.com', 'pw')

    def post_data(self, email, **kwargs):
        data = {'first_name': 'Paul', 'last_name': 'Johnson', 'email': email}
        data.update(kwargs)
        return data

    def test_fresh_address_is_accepted_and_reported_as_requested(self):
        form = EditUserForm(self.post_data('new@example.com'),
                            instance=self.user)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.requested_email(), 'new@example.com')

    def test_saving_never_writes_the_requested_address(self):
        form = EditUserForm(self.post_data('new@example.com'),
                            instance=self.user)
        self.assertTrue(form.is_valid())

        form.save()

        self.assertEqual(User.objects.get(pk=self.user.pk).email,
                         'paul@example.com')

    def test_address_another_account_holds_is_rejected(self):
        form = EditUserForm(self.post_data('eddie@example.com'),
                            instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_address_another_account_holds_is_rejected_differing_case(self):
        # Addresses came to be shared partly through differences of case and
        # collation, so the check has to be case-insensitive to be worth
        # anything.
        form = EditUserForm(self.post_data('Eddie@Example.COM'),
                            instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_address_pending_for_another_account_is_rejected(self):
        PendingEmailChange.objects.request_change(self.other, 'new@example.com')

        form = EditUserForm(self.post_data('new@example.com'),
                            instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_expired_pending_address_does_not_block(self):
        change = PendingEmailChange.objects.request_change(self.other,
                                                           'new@example.com')
        PendingEmailChange.objects.filter(pk=change.pk).update(
            date_requested=timezone.now() - EMAIL_CHANGE_EXPIRATION
                           - datetime.timedelta(minutes=1))

        form = EditUserForm(self.post_data('new@example.com'),
                            instance=self.user)

        self.assertTrue(form.is_valid())

    def test_member_sharing_an_address_can_still_save(self):
        """The regression a naive uniqueness check invites.

        A member who shares an address with another account, saving an edit
        that does not touch the email field at all. Against an implementation
        that runs the uniqueness check unconditionally -- exclude(pk=
        self.instance.pk) and nothing else -- this fails, and every member in
        that position can never save a profile edit again.

        Members were in that position when this guard was written. The
        unique index on LOWER(email) has since made the state unreachable
        through the site, so the test builds it by dropping the index for the
        duration of its own transaction. The guard is kept because the state is
        not unreachable everywhere -- a backup restored from before the index,
        and MySQL, which does not carry it.

        """
        _suspend_email_uniqueness()
        twin = User.objects.create_user('twin', 'paul@example.com', 'pw')

        form = EditUserForm(self.post_data('paul@example.com'), instance=twin)

        self.assertTrue(form.is_valid(),
                        msg='a member sharing an address cannot save: %r'
                            % form.errors)
        self.assertIsNone(form.requested_email())

    def test_recasing_your_own_address_is_not_a_change(self):
        # Same mailbox, so there is nothing to verify -- and treating it as a
        # change would make the member confirm an address they already own.
        form = EditUserForm(self.post_data('Paul@Example.com'),
                            instance=self.user)

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.requested_email())

    def test_unchanged_address_is_not_a_change(self):
        form = EditUserForm(self.post_data('paul@example.com'),
                            instance=self.user)

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.requested_email())
