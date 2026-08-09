# pytz → zoneinfo: audit of all 17 call sites

Taken 2026-08-04 during Step 13 task 03 (the Django 4.0 rung), on Django 4.0.10
/ Python 3.10 / pytz 2021.3.

> **RE-MEASURED 2026-08-08, and the headline finding below no longer holds.**
> The section "The finding that changes the shape of the work" reported that
> `zoneinfo` could not resolve the names 93.6% of profiles have stored. On the
> image as it stands today **that number is zero** — 0 of 439 `common_timezones`
> and 0 of 15,227 profiles fail to resolve. It is kept below as written, because
> the reason it changed is the useful part; the correction follows it under
> "What changed, and why it is not yet safe". **Read both before scoping task
> 09: the hardest-looking item in this audit is already solved, and what remains
> is one line of `requirements.txt`.** The other two hard cases —
> `NonExistentTimeError` and the `common_timezones` list — are untouched by this
> and still stand.

## Verdict

**All 17 sites are deferred, and they should move with the `USE_TZ` conversion
(task 09) rather than on a version rung.** The plan had `zoneinfo` pencilled in
against the 4.1 rung; that sequencing is wrong for three reasons:

1. **Nothing forces it.** Django 4.0 moved its *own* internals to `zoneinfo`,
   but this application uses pytz **directly**, not through Django. pytz keeps
   working; no rung breaks on it. (`USE_DEPRECATED_PYTZ` — the transitional
   setting deprecated in 4.0 and removed in 5.0 — governs Django's internal
   behavior and is deliberately left unset. It is irrelevant here.)
2. **Converting now means converting twice.** While `USE_TZ` is `False`, the
   `SERVER_TZ.localize(...)` idiom is not legacy — it is *correct and load-
   bearing*, because the ORM hands back naive values. Task 09 will delete most
   of these call sites rather than port them.
3. **The hard cases are timezone-semantics decisions, not API swaps**, and they
   belong with the person doing the timezone conversion.

The audit below is the input to that task.

## The finding that changes the shape of the work

**`zoneinfo` cannot resolve the timezone names 93.6% of this site's users
have stored.**

`bio.UserProfile.time_zone` is populated from a dropdown built out of
`pytz.common_timezones` (`tools/tz.py`). That list contains legacy "backward"
names — `US/Pacific`, `US/Eastern`, `Canada/Eastern` — which pytz bundles and
which a stock `python:3.10-slim` image's system tzdata does not carry:

| | count |
| --- | --- |
| `pytz.common_timezones` | 439 |
| `zoneinfo.available_timezones()` (stock slim image) | 486 |
| in `common_timezones` but **unresolvable** by `zoneinfo` | **17** |

The 17: `Asia/Choibalsan`, `Canada/{Atlantic,Central,Eastern,Mountain,`
`Newfoundland,Pacific}`, `Europe/{Kiev,Uzhgorod,Zaporozhye}`,
`US/{Alaska,Arizona,Central,Eastern,Hawaii,Mountain,Pacific}`.

They do not merely fail to *list* — `ZoneInfo('US/Pacific')` raises
`ZoneInfoNotFoundError`. And that is what users actually chose:

