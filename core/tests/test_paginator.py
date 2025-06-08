import doctest
import unittest

from core import paginator

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(paginator))
    return tests
