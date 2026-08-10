"""
Unit tests for the comments app template tags.

"""

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.template import Context, Template
from django.test import TestCase
from django.utils import timezone
from lxml import html

from comments.models import Comment
from potd.models import Photo


class GetCommentCountTestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% get_comment_count for photo as count %}'
        'Number of comments: {{ count }}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()

        content_type = ContentType.objects.get(app_label='potd', model='photo')
        c = Comment(content_type=content_type, object_id=self.photo.pk,
                    user=self.user, comment='Nice', ip_address='127.0.0.1')
        c.save()

    def test_renders_comment_count(self):
        rendered = self.TEMPLATE.render(Context({'photo': self.photo}))
        self.assertIn('Number of comments: 1', rendered)


class GetCommentListTestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% get_comment_list for photo as comments %}'
        '{% for comment in comments %}'
        '<p>{{ comment.comment }}</p>'
        '{% endfor %}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()

        content_type = ContentType.objects.get(app_label='potd', model='photo')
        c = Comment(content_type=content_type, object_id=self.photo.pk,
                    user=self.user, comment='Nice', ip_address='127.0.0.1')
        c.save()
        c = Comment(content_type=content_type, object_id=self.photo.pk,
                    user=self.user, comment='Cool', ip_address='127.0.0.1')
        c.save()

    def test_renders_comment_list(self):
        rendered = self.TEMPLATE.render(Context({'photo': self.photo}))
        self.assertIn('<p>Nice</p>', rendered)
        self.assertIn('<p>Cool</p>', rendered)


def test_form(self, doc):
    textareas = doc.xpath('//textarea')
    self.assertIsNotNone(textareas)
    self.assertEqual(len(textareas), 1)

    ct_inputs = doc.xpath('//input[@id="id_content_type"]')
    self.assertIsNotNone(ct_inputs)
    self.assertEqual(len(ct_inputs), 1)

    ct_input = ct_inputs[0]
    self.assertEqual(ct_input.name, 'content_type')
    self.assertEqual(ct_input.type, 'hidden')
    self.assertEqual(ct_input.value, 'potd.photo')

    pk_inputs = doc.xpath('//input[@id="id_object_pk"]')
    self.assertIsNotNone(pk_inputs)
    self.assertEqual(len(pk_inputs), 1)

    pk_input = pk_inputs[0]
    self.assertEqual(pk_input.name, 'object_pk')
    self.assertEqual(pk_input.type, 'hidden')
    self.assertEqual(pk_input.value, str(self.photo.pk))


class GetCommentFormTestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% get_comment_form for photo as form %}'
        # as_table rather than a bare {{ form }}: the assertions below only
        # look for the fields, but naming the style keeps this rendering the
        # same markup after Django changes what an unqualified form renders as.
        '{{ form.as_table }}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()

    def test_renders_comment_form(self):
        rendered = self.TEMPLATE.render(Context({'photo': self.photo}))
        doc = html.fragment_fromstring(rendered)
        test_form(self, doc)


class RenderCommentFormTestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% render_comment_form user photo %}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()

    def test_renders_comment_form(self):
        rendered = self.TEMPLATE.render(Context({
            'user': self.user,
            'photo': self.photo,
        }))
        doc = html.fragment_fromstring(rendered)
        test_form(self, doc)

    def test_renders_comment_form_logged_out(self):
        anon_user = AnonymousUser()
        rendered = self.TEMPLATE.render(Context({
            'user': anon_user,
            'photo': self.photo,
        }))
        doc = html.fragment_fromstring(rendered)
        links = doc.xpath('//a')
        self.assertIsNotNone(links)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].items()[0], ('href', '/accounts/login/'))
        self.assertEqual(links[1].items()[0], ('href', '/accounts/register/'))


class RenderCommentFormV3TestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% render_comment_form_v3 user photo %}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()

    def test_renders_comment_form(self):
        rendered = self.TEMPLATE.render(Context({
            'user': self.user,
            'photo': self.photo,
        }))
        # Just make sure nothing blows up
        self.assertIsNotNone(rendered)
        self.assertTrue(len(rendered) > 0)

    def test_renders_comment_form_logged_out(self):
        anon_user = AnonymousUser()
        rendered = self.TEMPLATE.render(Context({
            'user': anon_user,
            'photo': self.photo,
        }))
        doc = html.fragment_fromstring(rendered)
        links = doc.xpath('//a')
        self.assertIsNotNone(links)
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].items()[0], ('href', '/accounts/login/'))
        self.assertEqual(links[1].items()[0], ('href', '/accounts/register/'))


class RenderCommentListTestCase(TestCase):
    TEMPLATE = Template(
        '{% load comment_tags %}'
        '{% render_comment_list photo %}'
        )

    def setUp(self):
        self.user = User.objects.create_user('pjmoto', '', 'pw')
        self.user.save()
        self.photo = Photo(pk=4096, user=self.user, date_added=timezone.now())
        self.photo.save()
        content_type = ContentType.objects.get(app_label='potd', model='photo')
        c = Comment(content_type=content_type, object_id=self.photo.pk,
                    user=self.user, comment='Nice', ip_address='127.0.0.1')
        c.save()
        c = Comment(content_type=content_type, object_id=self.photo.pk,
                    user=self.user, comment='Cool', ip_address='127.0.0.1')
        c.save()

    def test_renders_comment_list(self):
        rendered = self.TEMPLATE.render(Context({
            'photo': self.photo,
        }))
        self.assertIn('Nice', rendered)
        self.assertIn('Cool', rendered)

