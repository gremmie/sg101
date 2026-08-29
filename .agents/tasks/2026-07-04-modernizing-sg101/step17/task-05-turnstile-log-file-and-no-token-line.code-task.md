# Task: Log the Submissions That Never Get a Token, and Give Turnstile Its Own File

## Description
Close the one blind spot in this site's CAPTCHA instrumentation: a submission
that arrives with no token is refused without a trace, because the guard raises
before anything is logged. Add a line for it, and move all Turnstile logging to
a dedicated file so the new volume costs `sg101.log` nothing.

Independent of tasks 03 and 04, and it can run before or after them. Doing it
**before** 03 is worth considering: registration is the more heavily targeted
form, and the file should exist before its volume arrives.

## Background

### The blind spot, and why it is not a corner case
`contact/forms.py` raises on an absent `cf-turnstile-response` before calling
`turnstile.verify()`. That is deliberate — acceptance criterion 4 of task 02,
and the property that makes bots cost nothing. The consequence is that an
absent log line means three incompatible things: nobody visited, the widget is
broken, or bots are posting directly.

`STATUS.md` records what the ambiguity has already cost. The reCAPTCHA decline
from 71 to 20 assessments a month "is therefore not readable as health on its
own", and settling whether the classic key had degraded needed a *recent
success* rather than a clean tally. A revoked sitekey or a blocked `api.js`
produces **zero** server-side evidence today, and would keep producing zero for
as long as it lasted.

### Measured 2026-08-28 — the majority of the form's traffic is invisible
Full numbers and their caveats live in `STATUS.md`, section *PLANNING — Step 17
task 05*. The three that decide this task:

| | |
|---|---|
| `POST /contact/`, 61 days | **3,669** |
| ...that reach `ContactForm.clean()` (HTTP 200 + 302) | **2,348** — would log, ~37.6/day |
| ...real messages sent (HTTP 302) | **52**, 0.85/day |

**36% of the POSTs are CSRF 403s that never reach the form**, so they cost
nothing and need no line — verified, not assumed. The 225 reCAPTCHA
verifications behind this step's rationale were counting only the traffic that
got as far as a token; the form's actual load is ~25x that.

### Why a dedicated file, not `sg101.log`
`sg101.log` holds 149 days in 100 KB x 10 — about 7.1 KB/day. Adding 37.6 lines
a day at ~63 bytes is 2.3 KB/day, which cuts retention to ~113 days, **24% off
the file every volume measurement in this step depends on.**

`auth.log` and `search.log` already exist for exactly this reason, and
`STATUS.md` states it: "propagate: False keeps every executed search out of
sg101.log, which the root logger would otherwise collect." At the auth/search
budget of 2 MB x 5, this volume is thousands of days.

**The cost of moving, stated so it is not discovered later:** the `passed` and
`rejected` lines leave `sg101.log`, where CAPTCHA lines have lived since 2018.
Historical comparison already needs two patterns — the old lines read
`Contact Form captcha response:` — so this makes an existing two-grep job no
worse, but it does make it permanent.

### One design decision this task must make, not inherit
The no-token event is **not** a verification, and the form is what detects it.
Two shapes, and the task should pick one with reasons rather than default:

**A — a second entry point on the helper.** `turnstile.no_token(source)` logs
the line. The form keeps its guard; one module owns the vocabulary and one
logger owns the file.

**B — a fourth outcome.** `verify(None)` returns `NO_TOKEN` without calling out,
and the form stops guarding — it always calls `verify()` and branches on the
result. Fewer concepts at the call site and one log line per submission from one
place, but it moves task 02's criterion 4 (no HTTP request on an absent token)
inside the helper, where it must be re-proven by test.

**B is the more coherent shape and the more invasive one.** Whichever is chosen,
`TurnstileOutcome` gains meaning it did not have: today every member describes
something Cloudflare said, and `NO_TOKEN` would describe something it was never
asked.

## Reference Documentation
**Required:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, sections
  *PLANNING — Step 17 task 05* (the measurement) and *Step 17 task 02* (the
  `source` label decision and the log format it produced)

**Additional References:**
- `sg101/settings/production.py` — the `LOGGING` dict, and the `email` logger's
  `propagate: True` comment, which is the argued precedent *against* splitting
- `.agents/tasks/2026-07-04-modernizing-sg101/step16/task-09-email-send-logging.code-task.md`

## Technical Requirements
1. One INFO line when a submission presents no token, naming the form the same
   way the other three outcomes do — `Turnstile: no token (contact form)`.
   **No HTTP request may be made on this path**; task 02's criterion 4 survives
   this task unchanged.
2. Decide between shapes A and B above, and record the reasoning where the
   decision lives, not only in the commit.
3. A dedicated handler carrying **all** Turnstile lines, on the `auth`/`search`
   pattern: `RotatingFileHandler`, 2 MB x 5, `logs/` beside the others.
4. An `antispam.turnstile` logger entry with `propagate: False`, so the volume
   does not reach `sg101.log`.
5. **Both settings modules** — `production.py` and `local.py`. They carry
   near-identical `LOGGING` dicts and drifting them is how a line that works in
   development vanishes in production.
6. Update the spam-baseline grep pattern recorded in `STATUS.md`'s Step 17
   *Still open* register to name the new file.

## Dependencies
- Task 02 (done, 2026-08-28) — the `source` label and the log line format.
- Independent of tasks 03 and 04.
- Touches `LOGGING`, which Step 19 has queued for a settings-module cleanup.
  Leave that cleanup alone; adding one handler and one logger is not the moment.

## Implementation Approach
1. Pick shape A or B, and write down why.
2. Add the handler and logger to both settings modules first, so the line has
   somewhere to land the moment it exists.
3. Add the line, with its test, and watch the test fail.
4. Verify the routing end to end: the suite cannot see `LOGGING` wiring, so run
   the four cases against the Docker stack and read the file. Step 16 task 09
   needed exactly this and recorded why.
5. Confirm `sg101.log` no longer receives Turnstile lines.

## Acceptance Criteria

1. **The invisible case becomes visible**
   - Given a POST to the contact form carrying no `cf-turnstile-response`
   - When the form is validated
   - Then one INFO line is written naming the form, and **no HTTP request is
     made**

2. **CSRF rejections stay silent**
   - Given a POST with no CSRF token
   - When Django's middleware rejects it
   - Then no line is written — 36% of real traffic must not reach this path

3. **All four outcomes land in the new file**
   - Given passed, rejected, unavailable and no-token submissions
   - When each is exercised against the running stack
   - Then each appears in the dedicated file, and each names its form

4. **`sg101.log` is relieved, not duplicated**
   - Given the same four submissions
   - When `sg101.log` is read
   - Then it contains none of them

5. **Both settings modules agree**
   - Given `production.py` and `local.py`
   - When their `LOGGING` dicts are compared for this handler and logger
   - Then they differ only where they already differ for `auth` and `search`

6. **Unit test coverage**
   - Given the changed form or helper
   - When the suite runs
   - Then every criterion a unit test can reach is covered and each test has
     been watched to fail

## Metadata
- **Complexity**: Low
- **Labels**: Turnstile, logging, settings, instrumentation
- **Required Skills**: Django logging configuration, mocking, log-format discipline
