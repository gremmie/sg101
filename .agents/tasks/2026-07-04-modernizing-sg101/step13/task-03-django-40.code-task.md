# Task: Django 3.2 → 4.0 (Rung 1)

## Description
Move Django from 3.2.25 to the 4.0 line with the interpreter held fixed at 3.10,
and settle the `USE_TZ` question that this rung forces into view.

One variable per rung. That discipline is what surfaced the real breakers in
every upgrade step so far — Step 10's three rungs each produced a distinct
failure that a combined jump would have pooled.

## Background
**4.0 is where the Python floor bites.** It requires 3.8+, which is why task 01
had to come first and why Step 14 could not own the interpreter move.

**The removals task 02 already cleared.** If task 02 is done, this rung should
not hit `ifequal`, `is_ajax`, `providing_args`, `force_text`, `urlquote` or
`ugettext_lazy`. If it does, task 02 missed something — treat that as a finding
about the sweep, not as work to absorb here.

**`django.conf.urls.url` costs nothing.** Verified 2026-08-03: the tree has zero
usages. The only `conf.urls` import is `conf.urls.static.static`
(`sg101/urls.py:1`), which is not removed. 89 modules already use
`django.urls`.

### The real question this rung raises: `USE_TZ`

**`USE_TZ` is not set anywhere in `sg101/settings/`.** Verified 2026-08-03 —
`base.py` sets `TIME_ZONE = 'America/Chicago'` (line 28) and `CELERY_TIMEZONE`
from it (line 220), and nothing sets `USE_TZ` at all. Django 3.2's default is
`False`, so **the site runs on naive datetimes in America/Chicago**.

That matters more here than it would in most projects, because Step 11 moved the
database to PostgreSQL, where Django's `DateTimeField` maps to `timestamptz`.
Step 11 task 05 found **every datetime 5–6 hours early** after the pgloader
conversion — naive MySQL local time loaded into `timestamptz` as though it were
UTC — and fixed it. So this codebase has already been bitten once by exactly the
seam `USE_TZ` governs, and the fix that was applied assumed the current setting.

Two things to establish before touching anything:

1. **What the columns actually hold now.** After the Step 11 fix, are stored
   values America/Chicago wall time stored as UTC, or genuine UTC? The answer
   determines whether flipping `USE_TZ` is a settings change or a data
   migration.
2. **Whether the default flips underneath us later.** Django's `USE_TZ` default
   changes to `True` in a later release. Confirm which one against the release
   notes for the versions in play — do not take this task file's word for it —
   because an unset setting that changes meaning during Step 14 is precisely the
   kind of silent behavior change this ladder exists to prevent.

**Set `USE_TZ` explicitly in this task either way.** Whether the decision is
"stay naive for now" or "go aware," the setting must stop being implicit. If the
decision is to stay `False`, say so in a comment with the reason and the
deferral target, so the next reader knows it was chosen rather than inherited.

**pytz is used for real, not incidentally.** Six modules, 17 lines:
`forums/latest.py` (including `pytz.NonExistentTimeError` at line 317),
`forums/templatetags/forum_tags.py`, `bio/forms.py`, `gcalendar/forms.py`,
`gcalendar/calendar.py`, `tools/tz.py` (which iterates `pytz.common_timezones`).
Django 4.0 begins the move to `zoneinfo` and pytz support is on the way out, but
`zoneinfo` has no direct equivalent for `NonExistentTimeError` and no
`common_timezones` list, and `bio/forms.py` validates **user-supplied** timezone
names. This is not a find-and-replace. **Scope it in this task; it is acceptable
to defer the conversion to task 05 or later, but not to leave it unexamined** —
record what each of the six call sites needs.

**`CSRF_TRUSTED_ORIGINS` now requires a scheme** (`https://example.com`, not
`example.com`). Verified 2026-08-03: the setting is not present in
`sg101/settings/`. Confirm it is genuinely unset in production rather than
absent from the repo before concluding this is free.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Suggested order" item 3)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 11 task 05 — the datetime defects and how they were fixed)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to the 4.0 line in both `requirements.txt` and
   `requirements-docker.txt`. Interpreter stays at 3.10; no other rung in the
   same change.
