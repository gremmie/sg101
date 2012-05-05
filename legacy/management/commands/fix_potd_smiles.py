"""
This command fixes the old 1.0 smiley system to match the new scheme.

"""
from django.core.management.base import NoArgsCommand
from comments.models import Comment


SMILEY_MAP = {
    ':confused:': ':?',
    ':upset:': ':argh:',
    ':eek:': ':shock:',
    ':rolleyes:': ':whatever:',
    ':mad:': 'X-(',
    ':shy:': ':oops:',
    ':laugh:': ':lol:',
    ':dead:': 'x_x',
    ':cry:': ':-(',
    ';)': ':wink:',
    ':|': ':-|',
    ';-)': ':wink:',
    ':D': ':-D',
    ':P': ':-P',
    'B)': '8)',
    ':(': ':-(',
    ':)': ':-)',
}


class Command(NoArgsCommand):

    def handle_noargs(self, **opts):

        comments = Comment.objects.filter(id__gt=3000)
        for comment in comments:
            save = False
            for key, val in SMILEY_MAP.items():
                if key in comment.comment:
                    comment.comment = comment.comment.replace(key, val)
                    save = True

            if save:
                comment.save()

