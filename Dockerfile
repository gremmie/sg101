# Legacy SG101 image: Python 2.7 / Django 1.9 (Step 1 of the modernization).
#
# This image lets us run the unmodified legacy stack on a modern Mac that can no
# longer run Python 2.7 natively. The base Python and Django pins advance rung by
# rung as we climb the LTS ladder; this is the very first rung.
#
# The official python:2.7 image still exists on Docker Hub but is frozen and
# based on Debian Buster, which is now end-of-life -- its package mirrors have
# moved to archive.debian.org, so we repoint apt there before installing the
# system libraries the C-extension Python packages need.

FROM python:2.7

# Don't buffer stdout/stderr (so logs show up immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# --- System build/runtime dependencies ---------------------------------------
# Buster is archived, so point apt at archive.debian.org and skip the (now gone)
# buster-updates suite and Valid-Until checks.
#   default-libmysqlclient-dev : build mysqlclient
#   libxml2-dev / libxslt1-dev : build lxml
#   libjpeg-dev / zlib1g-dev / libfreetype6-dev : build Pillow
#   default-mysql-client       : the `mysql` CLI, to load the DB snapshot
#   git                        : install the django-elsewhere editable git dep
RUN set -eux; \
    sed -i 's|http://deb.debian.org|http://archive.debian.org|g; \
            s|http://security.debian.org|http://archive.debian.org|g' \
            /etc/apt/sources.list; \
    sed -i '/buster-updates/d' /etc/apt/sources.list; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        default-mysql-client \
        libxml2-dev \
        libxslt1-dev \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        git; \
    rm -rf /var/lib/apt/lists/*

# Pin a pip/setuptools that still speaks Python 2.7 and can resolve the old pins.
RUN pip install --upgrade "pip<21" "setuptools<45" "wheel<0.34"

WORKDIR /app

# Install Python deps first so the layer caches across code changes.
# --src puts the editable git dep (django-elsewhere) OUTSIDE /app so the dev
# bind-mount of /app (see docker-compose.yml) doesn't shadow/erase it.
COPY requirements-docker.txt /app/requirements-docker.txt
RUN pip install --src=/usr/local/src -r requirements-docker.txt

# The legacy LOGGING config writes to sg101/logs/*.log; make sure it exists even
# when the code isn't bind-mounted.
RUN mkdir -p /app/sg101/logs

# Copy the source (in dev this is shadowed by a bind mount from compose).
COPY . /app

EXPOSE 8000

# Default: run the Django dev server. Compose overrides the command per service.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
