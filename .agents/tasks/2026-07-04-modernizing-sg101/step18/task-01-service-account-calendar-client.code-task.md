# Task: The Calendar Client on a Service Account

## Description
Port `gcalendar/calendar.py` from the Python-2-era Google stack
(`httplib2` / `apiclient` / `oauth2client`) to **`google-api-python-client` v2 +
`google-auth`**, authenticating as a **service account** rather than as a human
via OAuth. Add the dependencies, repoint the credentials setting at a service
account JSON key, remove the Step 8 import guard, and cover the module with the
tests it has never had.

`gcalendar/oauth.py` is **not** deleted in this task — task 02 does that. Here it
simply stops being called. `admin.py` is touched only as much as is needed to
keep the sync page running.

## Background

### What actually broke, because the plan used to say otherwise
`plan.md` described this step as resolving the Step 8 stub, which implies the
Python 3 flip took the calendar out. It did not. **Google deprecated the client
library, and Python 2.7 made upgrading impossible** (Brian, 2026-08-31). The
stub, added 2026-07-19, disabled a path that had already been dead for five
years. Measured against the database:

| | |
|---|---|
| Events on the Google calendar | **1,478** |
| Last one to reach Google | submitted **2020-03-03** |
| Stranded (`NEW` / `NEW_APRV`) | **32** |
| Approved by hand and never pushed | **3**, on 2021-02-22 |

Steps 8 and 13 removed the blocker rather than causing the outage. **This code
has not successfully talked to Google in six years, so nothing here should be
assumed still true merely because it is written down.**

### Service account, not OAuth — DECIDED 2026-08-31
The current design has the app act **as Brian's Google account**. A service
account is its own identity, and the SG101 calendar is shared with its address
the way it would be shared with a person. Brian owns the calendar (confirmed in
the Google Calendar console, 2026-08-31), which is the permission this requires.

The decision rests on **surface, not on failure modes** — an earlier draft
argued it would prevent what broke in 2021 and that argument was wrong and has
been withdrawn. What it actually buys: ~150 lines stop existing, nobody ever
re-authorizes, and there is no OAuth consent screen to keep in *Testing* (where
refresh tokens on the calendar scope expire in 7 days) or push through
verification.

### The Step 8 guard this removes
`calendar.py:14-24` wraps the imports in `try/except ImportError`, sets
`_GCAL_API_AVAILABLE`, and `Calendar.__init__` raises `NotImplementedError` when
it is false. The whole construct exists so the admin could import cleanly with
the libraries uninstalled. Once the modern libraries are a real dependency the
guard is dead weight, and leaving it in would let a missing dependency present
as a polite runtime message instead of an import error at startup.

### `_make_time()` has never been tested, and it was rewritten under us
`calendar.py:134` converts an event's local wall clock to the UTC string Google
receives — it decides **what time an event appears at**. It has **zero
coverage**, and Step 13 task 09 rewrote it from `pytz` to `zoneinfo` without a
test proving the conversion. This task is where that gets fixed; it is the
highest-value test in the file.

### The batch API changed shape in v2
`BatchHttpRequest()` is no longer constructed directly — v2 wants
`service.new_batch_http_request()`, which binds the batch to the service's
endpoint. The `callback=` / `request_id=` contract is otherwise unchanged, so
the three callbacks in `sync_events` keep their structure.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R27)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 18` — the measurements, the decisions, and two recorded corrections
- Google: `googleapis.github.io/google-api-python-client/docs/` (batch requests)
- Google: `google-auth.readthedocs.io` (`service_account.Credentials`)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `google-api-python-client` and `google-auth` to `requirements.txt`, pinned
   to exact versions in the style of the surrounding pins. **Correct the header
   comment at lines 3-6**, which still states these were dropped pending a later
   revival — that is this task.
2. `GCAL_CREDENTIALS_PATH` in `sg101/settings/base.py:351` now names a **service
   account JSON key file**. Update the comment block above it (currently
   "GCalendar/Google OAuth settings") and the corresponding `.env.example:22-25`
   comment, which says blank disables the integration.
3. Leave `GCAL_CLIENT_ID` and `GCAL_CLIENT_SECRET` in place — task 02 removes
   them. They must simply stop being read by `calendar.py`.
3a. **Add a `.gitignore` entry for the service account key before the key exists
   on disk.** `docker-compose.yml` bind-mounts the repo root at `/app`, so the
   natural place to put a key the container can read is inside the repo, and
   nothing in `.gitignore` currently matches a `.json` key. Choose a committed,
   documented filename (and put it in `.env.example`'s comment), then ignore it.
   Getting this in first is the point — a key that reaches a commit has to be
   rotated, not deleted.
4. Build the service with
   `service_account.Credentials.from_service_account_file(path, scopes=[...])`
   and `build('calendar', 'v3', credentials=creds)`. The `httplib2.Http()` +
   `credentials.authorize(http)` dance goes away entirely.
5. Remove `_GCAL_API_AVAILABLE`, the `try/except ImportError` block, and the
   `NotImplementedError` branch in `Calendar.__init__`. Imports become
   unconditional.
6. Use `service.new_batch_http_request()` rather than constructing
   `BatchHttpRequest()`.
7. **A missing or unreadable key file MUST raise `CalendarError`**, not an
   unhandled `OSError` or `ValueError`. `admin.google_sync` already renders
   `CalendarError` into the page; anything else becomes a 500 on an admin view.
8. Adjust `admin.py:88-95` so it no longer passes `credentials=` to `Calendar`.
   Keep the change minimal — task 02 rewrites that block properly.
9. `SCOPE` currently lives in `oauth.py:36`
   (`https://www.googleapis.com/auth/calendar`). Move it to `calendar.py`; task
   02 deletes its old home.

