# Task: Log Every Email the Site Sends

## Description
Write one structured log line per outbound message to a dedicated `email.log`,
recording what was sent, why, to how many people, and whether it succeeded.
**Brian's call, 2026-08-16**, asked as "would it be useful to log when the site
sends an email so we can get a better idea of the frequency and purpose of
each."

It would, and the Step 16 planning already demonstrated the gap twice.

## Background

### Two decisions in this step were made without data that should have existed
- **Email-a-friend was deleted on judgement, not measurement.** Task 04 records
  it plainly: no send log, no counter, nothing in the database recording
  invocations, so its usage could not be established. Brian's read was almost
  certainly right, but it was a read.
- **The volume figures underpinning the provider choice are *inferred*, not
  measured.** ~875 forum notifications/month comes from joining posts against
  topic subscriber counts, and the ~1,000–1,800/month total is that plus
  registration and PM counts. It is a good estimate. It is not a measurement,
  and after cutover Postmark's own dashboard will produce the real number —
  at which point a discrepancy will be interesting and unexplainable without
  per-category data.

  **This argument got stronger on 2026-08-17, not weaker.** The figures were
  re-derived from the snapshot after Brian challenged them: 4,487 posts → 9,819
  notification emails in 12 months, ~900/month all-in, not 1,000–1,800. The
  notification estimate held (10,494 inferred vs 9,819 measured); **the summary
  range did not**. And the re-derivation is still not a measurement of *sent
  mail* — it joins today's subscriber set against past posts, cannot see failed
  or suppressed sends, and cannot separate the categories at all. **A database
  query is a better inference, not a substitute for a log.** After cutover,
  Postmark's dashboard gives a total with no category breakdown; this task is
  what makes a discrepancy explainable.

### House precedent
Step 12 kept the search query logging and gave it a dedicated `search.log`:
one INFO line per search with terms, models, **username and IP**. That decision
was Brian's and is recorded in the Step 12 idea-honing. This task follows the
same shape, which also settles the privacy question below by precedent rather
than by fresh argument.

### What exists today, and why it is not enough
`core/functions.py:60` already logs, at DEBUG, with the **entire message body**:

```python
logging.debug('EMAIL:\nFrom: %s\nTo: %s\nReply-To: %s\nSubject: %s\nMessage:\n%s', ...)
```

Three problems: DEBUG is off in production, so it never fires; it emits the full
body, which is far more than is wanted and includes whatever members typed; and
it carries no category, so even if enabled it could not answer "how many
password resets last month" without parsing subject lines.

### The wrapper is not the single choke point — corrected 2026-08-16
Earlier Step 16 notes state that every site email funnels through
`core.functions.send_mail`. **That is wrong, and the exception matters here.**

`accounts/urls.py:48-55` wires **Django's stock
`auth_views.PasswordResetView`** with no `form_class` override. Password reset
therefore sends through `PasswordResetForm.send_mail()` →
`EmailMultiAlternatives` directly:

- it never touches `core.functions.send_mail`, so this task would not log it
- it never touches Celery, so it sends **synchronously inside the user's
  request**
- it gets no retry from task 02, and with `EMAIL_TIMEOUT` unset a slow provider
  hangs the request thread

The last two points belong to task 02, which has been amended. For this task the
consequence is narrower: **a log that silently omits password resets is worse
than no log**, because it would be read as complete.

`defer=False` has no non-test callers, so everything else genuinely does go
through the wrapper and on to Celery.

### The categories to record
Eight, from the call sites: `registration`, `password_reset`,
`forgot_username`, `topic_notification`, `pm_notification`, `contact_form`,
`admin_notification` (the `email_admins`/`email_managers` family — flags, spam
trips, pending downloads and links), and `error_report` (Django's
`AdminEmailHandler`, which sends from `SERVER_EMAIL` and is also outside the
wrapper).

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 12's
  `search.log` decision, the precedent for both the file and the privacy call
- `step16/task-02-postmark-backend.code-task.md` — the retry work this
  coordinates with; both touch `core/tasks.py`
- `sg101/settings/production.py:120-160` — the logging configuration to extend
- `core/functions.py:44-77` and `core/tasks.py:11-21`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Log at send time, not dispatch time**, so the line carries the outcome.
   Task 02 adds retries; a line written when the task was queued would report
   intent and could not distinguish delivered from permanently failed.

2. **Add a `category` argument to `core.functions.send_mail`**, defaulting to
   something explicit like `'uncategorized'` rather than `None`, and pass it
   from all fourteen call sites. Guessing purpose from the subject line is
   fragile and would break the first time a subject is reworded.

