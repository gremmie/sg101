"""Tests for the Cloudflare Turnstile verification helper."""
import logging
import os
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import TestCase
import requests

from antispam.turnstile import TurnstileOutcome, verify


def _response(status_code=200, json_value=None, json_exc=None):
    """Build a mock requests response."""
    response = Mock()
    response.status_code = status_code
    if json_exc is not None:
        response.json.side_effect = json_exc
    else:
        response.json.return_value = json_value
    return response


class VerifyTestCase(TestCase):
    """The three Cloudflare outcomes and the failure modes that produce them."""

    def test_success_passes(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.PASSED)
        self.assertEqual(result.error_codes, ())

    def test_failure_is_rejected_and_keeps_error_codes(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={
                'success': False,
                'error-codes': ['invalid-input-response'],
            })
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.REJECTED)
        self.assertEqual(result.error_codes, ('invalid-input-response',))

    def test_timeout_is_unavailable(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.side_effect = requests.Timeout('too slow')
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.UNAVAILABLE)

    def test_connection_error_is_unavailable(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.side_effect = requests.ConnectionError('no route')
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.UNAVAILABLE)

    def test_non_200_is_unavailable(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(status_code=500, json_value={})
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.UNAVAILABLE)

    def test_unparseable_body_is_unavailable(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_exc=ValueError('not json'))
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.UNAVAILABLE)

    def test_non_dict_body_is_unavailable(self):
        """A JSON array parses fine and then has no .get()."""
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value=['unexpected'])
            result = verify('a-token')

        self.assertEqual(result.outcome, TurnstileOutcome.UNAVAILABLE)

    def test_rejected_and_unavailable_are_distinguishable(self):
        """The whole reason the helper returns outcomes and not a bool."""
        self.assertNotEqual(TurnstileOutcome.REJECTED,
                            TurnstileOutcome.UNAVAILABLE)


class NoTokenTestCase(TestCase):
    """The fourth outcome: Cloudflare was never asked.

    A submission carrying no token is not a verification, but it gets an
    outcome anyway so that every caller refuses it the same way and so that
    the never-call-out-without-a-token property is proven here once instead of
    re-implemented in each form.
    """

    def test_none_is_no_token(self):
        with patch('antispam.turnstile.requests.post'):
            result = verify(None)

        self.assertEqual(result.outcome, TurnstileOutcome.NO_TOKEN)

    def test_no_token_makes_no_request(self):
        """A bot that never loads the widget must cost nothing."""
        with patch('antispam.turnstile.requests.post') as post:
            verify(None)

        post.assert_not_called()

    def test_empty_string_is_no_token(self):
        """A present-but-empty form field arrives as '', not None."""
        with patch('antispam.turnstile.requests.post') as post:
            result = verify('')

        self.assertEqual(result.outcome, TurnstileOutcome.NO_TOKEN)
        post.assert_not_called()

    def test_no_token_carries_no_error_codes(self):
        """Nothing was asked, so there is nothing for Cloudflare to have said."""
        with patch('antispam.turnstile.requests.post'):
            result = verify(None)

        self.assertEqual(result.error_codes, ())

    def test_all_four_outcomes_are_distinct(self):
        self.assertEqual(len(set(TurnstileOutcome)), 4)


