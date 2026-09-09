# Task: Read Deployment Settings in a Subprocess, Not in the Test Process

## Description
`SearchLoggingSettingsTestCase` imports `sg101.settings.local` and
`sg101.settings.production` into the running test process to read their `LOGGING`
dicts. Move it onto the subprocess helper that already exists for exactly this,
keeping its assertions aimed at the deployment modules.

**This task changes no settings and extracts nothing.** The `LOGGING` duplication
these two modules carry is real and is deliberately left alone — it moved to
Step 20 on 2026-09-08, with the `local`/`docker` consolidation. See *Background*
for why, because it is the reason this task is small.

## Background

### What the test does now
`search/tests/test_views.py:192`:

```python
def settings_modules(self):
    from sg101.settings import local, production
    return {'local': local.LOGGING, 'production': production.LOGGING}
```

Its docstring is right about *why* it exists — the suite runs under `test`, which
configures no search logger, so the only way to cover "search logging lands in its
own file and does not reach the site log" is to read the configuration the site
deploys. **The method is what is wrong.**

### Why importing a settings module into a live process is the hazard
A settings module is not inert. `from base import *` binds `base`'s own list
objects, so a module that appends to `MIDDLEWARE` or `INSTALLED_APPS` edits the
settings of whatever is already running. **This is not hypothetical**: it is what
detonated Step 13 task 06's debug-toolbar bump, where importing `local.py` spliced
the toolbar's middleware into the running process and produced 105 errors from an
app registry and an `INSTALLED_APPS` that disagreed.

**Be accurate about the current state rather than inheriting the alarm.** Task 06
fixed `local.py` to rebind copies instead of mutating in place, and its comment
says so in as many words — *"importing this one for its LOGGING dict is a thing
the suite does."* `production.py` performs no in-place mutation at all now, its
template-loader block having been deleted once measurement showed it reproduced a
Django default. **So this is not a live fire.** What remains is a pattern that
re-arms every time either module grows a line, guarded only by a comment, in a
project about to restructure both modules at Step 20.

### The helper that already exists
`core/tests/test_settings.py:37`:

```python
def _run(env_overrides, snippet=SNIPPET):
    """Load settings in a subprocess; return (returncode, stdout, stderr)."""
```

Two things about it matter here and neither requires changing it:

- It sets `DJANGO_SETTINGS_MODULE=sg101.settings.docker_test` **and then applies
  `env_overrides` on top**, so passing
  `{'DJANGO_SETTINGS_MODULE': 'sg101.settings.production'}` already targets
  another module.
- `snippet` is a parameter precisely so a caller can read a different setting;
  the default only reads `SECRET_KEY` back out.

Verified 2026-08-07 that production settings load standalone with no env help
(`REDIS_UNIX_SOCKET` defaults at `base.py:228`), so there is no friction to
loading them this way.

### The trap — the reason this is a task and not a one-line edit
**Do not repoint the assertions at anything other than the deployment module's own
`LOGGING`.** The property the test exists for is *"the configuration the site
actually deploys sends search records to search.log and nowhere else."* A test
that reads a shared helper proves the helper is right and says nothing about
whether `production.py` uses it — a later `LOGGING = {...}` override there would
pass.

This matters more after this task than before it. **Step 20 will extract a shared
`LOGGING` module**, and at that moment this test is the only thing standing
between "production uses the shared config" and "production has quietly stopped
using it." Leaving it correctly aimed is this task's real deliverable; the
subprocess is just how it gets there safely.

