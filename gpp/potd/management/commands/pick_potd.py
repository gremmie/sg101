"""
pick_potd is a custom manage.py command for the POTD application. 
It is intended to be called from a cron job at midnight to pick the
new POTD.
"""

import random
from django.core.management.base import NoArgsCommand

from potd.models import Current
from potd.models import Sequence
from potd.models import Photo

def get_sequence():
    try:
        s = Sequence.objects.get(pk=1)
        if s.seq:
            return [int(x) for x in s.seq.split(',')]
    except:
        pass
    return []

def new_sequence():
    the_ids = Photo.objects.values_list('id', flat=True).order_by('id')
    ids = []
    for id in the_ids.iterator():
        ids.append(int(id))

    random.shuffle(ids)
    try:
        s = Sequence.objects.get(pk=1)
    except Sequence.DoesNotExist:
        s = Sequence()

    s.seq = ','.join([str(id) for id in ids])
    s.save()
    return ids

class Command(NoArgsCommand):
    help = "Chooses the next POTD. Run this command at midnight to update the POTD."
    #requires_model_validation = False

    def handle_noargs(self, **options):
        try:
            c = Current.objects.get(pk=1)
            current = c.potd.pk
        except Current.DoesNotExist:
            c = Current()
            current = None

        seq = get_sequence()
        if current is None or len(seq) == 0 or current == seq[-1]:
            # time to generate a new random sequence
            seq = new_sequence()
            # set current to the first one in the sequence
            if len(seq) > 0:
                try:
                    c.potd = Photo.objects.get(pk=seq[0])
                    c.potd.potd_count += 1
                    c.potd.save()
                    c.save()
                except:
                    pass
        else:
            # find current in the sequence, pick the next one
            try:
                i = seq.index(current)
                c.potd = Photo.objects.get(pk=seq[i + 1])
                c.potd.potd_count += 1
                c.potd.save()
                c.save()
            except:
                pass
                    
