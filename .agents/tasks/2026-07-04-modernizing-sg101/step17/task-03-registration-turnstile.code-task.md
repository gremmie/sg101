# Task: Add Turnstile to Registration, Stage One

## Description
Put the Turnstile widget on `RegisterForm` and verify it server-side. **Remove
nothing.** `question1`, both honeypots and the two-step code flow all keep
working; registration is deliberately over-protected at the end of this task.

Task 04 does the removals. Splitting them this way means the new check is proven
working before anything old is deleted, and it keeps a user-visible flow change
out of a commit that is otherwise additive.

## Background

### Registration has no CAPTCHA and never has
The plan assumed otherwise. What `accounts/forms.py` actually has is a static
knowledge question (`question1`, answer `101`), a hidden honeypot (`question2`),
a visible honeypot (`question3`), and a session-held code echoed back across two
pages.

### Stage one is the right stage, and the reason is cost
The flow is `register` → `register1` (code displayed) → `register2` (code
entered) → `register_thanks`, plus the emailed activation link at
`register_confirm`.

**The widget goes on `register`.** A challenge at stage one is paid before a
session exists, before a `PendingUser` row is written, and before a confirmation
email is sent. On `register2` a bot gets all three for free and is only stopped
afterwards. Recorded as decided in `STATUS.md`.

### What the measurement says this should catch
Over 19.5 months of `auth.log`, 1,038 registrations succeeded and **seven
accounts registered successfully and were later deactivated for spam** within
`sg101.log`'s ~5-month window — about **1.4/month**, counting only those caught.

What a bot needs today is: answer a fixed constant, leave two fields blank, run
JavaScript, echo a value the server just handed it, and control a mailbox.
**Every one of those is scriptable except the mailbox.** Turnstile is the first
check in this flow that is not.

### The baseline is perishable
`sg101.log` rotates at 100 KB x 10 and holds roughly five months. **The 1.4/month
figure is the only thing "did it work" can be judged against**, and it has to be
re-read before it rotates away. Recorded in the *Open* register of the Step 17
section.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R23)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 17` — especially *Which layer stops bots and which stops
  people* and the decision table
- `.agents/tasks/2026-07-04-modernizing-sg101/step17/task-01-turnstile-verification-helper.code-task.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Render the Turnstile widget in `sg101/templates/accounts/register.html` and
   pass `TURNSTILE_SITE_KEY` into the context from `accounts/views.py:register`.
2. Verify `cf-turnstile-response` in `RegisterForm`, using the task 01 helper.
3. `RegisterForm.__init__` already takes an `ip` kwarg
   (`accounts/views.py:33`). Use it for the helper's `remoteip` rather than
   reaching for the request a second time.
4. A missing token MUST fail validation **without** an HTTP call, matching the
   property `contact/forms.py:45` has today.
5. Failures MUST be logged through the existing `auth` logger with the IP, in the
   same shape as `_validation_error` — the measurement in `STATUS.md` depends on
   that format, and a new failure mode invisible to it would be a blind spot in
   the only instrument this flow has.
6. Change nothing else. `question1`, `question2`, `question3`, `RegisterCodeForm`
   and the `register1`/`register2` views all keep their current behaviour.
7. Existing registration tests MUST keep passing, which means their POST bodies
   gain a token field and the helper is mocked.

## Dependencies
- Task 01's helper and settings.
- `accounts/tests/test_views.py` — 47 tests, many POSTing to `accounts-register`.
  All registration cases need a mocked helper and a token in the body.

## Implementation Approach
1. Add the widget to the template and the site key to the context.
2. Add verification to `RegisterForm`, reusing the `ip` already passed in.
3. Update existing registration tests to mock the helper and supply a token.
4. Add tests for the new outcomes.
5. Verify in a browser with the test keys that registration still completes end
   to end, including the code pages, which are still present.

## Acceptance Criteria

1. **The widget renders on stage one**
   - Given a GET of `accounts-register`
   - When the page renders
   - Then it contains the Turnstile widget and the configured site key, and
     `register1`/`register2` are unchanged

2. **A valid token registers**
   - Given the helper is mocked to report passed
   - When a valid registration is POSTed
   - Then the flow proceeds to `accounts-register1` exactly as before

3. **A rejected token blocks registration**
   - Given the helper is mocked to report rejected
   - When an otherwise valid registration is POSTed
   - Then no `reg_info` is written to the session and the form redisplays with an
     error

4. **A missing token costs nothing**
   - Given a POST with no `cf-turnstile-response`
   - When the form is validated
   - Then validation fails and no HTTP request is made

5. **An outage is distinguishable**
   - Given the helper is mocked to report could-not-determine
   - When a registration is POSTed
   - Then behaviour matches task 01's documented decision and differs from
     criterion 3

6. **Failures are visible to the instrument**
   - Given a rejected token
   - When the failure is logged
   - Then the line carries the client IP and is greppable in the same shape as
     the existing `Accounts/registration [%s]: %s` entries

7. **The old layers still work**
   - Given a POST with the hidden honeypot filled, and separately a wrong
     `question1`
   - When each is validated
   - Then each still fails for its own reason, with its existing log line

8. **Unit test coverage**
   - Given the changed form and view
   - When the suite runs
   - Then every criterion above is covered and each test has been watched to fail

## Metadata
- **Complexity**: Medium
- **Labels**: Turnstile, accounts, registration, antispam
- **Required Skills**: Django forms and views, mocking, log-format discipline
