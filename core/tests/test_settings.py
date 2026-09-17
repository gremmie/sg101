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
import json
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


# The two modules the site actually deploys. Both are asserted about below, for
# the same reason each time: what they configure is never exercised by the suite,
# which runs under `test`.
DEPLOYMENT_SETTINGS = ['sg101.settings.dev', 'sg101.settings.production']

SEARCH_LOGGING_SNIPPET = (
    "import json\n"
    "import sys\n"
    "from django.conf import settings\n"
    "config = settings.LOGGING\n"
    "sys.stdout.write(json.dumps({\n"
    "    'handler': config['handlers']['search'],\n"
    "    'logger': config['loggers']['search'],\n"
    "}))\n"
)


def _run(env_overrides, snippet=SNIPPET):
    """Load settings in a subprocess; return (returncode, stdout, stderr).

    snippet defaults to reading SECRET_KEY back out; pass another to read a
    different setting, since any attribute access is enough to force the
    settings module -- and base.py's env-var reads -- to load.
    """
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'sg101.settings.docker_test'
    env['DOTENV_PATH'] = NO_DOTENV
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    proc = subprocess.Popen(
        [sys.executable, '-c', snippet],
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


class UserPhotoUploadSettingsTests(SimpleTestCase):
    """The upload destination and the user-content whitelist have to agree.

    USER_IMAGES_SOURCES lists the hosts members may reference in posts, enforced
    by core.html.image_check() at submit time. Uploading a photo is only useful
    because the detail page hands the member markup to paste into a post, so an
    upload host missing from that list produces a photo that uploads, appears in
    its gallery, and cannot be posted. Settings refuse to load instead.
    """

    def test_defaults_reproduce_the_previous_hardcoded_values(self):
        """With nothing set, the env-backed settings match what they replaced."""
        code, out, err = _run({
            'SECRET_KEY': 'x',
            'USER_PHOTOS_BUCKET': None,
            'USER_PHOTOS_BASE_URL': None,
            'USER_PHOTOS_REGION': None,
        }, snippet=(
            "from django.conf import settings\n"
            "import sys\n"
            "sys.stdout.write('|'.join([settings.USER_PHOTOS_BUCKET,\n"
            "                           settings.USER_PHOTOS_BASE_URL,\n"
            "                           settings.USER_PHOTOS_REGION]))\n"
        ))
        self.assertEqual(code, 0, msg=err)
        self.assertEqual(
            out.strip(),
            'sg101.user.photos|https://s3-us-west-1.amazonaws.com|us-west-1')

    def test_all_three_are_read_from_the_environment(self):
        """Each of the three overrides reaches its setting.

        The base URL override uses a host that is already whitelisted, so this
        exercises the override rather than the guard below.
        """
        code, out, err = _run({
            'SECRET_KEY': 'x',
            'USER_PHOTOS_BUCKET': 'bucket-from-env',
            'USER_PHOTOS_BASE_URL': 'https://s3.amazonaws.com',
            'USER_PHOTOS_REGION': 'region-from-env',
        }, snippet=(
            "from django.conf import settings\n"
            "import sys\n"
            "sys.stdout.write('|'.join([settings.USER_PHOTOS_BUCKET,\n"
            "                           settings.USER_PHOTOS_BASE_URL,\n"
            "                           settings.USER_PHOTOS_REGION]))\n"
        ))
        self.assertEqual(code, 0, msg=err)
        self.assertEqual(
            out.strip(),
            'bucket-from-env|https://s3.amazonaws.com|region-from-env')

    def test_upload_host_outside_the_whitelist_refuses_to_boot(self):
        code, out, err = _run({
            'SECRET_KEY': 'x',
            'USER_PHOTOS_BASE_URL': 'https://elsewhere.example.com',
        })
        self.assertNotEqual(code, 0)
        self.assertIn('ImproperlyConfigured', err)
        self.assertIn('USER_IMAGES_SOURCES', err)
        self.assertIn('elsewhere.example.com', err)


class SettingsImportIsolationTests(SimpleTestCase):
    """Importing a settings module must not reconfigure the running one.

    `from base import *` binds base's own mutable objects, so a module that
    edits MIDDLEWARE, INSTALLED_APPS or TEMPLATES in place edits them for
    whatever configuration is already live. Both deployment modules once did:
    an insert spliced the debug toolbar's middleware into every test that ran
    after the import -- harmless until debug-toolbar shipped a model, then 105
    errors from an app the registry never saw. production.py's version edited
    TEMPLATES, which changed how every later test loaded templates and never
    failed anything.

    No test reads a value out of these modules any more -- the ones that need
    what a deployment module configures load it in a subprocess. This case
    imports them because the import is the thing under test.

    Both are covered because the property belongs to the whole package, not to
    whichever module currently happens to edit something.

    Each module is reloaded so the assertion faces a real import rather than
    sys.modules handing back a module some earlier test already ran.
    """

    def live_settings(self):
        return (list(settings.MIDDLEWARE),
                list(settings.INSTALLED_APPS),
                copy.deepcopy(settings.TEMPLATES))

    def test_importing_deployment_settings_leaves_the_live_ones_alone(self):
        before = self.live_settings()
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                sys.modules.pop(name, None)
                importlib.import_module(name)
                self.assertEqual(self.live_settings(), before)


class SearchLoggingSettingsTests(SimpleTestCase):
    """Where the deployed configuration sends search records.

    The suite runs under `test`, which configures no search logger, so the only
    way to cover "search logging lands in its own file and nowhere else" is to
    read the configuration the site deploys.

    Each module is loaded in a subprocess rather than imported, and what is read
    is that module's own LOGGING. Both matter: the subprocess keeps a settings
    module out of the running process, and reading the module's own value is
    what makes a deployment module that quietly stops using a shared
    configuration fail here rather than pass on the shared one.
    """

    def search_logging(self, module):
        """The `search` handler and logger as `module` configures them."""
        code, out, err = _run({'DJANGO_SETTINGS_MODULE': module,
                               'SECRET_KEY': 'x'},
                              snippet=SEARCH_LOGGING_SNIPPET)
        # Checked before the output is parsed: a subprocess that never loaded
        # settings would otherwise be asserted about vacuously.
        self.assertEqual(code, 0, msg=err)
        return json.loads(out)

    def test_search_gets_its_own_file(self):
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                handler = self.search_logging(name)['handler']
                self.assertTrue(handler['filename'].endswith('search.log'))

    def test_search_does_not_reach_the_site_log(self):
        # propagate False is what keeps the root logger, and so sg101.log,
        # from collecting a copy of every search.
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                logger_config = self.search_logging(name)['logger']
                self.assertFalse(logger_config['propagate'])
                self.assertEqual(logger_config['handlers'], ['search'])


TOOLBAR_WIRING_SNIPPET = (
    "import json\n"
    "import sys\n"
    "import django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "from django.test import Client\n"
    "sys.stdout.write(json.dumps({\n"
    "    'first_middleware': settings.MIDDLEWARE[0],\n"
    "    'installed': 'debug_toolbar' in settings.INSTALLED_APPS,\n"
    "    'disabled_panels': sorted(\n"
    "        settings.DEBUG_TOOLBAR_CONFIG.get('DISABLE_PANELS', [])),\n"
    "    'append_slash_status': Client().get('/forums').status_code,\n"
    "}))\n"
)

REDIRECTS_PANEL = 'debug_toolbar.panels.redirects.RedirectsPanel'


class DebugToolbarWiringTests(SimpleTestCase):
    """How the debug toolbar is wired into the dev settings.

    Three properties, none of which the suite can see for itself: it runs under
    `test`, which installs no toolbar at all. They are read out of the dev
    module in a subprocess, for the reason the whole file uses one -- importing
    a deployment module here would splice its middleware into the running
    configuration.

    The position is load-bearing and was measured rather than argued. From
    index 1 the toolbar sits *inside* CommonMiddleware, so an APPEND_SLASH
    request records as the inner 404 it really is and the 301 never reaches the
    history panel. From index 0 it records the 301 -- but only with
    RedirectsPanel off, because that panel answers the redirect with a 200
    interstitial instead of passing it through.

    What each case actually catches, from mutating this configuration and
    watching these tests:

      * toolbar moved to index 1  -> only the middleware assertion fails. The
        redirect still answers 301 from index 1, so the observable below does
        *not* cover the position.
      * RedirectsPanel re-enabled -> the panel assertion and the redirect both
        fail (200, the interstitial).
      * toolbar dropped from INSTALLED_APPS -> all three, because the
        subprocess dies on the app-registry mismatch described above.

    So the position has exactly one guard and the panel has two; nothing here
    covers SHOW_TOOLBAR_CALLBACK, which only affects whether the toolbar is
    visible.
    """

    def toolbar_wiring(self):
        code, out, err = _run({'DJANGO_SETTINGS_MODULE': 'sg101.settings.dev',
                               'SECRET_KEY': 'x'},
                              snippet=TOOLBAR_WIRING_SNIPPET)
        # Checked before parsing: a subprocess that never loaded settings would
        # otherwise be asserted about vacuously.
        self.assertEqual(code, 0, msg=err)
        return json.loads(out)

    def test_toolbar_is_installed_and_first_in_middleware(self):
        wiring = self.toolbar_wiring()
        self.assertTrue(wiring['installed'])
        self.assertEqual(wiring['first_middleware'],
                         'debug_toolbar.middleware.DebugToolbarMiddleware')

    def test_redirects_panel_is_disabled(self):
        self.assertEqual(self.toolbar_wiring()['disabled_panels'],
                         [REDIRECTS_PANEL])

    def test_append_slash_redirect_is_not_intercepted(self):
        """The observable the position was chosen on: a 301, not a 200.

        /forums resolves only with its trailing slash, so CommonMiddleware
        answers the request itself and no view -- and no database -- is
        reached. A 200 here is the RedirectsPanel interstitial.
        """
        self.assertEqual(self.toolbar_wiring()['append_slash_status'], 301)