| stored timezone | profiles |
| --- | --- |
| `US/Pacific` | 12,619 |
| `US/Eastern` | 940 |
| `US/Central` | 406 |
| `US/Mountain` | 147 |
| `Canada/Eastern` | 45 |
| `US/Arizona` | 32 |
| others (Canada/*, US/Hawaii, Europe/Kiev…) | 59 |
| **total on an unresolvable name** | **14,248 of 15,227 (93.6%)** |

Worse, `forums/templatetags/forum_tags.py:33` hardcodes
`DEFAULT_TZ = timezone('US/Pacific')` at **module level**. Under a naive swap
that raises at import, so the entire `forum_tags` library fails to load and the
forums stop rendering — not for 93.6% of users, for everyone.

### The remedy, and the lesson under it

Adding the PyPI **`tzdata`** package fixes all of it — measured on a clean
`python:3.10-slim`:

| | `available_timezones()` | `US/Pacific` |
| --- | --- | --- |
| without `tzdata` | 486 | `ZoneInfoNotFoundError` |
| with `tzdata` | 599 | resolves |

So the fix is one dependency line. **The lesson is the part worth carrying:
`zoneinfo` reads the *host's* tzdata, while pytz bundles its own.** Swapping
makes this site's timezone correctness depend on the OS image's tzdata
packaging — something that can differ between the dev image, CI, and the Step 21
deploy host, and that no test would catch if all three happen to agree. Pin
`tzdata` explicitly as part of the conversion rather than relying on the base
image.

Whether to *also* migrate the 14,248 stored names to canonical ones
(`US/Pacific` → `America/Los_Angeles`) is a separate call for task 09. `tzdata`
makes it unnecessary; doing it anyway would retire a deprecated naming scheme,
but it rewrites user data to fix something that is not broken.

## What changed, and why it is not yet safe (re-measured 2026-08-08)

**The `tzdata` package is already installed, so every name resolves today.**
Measured on the current image, against the production snapshot:

| | audit, 2026-08-04 | 2026-08-08 |
| --- | --- | --- |
| `common_timezones` unresolvable by `zoneinfo` | 17 of 439 | **0 of 439** |
| profiles on an unresolvable name | 14,248 of 15,227 | **0 of 15,227** |
| `zoneinfo.available_timezones()` | 486 | 599 |

All 95 distinct stored values resolve, `US/Pacific` included.

**Nobody decided this. `pip show tzdata` reports `Required-by: kombu`,** so it
arrived with task 06's celery 5.6.3 / kombu 5.6.2 bump on 2026-08-07 — three
days after this audit was written, as a transitive dependency of a change about
something else entirely. The remedy this file recommends was applied by
accident.

**It rests on nothing we control.** The base image's own tzdata does not carry
the backward names at all — `/usr/share/zoneinfo/US` does not exist, and
`zoneinfo` finds `US/Pacific` only by falling back to the `tzdata` package on
`sys.path`. Nothing in `requirements.txt` asks for it. If kombu ever drops the
dependency, 12,619 profiles stop resolving, and the failure arrives as a
`ZoneInfoNotFoundError` from a template tag rather than as a failed build.

**This is not a live risk today**, because the code still calls pytz and pytz
bundles its own copy of the database. It becomes load-bearing at the moment
task 09 switches to `zoneinfo`.

**So the action is one line: pin `tzdata` in `requirements.txt` as a direct
dependency**, commented as the timezone database rather than a celery detail,
as the first commit of task 09. That converts the largest-looking item in this
audit into a declared dependency. A test asserting that every name in the
timezone dropdown resolves — and that the dropdown covers all 95 values already
stored — is what keeps it that way when tzdata updates.

**The lesson stands and gets sharper.** The original note said swapping to
`zoneinfo` makes timezone correctness depend on the host image's tzdata
packaging. It now also depends on the *dependency graph*, which moves under you
between tasks. A finding about the environment has a shelf life; this one lasted
three days.

## The other two hard cases

### `pytz.NonExistentTimeError` — `forums/latest.py:317`

**No `zoneinfo` equivalent exists.** `zoneinfo` has exactly one exception,
`ZoneInfoNotFoundError`, and it is about missing zone *data*, not impossible
times. Measured on 2:30 AM on a spring-forward date (2026-03-08), an hour that
does not exist in `America/Chicago`:

- `pytz.localize(d, is_dst=None)` → `NonExistentTimeError`
- `zoneinfo` → **no error**, silently returns `02:30:00-06:00`

So this is not a port; it is a decision about what should happen in the DST gap.
The current code catches the error, which means it currently *detects* the gap.
A swap deletes that detection silently. Whoever converts must decide whether the
gap still needs handling and implement the check by hand (compare `utcoffset()`
before and after, or use `fold`).

### User-supplied zone names — `bio/forms.py:58-59`, and the same shape in `gcalendar`

`bio/forms.py` validates a timezone name **submitted by a user**. pytz raises a
single exception; `zoneinfo` raises **two different ones**:

| input | `zoneinfo` raises |
| --- | --- |
| `'Not/AZone'` | `ZoneInfoNotFoundError` (a `KeyError` subclass) |
| `'../etc/passwd'` | `ValueError` |
| `''` | `ValueError` |

A port that catches only `ZoneInfoNotFoundError` — the obvious one-to-one
translation of `except pytz.UnknownTimeZoneError` — **turns malformed input into
an unhandled 500 instead of a form validation error**, on a field a user
controls. Catch both. This applies identically at `gcalendar/forms.py:165-166`
and `gcalendar/calendar.py:154-155`.

The empty string is already guarded here (`bio/forms.py` does `if tz:` after
stripping, and blank is a legal value), so it is the *path-shaped* input like
`'../etc/passwd'` that carries the risk — which is exactly the input a
validator on a user-controlled field should be most careful with.

## Per-site register

| # | site | what it does | verdict |
| --- | --- | --- | --- |
| 1 | `forums/latest.py:63` | `import pytz` | defer — follows 2–3 |
| 2 | `forums/latest.py:79` | `SERVER_TZ = pytz.timezone(TIME_ZONE)` | defer to task 09; likely deleted with `USE_TZ` |
| 3 | `forums/latest.py:317` | `except pytz.NonExistentTimeError` | **hard** — no equivalent; decide DST-gap behavior |
| 4 | `forums/templatetags/forum_tags.py:6` | `from pytz import timezone, UnknownTimeZoneError` | defer — follows 5–7 |
| 5 | `forum_tags.py:32` | `SERVER_TZ = timezone(TIME_ZONE)` | defer to task 09; deleted with `USE_TZ` |
| 6 | `forum_tags.py:33` | `DEFAULT_TZ = timezone('US/Pacific')` | needs `tzdata` — **satisfied since 2026-08-07, pin it** |
| 7 | `forum_tags.py:73,101` | `SERVER_TZ.localize(...)` | correct while `USE_TZ` is off; task 09 deletes both |
| 8 | `forum_tags.py:78,105` | `timezone(profile.time_zone)` | needs `tzdata` — reads the 93.6% names; **satisfied, pin it** |
| 9 | `tools/tz.py:5` | `import pytz` | defer — follows 10–11 |
| 10 | `tools/tz.py:14` | `pytz.common_timezones` (grouping) | **hard** — no curated equivalent; 439 vs 486, and the sets differ both ways |
| 11 | `tools/tz.py:23` | `pytz.common_timezones` (choices) | **hard** — same; this is what populated the 14,248 profiles |
| 12 | `bio/forms.py:12` | `import pytz` | defer — follows 13–14 |
| 13 | `bio/forms.py:58` | `pytz.timezone(tz)` on user input | needs `tzdata` — **satisfied, pin it** |
| 14 | `bio/forms.py:59` | `except pytz.UnknownTimeZoneError` | **hard** — must catch `ValueError` too, or 500 on bad input |
| 15 | `gcalendar/forms.py:5,165,166` | same validation shape | same as 13–14 |
| 16 | `gcalendar/calendar.py:7,154,155` | same validation shape | same as 13–14 |
| 17 | `gcalendar/calendar.py:157` | `tz.localize(d)` | correct while `USE_TZ` is off; revisit in task 09 |

(`bio/forms.py:50` is a docstring mention, not a call site; counting it is what
makes the total 17 by line rather than 16.)

## Note for whoever does task 09

`gcalendar` is currently stubbed (its Google integration was removed pending
Step 18), so sites 15–17 cannot be smoke-tested end to end. Their unit tests
still run. Do not read "no observable breakage" there as evidence.
