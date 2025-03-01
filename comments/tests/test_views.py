"""
Unit tests for the comments app views.

"""
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import ANY, call, patch

from comments.models import Comment, CommentFlag
from potd.models import Current, Photo


class PostCommentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.post_url = reverse('comments-post')
        potd1 = Photo(pk=4096, user=self.user, date_added=datetime.today())
        potd1.save()
        potd2 = Photo(pk=8192, user=self.user, date_added=datetime.today())
        potd2.save()
        current = Current(potd=potd2)
        current.save()

    def test_no_ctype_or_object(self):
        response = self.client.post(self.post_url, data={})
        self.assertEqual(response.status_code, 400)

    def test_no_ctype(self):
        response = self.client.post(self.post_url, data={
            'object_pk': '4096',
        })
        self.assertEqual(response.status_code, 400)

    def test_no_object(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'bulletins.Bulletin',
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_model(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'wut.Model',
            'object_pk': '4096',
        })
        self.assertEqual(response.status_code, 400)

    def test_bad_content_type(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'wut',
            'object_pk': '4096',
        })
        self.assertEqual(response.status_code, 400)

    def test_object_does_not_exist(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'potd.Photo',
            'object_pk': '1024',
        })
        self.assertEqual(response.status_code, 400)

    def test_cannot_comment_on_object(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'potd.Photo',
            'object_pk': '4096',
        })
        self.assertEqual(response.status_code, 403)

    def test_form_is_not_valid(self):
        response = self.client.post(self.post_url, data={
            'content_type': 'potd.Photo',
            'object_pk': '8192',
            'comment': '',
        })
        self.assertEqual(response.status_code, 400)

    @patch('comments.views.antispam.utils.spam_check')
    def test_comment_fails_spam_check(self, spam_check_mock):
        spam_check_mock.return_value = True
        response = self.client.post(self.post_url, data={
            'content_type': 'potd.Photo',
            'object_pk': '8192',
            'comment': 'spam!',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(spam_check_mock.mock_calls, [
            call(ANY, 'spam!'),
        ])

    @patch('comments.views.antispam.utils.spam_check')
    def test_happy_path(self, spam_check_mock):
        spam_check_mock.return_value = False
        response = self.client.post(self.post_url, data={
            'content_type': 'potd.Photo',
            'object_pk': '8192',
            'comment': '**Nice**',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(spam_check_mock.mock_calls, [
            call(ANY, '**Nice**'),
        ])
        self.assertIn('<strong>Nice</strong>', response.content)

        self.assertEqual(Comment.objects.count(), 1)
        comments = Comment.objects.for_object(Photo.objects.get(pk=8192))
        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertEqual(comment.content_type.model, 'photo')
        self.assertEqual(comment.object_id, 8192)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.comment, '**Nice**')
        self.assertIn('<strong>Nice</strong>', comment.html)

        now = datetime.now()
        delta = timedelta(seconds=1)
        self.assertGreater(comment.creation_date, now - delta)
        self.assertLess(comment.creation_date, now + delta)
        self.assertTrue(comment.is_public)
        self.assertFalse(comment.is_removed)

class FlagCommentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.post_url = reverse('comments-flag')

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.post_url, data={
            'id': '8192',
        })
        self.assertEqual(response.status_code, 403)

    def test_no_id_supplied(self):
        response = self.client.post(self.post_url, data={})
        self.assertEqual(response.status_code, 400)

    def test_invalid_comment(self):
        response = self.client.post(self.post_url, data={
            'id': '8192',
        })
        self.assertEqual(response.status_code, 400)

    @patch('comments.views.email_admins')
    def test_happy_path(self, email_mock):
        content_type = ContentType.objects.get(app_label='potd', model='photo')
        c = Comment(content_type=content_type, object_id=512, user=self.user,
                    comment='Nice', ip_address='127.0.0.1')
        c.save()
        response = self.client.post(self.post_url, data={
            'id': str(c.pk)
        })
        self.assertEqual(response.status_code, 200)

        self.assertEqual(email_mock.mock_calls, [
            call('A Comment Has Been Flagged',
                 'Hello,\n\nA user has flagged a comment for review.\n'),
        ])

        self.assertEqual(CommentFlag.objects.count(), 1)
        flag = CommentFlag.objects.all()[0]
        self.assertEqual(flag.user, self.user)
        self.assertEqual(flag.comment.pk, c.pk)

        now = datetime.now()
        delta = timedelta(seconds=1)
        self.assertGreater(flag.flag_date, now - delta)
        self.assertLess(flag.flag_date, now + delta)

class MarkdownPreviewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.post_url = reverse('comments-markdown_preview')

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.post_url, data={
            'data': 'Test',
        })
        self.assertEqual(response.status_code, 403)

    def test_no_data_supplied(self):
        response = self.client.post(self.post_url, data={})
        self.assertEqual(response.status_code, 400)

    def test_happy_path(self):
        response = self.client.post(self.post_url, data={
            'data': 'Test',
        })
        self.assertEqual(response.status_code, 200)
        expected_content = (
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '<meta charset="utf-8" />\n'
            '<title>Markdown Preview</title>\n'
            '<link rel="stylesheet" href="/static/js/markitup/templates/preview.css" />\n'
            '</head>\n'
            '<p>Test</p>\n'
            '</body>\n'
            '</html>')
        self.assertEqual(response.content.strip(), expected_content)

class MarkdownPreviewV3TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.client.login(username='pjmoto', password='pw')
        self.post_url = reverse('comments-markdown_preview_v3')

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.post_url, data={
            'data': 'Test',
        })
        self.assertEqual(response.status_code, 403)

    def test_no_data_supplied(self):
        response = self.client.post(self.post_url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '')

    def test_happy_path(self):
        response = self.client.post(self.post_url, data={
            'data': 'Test',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.strip(), '<p>Test</p>')
