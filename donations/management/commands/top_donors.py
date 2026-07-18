"""top_donors.py

A management command to display top donor data.

"""
from django.core.management.base import BaseCommand

from donations.models import Donation


ROW_FMT = '{n:<5} {name:<32} ${amount}\n'


class Command(BaseCommand):
    help = "Display the top N donors and stats"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--number',
                        action='store',
                        type=int,
                        default=10,
                        help='number of donors to display')

    def handle(self, *args, **kwargs):
        """Display the top n donors and their amounts."""

        n = kwargs['number']

        donors = Donation.objects.top_donors(n)
        for i, donor in enumerate(donors, start=1):
            self.stdout.write(ROW_FMT.format(n=i, name=donor.username,
                amount=donor.total_donations))