## Dependencies
- `google-api-python-client` v2 and `google-auth`, added by this task. Both are
  pure-Python wheels and need no Dockerfile change; confirm that by building.
- `httplib2` returns as a **transitive** dependency of the API client. That is
  expected — what this task removes is the code that drove it directly.
- A service account JSON key is **not** required to complete this task. Every
  test mocks Google. The real key is task 03's business.
- `gcalendar/oauth.py` still exists and still imports. Do not delete it here.

## Implementation Approach
1. Pin the two packages, fix the requirements header, rebuild the image and
   confirm the container imports `googleapiclient` and `google.oauth2`.
2. Write the `_make_time()` tests **first**, against the current implementation —
   they describe behavior this task must not change, and the module has no tests
   to regress against otherwise.
3. Replace the credential and service construction; delete the Step 8 guard.
4. Move the batch onto `new_batch_http_request()` and confirm the three callbacks
   still receive `(request_id, response, exception)` as written.
5. Cover `sync_events` with mocked responses: each of the three statuses on the
   success path, each on the failure path, and the invalid-status branch.
6. Mutation-verify every new test before closing (see `STATUS.md` for the
   standard — a passing test that has not been seen to fail is not yet evidence).

## Acceptance Criteria

1. **The stub is gone**
   - Given the modern libraries are installed
   - When `gcalendar.calendar` is imported
   - Then there is no `_GCAL_API_AVAILABLE` flag and constructing a `Calendar`
     does not raise `NotImplementedError`

2. **Credentials come from a service account key**
   - Given `GCAL_CREDENTIALS_PATH` points at a service account JSON key
   - When a `Calendar` is constructed
   - Then credentials are loaded via `service_account.Credentials` with the
     calendar scope, and no `httplib2.Http()` is constructed by our code

3. **A missing key file is a CalendarError**
   - Given `GCAL_CREDENTIALS_PATH` points at a file that does not exist, and
     separately at a file that is not valid JSON
   - When a `Calendar` is constructed
   - Then `CalendarError` is raised in both cases, not `OSError` or `ValueError`

4. **A new event is inserted and recorded**
   - Given a pending event in `NEW_APRV` and a mocked successful insert
   - When `sync_events` runs
   - Then the event's `status` becomes `ON_CAL`, `google_id` and `google_url` are
     taken from the response, and `notify_on_calendar()` is called

5. **Update and delete follow their own paths**
   - Given events in `EDIT_APRV` and `DEL_APRV` with mocked successful responses
   - When `sync_events` runs
   - Then the first becomes `ON_CAL` and the second is deleted from the database

6. **Per-event failures are collected, not swallowed**
   - Given a batch of three events where the middle one's callback receives an
     exception
   - When `sync_events` runs
   - Then `CalendarError` is raised naming the failed event, and the two
     successful events have been saved

7. **An invalid status is refused**
   - Given a queryset containing an event in `NEW`
   - When `sync_events` runs
   - Then `CalendarError` is raised identifying the invalid status

8. **The UTC conversion is correct and unchanged**
   - Given a date, a time, and a named zone such as `US/Pacific`
   - When `_make_time` runs
   - Then the result is the correct instant in `...Z` form, and a naive value is
     produced when no zone is given
   - And an unknown or path-shaped zone name raises `CalendarError`

9. **The suite is green and the tests have been mutation-verified**
   - Given the full test suite
   - When it is run in the container
   - Then it passes, and each new assertion has been observed to fail against a
     deliberate mutation

## Metadata
- **Complexity**: Medium
- **Labels**: gcalendar, Google API, service account, dependencies, test coverage
- **Required Skills**: google-api-python-client v2, google-auth, Django, mocking, zoneinfo
