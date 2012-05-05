"""
Tests for the pick_potd() function.

"""
from django.test import TestCase
from django.contrib.auth.models import User

from potd.models import Current, Photo, Sequence
from potd.tools import pick_potd


class PickPotdTest(TestCase):

    fixtures = ['potd_test.json']

    def test_pick(self):

        pick_potd()

        curr = Current.objects.get(pk=1)
        self.assertEqual(curr.potd.pk, 2)

    def test_shuffle(self):

        photo = Photo.objects.get(pk=3)
        curr = Current.objects.get(pk=1)
        curr.potd = photo
        curr.save()

        pick_potd()

        ids = Sequence.objects.get(pk=1).seq.split(',')
        curr = Current.objects.get(pk=1)
        self.assertEqual(len(ids), 3)
        self.assertEqual(curr.potd.pk, int(ids[0]))
