# Task: Consolidate the Settings Package and Split the Dev and Prod Images

## Description
Give the project one settings module per deployment and a production image that
is actually distinct from the development one, and fix the database backend both
settings modules still declare. This is the first task of Step 20 because every
task after it configures a production settings module that does not yet exist in
usable form.

**Amended 2026-09-17.** As generated, this task covered the image split and
`from_env()` but not the settings consolidation `plan.md` moved into Step 20 on
2026-09-08, and its first requirement named the wrong requirements file. Both are
corrected below; see *Amendment record* at the end for exactly what changed.

## Background
**Carried in 2026-08-07 from Step 13 task 06, and unresolved since.**
`research/docker-strategy.md` records both *"the dev override owns the debug
toolbar"* and *"one image runs dev and prod"*, and those cannot both hold: one
image means the production image either carries `django-debug-toolbar` or it does
not.

**Three things are measurably wrong today:**

- `sg101/settings/production.py:14` and `sg101/settings/local.py:11` both declare
  `django.db.backends.mysql`, five steps after the PostgreSQL move.
  `sg101/settings/databases.py` already provides `from_env()` and is not used by
  either.
- The `if DEBUG and find_spec(...)` guard around the debug toolbar protects
  nothing in production, because `production.py` never goes through `local.py`.
- `Dockerfile` is a single stage ending in
  `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`, so there is no
  production image to speak of.

**The toolbar's MIDDLEWARE position is deliberate — and it is index 0, not after
`CommonMiddleware`.** `local.py:55` is
`MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + list(MIDDLEWARE)`,
and `base.py:113` starts `MIDDLEWARE` with `CommonMiddleware`, so the toolbar is
first. **Corrected 2026-09-17**: this file said "after `CommonMiddleware`",
inherited from `plan.md`, which had not been updated when Step 14 task 04 moved
it on 2026-08-15 (both sources now corrected).

The move was Brian's call and was measured in both directions with a control,
recorded in `STATUS-archive-steps-01-15.md`:

| toolbar position | RedirectsPanel | `/forums` |
|---|---|---|
| index 1 (after `CommonMiddleware`) | on | 301 |
| index 0 | on | 200 interstitial |
| **index 0** | **off** | **301** |

The interstitial that made the old position look load-bearing was self-inflicted
configuration: the toolbar disables `RedirectsPanel` and `ProfilingPanel` by
default, so this project's `DISABLE_PANELS: set()` meant "turn both on", not
"leave the defaults alone". `DISABLE_PANELS` is now `{RedirectsPanel}`. Index 0
is also what the toolbar's authors ask for — the docs want it as early as
possible, and `check_middleware()` enforces exactly one ordering rule, about
content-encoding middleware. **Adding a `GZipMiddleware` later is the single
thing that would change that answer.**

**So: preserve index 0.** Do not "restore" the older position, and note that
`DISABLE_PANELS` and the comment explaining the position travel with it.

### The settings consolidation, moved here from Step 19 Phase D on 2026-09-08

`plan.md` states four things to settle **together**, "because settling them apart
is what produced the chain." All four are this task's. Anchors below re-verified
against the tree on 2026-09-17, after the 2026-09-09 commits that touched both
modules — the 2026-09-08 figures still hold.

