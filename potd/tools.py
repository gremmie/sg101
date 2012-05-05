"""
Tools for the Photo of the Day (potd) application.

"""
import random
import logging

from potd.models import Current, Sequence, Photo


logger = logging.getLogger(__name__)


def get_sequence():
    """
    Reads the photo sequence object from the database and converts it into a
    list of photo IDs. If the sequence object is not found, and empty list is
    returned.

    """
    try:
        s = Sequence.objects.get(pk=1)
    except Sequence.DoesNotExist:
        return []

    return [int(x) for x in s.seq.split(',')]


def new_sequence():
    """
    Generates a new random sequence of photos and saves it to the database.
    The sequence is returned as a list of photo IDs.

    """
    ids = list(Photo.objects.values_list('id', flat=True))
    random.shuffle(ids)

    try:
        s = Sequence.objects.get(pk=1)
    except Sequence.DoesNotExist:
        s = Sequence()

    s.seq = ','.join([str(n) for n in ids])
    s.save()
    return ids


def pick_potd():
    """
    Chooses the next POTD. Run this command at midnight to update the POTD.

    """
    # Get the "current" record for the now old POTD:
    try:
        c = Current.objects.get(pk=1)
        current = c.potd.pk
    except Current.DoesNotExist:
        c = Current()
        current = None

    # Get the sequence of photo ID's:
    seq = get_sequence()

    # If there is no current object, sequence, or if this was the last POTD in
    # the sequence, generate a new random sequence:

    if current is None or not seq or current == seq[-1]:
        # time to generate a new random sequence
        seq = new_sequence()
        # set current to the first one in the sequence
        if seq:
            try:
                c.potd = Photo.objects.get(pk=seq[0])
            except Photo.DoesNotExist:
                logger.error("POTD: missing photo %d", seq[0])
            else:
                c.potd.potd_count += 1
                c.potd.save()
                c.save()
    else:
        # find current in the sequence, pick the next one
        try:
            i = seq.index(current)
        except ValueError:
            logger.error("POTD: current photo (%d) not in sequence", current)
            return

        n = i + 1
        try:
            c.potd = Photo.objects.get(pk=seq[n])
        except Photo.DoesNotExist:
            logger.error("POTD: missing next photo %d", n)
        else:
            c.potd.potd_count += 1
            c.potd.save()
            c.save()
