# Task: Django 4.1 → 4.2 (Rung 3) and the Step 13 Smoke Checklist

## Description
Move Django from the 4.1 line to 4.2 with the interpreter held at 3.10, then run
the full smoke checklist that closes Step 13.

**4.2 is a pass-through, not a resting place.** It is EOL, so the site does not
stay here — Step 14 continues to 5.2 LTS. The point of stopping is to have a
green, verified state between the two halves of the ladder, not to ship 4.2 as a
destination.

## Background
**What 4.2 brings that this project cares about:**

- **`psycopg` 3 support.** 4.2 is the first release that supports it. This is
  the rung that unblocks the psycopg 3 question Step 11 deferred — but
  **evaluate it in task 06, not here.** Changing the database driver in the same
  change as a Django version defeats the one-variable rule that the entire
  ladder is built on.
- **`STORAGES` setting** replacing `DEFAULT_FILE_STORAGE` and
  `STATICFILES_STORAGE`. Step 9 did a staticfiles sweep, so check what that
  left behind before assuming the settings are absent.
- **Model field `db_default` / comment support** — additive.
- **`django.utils.timezone.utc` deprecated** in favor of `datetime.timezone.utc`
  — relevant given task 03's `USE_TZ` work and the six pytz modules.
- **`index_together` deprecated** in favor of `Meta.indexes`. The `search` app
  from Step 12 adds a GIN index; confirm how it is declared.

**On deprecation warnings.** 4.2 is where warnings for 5.x removals begin
appearing. Do **not** clear them here — collect them. Step 14 owns the 5.2 move
and should inherit a written inventory the way task 02 inherited Step 10's. A
recorded list is the deliverable; a cleared list is scope creep into the next
step.

**The Step 13 smoke checklist.** This rung closes the step, so the verification
is the step's, not just the rung's. Everything below has been broken at least
once by an earlier step in this project, which is why each is named:

- Forums: read a thread, post a reply, the latest-posts feed
  (`forums/latest.py` — timezone-sensitive)
- Search: a plain query, a query with an exclusion, per-type counts, the forums
  quick-search endpoint at `/search/topics/`
- Images: upload a photo and generate a thumbnail (Pillow's path — see task 07)
- Markup: post content containing markdown and HTML, exercising `clean_html`
  (bleach's path — see task 01)
- Celery: the incremental search indexing task, and Beat's Sunday 03:30
  reconcile sweep
- Calendar, profile edit with a non-default timezone, private messages,
  downloads, the podcast feed

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Suggested order" item 3; the Step 13 Tests/Demo line)
- `.agents/planning/2026-07-04-modernizing-sg101/research/upgrade-path.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to the 4.2 line in both requirements files. Interpreter stays at
   3.10. **No driver change and no dependency alignment in this task** — those
   are task 06.
2. Adopt the `STORAGES` setting if the project sets either superseded storage
   setting; check what Step 9's staticfiles sweep left first.
3. Replace `django.utils.timezone.utc` usages if any exist, consistent with the
   `USE_TZ` decision made in task 03.
4. Confirm how the search app's GIN index is declared and migrate off
   `index_together` if it is used anywhere.
5. **Collect the 5.x deprecation warnings into a written inventory for Step 14.
   Do not clear them.**
6. Run the full Step 13 smoke checklist above against a running site, not only
   the test suite.
7. `check`, `check --deploy` and `makemigrations --check` clean; suite green.
8. Update STATUS and the plan's Step 13 checklist line together. **Both** — the
   2026-08-02 cleanup found `plan.md`'s Step 12 line stale while STATUS said
   complete.

## Dependencies
- Task 04 (Django 4.1, green)
- Tasks 01–03 (interpreter, backlog, 4.0)
- Celery/Beat running, for the smoke checklist's async items

## Implementation Approach
1. Bump, build, run the suite, collect the failure list before fixing anything.
2. Fix breakers one category at a time.
3. Do the settings work (`STORAGES`, timezone utc, `index_together`) explicitly
   rather than waiting for something to break — these are quiet changes.
4. Capture the 5.x deprecation warning inventory with warnings promoted to
   errors in a throwaway run, and write it down.
5. Run the full smoke checklist against a live container, including the Celery
   and Beat paths.
6. Update STATUS **and** `implementation/plan.md`'s Step 13 checklist line.

## Acceptance Criteria

1. **Django 4.2 Installed and Running**
   - Given the updated requirements
   - When `django.get_version()` is read in the built image
   - Then it reports 4.2.x on Python 3.10

2. **Storage Settings Are Current**
   - Given the project's settings modules
   - When storage configuration is inspected
   - Then no superseded storage setting remains in use, or their absence is
     confirmed and recorded

3. **Smoke Checklist Passes**
   - Given a running site on Django 4.2
   - When every item in the Step 13 smoke checklist is exercised by hand
   - Then each works, including the Celery indexing task and the Beat-scheduled
     reconcile sweep

4. **Search Survived the Ladder**
   - Given the search page after three Django rungs
   - When a plain query, an exclusion query and a categorical query are run
   - Then results, ordering, per-type counts and headline escaping match the
     behavior Step 12 established

5. **5.x Deprecations Inventoried, Not Cleared**
   - Given Django 4.2
   - When deprecation warnings are collected
   - Then a written inventory exists for Step 14, and the warnings themselves
     remain in place

6. **Suite Green and Checks Clean**
   - Given Django 4.2
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check`, `check --deploy` and
     `makemigrations --check` are clean

7. **Planning Docs Agree**
   - Given the completed rung
   - When `STATUS.md` and `implementation/plan.md` are compared
   - Then both reflect the same state of Step 13, with neither left stale

## Metadata
- **Complexity**: Medium
- **Labels**: Django 4.2, Upgrade, Smoke Testing, Settings, Step 13
- **Required Skills**: Django upgrades and release notes, Django settings and
  storage configuration, manual verification of a running site
