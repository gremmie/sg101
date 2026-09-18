# SG101 image: Python 3.12.
#
# The interpreter crossed from Python 2.7 to 3.7 at the Python 3 flip, then to
# 3.10 when Django 4.0 -- which needs 3.8+ -- came into range, and to 3.12 for
# the climb to Django 5.2. The Django pin advances rung by rung; the exact pins
# live in the requirements files, and this base image only fixes the Python
# minor.
#
# 3.12 is supported by Django 4.2 and by 5.2 alike, so the interpreter could
# move on its own with the Django pin untouched -- the same opening 3.10 gave
# when it was the one version shared by Django 3.2 and 5.2. Unlike that move,
# this one needed no dependency bumps at all.
#
# Five pins have no wheel for this interpreter and build from source here:
# mysqlclient, psycopg2, ftfy, simplejson and repoze.timeago. That is what the
# apt build dependencies below are for. Together they cost about 5s of an
# uncached build, two thirds of it psycopg2; only simplejson is new at 3.12,
# the other four built from source on 3.10 too.
#
# Two targets:
#
#   prod  the runtime pins and nothing else
#   dev   prod plus the test and debugging tools
#
# dev builds FROM prod, so the runtime layers are shared and the dev tools are
# one thin layer on top. Build one explicitly with --target; compose names `dev`
# for web/worker/beat.

FROM python:3.12 AS prod

# Don't buffer stdout/stderr (so logs show up immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- System build/runtime dependencies ---------------------------------------
#   default-libmysqlclient-dev : build mysqlclient (the 1.4.x pin has no wheel)
#   default-mysql-client       : the `mysql` CLI, to load the DB snapshot
#   libpq-dev                  : build psycopg2 from source (headers + pg_config)
#   pkg-config                 : mysqlclient's build finds libmysqlclient through it
# The two MySQL entries look like leftovers now that the site runs on PostgreSQL.
# They are not: converting a production snapshot loads the dump with the `mysql`
# CLI, and tools/pgloader/verify.py + verify_data.py then compare both engines
# through MySQLdb, which is what mysqlclient needs these headers to build. That
# comparison is the only thing that catches a conversion which silently shifted
# or dropped data, and it runs from this image. See the mysqlclient note in
# requirements.txt before removing either one.
# lxml and Pillow install from manylinux wheels on 3.12, so their C-library -dev
# headers (libxml2/libxslt, libjpeg/zlib/freetype) are not needed. Check that
# again after either pin moves: a version with no wheel for this interpreter
# falls back to an sdist build, and Pillow's will quietly succeed without
# libjpeg and produce a build that imports fine and cannot open a JPEG. `python
# -c "from PIL import features; print(features.check('jpg'))"` answers it.
# No psql CLI here on purpose: the postgres service image carries one matched to
# the server (`docker compose exec postgres psql ...`), so a second client here
# would only be a version to keep in step.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        default-mysql-client \
        libpq-dev \
        pkg-config; \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /app

# Install Python deps first so the layer caches across code changes. The editable
# git dep (django-elsewhere) is gone -- the fork is vendored into the repo now --
# so no `git` in the image and no `--src` shadowing workaround.
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# The LOGGING config writes to sg101/logs/*.log; make sure it exists even when
# the code isn't bind-mounted.
RUN mkdir -p /app/sg101/logs

# Copy the source (in dev this is shadowed by a bind mount from compose).
COPY . /app

EXPOSE 8000

# Collect the static files into the image rather than at container start, so a
# container comes up serving and the manifest cannot disagree with the code it
# was built from. collectstatic imports settings before it copies anything, so
# it needs a SECRET_KEY; this one never leaves the build step, and the running
# container reads the real one from the environment.
RUN SECRET_KEY=build-time-only \
    DJANGO_SETTINGS_MODULE=sg101.settings.production \
    python manage.py collectstatic --noinput

# Workers are sized at start from the CPUs the container actually gets, rather
# than baked in here: the image is built on a developer's machine and run on a
# VM with a different count. The usual starting point for sync workers is
# 2*CPU+1, which at this site's rate -- about 1 request a second, with a busiest
# measured minute near 8 -- is already far more concurrency than it needs.
CMD ["sh", "-c", "exec gunicorn sg101.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers ${GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))} \
     --access-logfile - --error-logfile -"]


# --- dev ---------------------------------------------------------------------
# The test suite and the debug toolbar, layered on the runtime image. The dev
# requirements pull the runtime ones through `-r`, but those are already
# installed by the layers above, so this resolves to the three tools it adds.
# No COPY needed: the source, requirements file included, arrived above.
FROM prod AS dev

RUN pip install -r requirements_dev.txt

# Development runs the auto-reloading server; compose overrides this per service
# anyway, but the target's own default should not be gunicorn.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