2. **Set `USE_TZ` explicitly in `sg101/settings/base.py`**, with a comment
   giving the reason and, if staying `False`, the deferral target.
3. **Characterize the current datetime behavior before deciding.** Establish
   what the `timestamptz` columns hold post-Step-11 and what the site renders,
   so the decision rests on the data rather than on the setting's name.
4. Audit all 17 pytz call sites across the 6 modules. Convert or explicitly
   defer, with a note per site — `NonExistentTimeError`, `common_timezones` and
   the user-supplied-name validation in `bio/forms.py` are the three that do not
   map cleanly.
5. Confirm `CSRF_TRUSTED_ORIGINS` is unset in the real production config, not
   merely absent from the repo. If set, add the scheme.
6. Resolve every 4.0 breaker the build and suite surface, keeping each fix
   attributable to this rung.
7. `check` and `makemigrations --check` clean; suite green.

## Dependencies
- Task 01 (Python 3.10 — 4.0 will not install on 3.7)
- Task 02 (the removal backlog cleared, so this rung's failures are 4.0's own)
- PostgreSQL with `timestamptz` columns, from Step 11

## Implementation Approach
1. Answer the datetime question first, with queries against the converted
   database and a look at what the site renders. The `USE_TZ` decision should be
   made on evidence, before the version bump makes everything noisier.
2. Bump Django, build, and run the suite. Collect the failure list before fixing
   anything — the shape of it is the finding.
3. Fix breakers one category at a time, re-running the suite between categories.
4. Audit pytz and record the per-site verdict, converting what maps cleanly.
5. Smoke the site with attention to anything that renders a timestamp: forums
   post times, the latest-posts feed (`forums/latest.py`), the calendar
   (`gcalendar`), and a profile with a non-default timezone (`bio/forms.py`).

## Acceptance Criteria

1. **Django 4.0 Installed and Running**
   - Given the updated requirements
   - When the image is built and `django.get_version()` is read
   - Then it reports 4.0.x on Python 3.10

2. **USE_TZ Is Explicit**
   - Given `sg101/settings/base.py`
   - When `USE_TZ` is inspected
   - Then it is set to a literal value with a comment giving the reason, so a
     future change to Django's default cannot alter this site's behavior

3. **The USE_TZ Decision Is Evidenced**
   - Given the `timestamptz` columns as Step 11 left them
   - When the current stored values and rendered output are characterized
   - Then the recorded finding states what the columns hold and what the site
     displays, and the chosen `USE_TZ` value follows from it

4. **Timestamps Render Correctly**
   - Given a forum post, a calendar event and a profile with a non-default
     timezone
   - When each is rendered before and after the rung
   - Then displayed times are identical, with no repeat of the 5–6 hour shift
     Step 11 task 05 found

5. **pytz Sites Are Accounted For**
   - Given the 17 pytz call sites in 6 modules
   - When the audit is complete
   - Then each is either converted to `zoneinfo` or carries a recorded reason
     for deferral, with `NonExistentTimeError`, `common_timezones` and the
     user-supplied-name validation addressed by name

6. **Timezone Validation Still Rejects Bad Input**
   - Given `bio/forms.py` and `gcalendar/forms.py`
   - When a user submits an invalid timezone name
   - Then it is rejected as before, regardless of which library performs the
     lookup

7. **Suite Green and Checks Clean**
   - Given Django 4.0
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check` and `makemigrations --check` are clean

8. **Breakers Recorded**
   - Given the completed rung
   - When STATUS is updated
   - Then every 4.0 breaker encountered is named with its fix, so the rung's
     cost is on record rather than inferred from the diff

## Metadata
- **Complexity**: High
- **Labels**: Django 4.0, Upgrade, Timezones, PostgreSQL, Step 13
- **Required Skills**: Django upgrades and release notes, timezone-aware
  datetime handling, PostgreSQL `timestamptz` semantics
