# SG101 image: Python 3.10.
#
# The interpreter crossed from Python 2.7 to 3.7 at the Python 3 flip, and from
# 3.7 to 3.10 when Django 4.0 -- which needs 3.8+ -- came into range. The Django
# pin then keeps advancing rung by rung as we climb the LTS ladder. The exact
# pins live in the requirements files; this base image only fixes the Python
# minor.
#
# 3.10 is the waypoint rather than the 3.8 minimum because it is the only version
# supported by Django 3.2 *and* by everything through 5.2, which is what let the
# interpreter move by itself with the Django pin untouched.

FROM python:3.10

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
# lxml and Pillow install from manylinux wheels on 3.10, so their C-library -dev
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
COPY requirements-docker.txt /app/requirements-docker.txt
RUN pip install -r requirements-docker.txt

# The LOGGING config writes to sg101/logs/*.log; make sure it exists even when
# the code isn't bind-mounted.
RUN mkdir -p /app/sg101/logs

# Copy the source (in dev this is shadowed by a bind mount from compose).
COPY . /app

EXPOSE 8000

# Default: run the Django dev server. Compose overrides the command per service.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
