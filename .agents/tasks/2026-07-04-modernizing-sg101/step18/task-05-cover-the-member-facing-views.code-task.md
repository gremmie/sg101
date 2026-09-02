# Task: Cover the Member-Facing Calendar Views

## Description
Give `gcalendar/views.py` and `gcalendar/forms.py` their first tests. Tasks 01
through 04 cover the client, the admin, the live calendar and the navigation;
none of them touches the half of the pipeline a *member* uses — submitting an
event, listing their own, editing one, and deleting one. This task adds
`gcalendar/tests/test_views.py` and `gcalendar/tests/test_forms.py`, and with
them the "functional test for the calendar page" Step 18 asked for and task
generation did not assign.

These are **characterization tests**: they pin what these five views do today,
including the parts that are surprising. One measured defect falls out of
writing them (below) and is reported, not silently repaired.

## Background

### Why this is a task and not a section of another one
The step's own Tests paragraph promises "unit tests with mocked Google responses
for the insert/update/delete callbacks and their error paths, the `_make_time`
conversion, and a functional test for the calendar page". The first two landed
in task 01. The third has no owner: task 04's tests render `base.html` and
`v3/base.html` to prove the Calendar link resolves, which exercises the URLconf
and not the view behind it. Nothing in the step opens `views.py` at all, so
there is no functional task to fold this into.

Coverage before this task is entirely incidental — other apps importing the
URLconf: `views.py` **30%**, `forms.py` **34%**.

### Measured 2026-09-01: the delete button is dead, and CSRF is why
`gcalendar/static/js/gcalendar_edit.js` POSTs to `/calendar/delete/` with
`data: { id: ... }` and **nothing else** — no `csrfmiddlewaretoken` field, no
`X-CSRFToken` header, and there is no `$.ajaxSetup` anywhere in the tree that
would add one. `delete_event` carries no `csrf_exempt`, and
`django.middleware.csrf.CsrfViewMiddleware` is installed
(`sg101/settings/base.py:114`).

Probed with the test client under `enforce_csrf_checks=True`, sending exactly
what the shipped JS sends: **403, and the event's status is unchanged**. The
button is rendered and wired on the live page (`edit.html:51` and the `<script>`
at line 71), so a member clicking Delete today gets the JS error alert.

**Report it, do not fix it here.** The fix is a line of JavaScript, but which
line depends on whether Brian wants the token in the page or a global
`ajaxSetup` for the site's other AJAX callers, and that is a decision, not a
detail. Write the test that proves the view *accepts* a properly-tokened POST
and a second that pins the 403 for the untokened one, and put the finding in
`STATUS.md`.

### The hidden `time_zone` field is required in practice
`EventEntryForm.time_zone` is `required=False`, so an absent value arrives as
`''` — and `clean_time_zone` hands it straight to `ZoneInfo`, which raises
`ValueError` on the empty string ("keys must be normalized relative paths"),
caught and re-raised as "Invalid timezone." Measured against the container's
Python: `''` → `ValueError`, `'bogus/zone'` → `ZoneInfoNotFoundError`,
`'US/Pacific'` → fine.

The practical consequence is for the tests themselves: **every POST to
`add_event` or `edit_event` must carry a valid `time_zone`**, or the form comes
back invalid and the view renders 200 with errors instead of redirecting. A test
that asserts only on the status code will pass against a form that saved
nothing.

### `edit_events` lists only `ON_CAL`, and `edit_event` does not care
`edit_events` filters `status=Event.ON_CAL`, so a member cannot see — and
therefore cannot reach — their own event until it has actually landed on the
Google calendar. A newly submitted `NEW` event is invisible to its submitter.

`edit_event` has no such filter: it fetches by pk, checks ownership, and on a
valid POST sets `status = Event.EDIT_REQ` **whatever the status was**. So the
reachable path is `ON_CAL → EDIT_REQ`, but a member who kept the URL can move a
`NEW` event to `EDIT_REQ` directly. Both are characterization: pin them, do not
change them. Step 18 is not the place to redesign the member workflow.