class CallSignatureTestCase(TestCase):
    """What actually goes on the wire."""

    def test_timeout_is_passed(self):
        """Without this the call can hang inside a user's request."""
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            verify('a-token')

        self.assertEqual(post.call_args.kwargs['timeout'],
                         settings.TURNSTILE_TIMEOUT)

    def test_url_and_payload(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            verify('a-token', remoteip='198.51.100.7')

        self.assertEqual(post.call_args.args[0], settings.TURNSTILE_URL)
        self.assertEqual(post.call_args.kwargs['data'], {
            'secret': settings.TURNSTILE_SECRET_KEY,
            'response': 'a-token',
            'remoteip': '198.51.100.7',
        })

    def test_missing_remoteip_is_omitted_not_stringified(self):
        """Sending the string "None" would be a malformed address, not absence."""
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            verify('a-token')

        self.assertNotIn('remoteip', post.call_args.kwargs['data'])


class LoggingTestCase(TestCase):
    """One line per verification, and never the token."""

    def setUp(self):
        # The test settings disable logging wholesale, so assertLogs sees
        # nothing without this. Same dance as contact/tests/test_views.py.
        old_disable = logging.getLogger().manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, old_disable)

    def test_pass_logs_without_the_token(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify('super-secret-token')

        self.assertEqual(len(logged.output), 1)
        self.assertIn('passed', logged.output[0])
        self.assertNotIn('super-secret-token', logged.output[0])

    def test_rejection_logs_the_error_codes(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={
                'success': False,
                'error-codes': ['timeout-or-duplicate'],
            })
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify('super-secret-token')

        self.assertIn('rejected', logged.output[0])
        self.assertIn('timeout-or-duplicate', logged.output[0])
        self.assertNotIn('super-secret-token', logged.output[0])

    def test_source_names_the_calling_form(self):
        """Two callers share this logger; a count is useless without the name."""
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify('a-token', source='contact form')

        self.assertIn('(contact form)', logged.output[0])

    def test_source_is_omitted_when_unnamed(self):
        with patch('antispam.turnstile.requests.post') as post:
            post.return_value = _response(json_value={'success': True})
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify('a-token')

        self.assertNotIn('(', logged.output[0])

    def test_source_survives_the_unavailable_path(self):
        """The path that most needs attribution: the check did not happen."""
        with patch('antispam.turnstile.requests.post') as post:
            post.side_effect = requests.Timeout('too slow')
            with self.assertLogs('antispam.turnstile',
                                 level='WARNING') as logged:
                verify('a-token', source='contact form')

        self.assertIn('(contact form)', logged.output[0])
        self.assertIn('too slow', logged.output[0])

    def test_unavailable_logs_at_warning(self):
        """Callers fail open, so this line is the only record the check was
        skipped -- INFO would bury it beside ordinary passes."""
        with patch('antispam.turnstile.requests.post') as post:
            post.side_effect = requests.Timeout('too slow')
            with self.assertLogs('antispam.turnstile',
                                 level='WARNING') as logged:
                verify('super-secret-token')

        self.assertIn('unavailable', logged.output[0])
        self.assertTrue(logged.output[0].startswith('WARNING'))
        self.assertNotIn('super-secret-token', logged.output[0])


    def test_no_token_logs_at_info_naming_the_form(self):
        """The blind spot this line exists to close: without it an absent
        entry means nobody visited, the widget broke, or bots are posting
        direct, and there is no way to tell which."""
        with patch('antispam.turnstile.requests.post'):
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify(None, source='contact form')

        self.assertEqual(len(logged.output), 1)
        self.assertIn('no token', logged.output[0])
        self.assertIn('(contact form)', logged.output[0])
        self.assertTrue(logged.output[0].startswith('INFO'))

    def test_no_token_omits_the_source_when_unnamed(self):
        with patch('antispam.turnstile.requests.post'):
            with self.assertLogs('antispam.turnstile', level='INFO') as logged:
                verify(None)

        self.assertNotIn('(', logged.output[0])


class SettingsTestCase(TestCase):
    """A fresh checkout must have working forms without configuration."""

    TEST_SITE_KEY = '1x00000000000000000000AA'
    TEST_SECRET_KEY = '1x0000000000000000000000000000000AA'

    def test_keys_are_not_blank(self):
        """A blank key is how a clean clone ends up with an unusable form."""
        self.assertTrue(settings.TURNSTILE_SITE_KEY)
        self.assertTrue(settings.TURNSTILE_SECRET_KEY)

    def test_timeout_is_a_positive_int(self):
        self.assertIsInstance(settings.TURNSTILE_TIMEOUT, int)
        self.assertGreater(settings.TURNSTILE_TIMEOUT, 0)

    def test_env_example_documents_the_cloudflare_test_keys(self):
        """The committed defaults are what make a fresh checkout work."""
        path = os.path.join(settings.PROJECT_PATH, os.pardir, '.env.example')
        with open(path, encoding='utf-8') as f:
            contents = f.read()

        self.assertIn('TURNSTILE_SITE_KEY=' + self.TEST_SITE_KEY, contents)
        self.assertIn('TURNSTILE_SECRET_KEY=' + self.TEST_SECRET_KEY, contents)
