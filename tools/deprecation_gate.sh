#!/bin/sh
# The deprecation gate's warning filter, in one place.
#
# The gate is the test suite run with deprecation warnings promoted to errors.
# It is what has caught every Django removal on this project a version before it
# landed, and it lives here rather than in .github/workflows/ci.yml so that CI
# and a developer run the *same* list. A second copy typed into the workflow
# would rot silently, because nothing compares the two.
#
# Usage -- run the gated suite locally:
#
#   docker compose run --rm -e PYTHONWARNINGS="$(tools/deprecation_gate.sh)" web \
#       python manage.py test --noinput --settings=sg101.settings.docker_test
#
# PYTHONWARNINGS rather than -W, and this is not a style choice: -W applies to
# the interpreter it is passed to and does not reach subprocesses, while
# PYTHONWARNINGS is inherited through the environment. core/tests/test_settings.py
# runs its assertions through a subprocess helper, which under -W sits outside
# the gate entirely.
#
# It also has to be passed *into the container* with `-e`. The suite runs under
# `docker compose run`, so a GitHub `env:` block would set this on the runner and
# never reach the interpreter that matters -- and an unbound gate is
# indistinguishable from a passing one. That failure has happened here before: a
# dotted `-W error::django.utils.deprecation.RemovedInDjango50Warning` printed
# one line to stderr, was discarded, and certified 813 green tests with the
# deprecation still in the tree.
#
# On the filter syntax:
#   * Order matters. Filters are applied with later entries taking precedence,
#     so the blanket `error::` rules come first and the ignores after.
#   * Ignore by MESSAGE, never by module. The module field is matched against the
#     frame a warning is *attributed* to after stacklevel, not the module that
#     raised it, so `ignore::DeprecationWarning:some_package` silently binds
#     nothing.
#   * The message is a literal prefix, not a regex -- warnings._setoption()
#     calls re.escape() on it -- so `utcnow()` needs no escaping. But the fields
#     are split on ':' and the filters on ',', so a message must be truncated
#     before either character appears.
#
# The list is derived from an unfiltered inventory after every dependency change:
#
#   docker compose run --rm web python -W default::DeprecationWarning \
#       -W default::PendingDeprecationWarning manage.py test --noinput \
#       --settings=sg101.settings.docker_test 2>&1 | grep Warning:
#
# An ignore is retired only when it is absent from that run, and every surviving
# ignore is re-proven by deleting it and watching the suite fail.

set -eu

# Both categories: Django re-parents its removal warnings from
# PendingDeprecationWarning to DeprecationWarning one release before the
# removal, so watching only one category means missing a release. That
# re-parenting has broken this gate four times.
FILTERS='error::DeprecationWarning,error::PendingDeprecationWarning'

# Ours, and deliberate. Django 5.0 deprecated the http:// that forms.URLField
# prepends to a bare domain; this project opted into https now by setting
# FORMS_URLFIELD_ASSUME_HTTPS, and that transitional setting announces its own
# removal. Retires at Django 6.0, when the setting goes away.
FILTERS="$FILTERS,ignore:The FORMS_URLFIELD_ASSUME_HTTPS transitional setting is deprecated:DeprecationWarning"

# repoze.timeago 0.5 calls datetime.utcnow(), deprecated in Python 3.12. Upstream
# stopped in 2011 and there is no newer release, so this ignore stays until the
# library is replaced -- recommended into Step 19, where the _NOW monkeypatch in
# core/templatetags/core_tags.py is the reason it is app work and not a bump.
FILTERS="$FILTERS,ignore:datetime.datetime.utcnow() is deprecated:DeprecationWarning"

printf '%s' "$FILTERS"
