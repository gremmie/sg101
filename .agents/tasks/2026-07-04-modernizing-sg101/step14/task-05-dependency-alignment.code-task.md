# Task: Final Dependency Alignment

## Description
Close the step by aligning the dependencies the Django ladder never forced. Step
13 task 06 aligned everything the *framework* required; what is left is the set
of pins that have simply never moved — several of them chosen under constraints
that expired four interpreters ago — plus one decision that was explicitly
deferred to this step.

Two of those pins turn out to be **dead weight**, measured rather than suspected.

## Background
**This is deliberately the last task in the step, not the first.** Every earlier
task holds one variable still; this one changes many at once, so it runs when
the framework is settled and any breakage is unambiguously a dependency's fault.

### The psycopg 3 decision, which this step inherits

Step 13 task 06 evaluated psycopg 3 and returned **"defer"** — and the plan
routes the re-decision here. The reason it was deferred is structural rather
than cautious, and it is written down: **the three `tools/pgloader/` scripts
import `psycopg2` directly**, so it stays in the image either way, and adopting
psycopg 3 would mean running *two* PostgreSQL drivers rather than a newer one.

The plan states exactly what would change that arithmetic: *"the MySQL box being
decommissioned (Step 21), which retires those tools and psycopg2 with them — so
if the cutover has happened by the time this step runs, the decision is worth
re-taking rather than inheriting."*

**The cutover has not happened** — it is Step 21, and this is Step 14. So the
structural reason still holds and the expected outcome is to inherit the defer.
**Record the re-decision explicitly anyway**, with its date and its reason. A
decision that is silently carried forward becomes indistinguishable from one
nobody revisited, which is how the `mysqlclient` pin sat bare and
unexplained until Step 13.

### Two pins are dead weight — measured 2026-08-12

| pin | requirers | imports in app code |
|---|---|---|
| `html5lib==1.1` | **none** | **none** |
| `simplejson==3.17.6` | **none** | **none** |

Both appear nowhere but the two requirements files. `html5lib` was pulled in by
`bleach`, and **bleach dropped it when it moved to 6.4.0** during Step 13 task
01 — the pin has been orphaned since, without anyone noticing, because an
orphaned pin installs perfectly well. `simplejson` predates the standard
library's `json` being good enough and was left behind when Step 7 moved the
JSON call sites.

**Dropping `html5lib` also halves `six`.** The comment at `requirements.txt:29-36`
says six has two requirers left, "html5lib 1.1 and python-dateutil 2.8.2." Remove
html5lib and only `python-dateutil` remains — and that one is required by
`celery`, so **six does not leave the image in this task**. Say so in the comment
rather than deleting a pin and leaving prose that names a requirer that is gone.

`html5lib` also appears in `sg101/templates/fixed/colophon.html:15`, alongside
`python-memcached` and Haystack, both of which left the project steps ago. **That
whole page is Step 20's**, not this task's — do not fix it here, but note that
the list keeps growing.

### The pins that never moved

Each of these installs and imports fine on 3.12 today, so none of them is
blocking anything. They are here because the step's objective is "final
dependency alignment," and because several were pinned under constraints that no
longer exist.

| pin | current | why it is where it is | where it is used |
|---|---|---|---|
| `django-environ==0.4.5` | 0.14.0 | **the highest-risk bump here.** Chosen in Step 3 as "the last Py2.7 line" — a constraint five interpreters stale | `sg101/settings/base.py`, `databases.py`, `docker.py`, and `core/tests/test_settings.py` |
| `lxml==4.9.4` | 6.1.1 | never moved; has a cp312 wheel at the current pin | `core/html.py`, `core/management/commands/ssl_images.py`, `news/management/commands/fix_news_embeds.py`, `comments/tests/test_templatetags.py` |
| `requests==2.27.1` | 2.34.2 | adopted in Step 7 for the donations IPN | `donations/views.py`, `contact/forms.py`, `core/download.py`, `ssl_images.py`, plus tests and `tools/pgloader/smoke.py` |
| `ftfy==5.9` | 6.3.1 | never moved; builds from sdist on 3.12 | `comments/admin.py`, `news/admin.py` |
| `docutils==0.16` | 0.23 | never moved | `core/management/commands/make_fixed_page.py` |
| `testfixtures==6.18.5` | 12.3.0 | dev-only | three `test_receivers.py` / `test_decorators.py` modules |
| `mock==4.0.3` | 5.2.0 | dev-only, and a **rolling backport of `unittest.mock`** | ~4 test modules |

**`mock` is worth a decision rather than a bump.** The PyPI package exists to
backport `unittest.mock` to interpreters that lack it; on 3.12 the standard
library version is ahead of nothing. Either bump it or replace the imports with
`unittest.mock` and drop the pin — the second is the smaller long-term surface,
but it touches test files, so it is a judgment call worth recording either way.

**`repoze.timeago==0.5` is a special case: do not bump it, flag it.** Upstream
stopped in 2011 and there is no newer release. It is also entangled with a
monkeypatch — `core/templatetags/core_tags.py` patches `repoze.timeago._NOW`,
which Step 13 task 09 documented while fixing a host-clock dependency, and which
I initially mis-read as a live production bug. Replacing this library is app
modernization, not dependency alignment: **recommend it into Step 19** with the
monkeypatch as the reason, and leave the pin alone.

