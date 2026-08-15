"""Tests for potd signal handlers."""
from django.contrib.auth.models import User
from django.test import TestCase

from unittest.mock import Mock

from potd.models import Photo, Sequence, Current


class PotdSignalRcvrTestCase(TestCase):

    fixtures = ['potd_test.json']

    def test_on_photo_save(self):
        user = User.objects.get(pk=1)
        photo = Photo(photo='/tmp/1.jpg',
                      caption='caption',
                      description='desc',
                      user=user)
        photo.generate_thumb = Mock()
        photo.save()

        current = Current.objects.get_current_id()
        self.assertTrue(current != photo.pk)

        seq = Sequence.objects.get(pk=1)
        expected = '1,{},2,3'.format(photo.pk)
        self.assertEqual(seq.seq, expected)

    def test_on_photo_delete(self):
        photo = Photo.objects.get(pk=2)
        photo.delete()
        seq = Sequence.objects.get(pk=1)
        self.assertEqual(seq.seq, '1,3')
