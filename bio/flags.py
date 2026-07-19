"""
This module contains country flag data & functions.

"""
import functools
import io
import json
import os.path
import locale
import logging


# Read flag data from external JSON file:

FLAG_DATA = {}

datafile = os.path.join(os.path.split(__file__)[0], 'flag_data.json')

try:
    with io.open(datafile, 'r', encoding='utf-8') as fp:
        FLAG_DATA = json.load(fp)
except IOError:
    FLAG_DATA = {}
    logging.error("Could not load flag_data.json")

# Build a choices list for use with Django models, etc.
# The locale is set in order to sort the place names correctly:

locale.setlocale(locale.LC_ALL, '')

FLAG_CHOICES = sorted(FLAG_DATA.items(),
        key=functools.cmp_to_key(
            lambda lhs, rhs: locale.strcoll(lhs[1], rhs[1])))
