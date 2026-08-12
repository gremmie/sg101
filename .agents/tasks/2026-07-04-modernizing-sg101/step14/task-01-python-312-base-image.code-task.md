# Task: Move the Base Image from Python 3.10 to 3.12

## Description
Bump the Docker base image from `python:3.10` to `python:3.12` with
`Django==4.2.30` held fixed, so the suite comes back green on the new
interpreter before the first Django rung starts.

This is the same shape as Step 13's task 01, and for the same reason: 3.12 is
supported by **both** the Django we are on and the Django we are going to, so
the interpreter can move by itself with one variable changing.

| Django | Python |
| --- | --- |
| 4.2 | 3.8 – 3.12 |
| 5.0 | 3.10 – 3.12 |
| 5.1 | 3.10 – 3.13 |
| 5.2 | 3.10 – 3.13 |

Unlike Step 13's interpreter move, **3.12 is not on the critical path** — 3.10
is supported for the whole 5.2 LTS window, so this task could be skipped and the
step would still reach its target. It is being done first anyway, because it is
cheap (see below), because it is the interpreter Django 6.0 will require, and
because doing it last would mean changing the interpreter under a Django release
this project has never run on 3.10.

## Background
**Measured 2026-08-12, and this time the prediction and the measurement agree:
there is no dependency breaker.** The entire pin set — `requirements.txt` and
`requirements_dev.txt` together — installs, imports, and exits cleanly on
`python:3.12-slim` with `Django==4.2.30` unchanged. All three rungs of this
project's ladder, run in that order:

- **Installs.** Every pin. `mysqlclient==1.4.6` still builds, `psycopg2==2.9.12`
  still builds, `lxml==4.9.4` has a cp312 wheel, and only `ftfy==5.9`,
  `simplejson==3.17.6` and `repoze.timeago==0.5` fall back to an sdist build —
  all three successfully.
- **Imports.** 29 modules imported, zero failures — including `MySQLdb`,
  `psycopg2`, `PIL.Image`, `lxml.etree`, `debug_toolbar` and `kombu`.
- **Exits.** Every probe returned status 0. This rung exists because Step 13's
  task 01 found `Pillow==6.2.2` importing fine on 3.10 and then aborting the
  interpreter at shutdown with `free(): invalid pointer`, exit 134. A probe
  ending in `print('ok')` reports success on a build like that.

`Pillow==12.3.0` reports `features.check('jpg') is True` on 3.12, so the
manylinux wheel is carrying its codecs and the Dockerfile still needs no
`libjpeg`/`zlib` headers.

**Contrast this with Step 13's interpreter move, where `bleach==3.1.5` was the
gate.** The difference is that Step 13's task 06 already did the dependency
alignment, and did it to the *current* line rather than the minimum that worked.
The bill for 3.12 was paid there.

**One measurement caveat, and it is the same one that qualified the 2026-08-02
figures.** The probe ran on `python:3.12-slim` with the Dockerfile's four apt
packages installed by hand (`build-essential`, `default-libmysqlclient-dev`,
`libpq-dev`, `pkg-config`). The real image is `python:3.12` — the full variant,
on a different Debian base than the 3.10 image. **Re-run the ladder in the
actual built image rather than inheriting this result.** It narrows what to
expect; it does not replace the build.

**A detail worth not "fixing": `python:3.12-slim` ships no `setuptools`.** 3.12
dropped `distutils` from the standard library and the images stopped seeding
`setuptools` alongside pip. The three sdist builds and both C-extension builds
succeed regardless, because pip's PEP 517 build isolation installs `setuptools`
into a throwaway build environment. If a build fails on the full image, the fix
is to look at *that package's* build backend — adding a global `setuptools` pin
to work around it would hide the real problem.

**Three things 3.12 removes that this project has already paid for.** Each was
cleared during Step 13 under a different label; this task is where the payment
is confirmed to have covered the debt:

1. **`SelectableGroups`** — the dict interface on `importlib.metadata.entry_points()`,
   removed in 3.12. `kombu==5.2` read its transport registry through
   `entry_points().get()`. Step 13 task 06 bumped kombu to 5.6.2 and recorded
   this as "a Step 14 prerequisite wearing a Step 13 label." **Confirm celery
   actually resolves its transports on 3.12** — this is the one item where a
   green unit suite proves the least, because the broker round-trip is what
   exercises it.
2. **`assertEquals`** and friends, removed from `unittest` in 3.12. Step 13
   task 05 cleared 21 sites across 5 test files.
3. **Invalid escape sequences.** `core/functions.py:120` was fixed in task 05.
   3.12 raises the category from `DeprecationWarning` to `SyntaxWarning`, so a
   surviving one is noisier but still not fatal. **A cached `.pyc` hides these**
   — they are emitted at compile time — so re-check by compiling the whole tree
   with warnings enabled rather than by running the suite.

`distutils` itself: **zero direct imports in application code**, measured. Third
party is covered by the import probe above.

**The Dockerfile header explains why 3.10 was chosen, and that reasoning
expires with this change.** Lines 1–11 describe 3.10 as "the waypoint rather
than the 3.8 minimum ... the only version supported by Django 3.2 *and* by
everything through 5.2." That is a true statement about a decision no longer in
force. Rewrite it rather than editing the numbers, the way task 01 rewrote the
3.7 EOL note.

