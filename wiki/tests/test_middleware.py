# coding=utf-8
"""
Tests for the wiki integration application.

"""
import hashlib
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.http import HttpResponse
from django.conf import settings

from core.services import get_redis_connection
from wiki.middleware import WikiMiddleware
from wiki.constants import SESSION_SET_MEMBER


class MiddleWareTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(u'Sérgio', u'test@example.com',
                u'password')
        self.conn = get_redis_connection()
        self.mw = WikiMiddleware()

        # Redis outlives the per-test database rollback, and any earlier test
        # that logs in over HTTP goes through this middleware and leaves a key
        # behind. Start from a known-empty set so the counts below mean
        # something regardless of what ran first.
        self.conn.delete(settings.WIKI_REDIS_SET)

    def tearDown(self):
        self.conn.delete(settings.WIKI_REDIS_SET)

    def create_request(self):
        request = self.factory.get('/contact/')
        request.session = {}
        request.user = self.user
        return request

    def test_middleware(self):

        request = self.create_request()
        response = HttpResponse()

        request.wiki_set_cookie = True
        response = self.mw.process_response(request, response)

        cookie = response.cookies.get(settings.WIKI_COOKIE_NAME)
        cookie_val = ''
        self.assertIsNotNone(cookie)
        if cookie:
            self.assertEqual(cookie['domain'], settings.WIKI_COOKIE_DOMAIN)
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['max-age'], settings.WIKI_COOKIE_AGE)

            cookie_val = cookie.value
            try:
                user, email, key = cookie_val.split('#')
            except ValueError:
                self.fail('invalid cookie value')
            else:
                self.assertEqual(user, self.user.username)
                self.assertEqual(email, self.user.email)
                self.assertEqual(len(key), 64)

        self.assertEqual(self.conn.zcard(settings.WIKI_REDIS_SET), 1)

        h = hashlib.sha256()
        h.update(cookie_val.encode('utf-8'))
        member = h.hexdigest()

        score = self.conn.zscore(settings.WIKI_REDIS_SET, member)
        now = datetime.datetime.utcnow()
        session_start = datetime.datetime.fromtimestamp(score)
        self.assertLess(now - session_start, datetime.timedelta(seconds=2))

        session_member = request.session.get(SESSION_SET_MEMBER)
        self.assertTrue(session_member and session_member == member)

        # test the destroy session logic

        request = self.create_request()
        request.wiki_delete_cookie = member
        response = self.mw.process_response(request, response)

        cookie = response.cookies.get(settings.WIKI_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        if cookie:
            self.assertEqual(cookie.value, '')
            self.assertEqual(cookie['domain'], settings.WIKI_COOKIE_DOMAIN)
            self.assertEqual(cookie['path'], '/')
            self.assertEqual(cookie['max-age'], 0)
            self.assertEqual(cookie['expires'], 'Thu, 01-Jan-1970 00:00:00 GMT')

        self.assertEqual(self.conn.zcard(settings.WIKI_REDIS_SET), 0)
