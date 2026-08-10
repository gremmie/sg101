"""donations_report.py

A management command to display donation statistics for a given year.

"""
import datetime
import decimal

from django.core.management.base import LabelCommand, CommandError
from django.db.models import Sum
from django.utils import timezone

from donations.models import Donation, in_month

ROW_FMT = '%10s %7s %7s'


class Command(LabelCommand):
    help = "Display donation statistics for a given year"
    args = "<year>"

    def handle_label(self, year, **kwargs):
        """Display donation statistics for a given year"""

        try:
            year = int(year)
        except ValueError:
            raise CommandError("invalid year")

        today = timezone.localdate()
        if year < 2011 or year > today.year:
            raise CommandError("invalid year")

        max_month = 12 if year != today.year else today.month

        self.stdout.write(ROW_FMT % ('Month', 'Gross', 'Net'))
        sep = ROW_FMT % ('-' * 10, '-' * 7, '-' * 7)
        self.stdout.write(sep)

        total_gross = decimal.Decimal()
        total_net = decimal.Decimal()

        for month in range(1, max_month + 1):
            r = in_month(Donation.objects, year, month).aggregate(
                    Sum('mc_gross'), Sum('mc_fee'))

            gross, fee = r['mc_gross__sum'], r['mc_fee__sum']

            gross = gross if gross else decimal.Decimal()
            fee = fee if fee else decimal.Decimal()

            net = gross - fee

            d = datetime.date(year=year, month=month, day=1)

            self.stdout.write(ROW_FMT % (d.strftime('%b %Y'), gross, net))

            total_gross += gross
            total_net += net

        self.stdout.write(sep)
        self.stdout.write(ROW_FMT % ('Total:', total_gross, total_net))
