# Task: Point Django at Postmark, and Give the Mail Task a Retry It Never Needed

## Description
Switch outbound mail from the local Postfix relay to Postmark over SMTP, and
**add retry and timeout handling to `core.tasks.send_mail`, which has neither.**

The second half is not optional polish. Today `msg.send()` hands the message to
a Postfix instance on `localhost` that accepts it in milliseconds and then owns
delivery — queueing, retrying and deferring for days if a remote server is
unreachable. **Pointing `EMAIL_HOST` at an external service silently deletes
that queue.** The same one-line task that could not realistically fail becomes a
network call across the public internet, and a Celery task with no
`autoretry_for` and no timeout turns a transient blip into permanently lost
registration confirmations.

Nothing in the plan flagged this, because from the application's point of view
the change looks like editing a hostname.

## Background

### The task as it stands
`core/tasks.py:11-21`, in full:

```python
@shared_task
def send_mail(**kwargs):
    msg = django.core.mail.EmailMessage(**kwargs)
    msg.send()
```

No `bind`, no `autoretry_for`, no `retry_backoff`, no `max_retries`, no
`acks_late`. Every site email goes through it — `core.functions.send_mail()`
defers to it whenever `defer=True`, which is the default and what all but a
couple of call sites use.

### What the local relay was silently providing
| | Postfix on `localhost` | Postmark over SMTP |
|---|---|---|
| Accepts in | ~1ms, local socket | network RTT, TLS handshake |
| On remote failure | queues, retries for days | task raises |
| On unreachable | cannot really happen | connection error, message lost |
| Delivery guarantee | the MTA's | **whatever Celery is told to do** |

An MTA is, among other things, a durable retry queue. Removing it without
replacing that property is the actual risk in this step, and it is invisible in
a diff that only touches settings.

### Password reset does not use the wrapper, and sends inside the request
**Correction, 2026-08-16.** Earlier notes in this step said every site email
funnels through `core.functions.send_mail`. One does not, and it is the worst
one to miss.

`accounts/urls.py:48-55` wires **Django's stock `auth_views.PasswordResetView`**
with template names and a `success_url` but **no `form_class` override**. So a
password reset sends through `PasswordResetForm.send_mail()` →
`EmailMultiAlternatives` directly. It therefore:

- **never reaches Celery** — it sends synchronously in the request/response
  cycle
- **gets none of this task's retry work**, since that lives in the task
- **hangs the user's request** if the provider is slow, unbounded, until
  `EMAIL_TIMEOUT` is set

Against a `localhost` Postfix this was a sub-millisecond handoff and entirely
invisible. Against `smtp.postmarkapp.com` it is a TLS handshake and a network
round trip **inside a page load**, on the one flow a locked-out member is
already frustrated by. Requirement 2's timeout is what stops it hanging;
requirement 10 is what gives it retries.

`defer=False` has no non-test callers, so everything else genuinely does go
through the wrapper and on to Celery.

### `EMAIL_TIMEOUT` defaults to `None`, which means no timeout
Django's SMTP backend passes `EMAIL_TIMEOUT` to `smtplib`. Unset, there is no
timeout, and a hung connection blocks the Celery worker thread **indefinitely**.
On a local socket that is a non-issue. Against a remote host it is a way to
exhaust the worker pool. Set it.

### Why SMTP rather than the Postmark API
Postmark offers both, and `django-anymail` wraps the API with bounce/open
webhooks and typed errors. **Recommendation: use plain SMTP**, because:

- It needs **no new dependency**. Task 01 already parameterizes every `EMAIL_*`
  setting, so the swap becomes environment-only and the code diff is confined to
  the retry work here.
- Step 16's scope is "replace the local mail server with a deliverable
  provider," and the project's standing scope is lift-and-prune, not new
  features. Webhooks are a feature.
- It keeps `EMAIL_BACKEND` on Django's own backend, so a future move to a
  different provider is again environment-only. Anymail would couple the code to
  Postmark specifically.

Record Anymail as the deliberate upgrade path if bounce webhooks are ever
wanted, so the decision is not silently re-opened.

### Message streams
Postmark separates transactional and broadcast streams, and mail defaults to the
transactional stream unless an `X-PM-Message-Stream` header says otherwise. All
of this site's mail is transactional in Postmark's sense — every message is
triggered by a specific user action, including forum topic notifications, which
are per-topic opt-ins rather than a mailing list. **The default stream is
correct; do not add the header.**

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `step16/task-01-email-settings-to-env.code-task.md` — the prerequisite
- `step16/task-03-dns-email-authentication.code-task.md` — DKIM/Return-Path must
  verify before cutover, or Postmark will refuse to send for the domain
