# Task: Retire the Registration Code Flow and the Two Weakest Layers

## Description
Collapse registration from four pages to one plus the emailed confirmation.
Remove the two-step code workflow, the `101` question and the visible honeypot.
Keep the hidden honeypot. Leave the emailed activation link alone.

**Brian's call, 2026-08-27**, on measured evidence: he built this flow before
reCAPTCHA existed and suspected it had become over-complicated. It had, and the
measurement showed the problem was worse than "extra steps" — two of the four
layers turn away more people than bots.

## Background

### The measurement that decided this
Counting blocks cannot separate a bot turned away from a human tripped up. The
discriminator used was **whether that IP ever completed a registration
afterwards**. Password-mismatch is the control: as close to a pure-human failure
as `auth.log` offers, it reads 68%.

| Layer | Hits | IPs | Later succeeded | Reading |
|---|---|---|---|---|
| `question2` — hidden honeypot | 161 | 111 | **8%** | near-pure bot |
| `question3` — visible honeypot | 276 | 202 | 27% | ~55 real people tripped |
| `question1` — the `101` question | 439 | 281 | 35% | ~98 real people tripped |
| **registration code mismatch** | 214 | 134 | **77%** | almost pure human |
| *(control)* password mismatch | 116 | 99 | 68% | humans by definition |

**The code step performs worse than the control.** It turns away ~1.6 IPs/month
that never return, while the people it stops are overwhelmingly humans who
mistyped or lost the code. Its only anti-bot function is proving the client runs
JavaScript, which task 03's widget now does far better.

`question1`'s answer is a fixed constant — it stops generic crawlers and is one
line of code for anything targeting this site by name.

**The hidden honeypot stays.** At 8% it is the cleanest bot signal in the system,
it is free, and users never see it. It also catches a different class than a
challenge widget does, so it complements Turnstile rather than duplicating it.

**Caveat carried from `STATUS.md`, not to be dropped when quoting these numbers:**
"IP later succeeded" is a proxy. Shared and CGNAT addresses inflate the overlap,
rotating IPv6 deflates it. The robust part is the *ordering* — the code step sits
above the control — not the absolute percentages. And because only failures are
logged, people who abandoned at the code page without failing are invisible, so
the friction cost is a floor.

### What the code flow actually is
`register` puts a generated code in the **session**; `register1` renders a
placeholder; `accounts/static/js/accounts_code.js` fetches it from the
`/register/code/` JSON endpoint (`accounts/views.py:82`, unauthenticated);
`register2` compares what the user types to the session copy. **The code is
handed to the client and echoed back.** It was described in earlier planning as
an emailed code word; that was wrong and is corrected in `STATUS.md`.

### The possession check is elsewhere and stays
`register_confirm` — the emailed activation link — is the only check in this flow
that requires controlling something. It is untouched by this task.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md` (R23)

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`, section
  `PLANNING — Step 17` — the layer measurement, the decision table, and the
  corrections
- `.agents/tasks/2026-07-04-modernizing-sg101/step17/task-03-registration-turnstile.code-task.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Delete** from `accounts/forms.py`: `question1` and `clean_question1`,
   `question3` and `clean_question3`, `RegisterCodeForm`, `CODE_WORD_CHOICES`
   and `generate_registration_code`.
2. **Keep** `question2` and `clean_question2` exactly as they are, including the
   CRITICAL log line.
3. Move the work in `RegisterCodeForm.save()` — creating the `PendingUser`,
   building the activation link, rendering and sending the confirmation email,
   and its `conf. email sent` log line — into `RegisterForm.save()`.
4. **The `conf. email sent` log line MUST keep its exact format.** It is the
   success signal every measurement in `STATUS.md` is built on, and 1,038 of them
   are the denominator. Changing its shape silently invalidates the baseline this
   step will be judged by.
5. `accounts/views.py:register` redirects to `accounts-register_thanks` on
   success. The `reg_info` session round-trip goes away entirely.
6. **Delete** views `register1`, `register2` and `get_code`; URL routes
   `accounts-register1`, `accounts-register2` and `accounts-code`; templates
   `sg101/templates/accounts/register1.html` and `register2.html`; and
   `accounts/static/js/accounts_code.js`.
7. Remove `question1` and `question3` from
   `sg101/templates/accounts/register.html`.
8. `@log_auth_failures('Register')` currently decorates `register2`. Decide
   deliberately whether `register` should carry it now, and record the reasoning —
   `fail2ban` watches that log, so dropping it silently changes what the site
   reports about itself.
9. `grep -rn` for `register1`, `register2`, `accounts-code`, `reg_info`,
   `RegisterCodeForm`, `question1`, `question3` MUST return nothing outside
   `.agents/`.

## Dependencies
- Task 03 must be complete and verified — Turnstile working before anything is
  removed.
- `accounts/tests/test_views.py` — **this is the bulk of the task.** 47 tests,
  most of the registration ones POSTing `question1` and `question3`, and the
  two-stage cases lose their second stage entirely.

## Implementation Approach
1. Move the `PendingUser`-and-email work into `RegisterForm.save()` first, with
   the code flow still present, and prove the email still sends with an identical
   log line.
2. Rewire `register` to redirect to `register_thanks`.
3. Delete the views, routes, templates, JS and form class.
4. Remove the two fields from the form and template.
5. Rewrite the tests. Expect this to be most of the diff.
6. Walk the whole flow in a browser: register, receive the mail, click the link,
   log in.

## Acceptance Criteria

1. **Registration is one form plus confirmation**
   - Given a valid registration with a passing token
   - When it is POSTed to `accounts-register`
   - Then a `PendingUser` is created, the confirmation email is sent, and the
     response redirects to `accounts-register_thanks` with no intermediate page

2. **The success log line is byte-compatible**
   - Given a successful registration
   - When the `conf. email sent` line is written
   - Then it matches the existing format exactly, such that the counting used in
     `STATUS.md` still works unchanged

3. **The hidden honeypot still works**
   - Given a POST with `question2` filled
   - When the form is validated
   - Then it fails, the CRITICAL line is logged with the IP, and no `PendingUser`
     is created

4. **The removed layers are gone**
   - Given the repository after this task
   - When grepping for `register1`, `register2`, `accounts-code`, `reg_info`,
     `RegisterCodeForm`, `question1` and `question3`
   - Then nothing matches outside `.agents/`

5. **The old routes no longer resolve**
   - Given a GET of `/accounts/register/1/`, `/accounts/register/2/` or
     `/accounts/register/code/`
   - When each is requested
   - Then each returns 404

6. **The activation link is unchanged**
   - Given a `PendingUser` created by the new flow
   - When its emailed activation link is followed
   - Then the account activates exactly as before, through the same
     `register_confirm` view and the same key comparison

7. **End to end in a browser**
   - Given the Docker stack with the test keys
   - When a real registration is walked through — form, email, activation link,
     login
   - Then it completes, and the flow is two pages rather than four

8. **Unit test coverage**
   - Given the rewritten registration tests
   - When the suite runs
   - Then it is green, every criterion above is covered, and each new test has
     been watched to fail

## Metadata
- **Complexity**: Medium-High — low risk per change, high test churn
- **Labels**: accounts, registration, simplification, antispam, UX
- **Required Skills**: Django forms/views/URLs, test rewriting, log-format discipline
