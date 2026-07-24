"""Vendored copy of django-elsewhere (social network / IM / website profile links).

Vendored from Brian Neal's fork:
    https://github.com/gremmie/django-elsewhere @ c8c6f5e6
Original upstream (Leah Culver & Chris Drackett; formerly "Django-PSN", created
for Pownce):
    https://github.com/leah/django-elsewhere
Neither repository ships an explicit license file.

It used to be an editable git dependency. It was vendored into the repo during the
Python 3 interpreter flip because the fork is tiny, frozen upstream, and needed a
few Py3 patches -- and vendoring drops the editable-git-in-Docker machinery.

Changes from upstream:
  - Python 3: django.core.urlresolvers -> django.urls, __unicode__ -> __str__,
    dict.has_key() -> `in`.
  - Trimmed to what SG101 actually uses: models + admin + the default-network data
    + the static/ icons (referenced by SG101's bio/elsewhere_links templates). The
    fork's own views.py, urls.py, and templates/elsewhere/example.html were dropped
    (SG101 provides its own bio views/templates and never wired the app's URLs).

The app has no migrations (unchanged from upstream); like before, Django creates
its tables via run-syncdb, matching the tables already in the production database.
"""
