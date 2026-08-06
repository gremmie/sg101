# Task: Turn `USE_TZ` on

## Description
Convert the site from naive datetimes in `America/Chicago` to timezone-aware
datetimes, and set `USE_TZ = True`.

**Run this on 4.2, with no version bump in flight.** It is the last task in the
step by sequence but it is not part of the traversal — it is a behavior change
that happens to have a deadline. It could equally be read as Step 14's task 00;
the only real requirement is that it sits *between* 4.2 landing and the 5.0
rung, on its own. Django 5.0 flips the default, so Step 14 cannot start with
this question still open, and debugging timezone semantics and a version bump in
the same change is exactly the pooling this ladder exists to prevent.

## Background

The site predates Django's timezone support and never converted. `USE_TZ` was
unset until the 4.0 rung set it explicitly to `False`
(`sg101/settings/base.py`), which silences 4.0's warning about the coming
default change but decides nothing.

### The data is already correct — this is not a data migration

**Measured 2026-08-04 on the 4.0 rung.** `DateTimeField` maps to `timestamptz`
on PostgreSQL, and Django sets the connection's `TimeZone` to `TIME_ZONE` while
`USE_TZ` is off, so PostgreSQL places every naive value written onto the real
timeline. Rows sampled across the whole history:

| row | what the app sees (naive) | what is stored |
| --- | --- | --- |
| `forums_post` pk=1 (2006) | `2006-02-26 19:24:30` | `2006-02-27 01:24:30 UTC` |
| `forums_post` pk=200000 (2011) | `2011-04-26 16:56:39` | `2011-04-26 21:56:39 UTC` |
| `forums_post` pk=484428 (2026) | `2026-07-26 15:40:53` | `2026-07-26 20:40:53 UTC` |

Those are genuine UTC instants, correctly offset. With `USE_TZ = True` Django
switches the connection to UTC and returns the same instants as aware datetimes,
which templates render back in `TIME_ZONE`. **No stored value needs rewriting.**

This is worth stating plainly because it is luck, not design: on the old MySQL
box `datetime` carried no offset, and the same conversion would have required
rewriting every datetime column in the database. The PostgreSQL move bought
this, and Step 11 task 05 is where the alignment was actually established (it
found every datetime 5–6 hours early after the pgloader conversion and fixed
it).

**Do not take the table above on faith — re-measure before starting.** It was
taken on the 4.0 rung, and tasks 04–08 land in between.

### The one thing that cannot be fixed

Naive local times inside the DST fall-back hour are genuinely ambiguous — 1:30
AM happened twice on those dates — and the conversion resolved each to one
instant. Some historical rows may sit an hour off. `USE_TZ` neither causes nor
worsens this, and the true value is not recoverable. Do not spend time on it;
note it and move on.

### What the code work is — measured 2026-08-04

**79 naive builders** in non-test, non-migration application code:

| construct | count |
| --- | --- |
| `datetime.now()` | 75 |
| `datetime.utcnow()` | 3 |
| `datetime.today()` | 1 |

These become `django.utils.timezone.now()`. **No site uses `timezone.now()`
today (0 occurrences)** — nothing is pre-adapted, but nothing is half-converted
either, which is the easier starting point.

**7 `date.today()` sites are unaffected.** `USE_TZ` governs `DateTimeField`
only. `DateField` (`bio.UserProfile.birthday`, `gcalendar.Event.start_date`)
does not change, and neither do `TimeField`s.

**3 `pytz.localize()` calls break outright**, which is the good kind of failure —
`localize()` refuses an already-aware value:

- `forums/templatetags/forum_tags.py:73` — `current_forum_time`
- `forums/templatetags/forum_tags.py:101` — `forum_date`
- `gcalendar/calendar.py:157`

### The actual risk: 8 lines of local-date rollup

Five queries across three files truncate or group `DateTimeField` values by
month or year:

- `donations/models.py:34-35` and `:64` — `payment_date__year` / `__month`
- `donations/management/commands/donations_report.py:44-45` — same
- `news/views.py:67` — `Story.objects.dates('date_submitted', 'month')`
- `news/views.py:78-79` — `date_submitted__year` / `__month`

