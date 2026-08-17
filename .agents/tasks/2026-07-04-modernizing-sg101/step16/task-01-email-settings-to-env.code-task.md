# Task: Move Email Configuration to Environment Variables

## Description
Finish the 12-factor work Step 3 skipped. Every email setting in the project is
a hardcoded literal, and `.env.example` contains **no mail variables at all**.
Parameterize them so the provider swap in task 02 is a change of environment
rather than a change of code, and so the same tree can talk to a console
backend in dev, `locmem` in tests, and Postmark in production.

**This task changes no behaviour.** Every new `env()` read takes the current
literal as its default, so an unset environment reproduces exactly what runs
today. That property is what makes the diff reviewable and the rollback trivial.

## Background

### What is hardcoded today
`sg101/settings/base.py:214-216`:

```python
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

`sg101/settings/production.py:68-70`:

```python
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

`sg101/settings/base.py:17-21,197`:

```python
ADMINS = (('Brian Neal', 'admin@surfguitar101.com'),)
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = ADMINS[0][1]
```

`base.py:296` holds `GPP_NO_REPLY_EMAIL = 'no_reply'`, combined with the `Site`
domain at five call sites.

`.env.example` has entries for the secret key, database, Google Calendar, S3 and
reCAPTCHA. **Nothing for mail.** Step 3 retired `secrets.json` and moved all
config to `django-environ`; email was simply missed, because at the time it was
`localhost` in every environment and therefore never looked like configuration.

### `SERVER_EMAIL` is unset, and that breaks on a provider
This is the finding that makes the task non-cosmetic. `SERVER_EMAIL` appears
nowhere in the settings tree, so Django uses its default: **`root@localhost`**.

It is not unused. `production.py:139,155` installs Django's `AdminEmailHandler`
on the `mail_admins` logging handler, and that path calls
`django.core.mail.mail_admins()`, which sends **from `SERVER_EMAIL`** — a
different code path from `core.functions.email_admins()`, which sends from
`no_reply@`. So every unhandled-exception email the site produces currently
claims to come from `root@localhost`.

A local Postfix accepted that without complaint. **Postmark will reject it
outright** — it is not a verified sender signature and the domain is not one
Postmark will sign for. Left unfixed, the first thing to break after cutover is
error reporting, which is exactly the channel you need working when something
breaks after a cutover.

### Do not break the console backend or the test suite
Dev relies on `console.EmailBackend` printing to stdout; keeping that as the
unset default preserves it. The suite needs no email settings at all —
Django's test runner swaps in `locmem` automatically via
`setup_test_environment()`, and `test.py` sets `CELERY_TASK_ALWAYS_EAGER = True`
so `send_mail_task.delay()` runs inline and lands in `mail.outbox`. **Do not add
an explicit `locmem` backend to `test.py`**; it is redundant and would mask a
future misconfiguration of the real default.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 3, which
  established the `django-environ` pattern and `.env.example`
- `step15/task-03-settings-and-env.code-task.md` — the closest precedent for
  this exact shape of change; follow its conventions
- `step16/task-02-postmark-backend.code-task.md` — the consumer of this work

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Parameterize with current values as defaults.** Every read takes the form
   `env('NAME', default=<today's literal>)`, so an empty environment is a no-op.

2. **Settings to add or parameterize**, in `base.py` unless noted:

   | Setting | Default | Note |
   |---|---|---|
   | `EMAIL_BACKEND` | `…console.EmailBackend` | `production.py` defaults to smtp |
   | `EMAIL_HOST` | `localhost` | |
   | `EMAIL_PORT` | `1025` (`25` in production) | `env.int` |
   | `EMAIL_HOST_USER` | `''` | Postmark's API token, as username |
   | `EMAIL_HOST_PASSWORD` | `''` | Postmark's API token again |
   | `EMAIL_USE_TLS` | `False` | `env.bool`; STARTTLS on 587 |
   | `EMAIL_TIMEOUT` | see task 02 | **must not stay `None`** |
   | `DEFAULT_FROM_EMAIL` | `admin@surfguitar101.com` | keep the current value |
   | `SERVER_EMAIL` | `admin@surfguitar101.com` | **new**; replaces `root@localhost` |
   | `GPP_NO_REPLY_EMAIL` | `no_reply` | local part only, as today |

3. **Set `SERVER_EMAIL` explicitly to a real, signable address.** Do not leave it
   defaulting. `admin@surfguitar101.com` is right: it is already
   `DEFAULT_FROM_EMAIL`, already routed to Brian's Gmail per task 06, and on the
   domain Postmark will sign for.

4. **Keep `DEFAULT_FROM_EMAIL` derived from a real setting, not from `ADMINS[0]`.**
   The current `DEFAULT_FROM_EMAIL = ADMINS[0][1]` couples the From address to
   the first admin tuple, so adding a second admin or reordering the tuple would
   silently change every outbound From. Break that coupling while here.

5. **Consider whether `ADMINS` itself should be env-driven.** It is a hardcoded
   tuple naming a person and an address. Parameterizing it is in the spirit of
   Step 3, but it is a nested structure that `django-environ` does not read
   cleanly, and there is exactly one admin. **Recommendation: leave `ADMINS`
   alone** and note the decision, rather than build a parser for a one-element
   list. Record the choice either way so it is not re-litigated.

6. **Do not add mail settings to `test.py` or `docker_test.py`.** See background.

7. **Document each variable in `.env.example`** in the established house style —
   the existing S3 block is the model, explaining not just the name but the
   consequence of getting it wrong.

8. **Do not put a real Postmark token in `.env.example`.** It ships in git and is
   seeded into CI. Blank defaults, with the real values in the git-ignored
   `.env` and in the production environment.

## Dependencies
- None. This lands cleanly before the Postmark account exists, and should — it
  is the prerequisite for task 02.

## Implementation Approach
1. Add the `env()` reads to `base.py` alongside the existing blocks, keeping the
   `#### Email ####` section header structure.
2. Reduce `production.py` to only the settings whose *defaults* legitimately
   differ from base, rather than restating values env now supplies.
3. Add `SERVER_EMAIL`, decouple `DEFAULT_FROM_EMAIL` from `ADMINS`.
4. Extend `.env.example` with a documented mail block.
5. Verify an unset environment reproduces today's values exactly — print the
   settings before and after and diff them.
6. Run the suite under `docker_test`, plus `check` and `check --deploy` and
   `tools/deprecation_gate.sh`.

## Acceptance Criteria
- **Given** an environment with no mail variables set
  **When** `base.py` and `production.py` are loaded
  **Then** every email setting resolves to the value it has today, except
  `SERVER_EMAIL`, which changes from `root@localhost` to
  `admin@surfguitar101.com`
- **Given** `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD` and `EMAIL_USE_TLS` set in the environment
  **Then** Django uses them, with no code change required
- **Given** the test suite
  **Then** mail still lands in `mail.outbox`, and no email backend is named in
  `test.py` or `docker_test.py`
- **Given** `DEFAULT_FROM_EMAIL`
  **Then** it no longer reads from `ADMINS[0][1]`, and adding a second admin
  does not change any outbound From address
- **Given** `.env.example`
  **Then** every new variable is present, documented, and blank where it is a
  credential
- **Given** the suite, `check`, `check --deploy` and `tools/deprecation_gate.sh`
  **Then** all are clean, and the test count is unchanged except for tests added
  here

## Metadata
- **Complexity**: Low
- **Labels**: Settings, 12-Factor, Environment, Email, Step 16
- **Required Skills**: `django-environ`, Django settings layering, Django's
  email and logging settings, knowing which defaults the test runner overrides
