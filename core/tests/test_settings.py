"""Tests for 12-factor env-var settings loading.

Configuration comes from environment variables. These verify the two properties
that matter:

  * a value set in the environment flows through to the Django setting, and
  * a missing REQUIRED variable (SECRET_KEY) makes the app refuse to start
    (ImproperlyConfigured) rather than booting with a bad/empty value.

Each case imports the settings in a fresh subprocess so we can control the
environment without disturbing the already-configured test process. DOTENV_PATH
points read_env() at a nonexistent file, so the environment we pass is the only
source of config.
"""
import copy
import importlib
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NO_DOTENV = os.path.join(ROOT, 'this-dotenv-does-not-exist.env')

# Accessing a setting forces the settings module -- and thus base.py's env-var
# reads -- to load.
SNIPPET = (
    "from django.conf import settings\n"
    "import sys\n"
    "sys.stdout.write('SECRET_KEY=' + settings.SECRET_KEY)\n"
)


def _run(env_overrides):
    """Load settings in a subprocess; return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'sg101.settings.docker_test'
    env['DOTENV_PATH'] = NO_DOTENV
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    proc = subprocess.Popen(
        [sys.executable, '-c', SNIPPET],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    return proc.returncode, out.decode('utf-8', 'replace'), err.decode('utf-8', 'replace')


class EnvVarSettingsTests(SimpleTestCase):

    def test_secret_key_read_from_environment(self):
        """A SECRET_KEY set in the environment reaches settings.SECRET_KEY."""
        code, out, err = _run({'SECRET_KEY': 'sentinel-from-env-12345'})
        self.assertEqual(code, 0, msg=err)
        self.assertIn('SECRET_KEY=sentinel-from-env-12345', out)

    def test_missing_required_var_fails_loudly(self):
        """With SECRET_KEY unset, importing settings raises ImproperlyConfigured."""
        code, out, err = _run({'SECRET_KEY': None})
        self.assertNotEqual(code, 0)
        self.assertIn('ImproperlyConfigured', err)
        self.assertIn('SECRET_KEY', err)


class SettingsImportIsolationTests(SimpleTestCase):
    """Importing a settings module must not reconfigure the running one.

    `from base import *` binds base's own mutable objects, so a module that
    edits MIDDLEWARE, INSTALLED_APPS or TEMPLATES in place edits them for
    whatever configuration is already live. Both `local` and `production` once
    did, and the suite imports both to read their LOGGING dicts, so local.py's
    insert spliced the debug toolbar's middleware into every test that ran after
    it -- harmless until debug-toolbar shipped a model, then 105 errors from an
    app the registry never saw. production.py's version edited TEMPLATES, which
    changed how every later test loaded templates and never failed anything.

    Both are covered because the property belongs to the whole package, not to
    whichever module currently happens to edit something.

    Each module is reloaded so the assertion faces a real import rather than
    sys.modules handing back a module some earlier test already ran.
    """
    MODULES = ['sg101.settings.local', 'sg101.settings.production']

    def live_settings(self):
        return (list(settings.MIDDLEWARE),
                list(settings.INSTALLED_APPS),
                copy.deepcopy(settings.TEMPLATES))

    def test_importing_deployment_settings_leaves_the_live_ones_alone(self):
        before = self.live_settings()
        for name in self.MODULES:
            with self.subTest(settings=name):
                sys.modules.pop(name, None)
                importlib.import_module(name)
                self.assertEqual(self.live_settings(), before)
