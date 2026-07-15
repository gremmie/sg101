"""Tests for the weblink app signal handlers."""

from django.contrib.auth.models import User
from django.test import TestCase

from weblinks.models import Category
from weblinks.models import Link


class ReceiverTestCase(TestCase):

    fixtures = ['weblinks_categories.json']

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'pw')

    def test_signal_handlers(self):

        category = Category.objects.get(pk=1)
        link = Link(category=category,
                    title='Title',
                    url='http://example.com/',
                    description='Cool stuff',
                    is_public=True,
                    user=self.user)
        link.save()

        category = Category.objects.get(pk=1)
        self.assertEqual(1, category.count)

        category2 = Category.objects.get(pk=4)
        link.category = category2
        link.save()

        category = Category.objects.get(pk=1)
        self.assertEqual(0, category.count)
        category2 = Category.objects.get(pk=4)
        self.assertEqual(1, category2.count)

        link.delete()
        category2 = Category.objects.get(pk=4)
        self.assertEqual(0, category2.count)