With `USE_TZ` on these compile to `AT TIME ZONE` using the **active** timezone.
If nothing is activated they resolve in UTC, so a donation made at 7pm Chicago
on Jan 31 lands in February's report. **Nothing raises — the totals are just
quietly wrong at the month boundary**, which makes this the only part of the
conversion that can fail silently. The whole risk is concentrated in these eight
lines, and the fix is to make the timezone explicit rather than to rewrite the
queries.

`core/templatetags/core_tags.py:174` (`birthday__month`) looks like this class
and is **not** — `birthday` is a `DateField`. Do not "fix" it.

### The forums get simpler, not harder

The site already does per-user timezones by hand: `bio.UserProfile.time_zone`,
and `forum_date` doing `SERVER_TZ.localize(date).astimezone(user_tz)`. Under
`USE_TZ` that is `timezone.localtime(date, user_tz)` — or activate the user's
zone once in middleware and let templates render normally, which deletes most of
the date machinery in `forums/templatetags/forum_tags.py`. This conversion
replaces hand-rolled logic with the feature Django added to do exactly it, so
the diff should be net-negative in that file.

### This task also owns the pytz → zoneinfo conversion

**All 17 pytz call sites were audited on the 4.0 rung and deferred here** — see
`research/pytz-audit.md` for the per-site register. The plan had `zoneinfo`
pencilled against the 4.1 rung; that was wrong, because nothing forces it (the
app uses pytz *directly*, not through Django, so no rung breaks on it) and
because while `USE_TZ` is `False` the `localize()` idiom is correct and
load-bearing rather than legacy. Converting before this task means converting
twice — this task deletes most of those call sites.

Three findings from that audit change what the work costs. Read the audit, but
in short:

- **`zoneinfo` cannot resolve the timezone names 93.6% of users have stored.**
  14,248 of 15,227 profiles are on legacy names like `US/Pacific` (12,619 alone)
  that `pytz.common_timezones` offers and a stock slim image's system tzdata
  does not carry. `forum_tags.py:33` also hardcodes `US/Pacific` at module
  level, so a naive swap raises at *import* and the forums stop rendering for
  everyone. **Adding the PyPI `tzdata` package fixes all of it** — and should be
  pinned explicitly, because `zoneinfo` reads the host's tzdata while pytz
  bundles its own, making correctness depend on image packaging that can differ
  between dev, CI and the deploy host.
- **`pytz.NonExistentTimeError` has no equivalent** (`forums/latest.py:317`).
  `zoneinfo` does not raise in the DST gap, it silently returns an offset. The
  current code *detects* the gap; a swap deletes that detection silently.
  Decide what should happen there rather than porting.
- **`zoneinfo` raises two exception types for bad zone names**, not one.
  Catching only `ZoneInfoNotFoundError` turns path-shaped input like
  `'../etc/passwd'` into an unhandled 500 on a user-controlled field
  (`bio/forms.py`, and the same shape twice in `gcalendar`).

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 11 task 05
  (the datetime defects and how they were fixed); Step 13 task 03 (where the
  measurements above were taken and why `USE_TZ` stayed `False` for the rungs)
- `sg101/settings/base.py` — the `USE_TZ = False` comment this task replaces
- `tools/pgloader/convert.sh` — why the database's timezone is set before the
  load, and what breaks if it is not

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Re-measure the storage alignment before changing anything. The table in this
   file was taken on the 4.0 rung; confirm it still holds on 4.2.
2. Set `USE_TZ = True` in `sg101/settings/base.py` and replace the deferral
   comment with one describing the converted state.
3. Convert all 79 naive builders to `django.utils.timezone.now()`. Confirm the
   count first — it was measured on the 4.0 rung and tasks 04–08 may move it.
4. **Run the suite with `RuntimeWarning` promoted to an error.** Django warns
   "received a naive datetime while time zone support is active" and then
   guesses a timezone; promoted, that guess becomes a hard failure and the test
   runner hands you the worklist. This is the single most useful technique in
   the task — the same gate-as-a-real-gate approach that surfaced the middleware
   `get_response` item in task 02, which no grep could have found.
5. Make the timezone explicit at the 5 rollup queries so month and year
   boundaries stay in `TIME_ZONE`. These do not fail loudly; they need tests
   that would catch a boundary shift.
6. Rework the 3 `localize()` sites. Prefer deleting hand-rolled conversion in
   favor of `timezone.localtime` / an activated timezone over transliterating
   the existing logic.
