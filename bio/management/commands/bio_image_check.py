"""bio_image_check

A management command to check profiles for non-secure images.
"""
from optparse import make_option

from django.core.management.base import NoArgsCommand

from bio.models import UserProfile
from core.html import image_check
from core.html import ImageCheckError


def _image_check(html):
    try:
        image_check(html)
    except ImageCheckError:
        return False
    return True


class Command(NoArgsCommand):
    help = "Checks user profiles for non-secure images"
    option_list = NoArgsCommand.option_list + (
            make_option('--resave',
                action='store_true',
                dest='resave',
                default=False,
                help='Re-save profile if issue found'),
    )

    def handle_noargs(self, **options):

        resave = options.get('resave', False)

        count = 0
        for p in UserProfile.objects.iterator():
            issue_found = False
            if p.profile_html and not _image_check(p.profile_html):
                self.stdout.write("%s: profile_text\n" % p.user.username)
                count += 1
                issue_found = True
            if p.signature_html and not _image_check(p.signature_html):
                self.stdout.write("%s: signature\n" % p.user.username)
                count += 1
                issue_found = True

            if issue_found and resave:
                p.save(content_update=True)

        self.stdout.write("%d problem field(s) found\n" % count)
