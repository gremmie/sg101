# Task: Production Logging That Survives Many Processes

## Description
Make production's log files safe to write from many processes at once, by
moving rotation out of the application and onto the host, and find out why a
Celery task's completion is logged nowhere.

**Generated 2026-09-19**, from two items task 03 found and recorded as open in
`STATUS.md` § Step 20 task 03, "Open, and not this task's". Brian chose the
approach the same day: keep the separate files, rotate them externally.

## Background

### The rotation race
`sg101/settings/logging_config.py` gives every file handler the class
`logging.handlers.RotatingFileHandler` — `sg101.log` at 100 KB × 10, and
`auth`, `search`, `email`, `turnstile` at 2 MB × 5. That handler rotates from
inside the process that writes: when the file passes `maxBytes`, *that* process
renames it and opens a new one.

**jaguar never had a problem with that**, because it served the site from one
mod_wsgi daemon process. The production stack does not. Since task 02 the site
runs under gunicorn with `2*CPU+1` worker processes, and since task 03 the
`worker` and `beat` containers mount the same `var/log/django` directory, so a
dozen processes write the same five files. When one rotates, the others keep
writing to the file it just renamed, until each reaches the limit on its own and
rotates again — lines land in the wrong file, and a rotation can discard a file
another process is still writing.

**The fix, decided 2026-09-19:** production uses
`logging.handlers.WatchedFileHandler`, which never rotates. Before each write it
checks whether the file at its path is still the one it opened, and reopens it if
not. Rotation moves to the host's `logrotate`, which renames once for everyone.

### Why not stdout and Docker's log driver
Considered and rejected. It is the container-native answer and has no race, but
it merges every logger into one stream per container, and **the separate files
have earned their keep.** `auth.log` holds ~19 months against `sg101.log`'s ~5,
and that retention is what the 2026 registration-spam analysis ran on. It is
also the natural file for Step 21's fail2ban to watch for login failures.

### Completion lines logged nowhere
In task 03's acceptance run the worker logged
`Task core.tasks.max_users[…] received` and then nothing: no `succeeded` line in
the container's output, nothing in any file under `var/log/django`. Celery's own
`inspect stats` confirmed the task ran. So "did that email go out?" cannot be
answered from the logs today.

**A hypothesis, not a finding:** production sets
`disable_existing_loggers: True`, and Celery's `celery.app.trace` logger — which
writes the `succeeded` line — may exist before Django applies `LOGGING`, in
which case it is disabled. Development sets it `False`. **Measure before
fixing**: read the logger's `disabled` flag inside the running worker, and check
whether development logs the line.

### Development is out of scope, and says why
Development's `web`, `worker` and `beat` also write one shared directory, so it
has the same race in principle. It is left alone: nobody reads development logs
for history, and development has no host `logrotate` to hand rotation to.

## Reference Documentation
**Required:**
- `sg101/settings/logging_config.py` — the shared `LOGGING` builder and its
  per-target table
- `STATUS.md` § Step 20 task 03 — where both items were found, with the
  measurements

**Additional References (if relevant to this task):**
- `STATUS.md` § Step 20 task 01 — why `LOGGING` is built from one table, and the
  logging tests that read each deployment's own dict
- `cutover-runbook.md` — where the host-side install goes

## Technical Requirements
1. Production's file handlers use `WatchedFileHandler`; development keeps
   `RotatingFileHandler`. The difference lives in `logging_config.TARGETS`,
   like the target's other differences.
2. Add a `logrotate` configuration to the repository, one stanza per file, with
   retention **at least** what the files keep today. Measure today's retention
   on jaguar rather than trusting the ~5 and ~19 month figures, which were read
   on 2026-08-27. `auth.log`'s long history is the reason this approach was
   chosen; do not shorten it.
3. Rotate by rename (`create`), not `copytruncate`. `WatchedFileHandler`
   follows a rename; `copytruncate` loses the lines written between the copy
   and the truncate.
4. Find out why a task's completion is not logged, and make it logged in
   production — to the container's output, a file, or both, decided with Brian
   once the cause is known.
5. Add a cutover-runbook entry for installing the `logrotate` configuration on
   the VM.
6. Keep `DeployedLoggingTests` passing, and extend it for the handler
   difference.

## Dependencies
- Task 03 — the production stack and its `var/log/django` mount
- Task 01 — the shared `LOGGING` builder

## Implementation Approach
1. Reproduce the race in the running production stack before changing anything:
   drive enough log volume through several gunicorn workers to cross
   `sg101.log`'s 100 KB, and show a line in the wrong file or missing.
2. Measure the completion-line cause inside the running worker.
3. Tests first for the handler difference; watch them fail.
4. Change the handler; write the `logrotate` configuration; run `logrotate -f`
   against the stack's `var/log/django` and confirm every process follows the
   rename.
5. Mutation-verify the new tests.

## Acceptance Criteria

1. **Production does not rotate from inside the application**
   - Given production settings
   - When the file handlers in `LOGGING` are read
   - Then every one is a `WatchedFileHandler`, and development's are unchanged

2. **Every process follows a rotation**
   - Given the production stack with several gunicorn workers, the worker and beat running
   - When the host `logrotate` rotates `var/log/django`
   - Then new lines from every process land in the new files, and none land in
     the rotated ones

3. **Retention is not shortened**
   - Given the `logrotate` configuration
   - When it is compared against what the files keep on jaguar, as measured
   - Then every file keeps at least as much, `auth.log` included

4. **A task's completion is logged**
   - Given the production stack
   - When a task is queued and the worker runs it
   - Then its completion appears where Brian decided it should

5. **The install is written down**
   - Given `cutover-runbook.md`
   - When section B is read
   - Then installing the `logrotate` configuration on the VM is an entry

## Metadata
- **Complexity**: Medium
- **Labels**: Logging, Celery, Production Hardening
- **Required Skills**: Python logging, logrotate, Celery
