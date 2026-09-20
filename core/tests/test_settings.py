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
from django.core.exceptions import ImproperlyConfigured
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


# Builds a toolbar against a bare HttpRequest and reports which panels came out
# enabled. No view runs and no query is issued, which is the point: the panel
# set is a property of the configuration, so reading it must not depend on the
# database being populated.
TOOLBAR_WIRING_SNIPPET = (
    "import json\n"
    "import sys\n"
    "import django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "from django.http import HttpRequest\n"
    "from debug_toolbar.toolbar import DebugToolbar\n"
    "request = HttpRequest()\n"
    "request.META['REMOTE_ADDR'] = '127.0.0.1'\n"
    "request.path = '/'\n"
    "toolbar = DebugToolbar(request, lambda r: None)\n"
    "sys.stdout.write(json.dumps({\n"
    "    'first_middleware': settings.MIDDLEWARE[0],\n"
    "    'installed': 'debug_toolbar' in settings.INSTALLED_APPS,\n"
    "    'disabled_panels': sorted(\n"
    "        settings.DEBUG_TOOLBAR_CONFIG.get('DISABLE_PANELS', [])),\n"
    "    'enabled_panels': sorted(p.panel_id for p in toolbar.enabled_panels),\n"
    "    'all_panels': sorted(p.panel_id for p in toolbar.panels),\n"
    "}))\n"
)

REDIRECTS_PANEL = 'debug_toolbar.panels.redirects.RedirectsPanel'
REDIRECTS_PANEL_ID = 'RedirectsPanel'