- `core/functions.py:44` — the single wrapper every caller uses
- Celery documentation on `autoretry_for`, `retry_backoff`, `acks_late`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Configure Postmark via environment only**, using task 01's variables:
   `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
   `EMAIL_HOST=smtp.postmarkapp.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`,
   and the **server API token as both `EMAIL_HOST_USER` and
   `EMAIL_HOST_PASSWORD`** — Postmark's SMTP interface expects the token in both
   fields. No code change should be required to point at Postmark.

2. **Set `EMAIL_TIMEOUT` to a bounded value** (10–30s). Never leave it `None`.

3. **Add retry to `core.tasks.send_mail`** with `autoretry_for` covering the
   transient failure modes — `smtplib.SMTPException`, `OSError`/`socket.error`
   — plus `retry_backoff`, `retry_jitter`, and a bounded `max_retries`.

4. **Do not retry permanent failures.** A rejected recipient or a refused sender
   signature will fail identically on every attempt; retrying wastes quota and
   delays the error reaching a human. Distinguish `SMTPRecipientsRefused` and
   `SMTPSenderRefused` from transient errors and let them fail fast, logged.

5. **Log every exhausted retry at ERROR with the recipient and subject.** A
   silently dropped registration confirmation is the failure mode this task
   exists to prevent; if it happens anyway, it must be visible. Take care that
   the log line does not become the site's only record of the message body.

6. **Consider `acks_late` deliberately and record the decision.** With
   `acks_late=True` a worker crash mid-send causes redelivery, so the message
   may be *sent twice*; with the default, a crash loses it. For a registration
   confirmation, a duplicate is a minor annoyance and a loss is a blocked signup
   — which argues for `acks_late=True`. State the reasoning either way rather
   than accepting the default silently.

7. **Do not change `core.functions.send_mail`'s signature.** Fourteen call sites
   depend on it and this task should not touch any of them.

8. **Verify DNS first.** Postmark refuses to send for an unverified domain, so
   task 03's DKIM and Return-Path records must be green before cutover. A
   deploy that flips `EMAIL_HOST` ahead of that fails closed — every message
   rejected — which is safer than the alternative but still an outage of all
   site mail.

9. **Keep the old configuration one environment change away.** Because
   everything is env-driven, rollback is restoring the previous variables and
   restarting. Confirm that actually works before considering the task done.

10. **Route password reset through the wrapper.** Give `PasswordResetView` a
    `form_class` subclassing `PasswordResetForm` whose `send_mail()` calls
    `core.functions.send_mail`, so the flow gains Celery, this task's retry, and
    task 09's logging. **This is a behaviour change beyond pointing at a new
    host — give it its own commit**, and note that it moves the send out of the
    request cycle, which is the point. Preserve the HTML-alternative body if the
    current templates produce one.

11. **Verify `EMAIL_TIMEOUT` applies to the reset path even if requirement 10
    slips.** The timeout is the difference between a slow provider and a hung
    request thread, and it must be in place before cutover regardless of whether
    the refactor lands first.

## Dependencies
- **Task 01** — the env plumbing. Hard prerequisite.
- **Task 03** — domain verified at Postmark before any real send.
- Postmark account with a server API token.

## Implementation Approach
1. Write a test that fails the send with a transient `SMTPException` and asserts
   the task retries; watch it fail against the current no-retry task.
2. Add the retry, timeout and error-classification logic to `core/tasks.py`.
3. Write a test asserting a permanent failure does **not** retry.
4. Set the Postmark variables in the production environment, not in code.
5. Send one real message through Postmark to a mailbox you control, and read the
   full headers before sending anything to a member.
6. Run the suite under `docker_test`, plus `check --deploy` and the gate.
7. Task 07 handles the broader smoke and the bounce-dashboard watch that
   replaced the stale-list warm-up (dropped 2026-08-20 on measurement).

## Acceptance Criteria
- **Given** a transient `SMTPException` raised by the backend
  **When** `core.tasks.send_mail` runs
  **Then** it retries with backoff up to `max_retries`, and the final failure is
  logged at ERROR with recipient and subject
- **Given** that retry test
  **When** run against the unmodified `core/tasks.py`
  **Then** it **fails** — mutation-verified, not merely green
- **Given** `SMTPRecipientsRefused`
  **Then** the task fails immediately without retrying, and logs
- **Given** the settings in any environment
  **Then** `EMAIL_TIMEOUT` is a bounded number, never `None`
- **Given** `EMAIL_HOST=smtp.postmarkapp.com` and a valid token in the
  environment
  **When** a real message is sent to a mailbox under our control
  **Then** it arrives, and its headers show `dkim=pass` with `d=surfguitar101.com`
  and `spf=pass`
- **Given** the previous environment variables are restored
  **Then** mail routes to the old path again with no code change — rollback
  demonstrated, not assumed
- **Given** `core/functions.py`
  **Then** its `send_mail` signature is unchanged and no call site was edited
- **Given** the suite under `docker_test`, `check --deploy` and
  `tools/deprecation_gate.sh`
  **Then** all are clean

## Metadata
- **Complexity**: Medium — the settings change is trivial; the delivery-semantics
  change it implies is not
- **Labels**: Email, Postmark, Celery, Reliability, Settings, Step 16
- **Required Skills**: Django SMTP backend, Celery retry semantics
  (`autoretry_for`, `retry_backoff`, `acks_late`), distinguishing transient from
  permanent SMTP failures
