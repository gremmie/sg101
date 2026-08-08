"""
Models for the Photo Of The Day (POTD) application.

"""
import datetime
import os
from PIL import ImageFile
from PIL import Image
from io import BytesIO

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_comma_separated_integer_list
from django.core.files.base import ContentFile
from django.urls import reverse

POTD_THUMB_WIDTH = 120

def scale_image(image):
    (w, h) = image.size
    if w <= POTD_THUMB_WIDTH:
        return image
    scale_factor = float(POTD_THUMB_WIDTH) / w
    new_height = int(scale_factor * h)
    return image.resize((POTD_THUMB_WIDTH, new_height), Image.Resampling.LANCZOS)


class Photo(models.Model):
    """Model to represent a POTD"""
    photo = models.ImageField(upload_to='potd/%Y/%m/%d')
    thumb = models.ImageField(upload_to='potd/%Y/%m/%d/thumbs', blank=True, null=True)
    caption = models.CharField(max_length=128)
    description = models.TextField()
    user = models.ForeignKey(User, related_name='potd_set',
                             on_delete=models.CASCADE)
    date_added = models.DateField()
    potd_count = models.IntegerField(default=0)

    class Meta:
        ordering = ('-date_added', '-caption')

    def __str__(self):
        return u'%s (%s)' % (self.caption, self.pk)

    def get_absolute_url(self):
        return reverse('potd-archive', args=[str(self.id)])

    def save(self, *args, **kwargs):
        if not self.pk:
            self.generate_thumb()
            self.date_added = datetime.datetime.now()

        super(Photo, self).save(*args, **kwargs)

    def can_comment_on(self):
        return Current.objects.get_current_id() == self.id

    def generate_thumb(self):
        if self.thumb:
            self.thumb.delete(save=False)

        parser = ImageFile.Parser()
        for chunk in self.photo.chunks():
            parser.feed(chunk)
        image = parser.close()
        # Capture the format BEFORE scaling and keep it for the save below.
        # scale_image() calls resize(), which returns a new image whose .format
        # is None -- only in-place helpers like thumbnail() carry it over. Move
        # this line after the scale and every thumbnail save loses its format.
        format = image.format
        image = scale_image(image)
        s = BytesIO()
        image.save(s, format)
        thumb_name = os.path.basename(self.photo.path)
        self.thumb.save(thumb_name, ContentFile(s.getvalue()), save=False)

    def ogp_tags(self):
        """
        Returns a dict of Open Graph Protocol meta tags.

        """
        desc = "Photo of the day: %s." % self.caption
        return {
            'og:title': self.caption,
            'og:type': 'article',
            'og:url': self.get_absolute_url(),
            'og:image': self.photo.url,
            'og:description': desc,
        }


class CurrentManager(models.Manager):
    """
    Manager for the Current model.

    """
    def get_current_photo(self):
        """
        Retrieves the current photo object from the current record.

        """
        try:
            c = self.get(pk=1)
            return c.potd
        except Current.DoesNotExist:
            return None

    def get_current_id(self):
        """
        Returns the ID of the current POTD from the current record.

        """
        potd = self.get_current_photo()
        if potd is not None:
            return potd.pk
        return None


class Current(models.Model):
    """This model simply stores the current POTD."""
    potd = models.ForeignKey(Photo, on_delete=models.CASCADE)

    objects = CurrentManager()

    def __str__(self):
        return u'%s' % self.potd

    class Meta:
        verbose_name_plural = 'Current'


class SequenceManager(models.Manager):
    """
    Manager for the Sequence model.

    """
    def insert_photo(self, photo_id):
        """
        Inserts the given photo_id just after the current photo so it
        will appear as tomorrow's POTD.

        """
        current = Current.objects.get_current_id()
        if current is not None:
            s = self.get(pk=1)
            seq = [int(x) for x in s.seq.split(',')]
            if photo_id not in seq:
                i = seq.index(current)
                seq.insert(i + 1, photo_id)
                s.seq = ','.join([str(x) for x in seq])
                s.save()

    def remove_photo(self, photo_id):
        """
        Removes a given photo id from the sequence of photos.

        """
        try:
            s = self.get(pk=1)
        except Sequence.DoesNotExist:
            pass
        else:
            seq = [int(x) for x in s.seq.split(',')]
            if photo_id in seq:
                seq.remove(photo_id)
                s.seq = ','.join([str(x) for x in seq])
                s.save()


class Sequence(models.Model):
    """This model stores the sequence of photos for the POTD."""
    seq = models.CharField(max_length=4096,
            validators=[validate_comma_separated_integer_list])

    objects = SequenceManager()

    def __str__(self):
        return u'POTD Sequence %d' % self.id

    class Meta:
        verbose_name_plural = 'Sequence'
