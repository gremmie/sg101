"""
Unit tests for the potd application tasks.

"""
from django.test import TestCase

from potd.models import Current, Photo, Sequence
from potd.tasks import pick_potd


class PickPotdTestCase(TestCase):
    """Testing the pick_potd celery task."""
    fixtures = ['potd_test.json']

    def test_picks_the_next_photo_in_sequence(self):
        task = pick_potd.s().apply()
        current_id = Current.objects.get_current_id()
        self.assertEqual(current_id, 2)

        new_photo = Photo.objects.get(pk=2)
        self.assertEqual(new_photo.potd_count, 6)

    def test_generates_a_new_sequence(self):
        current = Current.objects.get(pk=1)
        new_photo = Photo.objects.get(pk=3)
        current.potd = new_photo
        current.save()

        task = pick_potd.s().apply()

        # The sequence gets shuffled, but there is a good chance it
        # might be the same, so don't test that.

        current_photo = Current.objects.get_current_photo()
        new_seq = Sequence.objects.get(pk=1).seq.split(',')
        self.assertEqual(len(new_seq), 3)
        self.assertEqual(int(new_seq[0]), current_photo.pk)

        if current_photo.pk == 1 or current_photo.pk == 3:
            self.assertEqual(current_photo.potd_count, 7)
        elif current_photo.pk == 2:
            self.assertEqual(current_photo.potd_count, 6)
        else:
            self.fail('Unexpected photo pk in new sequence')