7. Audit Celery for naive datetimes — `CELERY_TIMEZONE` is derived from
   `TIME_ZONE` (`base.py`), and Beat schedules, task ETAs and the search
   reconcile sweep's `indexed_at` comparisons all cross this seam.
8. `check` and `makemigrations --check` clean; suite green.

## Before You Begin
Take a database snapshot: `tools/pg_snapshot.sh dump <label>`. It costs 8
seconds and 128 MB, and it is what turns an accidental deletion into a restore
rather than an afternoon. Added after Step 13 task 05 deleted a forum and its
4,626 topics through a `Forum.last_post` cascade -- see DOCKER.md section 8.

**And when you delete forum content, use `tools/pgloader/smoke.py`'s
`delete_topic()` rather than writing your own.** `Forum.last_post` is a
`OneToOneField` with `on_delete=CASCADE` pointing the wrong way: deleting the
post a forum points at takes the forum, and every topic and post in it, with it.

## Dependencies
- Task 05 (Django 4.2 — run this on the LTS, not mid-ladder)
- Tasks 04/05's pytz → `zoneinfo` decisions, which determine how much of the
  `localize()` work is left
- PostgreSQL with `timestamptz` columns, from Step 11

## Implementation Approach
1. Re-measure storage alignment and the call-site counts. Record any drift from
   this file's numbers as a finding.
2. Capture a before-state of rendered timestamps — forum post times, the
   latest-posts feed, the calendar, a profile with a non-default timezone, and
   the donations and news month rollups. Step 13 task 03 used a characterization
   script diffed before and after; reuse that shape. **The rollups are the
   addition** — task 03 did not capture them because they cannot move while
   `USE_TZ` is off.
3. Flip `USE_TZ`, then run the suite with `RuntimeWarning` as an error and work
   the list. Expect `TypeError` from naive/aware comparisons too; those are
   loud and self-locating.
4. Convert the rollup queries and add boundary tests — a donation and a story
   timestamped late enough in the evening that UTC would file them in the next
   month. **Verify each test fails before the fix**, per the technique lesson
   from Step 12 task 09: a test that passes against the bug proves nothing.
5. Rework the forums display path, aiming to delete rather than translate.
6. Diff the captured before-state. Every difference must be explained; the
   expected answer is that nothing moves except what the rollup fix corrects.

## Acceptance Criteria

1. **USE_TZ Is On and the Data Did Not Move**
   - Given the `timestamptz` columns
   - When `USE_TZ = True` and the sampled rows are re-read
   - Then the same instants come back as aware datetimes, and no stored value
     was rewritten

2. **Displayed Times Are Unchanged**
   - Given a forum post, the latest-posts feed, a calendar event, and a profile
     with a non-default timezone
   - When each is rendered before and after the conversion
   - Then displayed times are identical, for both an anonymous visitor and a
     user whose profile timezone differs from the server's

3. **No Naive Datetime Reaches the ORM**
   - Given the suite run with `RuntimeWarning` promoted to an error
   - When it completes
   - Then it is green, so no code path passes a naive datetime into a
     timezone-aware ORM

4. **Month and Year Rollups Respect TIME_ZONE**
   - Given a donation and a news story timestamped in the evening, late enough
     that the UTC date is the following day and month
   - When the donations report and the news archive are generated
   - Then both file the record under the `TIME_ZONE` month, and each test fails
     against the unconverted query

5. **The Forums Path Shrank**
   - Given `forums/templatetags/forum_tags.py`
   - When the conversion is complete
   - Then per-user timezone display uses Django's timezone machinery and the
     file is net smaller, rather than carrying translated `localize()` logic

6. **Celery Crossed the Seam**
   - Given Beat schedules, task ETAs, and the search reconcile sweep
   - When a scheduled task runs and the sweep compares `indexed_at`
   - Then behavior is unchanged and no naive datetime is compared to an aware one

7. **Suite Green and Checks Clean**
   - Given `USE_TZ = True`
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check` and `makemigrations --check` are clean

8. **The Setting Explains Itself**
   - Given `sg101/settings/base.py`
   - When `USE_TZ` is inspected
   - Then the deferral comment written during the 4.0 rung is gone, replaced by
     one describing the converted state

## Metadata
- **Complexity**: High
- **Labels**: Timezones, PostgreSQL, Behavior change, Step 13
- **Required Skills**: Timezone-aware datetime handling, PostgreSQL
  `timestamptz` semantics, Django ORM date lookups and `AT TIME ZONE`