### `event.repeat = 'none'` assigns to a field that does not exist
`views.py:44` and `views.py:89` both set `event.repeat` before saving. **`Event`
has no `repeat` field** — not in `models.py`, not in any migration, and not in
`Event._meta.get_fields()`, checked against the running model. The assignment
lands on the instance, is never persisted, and has no effect. It is a leftover
from a schema that predates this app's initial migration.

Leave it alone and **do not write an assertion about it**: a test asserting
`event.repeat == 'none'` on the in-memory instance would pass while proving
nothing, and one asserting it on a reloaded row would fail with
`AttributeError`. Note it in `STATUS.md` alongside the CSRF finding; deleting
two dead lines is Brian's call, and it belongs with the Step 19 sweep rather
than inside a test task.

### `clean()` skips its cross-field check more often than it looks
`EventEntryForm.clean` guards with
`if start_date and start_time and (all_day or (end_date and end_time))`. Because
`start_time` is `required=False`, an all-day event submitted without a start
time never reaches the `start > end` comparison — an all-day event ending before
it begins validates cleanly. Worth one test that records it.

### Things that are safe, and worth not re-deriving
- `index` reads `user.profile.time_zone` for an authenticated user and falls
  back to the literal `'US/Pacific'` for anonymous. `user.profile` cannot raise:
  `bio.receivers.on_user_save` creates a `UserProfile` on every user creation,
  and `time_zone` defaults to `'US/Pacific'` (`bio/models.py:97`).
- That `tz` is not decorative — `index.html:44` interpolates it into the Google
  embed's `ctz=` parameter, so it decides what times the iframe displays. Assert
  it reaches the URL, not merely the context.
