# Task: A Shared Turnstile Verification Helper

## Description
Build the server-side half of the Turnstile integration once, in `antispam/`,
before either form uses it: the settings, the `.env.example` entries, and one
reusable function that posts a token to Cloudflare's `siteverify` and returns a
verdict. Tasks 02, 03 and 04 all consume it.

Nothing user-visible changes in this task. reCAPTCHA keeps working; the contact
form is not touched until task 02.

## Background

### Why `antispam/`, when reCAPTCHA was never there
`plan.md` said Step 17 would "update the `antispam` app", and that was wrong
about reCAPTCHA — `contact/` is its only caller and `antispam/` is a spam-phrase
filter and auth-failure logger with no CAPTCHA in it. **The correction is
recorded in `STATUS.md`.** But the *helper* does belong there: it will have two
callers in different apps, and `antispam/` is the app whose stated job it is.

### The call being replaced has no timeout
`contact/forms.py:47`:

```python
r = requests.post(settings.RECAPTCHA_URL, data={
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': captcha_response,
        'remoteip': get_ip(self.request),
    })
```

No `timeout=`. A hung provider blocks the worker for as long as the OS lets it,
inside a user's request. **This is the same bug class as the `EMAIL_TIMEOUT`
finding in Step 16 task 02** — a call that could not realistically hang when it
was written, against a dependency that can. Fix it here rather than carry it
across; a port that preserves the defect is the one outcome this task should not
produce.

There is also no handling of a non-200 response, a malformed body, or a
`requests` exception. `r.json()` on an HTML error page raises, and the traceback
surfaces as a 500 on a contact form.

### Testing keys make this developable in Docker
Cloudflare publishes dummy keys that work **from any domain including
`localhost`**, with no account and no hostname allowlisting:

| Sitekey | Behaviour |
|---|---|
| `1x00000000000000000000AA` | always passes (visible) |
| `2x00000000000000000000AB` | always fails (visible) |
| `1x00000000000000000000BB` | always passes (invisible) |
| `3x00000000000000000000FF` | forces the interactive challenge |

| Secret | Behaviour |
|---|---|
| `1x0000000000000000000000000000000AA` | always passes |
| `2x0000000000000000000000000000000AA` | always fails |
| `3x0000000000000000000000000000000AA` | returns `timeout-or-duplicate` (token already spent) |

**This is a real improvement over what exists.** `.env.example:43-45` ships blank
reCAPTCHA keys, so a fresh checkout cannot exercise the contact form at all, and
reCAPTCHA needs `localhost` registered in its console before the widget will
render. Shipping the always-passes dummies as the committed defaults means the
Docker stack works on clone.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R23)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 17` — the measurements, the corrections, and the decision table
- Cloudflare: `developers.cloudflare.com/turnstile/` (siteverify, testing keys)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `TURNSTILE_URL`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` and
   `TURNSTILE_TIMEOUT` to `sg101/settings/base.py`, read through `env()` in the
   same style as the existing `RECAPTCHA_*` block at lines 419-422. Leave that
   block in place — task 02 removes it.
2. Default `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` to the **always-passes
   dummy keys**, not to `''`. A checkout with no `.env` must have a working
   registration and contact form in development.
3. Add the same entries to `.env.example`, with a comment saying the committed
   values are Cloudflare's public test keys and that production must override
   them.
4. Write one function in `antispam/` that takes the token and the client IP and
   returns a result object or enum distinguishing at least: **passed**,
   **rejected by Cloudflare** (carrying `error-codes`), and **could not be
   determined** (timeout, connection error, non-200, unparseable body).
5. `TURNSTILE_TIMEOUT` MUST be passed to `requests.post`. Default it to a small
   number of seconds.
6. Log one line per verification at INFO — outcome and error codes — following
   the precedent of `contact/forms.py:52`. Do not log the token.
7. The three outcomes MUST be distinguishable by callers. A provider outage and
   a failed challenge are different events and the caller decides what to do
   about each.

## Dependencies
- `requests`, already a dependency and already used for this call.
- `core.functions.get_ip` for the client address. Note its docstring: it reads
  `REMOTE_ADDR` only, which is correct **because** a front-end proxy rewrites it
  from `CF-Connecting-IP`. On the new VM that rewrite does not exist yet — it is
  recorded against Step 20 in task 03's *Open* register in `STATUS.md`. This task
  inherits the dependency and must not attempt to solve it.

## Implementation Approach
1. Add the settings and `.env.example` entries.
2. Write the helper with its three outcomes and an explicit timeout.
3. Cover it with tests that mock `requests.post`, including the failure modes the
   current code has none of: timeout, connection error, non-200, invalid JSON.
4. Decide and document what a caller should do on **could not be determined**.
   State the choice in a comment: failing open admits bots during an outage,
   failing closed takes the forms down with Cloudflare. Either is defensible;
   an undocumented accident is not.

## Acceptance Criteria

1. **Timeout is passed**
   - Given the helper is called
   - When `requests.post` is invoked
   - Then a `timeout` keyword argument is present and equals `TURNSTILE_TIMEOUT`

2. **A passing token verifies**
   - Given `siteverify` is mocked to return `{"success": true}`
   - When the helper runs
   - Then it reports passed

3. **A rejected token is distinguished from an outage**
   - Given one mocked call returns `{"success": false, "error-codes": [...]}` and
     another raises `requests.Timeout`
   - When the helper runs for each
   - Then the two results are different, and the error codes from the first are
     available to the caller

4. **Malformed responses do not raise**
   - Given `siteverify` is mocked to return a non-200 status, and separately a
     body that is not JSON
   - When the helper runs
   - Then it returns the could-not-determine outcome rather than propagating an
     exception

5. **Development defaults work with no `.env`**
   - Given a settings load with no `TURNSTILE_*` environment variables
   - When the settings are read
   - Then the site key and secret are Cloudflare's always-passes test keys

6. **The token is never logged**
   - Given a verification at INFO
   - When the log line is written
   - Then it contains the outcome and any error codes, and does not contain the
     token

7. **Unit test coverage**
   - Given the helper
   - When the suite runs
   - Then every outcome above has a test, and **each test has been watched to
     fail** against a deliberately broken implementation before being accepted

## Metadata
- **Complexity**: Low
- **Labels**: Turnstile, antispam, settings, 12-factor, resilience
- **Required Skills**: Django settings, `requests`, mocking, error classification