**Do not clean up the MySQL apt entries in passing.** `default-libmysqlclient-dev`
and `default-mysql-client` stay, for the reason spelled out in `requirements.txt`
and scheduled into Step 21: `tools/pgloader/verify.py` and `verify_data.py`
import `MySQLdb` to verify a production cutover, and their retirement is gated
on decommissioning the old box.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 14)
- `.agents/planning/2026-07-04-modernizing-sg101/research/upgrade-path.md`
  (the Django/Python support matrix)
- `.agents/tasks/2026-07-04-modernizing-sg101/step13/task-01-python-310-base-image.code-task.md`
  (the same move one interpreter earlier, and the source of the three-rung ladder)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Change the base image to `python:3.12` in `Dockerfile`, and **rewrite** the
   header comment — its explanation of why 3.10 was the waypoint describes a
   decision that no longer applies.
2. Hold `Django==4.2.30` unchanged in both requirements files. This task changes
   the interpreter and nothing else.
3. Run the full three-rung ladder **in the built image**, not the slim probe:
   every pin installs, every third-party package imports, and every probe
   process exits 0.
4. Verify `Pillow`'s compiled format support on the new image
   (`features.check('jpg')`), and `lxml`'s parser.
5. **Confirm celery resolves its transports** on 3.12 — the `SelectableGroups`
   payoff. Boot the worker and beat against the real broker; do not infer it
   from the unit suite.
6. Recompile the whole tree with warnings enabled to catch any `SyntaxWarning`
   for invalid escape sequences that a cached `.pyc` would hide.
7. Update the stale interpreter references in `.github/workflows/ci.yml` (line 4)
   and `DOCKER.md` (lines 3, 10, 53, 427).
8. `check` and `makemigrations --check` clean; full suite green.
9. Record which packages built from sdist versus installed from a wheel, and the
   cold image build time before and after — Step 13 task 01 recorded 26s vs 30s,
   and the comparison is only useful if it keeps being taken.

## Dependencies
- Step 13 complete (884 tests green on Django 4.2.30 / Python 3.10, pushed and
  CI green as of 2026-08-09)
- Step 13 task 06's dependency alignment, which is what makes this move cheap
- Docker Desktop; CI runs `--settings=sg101.settings.docker_test`

## Implementation Approach
1. Change `FROM`, build the image, and let it fail if it is going to. The
   failure list is the real inventory; the 2026-08-12 probe only says to expect
   a short one.
2. Run the ladder in order — install, import, exit status — before running a
   single test. Checking the exit status is the rung this project added most
   recently and the one most easily skipped.
3. Verify Pillow's codecs and lxml's parser.
4. Run the full suite, `check`, and `makemigrations --check`.
5. Boot the worker and beat and let a scheduled task fire. Step 6's lesson still
   holds: a green unit suite is not the same as a working deployment, and the
   management-command breakages that step found only surfaced this way.
6. Smoke the site.

## Acceptance Criteria

1. **The Image Builds on 3.12**
   - Given the updated `Dockerfile`
   - When the image is built from scratch with no layer cache
   - Then it completes, and `python --version` inside it reports 3.12

2. **Every Dependency Installs, Imports, and Exits**
   - Given the built image
   - When each third-party package is installed, imported, and the importing
     process is allowed to exit
   - Then all installs succeed, all imports succeed, and **every process returns
     status 0** — the Pillow exit-134 failure mode is checked for, not assumed
     absent

3. **Django Is Unchanged**
   - Given the completed task
   - When both requirements files are inspected
   - Then `Django==4.2.30` is untouched and no Django-version-driven code change
     is included

4. **Pillow Can Decode JPEG**
   - Given the new image
   - When a JPEG is opened and thumbnailed through the site's own image path
   - Then it succeeds, and `features.check('jpg')` is True

5. **Celery Resolves Its Transports**
   - Given the 3.12 image, where `SelectableGroups` no longer exists
   - When the worker and beat are booted against the real Redis broker and a
     scheduled task fires
   - Then the transport resolves and the task runs, confirming the kombu 5.6.2
     bump covered this removal

6. **No Hidden Compile-Time Warnings**
   - Given a clean tree with no cached bytecode
   - When every module is compiled with warnings enabled
   - Then no `SyntaxWarning` for an invalid escape sequence is emitted

7. **Suite Green on the New Interpreter**
   - Given the 3.12 image
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all 884 tests pass, and `check` and `makemigrations --check` are clean

8. **CI Green and Version Strings Current**
   - Given the pushed branch
   - When the GitHub Actions workflow runs
   - Then it builds the 3.12 image and the suite passes, with no stale "3.10"
     text left in `ci.yml` or `DOCKER.md`

9. **Interpreter Cost Recorded**
   - Given the completed move
   - When STATUS is updated
   - Then the sdist-versus-wheel split and the build times are recorded, and if
     the move was genuinely free it says so explicitly — a recorded no-op is a
     finding

## Metadata
- **Complexity**: Low
- **Labels**: Python 3.12, Docker, Interpreter, Dependencies, Step 14
- **Required Skills**: Docker image builds, Python packaging and C-extension
  builds, Celery/kombu transport resolution
