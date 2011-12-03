"""
The rate_limit_clear command is used to clear IP addresses out from our rate
limit protection database.

"""
from optparse import make_option
import re

from django.core.management.base import BaseCommand
import redis

IP_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


class Command(BaseCommand):
    help = """Remove IP addresses from the rate limit protection datastore."""
    option_list = list(BaseCommand.option_list) + [
        make_option("--purge", action="store_true",
            help="Purge all IP addresses"),
    ]

    def handle(self, *args, **kwargs):
        try:
            con = redis.Redis()

            # get all rate-limit keys
            keys = con.keys('rate-limit-*')

            # if purging, delete them all...
            if kwargs['purge']:
                if keys:
                    con.delete(*keys)
                return

            # otherwise delete the ones the user asked for
            ips = []
            for ip in args:
                if IP_RE.match(ip):
                    key = 'rate-limit-%s' % ip
                    if key in keys:
                        ips.append(key)
                    else:
                        self.stdout.write('%s not found\n' % ip)
                else:
                    self.stderr.write('invalid IP address %s\n' % ip)

            if ips:
                con.delete(*ips)

        except redis.RedisError, e:
            self.stderr.write('%s\n' % e)
