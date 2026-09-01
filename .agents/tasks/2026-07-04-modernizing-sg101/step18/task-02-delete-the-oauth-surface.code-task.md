# Task: Delete the OAuth Surface

## Description
Remove everything that existed to obtain and store a human's consent, now that
task 01 has the calendar client authenticating as a service account: delete
`gcalendar/oauth.py`, the `authorize` and `auth_return` admin views and their two
URLs, the credentials-status block and Authorize link in `google_sync.html`, and
the `GCAL_CLIENT_ID` / `GCAL_CLIENT_SECRET` settings. Simplify `google_sync` now
that credentials can no longer be absent, and give the admin its first tests.

Roughly 150 lines stop existing. Nothing about the sync's behavior changes.

## Background

### Why the whole file goes
`oauth.py` is 147 lines and every one of them serves the OAuth consent dance:
build a flow from a client ID and secret, park it in the Redis cache for 60
seconds (`FLOW_CACHE_KEY`, and see the comment at line 78 explaining why not the
session), redirect to Google, catch the redirect back, exchange the code, pickle
the credentials to disk. A service account does none of that — it signs a token
with its own key. There is no partial port to make.

`check_credentials_status()` is the one function that still runs today, because
it only stats a file. It goes too, and the reason is worth stating: under OAuth
that mtime was a **health signal** — it told you when consent was last granted
and therefore whether it might have lapsed. A service account key does not
expire, so the same mtime would report the date a file was copied to the server
and nothing more. Keeping it would leave the admin page displaying a number that
looks like status and is not.

### `SCOPE` has already moved
Task 01 moved `SCOPE` (`oauth.py:36`) into `calendar.py`. Confirm nothing else
reads it before deleting the file.

### A template condition that has never done anything
`sg101/templates/gcalendar/google_sync.html:29` wraps each event in
`{% if not event.on_calendar %}`. **`Event` has no `on_calendar` attribute** —
the model has `status`, `is_approved()` and `google_html()`. Django resolves the
missing attribute to `string_if_invalid`, which is `''` by default, so the
condition is always true and this filter has never filtered anything.

It is also **redundant by construction**: the view passes
`Event.pending_events.all()`, whose manager (`models.py:19`) already restricts to
the three approved-and-pending states, so an `ON_CAL` event cannot reach the
loop. **Delete the condition rather than repair it** — a working version would
be a second filter expressing what the manager already guarantees. Note it in
the commit message; it is a nine-year-old silent no-op, not this task's doing.

### The admin has no tests
`gcalendar/admin.py` is at 46% incidental coverage and has no test module.
`approve_events` in particular ratchets state and **awards a badge**
(`bio.badges.CALENDAR_PIN`), and nothing checks it. This task is where the admin
gets covered.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R27)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 18` — in particular the table of what a service account deletes
- `.agents/tasks/2026-07-04-modernizing-sg101/step18/task-01-service-account-calendar-client.code-task.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Delete `gcalendar/oauth.py` entirely.
2. Delete `EventAdmin.authorize` and `EventAdmin.auth_return`, and the
   `authorize/` and `auth_return/` entries from `EventAdmin.get_urls()`
   (`admin.py:38-51`). The `google_sync/` route stays.
3. Rewrite `EventAdmin.google_sync` (`admin.py:70-107`): drop the
   `oauth.get_credentials()` call, the `if credentials:` branch and the
   "Invalid or missing credentials" error path, and the `cred_status` context
   variable. Construct `Calendar` directly and keep the existing
   `except CalendarError` handling, which is now the single failure path.
4. In `google_sync.html`: delete the credentials-status paragraph (lines 19-23),
   unwrap the submit form from its `{% if cred_status %}` guard (lines 36-40) so
   the button renders whenever there are events, and delete the
   `{% if not event.on_calendar %}` condition (lines 29, 32).
5. Remove the `{% load core_tags %}` on line 2 **only if** `bool_icon` was its
   only use in this template. Check before removing.
6. Remove `GCAL_CLIENT_ID` and `GCAL_CLIENT_SECRET` from
   `sg101/settings/base.py:349-350` and from `.env.example`. `GCAL_CALENDAR_ID`
   and `GCAL_CREDENTIALS_PATH` stay.
7. Grep the whole tree for `oauth`, `GCAL_CLIENT`, `authorize`, `auth_return` and
   `cred_status` before finishing. `reverse('admin:gcalendar-authorize')` in a
   template raises `NoReverseMatch` at render time, not at import, so a missed
   reference will not show up as a failing import.
8. Add a test module for the admin covering `google_sync` and `approve_events`.

## Dependencies
- Task 01 must be complete: `Calendar` must already load its own credentials, or
  `google_sync` has nothing to construct.
- `bio.badges.award_badge` and `bio.badges.CALENDAR_PIN`, already imported by
  `admin.py` and exercised by `approve_events`.

## Implementation Approach
1. Write the admin tests **first**, against the current behavior, so the
   deletions have something to regress against.
2. Delete the two views and their URLs; rewrite `google_sync`.
3. Delete `oauth.py`, then grep for every reference to it and to the two removed
   URL names.
4. Trim the template; render the page in the running stack to confirm no
   `NoReverseMatch` and that the submit button still appears with events pending.
5. Remove the two settings and their `.env.example` entries.
6. Mutation-verify the new tests before closing.

## Acceptance Criteria

1. **The OAuth module is gone and nothing looks for it**
   - Given the working tree after this task
   - When the tree is grepped for `oauth`, `GCAL_CLIENT`, `authorize`,
     `auth_return` and `cred_status`
   - Then no reference to the deleted module, views, URL names or settings remains

2. **The sync page renders without the OAuth furniture**
   - Given an admin user and at least one pending approved event
   - When `admin:gcalendar-google_sync` is requested
   - Then the page returns 200, shows the event, shows the Synchronize button,
     and contains no credentials-status line and no Authorize link

3. **The removed routes are actually unrouted**
   - Given the admin URL configuration
   - When `admin:gcalendar-authorize` or `admin:gcalendar-auth_return` is reversed
   - Then `NoReverseMatch` is raised

4. **A successful sync reports success**
   - Given pending approved events and a `Calendar` mocked to sync cleanly
   - When the sync page is POSTed to
   - Then the success message is rendered and no error list appears

5. **A CalendarError is rendered, not raised**
   - Given a `Calendar` mocked to raise `CalendarError`
   - When the sync page is POSTed to
   - Then the response is 200 and the error text appears on the page, and the
     pending events are still listed

6. **Approval ratchets state and awards the badge**
   - Given events in `NEW`, `EDIT_REQ` and `DEL_REQ`
   - When `approve_events` runs over them
   - Then they become `NEW_APRV`, `EDIT_APRV` and `DEL_APRV`, the count in the
     user message is correct, and `CALENDAR_PIN` is awarded for the `NEW` one only

7. **Approval ignores events in the wrong state**
   - Given an event already in `ON_CAL`
   - When `approve_events` runs over it
   - Then its status is unchanged and it is not counted in the message

8. **The suite is green and the tests have been mutation-verified**
   - Given the full test suite
   - When it is run in the container
   - Then it passes, and each new assertion has been observed to fail against a
     deliberate mutation

## Metadata
- **Complexity**: Low
- **Labels**: gcalendar, deletion, Django admin, OAuth removal, test coverage
- **Required Skills**: Django admin, Django templates, testing
