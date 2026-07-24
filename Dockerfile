# SG101 image: Python 3.7 / Django 3.2.
#
# The interpreter crossed from Python 2.7 to 3.7 back at the Python 3 flip; the
# Django pin then keeps advancing rung by rung as we climb the LTS ladder (now on
# 3.2 LTS). The exact pins live in the requirements files -- this base image only
# fixes the Python minor.
#
# python:3.7 is EOL and frozen on Docker Hub (Debian Bullseye based). If a fresh
# build ever can't reach Bullseye's apt mirrors, they've moved to
# archive.debian.org -- repoint apt there (git history has the Buster recipe from
# the Python 2.7 image this replaced).

FROM python:3.7

# Don't buffer stdout/stderr (so logs show up immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- System build/runtime dependencies ---------------------------------------
#   default-libmysqlclient-dev : build mysqlclient (the 1.4.x pin has no wheel)
#   default-mysql-client       : the `mysql` CLI, to load the DB snapshot
#   pkg-config                 : mysqlclient's build finds libmysqlclient through it
# lxml and Pillow now install from manylinux wheels on Py3.7, so their C-library
# -dev headers (libxml2/libxslt, libjpeg/zlib/freetype) are no longer needed.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        default-mysql-client \
        pkg-config; \
    rm -rf /var/lib/apt/lists/*

# pip 24.1+ drops Python 3.7; cap it so `--upgrade` stays on the 3.7 line.
RUN pip install --upgrade "pip<24.1"

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