class DebugToolbarWiringTests(SimpleTestCase):
    """How the debug toolbar is wired into the dev settings.

    Properties the suite cannot see for itself: it runs under `test`, which
    installs no toolbar at all. They are read out of the dev module in a
    subprocess, for the reason the whole file uses one -- importing a deployment
    module here would splice its middleware into the running configuration.

    The middleware position is load-bearing and was measured rather than argued.
    From index 1 the toolbar sits *inside* CommonMiddleware, so an APPEND_SLASH
    request records as the inner 404 it really is and the 301 never reaches the
    history panel; from index 0 HistoryPanel records the 301. That only holds
    with RedirectsPanel off, because that panel answers the redirect with a 200
    interstitial rather than passing it through -- so position and panel are one
    decision.

    The panel is read as the toolbar itself resolves it, not out of the config
    dict alone. DISABLE_PANELS does not remove a panel from the list; it decides
    which panels come out enabled, and only an enabled panel intercepts
    anything.

    ProfilingPanel is asserted enabled for the same reason RedirectsPanel is
    asserted disabled: the toolbar disables both by default, so an empty
    DISABLE_PANELS does not mean "leave the defaults alone" -- it means "turn
    both on". Naming both pins the setting from both directions, and mutating
    the configuration shows why both are needed:

      * toolbar moved to index 1 -> the middleware case alone. The panels are
        unaffected by where the middleware sits.
      * DISABLE_PANELS emptied -> the config case, and RedirectsPanel comes out
        enabled.
      * the DISABLE_PANELS key misspelled -> the config case, and
        *ProfilingPanel* is lost. RedirectsPanel stays off, because the
        toolbar's own default already disables it -- so the typo is invisible
        from RedirectsPanel's side and only the ProfilingPanel assertion
        catches it.
      * ProfilingPanel added to DISABLE_PANELS -> the same two.

    So no single assertion here covers the setting; the pair does.

    Nothing here covers SHOW_TOOLBAR_CALLBACK, which only affects whether the
    toolbar is visible.
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

    def test_redirects_panel_is_the_only_one_turned_off(self):
        self.assertEqual(self.toolbar_wiring()['disabled_panels'],
                         [REDIRECTS_PANEL])

    def test_redirects_panel_is_not_enabled_on_the_toolbar(self):
        """Off where it counts: the panel set the toolbar actually consults."""
        wiring = self.toolbar_wiring()
        self.assertIn(REDIRECTS_PANEL_ID, wiring['all_panels'])
        self.assertNotIn(REDIRECTS_PANEL_ID, wiring['enabled_panels'])

    def test_the_panels_that_do_its_job_stay_enabled(self):
        """HistoryPanel replaces RedirectsPanel; ProfilingPanel is wanted."""
        enabled = self.toolbar_wiring()['enabled_panels']
        self.assertIn('HistoryPanel', enabled)
        self.assertIn('ProfilingPanel', enabled)


DEPLOYED_LOGGING_SNIPPET = (
    "import json\n"
    "import sys\n"
    "from django.conf import settings\n"
    "sys.stdout.write(json.dumps(settings.LOGGING, default=str))\n"
)

# The differences between the two deployments' logging, as sg101/settings/
# logging_config.py's TARGETS table expresses them. Spelled out here rather than
# imported from the helper: a test that reads its expectations out of the thing
# under test cannot fail when that thing changes.
EXPECTED_LOGGING_DIFFERENCES = {
    'disable_existing_loggers',
    'handlers.auth.level',
    'handlers.email.level',
    'handlers.search.level',
    'handlers.turnstile.level',
    'loggers.auth.level',
    'loggers.django.request',
    'root.level',
}


class DeployedLoggingTests(SimpleTestCase):
    """What the two deployments' LOGGING may and may not disagree about.

    Both dicts come from logging_config.for_target(). That is the point of the
    helper -- they ran to ~145 near-identical lines each, and adding a logger
    meant editing both by hand.

    Each module is loaded in a subprocess and its *own* LOGGING is read, for the
    reason the search-logging case above gives: reading the module's value is
    what makes a deployment module that quietly stopped using the shared helper
    fail here, rather than pass on the helper's own output.
    """

    def deployed_logging(self, module):
        code, out, err = _run({'DJANGO_SETTINGS_MODULE': module,
                               'SECRET_KEY': 'x'},
                              snippet=DEPLOYED_LOGGING_SNIPPET)
        self.assertEqual(code, 0, msg=err)
        return json.loads(out)

    def differences(self):
        """Every leaf key where the two deployed dicts disagree."""
        def walk(a, b, path=''):
            found = set()
            if isinstance(a, dict) and isinstance(b, dict):
                for key in set(a) | set(b):
                    here = '{}.{}'.format(path, key) if path else key
                    if key not in a or key not in b:
                        found.add(here)
                    else:
                        found |= walk(a[key], b[key], here)
            elif a != b:
                found.add(path)
            return found

        return walk(self.deployed_logging('sg101.settings.dev'),
                    self.deployed_logging('sg101.settings.production'))

    def test_the_deployments_differ_only_where_intended(self):
        """A new logger added to one module and not the other lands here."""
        self.assertEqual(self.differences(), EXPECTED_LOGGING_DIFFERENCES)

    def test_production_is_the_quieter_of_the_two(self):
        """The direction of the level differences, which the set above cannot say."""
        dev = self.deployed_logging('sg101.settings.dev')
        production = self.deployed_logging('sg101.settings.production')
        for app_log in ('auth', 'search', 'email', 'turnstile'):
            with self.subTest(handler=app_log):
                self.assertEqual(dev['handlers'][app_log]['level'], 'DEBUG')
                self.assertEqual(production['handlers'][app_log]['level'], 'INFO')
        self.assertEqual(dev['root']['level'], 'DEBUG')
        self.assertEqual(production['root']['level'], 'INFO')

    def test_only_production_mails_request_errors(self):
        self.assertNotIn('django.request',
                         self.deployed_logging('sg101.settings.dev')['loggers'])
        self.assertEqual(
            self.deployed_logging('sg101.settings.production')
                ['loggers']['django.request']['handlers'],
            ['mail_admins'])

    def test_an_unknown_target_fails_loudly(self):
        from sg101.settings import logging_config
        with self.assertRaises(ImproperlyConfigured):
            logging_config.for_target('staging', log_dir='/tmp')


DEPLOYED_BACKENDS_SNIPPET = (
    "import json\n"
    "import sys\n"
    "from django.conf import settings\n"
    "sys.stdout.write(json.dumps({\n"
    "    'engine': settings.DATABASES['default']['ENGINE'],\n"
    "    'options': settings.DATABASES['default'].get('OPTIONS', {}),\n"
    "    'cache': settings.CACHES['default'].get('LOCATION', ''),\n"
    "    'has_socket_setting': hasattr(settings, 'REDIS_UNIX_SOCKET'),\n"
    "    'broker': settings.CELERY_BROKER_URL,\n"
    "}))\n"
)


REDIS_SNIPPET = (
    "import json\n"
    "import sys\n"
    "from django.conf import settings\n"
    "sys.stdout.write(json.dumps({\n"
    "    'has_socket_setting': hasattr(settings, 'REDIS_UNIX_SOCKET'),\n"
    "    'broker': settings.CELERY_BROKER_URL,\n"
    "}))\n"
)

# Every module in the package, not only the two that deploy: base is where the
# socket default lived and test carried its own copy. Neither names a database,
# so neither can be read with DEPLOYED_BACKENDS_SNIPPET.
ALL_SETTINGS = ['sg101.settings.base', 'sg101.settings.test',
                'sg101.settings.docker_test'] + DEPLOYMENT_SETTINGS


class DeployedBackendsTests(SimpleTestCase):
    """Which database and cache the deployed modules actually name.

    Neither is exercised by the suite, which runs under `test` against its own
    database and a locmem cache, so the only way to cover "production connects
    to the things that exist" is to read what the module configures.

    Both modules went five Django versions naming MySQL over a unix socket on a
    host that no longer runs either, which nothing noticed because nothing
    loaded them.
    """

    def deployed_backends(self, module, **env):
        code, out, err = _run(dict({'DJANGO_SETTINGS_MODULE': module,
                                    'SECRET_KEY': 'x'}, **env),
                              snippet=DEPLOYED_BACKENDS_SNIPPET)
        self.assertEqual(code, 0, msg=err)
        return json.loads(out)

    def test_both_deployments_read_the_engine_from_the_environment(self):
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                backends = self.deployed_backends(name, DB_ENGINE='postgresql')
                self.assertEqual(backends['engine'],
                                 'django.db.backends.postgresql')

    def test_no_deployment_hardcodes_a_unix_socket(self):
        """A socket does not cross a container boundary, so naming one is a bug.

        The engine's own OPTIONS are checked rather than the whole dict: this is
        where `unix_socket` lived, and where a copy of the old configuration
        would land again. The cache is checked in the same case because it grew
        the same defect from the same cause; only production names one, since
        dev inherits base's locmem cache and a locmem cache has no LOCATION.
        """
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                backends = self.deployed_backends(name, DB_ENGINE='postgresql')
                self.assertNotIn('unix_socket', backends['options'])
                self.assertFalse(backends['cache'].startswith('unix://'),
                                 msg=backends['cache'])

    def test_no_deployment_reaches_redis_through_a_socket(self):
        """Redis is a separate service, and a socket does not cross a container.

        base.py used to default REDIS_UNIX_SOCKET to jaguar's path and point the
        broker URL at it, so every container module had to switch it back off by
        hand -- the dead architecture was the default and the live ones were the
        exceptions. The setting is gone rather than inverted: with nothing able
        to supply a socket, the branch that consumed it was unreachable.

        Asserted as absence, not falsity, because a falsy value is what the old
        explicit nulls looked like.
        """
        for name in DEPLOYMENT_SETTINGS:
            with self.subTest(settings=name):
                backends = self.deployed_backends(name, DB_ENGINE='postgresql')
                self.assertFalse(backends['has_socket_setting'],
                                 msg='REDIS_UNIX_SOCKET is back')
                self.assertNotIn('socket', backends['broker'])

    def test_every_settings_module_reaches_redis_over_tcp(self):
        """Including base and test, which no deployment loads on its own.

        base.py is where the socket default lived, and settings/test.py carried
        its own copy for a bare-metal run that no longer exists. Neither is in
        DEPLOYMENT_SETTINGS, so the inversion would have gone uncovered exactly
        where it was made.
        """
        for name in ALL_SETTINGS:
            with self.subTest(settings=name):
                code, out, err = _run({'DJANGO_SETTINGS_MODULE': name,
                                       'SECRET_KEY': 'x'},
                                      snippet=REDIS_SNIPPET)
                self.assertEqual(code, 0, msg=err)
                config = json.loads(out)
                self.assertFalse(config['has_socket_setting'],
                                 msg='REDIS_UNIX_SOCKET is back')
                self.assertTrue(config['broker'].startswith('redis://'),
                                msg=config['broker'])

    def test_production_broker_is_its_own_redis_database(self):
        """db 0 is kept state and db 2 the cache; the broker is db 1."""
        backends = self.deployed_backends('sg101.settings.production',
                                          DB_ENGINE='postgresql',
                                          REDIS_HOST='redis')
        self.assertEqual(backends['broker'], 'redis://redis:6379/1')


DEPLOYED_STATIC_SNIPPET = (
    "import json\n"
    "import sys\n"
    "from django.conf import settings\n"
    "sys.stdout.write(json.dumps({\n"
    "    'middleware': list(settings.MIDDLEWARE),\n"
    "    'static_root': settings.STATIC_ROOT,\n"
    "    'proxy_ssl_header': settings.SECURE_PROXY_SSL_HEADER,\n"
    "    'ssl_redirect': settings.SECURE_SSL_REDIRECT,\n"
    "    'hsts_seconds': settings.SECURE_HSTS_SECONDS,\n"
    "    'hsts_subdomains': settings.SECURE_HSTS_INCLUDE_SUBDOMAINS,\n"
    "    'hsts_preload': settings.SECURE_HSTS_PRELOAD,\n"
    "    'staticfiles_backend': settings.STORAGES['staticfiles']['BACKEND'],\n"
    "}))\n"
)

SECURITY_MIDDLEWARE = 'django.middleware.security.SecurityMiddleware'
WHITENOISE_MIDDLEWARE = 'whitenoise.middleware.WhiteNoiseMiddleware'
REAL_CLIENT_IP_MIDDLEWARE = 'core.middleware.RealClientIP'


class ProductionStaticAndSecurityTests(SimpleTestCase):
    """How production serves static files, and what it tells the browser.

    None of this is exercised by the suite: it runs under `test`, which serves
    no static files and sets no security headers. Read out of the production
    module in a subprocess, like the rest of this file.
    """

    def production_settings(self):
        code, out, err = _run({'DJANGO_SETTINGS_MODULE': 'sg101.settings.production',
                               'SECRET_KEY': 'x'},
                              snippet=DEPLOYED_STATIC_SNIPPET)
        self.assertEqual(code, 0, msg=err)
        return json.loads(out)

    def test_whitenoise_sits_directly_after_the_security_middleware(self):
        """Order is the point: SecurityMiddleware's headers must still reach
        the responses WhiteNoise serves, and WhiteNoise must come before
        anything that would otherwise handle a static URL."""
        middleware = self.production_settings()['middleware']
        self.assertEqual(middleware[1], SECURITY_MIDDLEWARE)
        self.assertEqual(middleware[2], WHITENOISE_MIDDLEWARE)

    def test_the_client_address_is_corrected_before_anything_reads_it(self):
        """REMOTE_ADDR is the proxy until this runs, and six applications
        record what it says. First, so that no middleware or view added later
        can read the address before it is the client's."""
        middleware = self.production_settings()['middleware']
        self.assertEqual(middleware[0], REAL_CLIENT_IP_MIDDLEWARE)

    def test_static_root_is_not_the_test_directory(self):
        """base.py's value is a /tmp path meant for the suite; shipping it
        would put collectstatic's output somewhere the system may clear."""
        static_root = self.production_settings()['static_root']
        self.assertFalse(static_root.startswith('/tmp'), msg=static_root)
        self.assertTrue(static_root.endswith('static_root'), msg=static_root)

    def test_the_scheme_is_taken_from_the_proxy(self):
        """TLS is terminated ahead of the application, so without this every
        request looks insecure to Django."""
        self.assertEqual(self.production_settings()['proxy_ssl_header'],
                         ['HTTP_X_FORWARDED_PROTO', 'https'])

    def test_https_is_enforced(self):
        """Plain HTTP is redirected, and browsers are told to remember that.

        The redirect is only safe because the proxy sets X-Forwarded-Proto on
        every request it forwards; without it Django sees every request as
        insecure and redirects it to itself.

        HSTS is the week the old host sent, set here rather than in the proxy
        so there is one header with one value. It stays off subdomains and out
        of the preload list: browsers cache both for the full duration, and
        other hosts under this domain are not this application's to promise.
        """
        settings_read = self.production_settings()
        self.assertTrue(settings_read['ssl_redirect'])
        self.assertEqual(settings_read['hsts_seconds'], 604800)
        self.assertFalse(settings_read['hsts_subdomains'])
        self.assertFalse(settings_read['hsts_preload'])

    def test_static_files_are_served_from_a_manifest(self):
        """The hashed names are what let WhiteNoise mark assets immutable."""
        self.assertEqual(
            self.production_settings()['staticfiles_backend'],
            'django.contrib.staticfiles.storage.ManifestStaticFilesStorage')
