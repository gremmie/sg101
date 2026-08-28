# Task: Swap the Contact Form to Turnstile, and Retire reCAPTCHA

## Description
Move `contact/` onto the task 01 helper and delete every remaining trace of
reCAPTCHA from the codebase: the settings, the template markup, the
`.env.example` entries, and the context variable. After this task the repository
contains no reference to reCAPTCHA.

The contact form goes first because its current behaviour is known and measured —
225 verifications between 2026-04-01 and 2026-08-27, all passing — so a
regression here is visible. Registration follows in tasks 03 and 04.

## Background

### What is there today
`sg101/templates/contact/contact_form.html:55,66` renders the widget and loads
`api.js`; `contact/views.py:34` passes `RECAPTCHA_SITE_KEY` into the context;
`contact/forms.py:42-58` reads `g-recaptcha-response` and calls `siteverify`.
It is **reCAPTCHA v2 checkbox** — confirmed from the widget attributes, not
assumed. Added 2018-04-14 in `153b6afd`.

### The existing test asserts the exact call
`contact/tests/test_views.py:60`:

```python
post_mock.assert_called_once_with(settings.RECAPTCHA_URL, data={
    'secret': settings.RECAPTCHA_SECRET_KEY,
    'response': 'crazy-google-string',
    'remoteip': '127.0.0.1',
})
```

**This assertion will fail once the helper adds a timeout, and that is wanted.**
It is the clearest available demonstration that the tests actually see the call
shape rather than merely exercising the view. Watch it fail before changing it.

### Single-use tokens, and a defect worth checking for
Turnstile tokens are single-use. If the form fails validation for an unrelated
reason — a missing message, a tripped honeypot — the page re-renders and the
token in the DOM is already spent, so the next submit fails with a confusing
challenge error rather than the real one.

**Whether this bug exists today under reCAPTCHA v2 has not been verified.** Check
it before deciding what to write: if it does, this task fixes a long-standing
defect and should say so; if it does not, this task must not introduce it. The
`3x0000000000000000000000000000000AA` secret reproduces the spent-token response
on demand.

### What the verification is worth
This form has never rejected anything. All 225 verifications in the log window
returned `success: true` and `error-codes` was never populated. The honeypot at
`contact/forms.py:36-40` is a separate check and stays.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R23)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 17`
- `.agents/tasks/2026-07-04-modernizing-sg101/step17/task-01-turnstile-verification-helper.code-task.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Replace the reCAPTCHA block in `ContactForm.clean()` with a call to the task
   01 helper, reading Turnstile's `cf-turnstile-response` POST field.
2. Render the Turnstile widget in `contact_form.html`, replacing the
   `g-recaptcha` div and the `api.js` script tag.
3. Pass `TURNSTILE_SITE_KEY` into the template context in `contact/views.py`,
   replacing `RECAPTCHA_SITE_KEY`.
4. **Delete** `RECAPTCHA_URL`, `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY`
   from `sg101/settings/base.py:419-422` and the two entries at
   `.env.example:43-45`.
5. Distinguish the helper's three outcomes at the form level. A challenge
   rejection and a provider outage MUST NOT produce the same message to the user,
   and the outage path MUST follow the fail-open/fail-closed decision documented
   in task 01.
6. Reset the widget on re-render so a spent token cannot strand a user, per the
   finding above.
7. `grep -ri recaptcha` over the repository MUST return only planning documents
   under `.agents/` after this task.

## Dependencies
- Task 01's helper, settings and `.env.example` entries.
- `contact/tests/test_views.py`, which will need its mock target and its call
  assertion updated.

## Implementation Approach
1. Run the contact tests and watch the call-shape assertion fail against task
   01's timeout. Do not repair it yet.
2. Swap the form, view and template.
3. Update the tests, including a case for each helper outcome.
4. Determine whether the spent-token defect exists today, record the answer, and
   handle it.
5. Remove the reCAPTCHA settings and `.env.example` entries, then grep to confirm.

## Acceptance Criteria

1. **A valid token submits the form**
   - Given the helper is mocked to report passed
   - When a complete contact form is POSTed
   - Then the message is sent and the response redirects to `contact-thanks`

2. **A rejected token blocks the send**
   - Given the helper is mocked to report rejected
   - When a complete contact form is POSTed
   - Then no mail is sent and the form redisplays with a validation error

3. **An outage is not reported as a failed challenge**
   - Given the helper is mocked to report could-not-determine
   - When a complete contact form is POSTed
   - Then the outcome matches the documented fail-open/fail-closed decision, and
     the user-facing message differs from criterion 2's

4. **A missing token is rejected without calling out**
   - Given a POST with no `cf-turnstile-response` field
   - When the form is validated
   - Then it fails validation and **no HTTP request is made** — the current code
     has this property at `contact/forms.py:45` and it must be preserved, because
     it is why bots cost nothing

5. **Spent tokens do not strand a user**
   - Given a submission that fails validation for a non-challenge reason
   - When the page redisplays and the user corrects the error and resubmits
   - Then the submission succeeds

6. **reCAPTCHA is gone**
   - Given the repository after this task
   - When `grep -ri recaptcha` runs
   - Then the only matches are planning documents under `.agents/`

7. **Browser-verified against the real widget**
   - Given the Docker stack with the test keys
   - When the contact form is loaded and submitted with `1x00000000000000000000AA`,
     then again with `2x00000000000000000000AB`
   - Then the first sends and the second is refused, **observed in a browser** —
     Step 16 task 05 found six defects in ten minutes this way that 946 green
     tests did not see

8. **Unit test coverage**
   - Given the changed form and view
   - When the suite runs
   - Then each outcome above is covered and each test has been watched to fail

## Metadata
- **Complexity**: Low
- **Labels**: Turnstile, contact, template, settings cleanup
- **Required Skills**: Django forms and templates, mocking, browser verification
