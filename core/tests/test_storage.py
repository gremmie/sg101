"""
JavaScript modules must import each other by their hashed names in production.

Production's ManifestStaticFilesStorage hashes every file name, and WhiteNoise
caches the hashed ones for good. A module that imported a sibling by its plain
name would load whatever copy the browser cached, so a deploy could pair a new
module with an old one. core.storage's subclass turns on Django's rewriting of
import specifiers; these tests check its output rather than trusting the flag.

The suite never runs this storage otherwise: the test settings use the plain
one, which accepts any name.
"""
import json
import os
import posixpath
import re
import shutil
import tempfile
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings


STORAGE = 'core.storage.ManifestStaticFilesStorage'

# The site's own modules, collected under the same prefix as in production.
SITE_MODULES = ('js/v3', os.path.join(settings.PROJECT_PATH, 'static', 'js', 'v3'))

# A relative specifier after `from`, or in a bare `import '…'`. Written
# independently of Django's patterns, so that a statement they skip -- one
# without its closing semicolon -- is still found here.
RELATIVE_SPECIFIER = re.compile(r"""\b(?:from|import)\s*['"](\.{1,2}/[^'"]+)['"]""")


def collect(source_dirs, backend=STORAGE):
    """Run collectstatic over source_dirs only; return (static_root, manifest).

    manifest maps each source name to its hashed name, as staticfiles.json
    records it.
    """
    static_root = tempfile.mkdtemp()
    with override_settings(
            STATIC_ROOT=static_root,
            STATICFILES_DIRS=source_dirs,
            STATICFILES_FINDERS=[
                'django.contrib.staticfiles.finders.FileSystemFinder'],
            STORAGES={
                'default': {
                    'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': backend},
            }):
        call_command('collectstatic', interactive=False, verbosity=0,
                     stdout=StringIO())
    with open(os.path.join(static_root, 'staticfiles.json')) as f:
        manifest = json.load(f)['paths']
    return static_root, manifest


def bad_imports(static_root, manifest):
    """Every relative import in a hashed module that is not a hashed file.

    Returns (module, specifier, reason) for each import that names an unhashed
    file, or a file collectstatic did not write.
    """
    hashed = set(manifest.values())
    found = []
    for module in sorted(hashed):
        if not module.endswith('.js'):
            continue
        with open(os.path.join(static_root, module)) as f:
            source = f.read()
        for specifier in RELATIVE_SPECIFIER.findall(source):
            target = posixpath.normpath(
                posixpath.join(posixpath.dirname(module), specifier))
            if not os.path.exists(os.path.join(static_root, target)):
                found.append((module, specifier, 'missing'))
            elif target not in hashed:
                found.append((module, specifier, 'unhashed'))
    return found


class ModuleImportHashingTests(SimpleTestCase):

    def setUp(self):
        self.source = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.source)

    def write(self, name, text):
        path = os.path.join(self.source, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(text)

    def collect_source(self):
        static_root, manifest = collect([self.source])
        self.addCleanup(shutil.rmtree, static_root)
        return static_root, manifest

    def write_tree(self, entry):
        self.write('m/a.js', 'export const a = 1;\n')
        self.write('m/b.js', 'export const b = 2;\n')
        self.write('m/sub/c.js', 'export const c = 3;\n')
        self.write('m/sub/entry.js', entry)

    def test_imports_and_reexports_name_hashed_files(self):
        self.write_tree(
            "import { c } from './c.js';\n"
            "import { b } from '../b.js';\n"
            "export { a } from '../a.js';\n")
        static_root, manifest = self.collect_source()

        self.assertEqual(bad_imports(static_root, manifest), [])
        with open(os.path.join(static_root, manifest['m/sub/entry.js'])) as f:
            entry = f.read()
        for source_name, specifier in [('m/sub/c.js', './'),
                                       ('m/b.js', '../'),
                                       ('m/a.js', '../')]:
            hashed_specifier = specifier + posixpath.basename(manifest[source_name])
            self.assertIn('"{}"'.format(hashed_specifier), entry)

    def test_an_import_without_its_semicolon_is_caught(self):
        """Django rewrites an import only when a semicolon ends it. Without
        one, the import keeps its plain name and collectstatic succeeds, so
        the page would load a stale copy in production with nothing failing."""
        self.write_tree(
            "import { b } from '../b.js'\n"
            "console.log(b);\n")
        static_root, manifest = self.collect_source()

        self.assertEqual(bad_imports(static_root, manifest),
                         [(manifest['m/sub/entry.js'], '../b.js', 'unhashed')])

    def test_a_missing_semicolon_before_another_import_fails_the_build(self):
        """Without the semicolon, the rewrite of the next `from` statement runs
        on across the line and names a file that does not exist. collectstatic
        refuses that, so the image build fails rather than the page."""
        self.write_tree(
            "import { b } from '../b.js'\n"
            "export { a } from '../a.js';\n")

        with self.assertRaisesRegex(ValueError, 'could not be found'):
            self.collect_source()

    def test_the_site_modules_import_only_hashed_files(self):
        static_root, manifest = collect([SITE_MODULES])
        self.addCleanup(shutil.rmtree, static_root)

        self.assertIn('js/v3/sg101.js', manifest)
        self.assertEqual(bad_imports(static_root, manifest), [])