**`mysqlclient==1.4.6` stays**, for the reason recorded in `requirements.txt` and
scheduled into Step 21: `tools/pgloader/verify.py` and `verify_data.py` import
`MySQLdb` to verify a production cutover, and retirement is gated on
decommissioning the old box, not on the site looking fine.

### The comments are part of the work

This project's requirements files carry long explanatory comments, and several
of them name facts that these bumps invalidate — the six comment names
html5lib; the `django-environ` line still says "12-factor env-var config" with
no note that its pin is a Py2.7 fossil. **A pin comment that has gone stale is
worse than none**, because it reads as current. Every pin this task touches gets
its comment brought to the truth, in **both** `requirements.txt` and
`requirements-docker.txt`.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 14's psycopg 3 paragraph; Step 21 for the cutover that would change it)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 13 task 06, the previous alignment and its method)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Re-take the psycopg 3 decision explicitly** and record it with its date and
   reason, whichever way it goes. Inheriting the defer is the expected outcome;
   inheriting it silently is not acceptable.
2. **Verify and then drop the two orphan pins** (`html5lib`, `simplejson`) from
   both requirements files. Verify by removing them, rebuilding, and running the
   suite — not by trusting the grep in this task file.
3. Update the `six` comment to reflect its single remaining requirer, and state
   why six is still in the image.
4. Bump the never-moved pins, **one at a time, with the suite run between each**
   so a failure is attributable. `django-environ` is the one most likely to
   break something and should be done on its own; `core/tests/test_settings.py`
   is the seam that covers it.
5. Decide `mock`: bump, or replace with `unittest.mock` and drop the pin. Record
   which and why.
6. Do **not** bump `repoze.timeago`; recommend its replacement into Step 19,
   naming the `_NOW` monkeypatch in `core/templatetags/core_tags.py`.
7. Do **not** touch `mysqlclient`, and do not "clean up" the MySQL apt entries in
   the Dockerfile.
8. Bring every touched pin's comment to the truth in both requirements files.
9. `check`, `check --deploy` and `makemigrations --check` clean; suite green;
   worker and beat booted.

## Dependencies
- Task 04 (Django 5.2 LTS, green) — this task runs against the settled framework
- A PostgreSQL snapshot before any DB-writing verification
  (`tools/pg_snapshot.sh dump <label>`)

## Implementation Approach
1. Take the psycopg 3 decision first, on paper, before touching pins — it
   determines whether this task is also a driver migration.
2. Drop the two orphans and get green. That is the cheapest real change here.
3. Bump the remaining pins one at a time, suite between each.
4. For `lxml`, exercise `core/html.py` and the two management commands that
   parse markup — the ORM does not cover them and `ssl_images` has a history of
   being the uncovered path (Step 13 task 07 found `resize_image()` wholly
   uncovered).
5. For `requests`, exercise the donations IPN path, which Step 7 rewrote onto
   requests and which has real branch coverage.
6. For `django-environ`, boot the stack from `.env` alone — the Step 3
   acceptance test — and run `core/tests/test_settings.py`.
7. Rewrite the comments last, once the facts are settled.

## Acceptance Criteria

1. **psycopg 3 Decision Recorded**
   - Given the deferred decision from Step 13 task 06
   - When this task completes
   - Then STATUS records the re-decision, its date, and its reason — and if the
     answer is still "defer," the structural reason is restated rather than
     referenced

2. **Orphan Pins Removed**
   - Given `html5lib` and `simplejson`
   - When both are removed from both requirements files and the image is rebuilt
   - Then the suite is green, the site smokes clean, and neither package is
     present in the image

3. **The six Comment Is True**
   - Given `html5lib`'s removal
   - When the six pin comment is read
   - Then it names `python-dateutil` as the single remaining requirer and
     explains why the pin stays

4. **Pins Bumped With Attributable Failures**
   - Given the never-moved pins
   - When each is bumped
   - Then the suite is run between bumps, so any failure is attributable to one
     package rather than to a batch

5. **django-environ Still Loads the Environment**
   - Given the bumped `django-environ`
   - When the stack is booted from `.env` alone
   - Then every setting resolves as before and `core/tests/test_settings.py`
     passes

6. **Markup and HTTP Paths Exercised**
   - Given the `lxml` and `requests` bumps
   - When `core/html.py`, `ssl_images`, `fix_news_embeds` and the donations IPN
     path are exercised
   - Then each behaves as before — verified by running them, since the suite
     does not fully cover the management commands

7. **repoze.timeago Left Alone and Recommended Forward**
   - Given its 2011 upstream and the `_NOW` monkeypatch
   - When this task completes
   - Then the pin is unchanged and its replacement is recommended into Step 19
     with the monkeypatch named as the reason

8. **Comments Match Reality**
   - Given every pin this task touched
   - When both requirements files are read
   - Then no comment asserts something the build no longer does

9. **Suite Green and Checks Clean**
   - Given the aligned dependencies on Django 5.2 / Python 3.12
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, `check`, `check --deploy` and
     `makemigrations --check` are clean, and the worker and beat boot cleanly

## Metadata
- **Complexity**: Medium
- **Labels**: Dependencies, psycopg, Pin Hygiene, Step 14
- **Required Skills**: Python packaging and dependency resolution, Django
  settings, reading a dependency graph rather than a requirements file