### One decision to make and record
The test's *subject* is search logging, which belongs in `search`; the *mechanism*
is settings loading, whose helper lives in `core`. Either move the test case to
`core/tests/test_settings.py` or share `_run()` with `search`. **Pick one and say
why in the commit** — do not copy `_run()` into a second file, which is how a
helper becomes two helpers that drift.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase D]` settings-module item as split on 2026-09-08, and Step 20's *"Also
  carries the settings consolidation"* for what this task is deliberately not doing
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 13 task 06 for
  the in-place-mutation defect
- `core/tests/test_settings.py` — the helper and its existing callers
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **No settings module is imported into the test process.** After this task, a
   sweep of the suite for `from sg101.settings import local` / `production`
   outside a subprocess snippet returns nothing.

2. **The assertions still name `local.LOGGING` and `production.LOGGING`.** Same
   two properties as today: the `search` handler's filename ends in `search.log`,
   and the `search` logger has `propagate` false with `handlers == ['search']`.
   Same coverage, different mechanism.

3. **`_run()` is shared, not duplicated.** Move the test or import the helper;
   either is fine, a second copy is not.

4. **`_run()` itself is not modified** unless something genuinely requires it —
   `env_overrides` already overrides `DJANGO_SETTINGS_MODULE`. If a change is
   needed, its existing callers in `core/tests/test_settings.py` must keep
   passing unchanged.

5. **Nothing in `sg101/settings/` changes.** No extraction, no shared logging
   module, no touching the duplicated dicts. That is Step 20's work and doing any
   of it here would put this task's own subject in flight.

6. **Step 13 task 06's copy fix in `local.py` stays exactly as it is**, including
   its comment. It is a standing constraint of the project, not a detail of this
   task.

7. **No shipped comment mentions the step or phase number.** Per `CODEASSIST.md`,
   comments describe the code, not the plan.

## Dependencies
- `core/tests/test_settings.py`'s `_run()`, which exists and works
- Production settings loading standalone with no env help — re-confirm rather than
  assume; it was verified 2026-08-07 and `base.py` has changed since
- Nothing blocks this, and nothing in Phase D depends on it

## Implementation Approach
1. Run the existing test and confirm it passes, so there is a baseline.
2. Write a snippet that prints the parts of `LOGGING` the assertions need, and
   confirm `_run()` can load `local` and `production` with it.
3. Decide where the test case lives; move it or share the helper.
4. Rewrite the two test methods against the subprocess output, keeping the
   deployment module as the subject.
5. Mutation-verify both directions (see criteria 3 and 4).
6. Run the suite the way CI does and the deprecation gate.

## Acceptance Criteria

1. **No in-process settings imports remain**
   - Given the test suite after the change
   - When it is swept for imports of `sg101.settings.local` or
     `sg101.settings.production` outside a subprocess snippet
   - Then there are no matches

2. **Coverage is unchanged**
   - Given the rewritten test case
   - When it runs
   - Then it still asserts, for both `local` and `production`, that the `search`
     handler writes to a file ending `search.log` and that the `search` logger has
     `propagate` false and `handlers == ['search']`

3. **The test still catches a broken deployment config — mutation-verified**
   - Given `production.py` edited so its `search` logger propagates, or its
     `search` handler points at another file
   - When the suite runs
   - Then the test **fails**, observed before the edit is reverted

4. **The test would catch a deployment module that stopped using a shared config**
   - Given a `LOGGING = {...}` literal added to `production.py` that omits the
     `search` handler entirely
   - When the suite runs
   - Then the test **fails** — this is the Step 20 property being protected in
     advance, and a test aimed at anything but `production.LOGGING` passes here

5. **The subprocess actually loaded what it claims**
   - Given a run of the helper against `sg101.settings.production`
   - When its return code and stderr are inspected
   - Then the return code is 0 and no `ImproperlyConfigured` was raised — a test
     asserting on the output of a subprocess that failed to start would pass
     vacuously

6. **Settings are untouched**
   - Given `git diff` for this task
   - When it is read
   - Then no file under `sg101/settings/` appears in it

7. **The suite and the gate are green**
   - Given `manage.py test --noinput --settings=sg101.settings.docker_test` and,
     separately, the deprecation gate
   - When both are run in the container
   - Then both pass, with the search logging tests present and passing and the
     existing `core/tests/test_settings.py` callers unaffected

## Metadata
- **Complexity**: Low
- **Labels**: settings, test-isolation, logging, search, Step 19 Phase D
- **Required Skills**: Django settings loading, subprocess-based test isolation, mutation-verified testing
