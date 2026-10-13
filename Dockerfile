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

# --- The account the application runs as -------------------------------------
# A code-execution bug in the application gets whatever the process has, and a
# root process is what most container escapes start from. Nothing here needs
# root: the ports are 8000 and above, and everything written at runtime is
# either a bind mount or this user's own home.
#
# A container user and a host user are matched by *numeric UID*, not by name, so
# this number is the contract with the VM: media/ and var/ on the host must be
# owned by it, which cutover-runbook B12 sets after B4's rsync. 1000 is the
# first ordinary account on Debian and Ubuntu, so it is almost certainly the
# administrator's own -- which keeps those directories manageable without sudo.
# A host where 1000 is taken by something else passes --build-arg APP_UID=.
#
# Docker Desktop on macOS translates bind-mount ownership and will accept
# almost anything here. The Linux VM will not, which is why CI -- ubuntu-latest,
# with real bind-mount semantics -- builds this image and checks it can write.
ARG APP_UID=1000
ARG APP_GID=1000
RUN set -eux; \
    groupadd --gid "$APP_GID" sg101; \
    useradd --uid "$APP_UID" --gid "$APP_GID" --create-home \
            --home-dir /home/sg101 --shell /usr/sbin/nologin sg101

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

# The two directories the application writes inside the image rather than onto a
# bind mount. sg101/logs is both: it is a mount point in production and a real
# directory in development, and it has to be writable either way.
RUN chown -R sg101:sg101 /app/sg101/logs /home/sg101

# Everything below runs as sg101. Declared after the build steps so those still
# run as root -- pip, collectstatic and the apt layers all write where this user
# cannot.
USER sg101

# No --access-logfile: Apache in front logs every request already, in the
# combined format fail2ban's filters are written against, and a second line per
# request in the container's stream would be the same record twice. --error-logfile
# stays, and the `gunicorn` entry in logging_config is what keeps it reaching
# anything at all.
#
# Workers come from GUNICORN_WORKERS, which docker-compose.prod.yml requires, so
# production runs a chosen number (.env.example says why it is what it is). The
# fallback, 2*CPU+1, is only for an image started some other way: on a 10-core
# laptop it is 21 workers and over 2 GB, far more than this site -- about 1
# request a second -- needs.
CMD ["sh", "-c", "exec gunicorn sg101.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers ${GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))} \
     --error-logfile -"]


# --- dev ---------------------------------------------------------------------
# The test suite and the debug toolbar, layered on the runtime image. The dev
# requirements pull the runtime ones through `-r`, but those are already
# installed by the layers above, so this resolves to the tools it adds.
# No COPY needed: the source, requirements file included, arrived above.
FROM prod AS dev

# Back to root, deliberately, and only here.
#
# Development bind-mounts the whole checkout over /app, so anything the
# container creates lands in the working tree owned by whoever the container
# runs as. Under Docker Desktop that ownership is translated and either choice
# works; on Linux a developer whose UID is not the one baked into the image
# would get files they cannot edit -- from makemigrations, from a test that
# writes, from pip installing into the tree.
#
# The reason for dropping root in production also does not apply: this stack
# publishes to localhost, carries the debug toolbar, and runs the test suite.
# What it protects against is not a threat it faces.
USER root

RUN pip install -r requirements_dev.txt

# The headless Chromium the browser tests drive, and the Debian libraries it
# needs (--with-deps runs apt-get, so this stays as root). --only-shell skips
# the full headed browser, which the tests never use.
#
# By default Playwright stores browsers under the installing user's home. A
# fixed path is found whichever user the container runs as, and it sits outside
# /app, where the bind mount would hide anything written under it.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps --only-shell chromium

# Development runs the auto-reloading server; compose overrides this per service
# anyway, but the target's own default should not be gunicorn.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