- **`docker.py` is a thin shim** doing `from sg101.settings.local import *` plus
  three overrides (DB over TCP, Redis/Celery over TCP, the toolbar behind
  Docker's NAT). It stayed thin so the legacy reproduction stayed faithful — a
  reason that expired when the site stopped running bare metal.
- **The default settings module is one nothing can use.** `manage.py:5` and
  `sg101/celery.py:11` both default to `sg101.settings.local`, whose MySQL DSN
  names a unix socket on a box nobody runs.
- **The shared `LOGGING` dicts:** `local.py:71-214` (144 lines) and
  `production.py:92-239` (148 lines), differing in **eight** behavioural places —
  `disable_existing_loggers`; the `auth`, `search`, `email` and `turnstile`
  *handler* levels; the `auth` *logger* level; `root`; and production's extra
  `django.request`→`mail_admins`. A differing `MARKDOWN` comment and a missing
  space in `'django':{` are not decisions. **The dicts reference `PROJECT_PATH`,
  so the log directory has to be a parameter** — importing `base` would make the
  helper a settings module.
- **`production.py` is jaguar's config, not the new host's.** Line 14 is MySQL
  over `/var/run/mysqld/mysqld.sock`; line 59 builds the cache `LOCATION` as
  `'unix://' + REDIS_UNIX_SOCKET + '?db=2'`; line 27 points `STATIC_ROOT` at
  jaguar's `static_serve` directory. **This module is rewritten here regardless
  of what else this task does**, which is also why extracting the shared
  `LOGGING` during Step 19 Phase D would have been the wrong order.

**The sockets do not come back** — asked directly 2026-09-08 and answered no, for
neither PostgreSQL nor Redis. Production is Compose on a single VM with each as
its own service, and a unix socket does not cross a container boundary. They are
a pre-container artifact that dies with jaguar, so they are **not** a dev/prod
distinction and do not belong in the merge.

**Two socket consequences are task 05's, not this task's** — inverting
`base.py:264`'s `REDIS_UNIX_SOCKET` default to TCP, and the now-unreachable
`core/services.py:26` `if unix_socket_path:` branch. Task 05 owns the socket
move; this task only stops `production.py` depending on it.

**The constraint that survives all four:** `search/tests/test_views.py`'s logging
assertions must keep naming the *deployment* module, not the shared helper, or
they stop proving the deployment module uses it. Step 19 Phase D task 08
(`8552a922`) moved that test onto a subprocess helper, so this task inherits a
test that already isolates correctly.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  20's "Four things to settle together here"
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md` —
  the two contradictory claims this task resolves
- `sg101/settings/databases.py` — the `from_env()` mechanism that already exists,
  and the shape `logging_config.py` should follow

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

### The images
1. Convert `Dockerfile` to a multi-target build: a `prod` target and a `dev`
   target built `FROM prod`. **The `prod` target installs
   `requirements-docker.txt`** (`Dockerfile:65-66`) — not `requirements.txt`,
   which is a hand-maintained twin, as the note at the top of that file says.
   The `dev` target layers `requirements_dev.txt`, which pulls
   `requirements.txt` in through `-r`. **Three files, three consumers** (see
   *Which requirements file is which* below), so a dependency this step adds
   goes in `requirements-docker.txt` **and** `requirements.txt`.
2. Point `docker-compose.yml` at the `dev` target so the development workflow is
   unchanged.

### The settings package
3. **Merge `local.py` and `docker.py` into one dev module** and repoint the
   `manage.py:5` and `sg101/celery.py:11` defaults at it. Name it for the
   deployment rather than for a machine — `local` has not meant "local" for a
   while.
4. **Extract the shared `LOGGING` into a side-effect-free
   `sg101/settings/logging_config.py`**, following `databases.py`: a table of
   per-target differences plus a `for_target(name)` / `from_env()`-shaped entry
   point, importing only the standard library and raising `ImproperlyConfigured`
   on an unknown name. **The log directory is a parameter**, not an import of
   `base`. The eight behavioural differences above are the table's contents; the
   two cosmetic ones are not.
5. **Rewrite `production.py` for the new host**: `databases.from_env()` rather
   than a hardcoded engine, the cache `LOCATION` off the unix socket, and
   `STATIC_ROOT` no longer jaguar's `static_serve` path. Do the `from_env()` half
   for the dev module too, so no MySQL engine string remains in either.
6. Move the debug toolbar into the dev module, and drop the
   `if DEBUG and find_spec(...)` guard entirely once the toolbar cannot reach
   production.
7. **Preserve the toolbar at MIDDLEWARE index 0**, with its explanatory comment
   and `DEBUG_TOOLBAR_CONFIG['DISABLE_PANELS'] == {RedirectsPanel}` intact. Also
   carry over `docker.py:55-59`'s `SHOW_TOOLBAR_CALLBACK` override, which is what
   makes the toolbar visible behind Docker's NAT — it is dev-only config and its
   own comment says it moves here.

### Which requirements file is which — confirmed by Brian 2026-09-17

Not interchangeable copies, and the distinction matters for every pin this step
adds:

| File | Who installs it |
|---|---|
| `requirements.txt` on **`main`** | **live production, jaguar** — Django 1.8.15, MySQL-python, the Xapian eggs. Untouched by this branch and stays until cutover. |
| `requirements.txt` on `modernize` | the runtime list of record for this branch; `requirements_dev.txt` inherits it via `-r`. **Not** read by the image or CI. |
| `requirements-docker.txt` | **the image and CI**, hand-maintained against the file above. |
| `requirements_dev.txt` | the `dev` target, on top of `requirements.txt`. |

`main` has no `requirements-docker.txt` at all, which is why the duplication
exists rather than being an oversight: one file describes the host being
decommissioned and one describes the image replacing it. **The duplication ends
with jaguar, not here** — do not try to collapse the two in this task.

**Out of scope, deliberately:** `STATIC_ROOT`'s final value and
`ManifestStaticFilesStorage` belong to task 02, which owns the static-file
decision. This task only stops `production.py` naming jaguar's path — leave a
value task 02 can replace, and do not settle `collectstatic` here.

## Dependencies
- `sg101/settings/databases.py`, already present and tested — the pattern to
  follow, not just a call to make
- `requirements-docker.txt` / `requirements.txt` / `requirements_dev.txt` — see
  the table above before adding a pin to any of them
- Step 19 Phase D task 08 (`8552a922`), which isolated the logging test
- The existing test suite as the regression gate

## Implementation Approach
1. Read the `Dockerfile` and all five settings modules, and record what each
   actually does before changing anything.
2. Split the Dockerfile into `prod` and `dev` targets, `dev` built `FROM prod`.
3. Merge `local.py` and `docker.py`, repoint the two defaults, and run the suite
   before touching anything else — this is the change most likely to break
   something silently.
4. Extract `logging_config.py` and make both deployment modules consume it.
   Diff the resulting `LOGGING` dicts against the originals rather than reading
   them for equivalence.
5. Rewire onto `from_env()` and rewrite `production.py`'s jaguar-isms, verifying
   against a running container rather than by reading.
6. Move the toolbar to the dev module and remove the dead guard.
7. Run the full suite; it is the gate, not a smoke script.

## Acceptance Criteria

1. **The prod image does not carry development tooling**
   - Given the image built at the `prod` target
   - When its installed packages are listed
   - Then `django-debug-toolbar` is absent

2. **The dev image is unchanged in behavior**
   - Given the image built at the `dev` target and the existing compose file
   - When the development stack is started
   - Then the debug toolbar renders as it does today

3. **There is one settings module per deployment**
   - Given the settings package
   - When its modules are listed
   - Then `docker.py` is gone, one dev module has taken its and `local.py`'s
     place, and `manage.py` and `sg101/celery.py` default to a module that can
     actually connect to PostgreSQL and Redis

4. **`LOGGING` has one home**
   - Given `sg101/settings/logging_config.py`
   - When both deployment modules are imported
   - Then each one's `LOGGING` is byte-identical to what it produced before the
     extraction, the eight behavioural differences are expressed as parameters,
     and the helper imports nothing from `sg101.settings`

5. **The deployment modules read the database from the environment**
   - Given `DB_ENGINE=postgresql`
   - When `DATABASES` is read from either deployment module
   - Then the backend is `django.db.backends.postgresql` and no MySQL engine
     string remains in the settings package

6. **`production.py` no longer describes jaguar**
   - Given production settings
   - When the module is searched for `/var/run/mysqld`, `unix://`,
     `REDIS_UNIX_SOCKET` and `static_serve`
   - Then none of them appears

7. **The toolbar's middleware position is preserved**
   - Given the dev settings module
   - When `MIDDLEWARE` is inspected
   - Then `MIDDLEWARE[0]` is
     `debug_toolbar.middleware.DebugToolbarMiddleware`, its comment survives,
     `DISABLE_PANELS` is still `{RedirectsPanel}`, and the
     `SHOW_TOOLBAR_CALLBACK` override still applies
   - And `/forums` answers **301**, not a 200 interstitial — the observable the
     position was chosen on

8. **The suite stays green**
   - Given the full test suite run the way CI runs it
     (`manage.py test --noinput --settings=sg101.settings.docker_test`)
   - When it is run against the dev and production modules
   - Then it passes, with new tests covering the settings split itself — and
     `search/tests/test_views.py` still names the deployment module, not the
     helper

## Metadata
- **Complexity**: Large (Medium as generated; the settings consolidation was
  added 2026-09-17)
- **Labels**: Docker, Settings, Configuration, Production Hardening
- **Required Skills**: Docker multi-stage builds, Django settings layout

## Amendment record — 2026-09-17

Three corrections, all found by checking this file against `plan.md`'s Step 20
scope rather than against the tree:

1. **Requirement 1 named `requirements.txt`** as what the `prod` target installs.
   `Dockerfile:65-66` installs `requirements-docker.txt`. Left uncorrected, the
   prod image would have quietly changed which file governs it. Brian confirmed
   the same day *why* both files are live: `requirements.txt` on `main` is what
   jaguar installs from today, so the twin is deliberate — recorded as a table in
   the requirements above rather than as a warning that would read as a smell.
2. **The settings consolidation was absent.** `plan.md` moved it into Step 20 on
   2026-09-08 as four things to settle together; this file had one of the four
   (`from_env()`) and a fragment of a second (a dev-only module for the toolbar).
   The `local.py`/`docker.py` merge, the `manage.py`/`celery.py` defaults, the
   `LOGGING` extraction and the `production.py` rewrite were in no task file at
   all.
3. **`STATIC_ROOT` was ambiguous between this task and task 02.** Scoped here to
   "stop naming jaguar's path", with the decision left to task 02.
4. **The toolbar's middleware position was recorded backwards** — "after
   `CommonMiddleware`", which is the position Step 14 task 04 *replaced* on
   2026-08-15. `local.py:55` puts it at index 0. Implementing the requirement as
   written would have reverted a measured decision, and acceptance criterion 7
   would have certified the regression. Corrected here and in the two stale
   sources it came from (`plan.md`'s Step 20 detail and its Step 21 carried-item
   line). The criterion now asserts the observable — `/forums` answering 301 —
   rather than a list index alone.
