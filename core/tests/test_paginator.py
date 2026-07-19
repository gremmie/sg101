import doctest
import unittest

from core import paginator

def load_tests(loader, tests, ignore):
    # IGNORE_EXCEPTION_DETAIL: Python 3 prints fully-qualified exception names
    # (django.core.paginator.EmptyPage) where the doctests expect the bare name
    # (EmptyPage); this flag matches on the exception type alone.
    tests.addTests(doctest.DocTestSuite(
        paginator, optionflags=doctest.IGNORE_EXCEPTION_DETAIL))
    return tests