3. **Pop `category` before constructing the `EmailMessage`.**
   `core.tasks.send_mail(**kwargs)` currently forwards everything straight into
   `EmailMessage(**kwargs)`, which will raise on an unexpected keyword. Give the
   task an explicit `category=...` parameter.

4. **Tolerate in-flight tasks queued by the previous code.** During a deploy,
   Celery may hold tasks serialized without `category`. The default keeps those
   working; verify it rather than assuming it, because the failure lands on
   whatever mail was queued at deploy time.

5. **Cover the two paths outside the wrapper**, or the log is misleading:
   - **Password reset** — the cleanest fix is to give `PasswordResetView` a
     `form_class` whose `send_mail` routes through `core.functions.send_mail`
     with `category='password_reset'`, which also buys it Celery and task 02's
     retry. That is a behaviour change beyond logging and should be its own
     commit; coordinate with task 02.
   - **`AdminEmailHandler`** — subclass it, or accept the gap and **state it in
     the log's header comment**. An acknowledged gap is fine; a silent one is
     not.

6. **One INFO line per message, no body.** Record timestamp, category, subject,
   recipient(s), From address, and outcome (sent / retrying / failed).
   Never log the body — it is high-volume and contains whatever members wrote.

7. **Log full recipient addresses.** Recommended, following `search.log`, which
   already records usernames and IPs — so the precedent for member-identifying
   data in a dedicated log is set. It is what makes "did this member get their
   confirmation" answerable, which is the main operational reason to build this.
   **Flagged as Brian's call**: the alternative is a count plus a hash. Record
   the decision either way.

8. **Dedicated `email.log` with rotation**, matching `search.log`'s handler
   shape. Do not let this land in the main application log, where it would
   drown the signal it exists to provide.

9. **Do not log to the database.** A row per email is a table nobody will prune
   and a write on a path that must not fail; a rotated file is enough to answer
   frequency and purpose.

10. **Remove or downgrade the existing DEBUG body log** at
    `core/functions.py:60`. Leaving both means one code path with two logging
    schemes and a body dump one settings change away from production.

11. **Keep logging failures from breaking sends.** A logging error must never
    prevent a registration confirmation going out. Guard accordingly.

## Dependencies
- **Task 02** touches the same function in `core/tasks.py`. Land 02 first and
  build on its structure, or the two will conflict.
- Independent of the DNS and inbound work.

## Implementation Approach
1. Land task 02 first.
2. Add the `category` parameter through `core.functions.send_mail` and
   `core.tasks.send_mail`, with the default and the kwargs pop.
3. Thread a category through all fourteen call sites.
4. Add the `email.log` handler and the logger configuration.
5. Write the log line at send time, including the outcome, in the shared path.
6. Handle password reset in its own commit, per requirement 5.
7. Remove the DEBUG body log.
8. Test: assert a line is emitted per send with the right category; assert a
   failed send logs the failure; assert a task queued without `category` still
   runs.
9. After a month in production, compare the measured totals against the
   estimates in STATUS and record the delta.

## Acceptance Criteria
- **Given** a message sent through any of the fourteen wrapper call sites
  **Then** exactly one INFO line appears in `email.log`, carrying category,
  subject, recipient, From and outcome — and **no message body**
- **Given** a send that fails permanently
  **Then** the line records the failure, and the failure is distinguishable from
  a success by a value in the line rather than by its absence
- **Given** a Celery task serialized without a `category` key
  **When** it runs after deploy
  **Then** it succeeds and logs `uncategorized`
- **Given** a password reset
  **Then** it is either logged with `category='password_reset'`, or its absence
  is documented in the log's header comment — not silently missing
- **Given** the logging subsystem raising
  **Then** the email is still sent
- **Given** `core/functions.py`
  **Then** the old DEBUG body log is gone
- **Given** `email.log` after a week in production
  **Then** it answers "how many of each category were sent" by counting lines,
  with no parsing of subjects
- **Given** the suite under `docker_test`
  **Then** it is green

## Metadata
- **Complexity**: Low-Medium — the logging is simple; threading a category
  through fourteen call sites and the two paths outside the wrapper is the work
- **Labels**: Email, Logging, Observability, Celery, Step 16
- **Required Skills**: Django logging configuration, Celery task signatures and
  serialization compatibility across a deploy
- **Decision**: Brian, 2026-08-16 — build it, after asking whether it was worth it
