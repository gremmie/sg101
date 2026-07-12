# Rough Idea: Modernizing SG101

**Project name:** Modernizing SG101
**Date:** 2026-07-04
**Working branch (hg):** `modernize`

## Initial Concept

I want to develop a plan to modernize the SG101 codebase, which is behind on
many Django versions and is still on Python 2.7. I created a branch in hg called
`modernize` where I have started this work.

My plan was to:

1. Increase unit test coverage.
2. Update Django one version at a time, until the point where I am required to
   migrate to Python 3.
3. Migrate to Python 3.
4. Continue updating Django versions.

I also have a parallel problem: the code is hosted on an Ubuntu 14.04.6 LTS
server, which is very out of date. I'd like to explore more modern hosting
options and not have to maintain a separate dedicated server.

## Known Starting State (observed 2026-07-04)

- Currently on **Django 1.9.13**, Python 2.7.
- Dependency stack is Python 2-era: boto 2.13, celery 3.1.23, python-dateutil
  1.5, Pillow 2.7, mysqlclient 1.4.6, redis 2.10.5, Markdown 2.5.1, six 1.8, etc.
- Search stack: django-haystack (TODO'd), xapian-haystack, custom `queues` /
  queued-search packages (some installed from private hg/git repos).
- Database: MySQL (mysqlclient).
- Many local Django apps (forums, news, downloads, bio, weblinks, potd, polls,
  membermap, bandmap, shoutbox, messages, etc.).
- Deployment currently via `fabfile.py` (Fabric) to a dedicated Ubuntu 14.04.6
  LTS server.