- `Event.save()` pops an `html` kwarg; `add_event` passes `form.html` and
  `edit_event` does not, so the edit path re-renders the markup through
  `site_markup` on the way in.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R27)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 18` — the app's coverage table and what the step promised
- `.agents/tasks/2026-07-04-modernizing-sg101/step18/task-02-delete-the-oauth-surface.code-task.md`
  — its admin tests are the sibling half of this app's coverage
- `contact/tests/test_views.py` and `bio/tests/test_views.py` for the house
  view-test shape

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `gcalendar/tests/test_views.py` covering all five views: `index`,
   `add_event`, `edit_events`, `edit_event`, `delete_event`.
2. Add `gcalendar/tests/test_forms.py` covering `EventEntryForm` —
   `clean_time_zone`, the `clean()` cross-field comparison, and the
   `create_forum_thread` field being dropped when an instance is passed.
3. Cover authentication on every protected view: `add_event`, `edit_events` and
   `edit_event` are `@login_required` and must redirect anonymously;
   `delete_event` is not decorated and returns 403 to an anonymous POST.
4. Cover ownership: `edit_event` raises `PermissionDenied` (403) for a
   non-owner, and `delete_event` returns `HttpResponseForbidden` for one.
5. Cover `delete_event`'s three bad-request paths — missing `id`, a
   non-numeric `id`, and an `id` that matches no event — all
   `HttpResponseBadRequest`.
6. Cover the CSRF finding with a client built `enforce_csrf_checks=True`: an
   untokened POST is 403 and leaves `status` alone; a tokened POST succeeds.
7. Cover `edit_events` pagination: `?page=` beyond the last page raises `Http404`
   via the `InvalidPage` handler.
8. Every POST fixture must carry a valid `time_zone`. Assert on the resulting
   `Event` row, not only on the response.
9. Do **not** change `views.py`, `forms.py` or `gcalendar_edit.js` in this task.
   Record the CSRF defect and the dead `event.repeat` assignment in `STATUS.md`
   for Brian's decision.

## Dependencies
- No task ordering. This touches files no other Step 18 task opens, and can run
  before, after or alongside tasks 02-04.
- `bio.receivers.on_user_save` for profile creation, and `core.paginator`'s
  `DiggPaginator` via `edit_events`.
- The templates must render, which means the tests exercise
  `gcalendar/index.html`, `event.html` and `edit.html` as well.

## Implementation Approach
1. Read `views.py` and `forms.py` end to end first. These tests describe
   existing behavior, so anything surprising is a finding to record, not a bug
   to fix mid-task.
2. Write the form tests first — they are pure and they establish the valid POST
   payload every view test then reuses.
3. Write the view tests in URL order, asserting on the database row after each
   state-changing request.
4. Run the CSRF pair last, and confirm the untokened case fails for the reason
   claimed (403 from the middleware) rather than for a missing fixture.
5. Mutation-verify every new test before closing (see `CODEASSIST.md` — a
   passing test that has not been seen to fail is not yet evidence, and a
   mutation that does not reproduce the fault proves nothing either).
6. Write the CSRF finding into `STATUS.md` with the measurement, not the
   conclusion alone.

## Acceptance Criteria

1. **The calendar page shows the viewer's own time zone**
   - Given a logged-in member whose profile time zone is not the default
   - When `gcalendar-index` is requested
   - Then the response is 200 and that time zone appears in the embed's `ctz`
     parameter in the rendered HTML

2. **The calendar page works logged out**
   - Given an anonymous visitor
   - When `gcalendar-index` is requested
   - Then the response is 200 and `US/Pacific` is the time zone rendered

3. **A submitted event is stored as NEW and owned by the submitter**
   - Given a logged-in member and a valid event payload including a `time_zone`
   - When it is POSTed to `gcalendar-add`
   - Then the response redirects to `gcalendar-add?thanks=1`, exactly one
     `Event` exists, its `user` is the member, and its `status` is `NEW`

4. **An invalid submission redisplays the form and saves nothing**
   - Given a payload with an empty `time_zone`, and separately one whose end
     precedes its start
   - When each is POSTed to `gcalendar-add`
   - Then the response is 200, the form reports the error, and no `Event` row
     is created

5. **The edit list shows only the member's own events, and only on-calendar ones**
   - Given the member owns one `ON_CAL` and one `NEW` event, and another member
     owns an `ON_CAL` event
   - When `gcalendar-edit_events` is requested
   - Then only the member's `ON_CAL` event is listed

6. **A page past the end is a 404**
   - Given fewer events than one page holds
   - When `gcalendar-edit_events` is requested with `?page=99`
   - Then the response is 404

7. **Editing an event requests a change rather than applying one**
   - Given the member's own `ON_CAL` event
   - When a valid change is POSTed to `gcalendar-edit_event`
   - Then the response redirects to `gcalendar-edit_events?thanks=1`, the row
     carries the new values, and its `status` is `EDIT_REQ`

8. **Another member's event cannot be read or written**
   - Given an event owned by someone else
   - When `gcalendar-edit_event` is requested with GET and with POST
   - Then both return 403 and the row is unchanged

9. **The delete view marks for deletion rather than deleting**
   - Given the member's own `ON_CAL` event and a CSRF-valid POST of its id
   - When `gcalendar-delete` is requested
   - Then the response is 200 with the id as its body, the row still exists,
     and its `status` is `DEL_REQ`

10. **The delete view rejects what it should**
    - Given an anonymous client, a non-owner, a missing `id`, a non-numeric
      `id`, and an `id` matching no event
    - When each POSTs to `gcalendar-delete`
    - Then the responses are 403, 403, 400, 400 and 400, and no event's status
      changes

11. **The CSRF defect is pinned and reported**
    - Given a client with `enforce_csrf_checks=True` and the exact payload
      `gcalendar_edit.js` sends
    - When it POSTs to `gcalendar-delete`
    - Then the response is 403 and the event's status is unchanged, and the
      finding is written up in `STATUS.md`

12. **Login is required where it is claimed**
    - Given an anonymous client
    - When `gcalendar-add`, `gcalendar-edit_events` and `gcalendar-edit_event`
      are requested
    - Then each redirects to the login URL

13. **The form's own rules are covered**
    - Given `EventEntryForm`
    - When it is validated with an empty, a malformed and a valid `time_zone`,
      with an end before its start, and when constructed with an `instance`
    - Then the first two are invalid with "Invalid timezone.", the third is
      valid, the fourth is invalid with the start-after-end error, and the
      instance form has no `create_forum_thread` field

14. **The suite is green and the tests have been mutation-verified**
    - Given the full test suite
    - When it is run in the container
    - Then it passes, and each new assertion has been observed to fail against a
      deliberate mutation

## Metadata
- **Complexity**: Low
- **Labels**: gcalendar, test coverage, Django views, Django forms, CSRF
- **Required Skills**: Django views and forms, Django test client, testing
