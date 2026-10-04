"""
Every static file a template names must exist as a file.

Production serves static files through ManifestStaticFilesStorage, which knows
only the files collectstatic copied; a template naming anything else -- a
missing file, or a directory -- is a 500 there. The test settings use the plain
storage, which accepts any name, so a page can pass every view test and still
fail in production. This reads the names straight from the templates instead.

Only literal names can be checked this way. `{% static src %}` and its kin take
the name from a variable; the third-party script and stylesheet tags read theirs
from GPP_THIRD_PARTY_JS and GPP_THIRD_PARTY_CSS, which are checked here too.
"""
import os
import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template import engines
from django.test import SimpleTestCase


STATIC_TAG = re.compile(r"""\{%\s*static\s+(['"])(.+?)\1""")


def template_static_names():
    """Yield (template path, static name) for every literal {% static %}."""
    for template_dir in engines['django'].template_dirs:
        for dirpath, _, filenames in os.walk(template_dir):
            for filename in filenames:
                if not filename.endswith('.html'):
                    continue
                path = os.path.join(dirpath, filename)
                with open(path, encoding='utf-8') as fp:
                    for match in STATIC_TAG.finditer(fp.read()):
                        yield path, match.group(2)


def third_party_static_names():
    """Yield (setting, static name) for each local third-party path."""
    for setting in ('GPP_THIRD_PARTY_JS', 'GPP_THIRD_PARTY_CSS'):
        for paths in getattr(settings, setting).values():
            for path in paths:
                if not path.startswith('http'):
                    yield setting, path


class StaticNamesTestCase(SimpleTestCase):

    def assert_all_files(self, names):
        missing = []
        for source, name in names:
            path = finders.find(name)
            if not path or not os.path.isfile(path):
                missing.append('{}: {}'.format(source, name))
        self.assertEqual(missing, [])

    def test_template_names_are_files(self):
        names = list(template_static_names())
        # Guard against the walk silently finding nothing.
        self.assertGreater(len(names), 50)
        self.assert_all_files(names)

    def test_third_party_names_are_files(self):
        self.assert_all_files(third_party_static_names())
