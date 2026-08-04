"""
Django-tagging

Vendored from PyPI django-tagging 0.5.0, the final release -- upstream stopped
in 2018 and the package does not import on Django 4.0. It is kept under its
original package name so the `tagging` app label, its three migrations and the
tables they created all continue to match what is already applied.

Local changes, both mechanical:

  * models.py: `smart_text` -> `smart_str`. The name was removed in Django 4.0,
    where it had been a plain alias for `smart_str` since 3.0.
  * this file: dropped `default_app_config`, which Django detects automatically
    and removed in 4.1.

The package's own test suite is not vendored: it ships its own settings.py and
urls.py, and `manage.py test` would discover and fail it.

Only the `news` app uses this -- story tags, via `TagField`, `Tag`/`TaggedItem`
and the `tagging_tags` templatetags. Replacing it is scheduled separately; a
Postgres ArrayField is a candidate, since the generic-foreign-key machinery here
is sized for tagging any model and this site tags one.
"""
__version__ = '0.5.0'
__license__ = 'BSD License'

__author__ = 'Jonathan Buchanan'
__author_email__ = 'jonathan.buchanan@gmail.com'

__maintainer__ = 'Fantomas42'
__maintainer_email__ = 'fantomas42@gmail.com'

__url__ = 'https://github.com/Fantomas42/django-tagging'
