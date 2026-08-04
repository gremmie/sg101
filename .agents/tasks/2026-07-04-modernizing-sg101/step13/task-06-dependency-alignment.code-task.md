# Task: Collect the Dependency Caps the Interpreter and Django 4.2 Release

## Description
Lift the pins that were held down by Python 3.7 or by Django's version, now that
both have moved, and evaluate psycopg 3 — which Django supports from 4.2 and
which Step 11 explicitly deferred to this point.

Several of these caps exist only because of each other. Untangling them in one
deliberate pass is cheaper and safer than discovering the chain during Step 14's
5.2 move.

## Background
**The caps that lift, and why each existed** (all verified in
`requirements-docker.txt` on 2026-08-03):

| Pin | Why it was capped | What changes |
|---|---|---|
| `psycopg2==2.9.9` | 2.9.10 needs Python ≥3.8 (Step 11) | free on 3.10 |
| `celery==5.2.7` / `kombu==5.2.4` | 5.3 needs Python ≥3.8 (Step 10) | free on 3.10 |
| `importlib-metadata==4.13.0` | kombu 5.2's shim calls `entry_points().get()`; 5+ returns a `.get()`-less `EntryPoints` | **kombu 5.3 fixes the shim** — this cap exists only to serve the kombu cap |
| `six==1.16.0` | transitive via bleach, html5lib, python-dateutil, python-memcached | task 01 bumped bleach; re-check who still requires it |

The `importlib-metadata` cap is the interesting one: it is a **second-order**
pin. Nothing in this project uses it directly. It is held down purely because
kombu is held down, and kombu was held down purely because of Python 3.7. Both
reasons are gone. Lift them together, and delete the comment explaining a
constraint that no longer applies.

**six is now worth re-examining, but probably does not go.** The pin comment
names four requirers. Task 01 bumped bleach; modern bleach dropped six. The
other three — html5lib, python-dateutil, python-memcached — need checking rather
than assuming. Note that `python-memcached` is scheduled to leave at the
memcached→Redis consolidation, which is not this step. If six still has
requirers, **leave the pin and correct the comment** rather than removing a pin
that would then float; the Step 10 interlude found it drift to 1.17.0 on a test
rebuild the moment it was unpinned.

### psycopg 3 — evaluate, and be willing to say no

Django supports psycopg 3 from 4.2, which is what makes the question askable
here. It is a real decision, not a bump:

- Step 11 chose psycopg2 deliberately and documented why in the pin comment
  (`requirements-docker.txt:39–44`): Django 3.2's PostgreSQL backend imports
  psycopg2 and will not start without it. That constraint is gone; the *choice*
  still needs remaking on its own merits.
- psycopg 3 changes adaptation behavior in ways that can surface as subtly
  different values rather than errors — the failure mode that cost Step 11 task
  05 four defects that row counts, column diffs and the whole suite passed over.
- The `search` app's `django.contrib.postgres` usage is the most driver-sensitive
  code in the tree.

**Deferring to Step 14 or later is an acceptable outcome**, as long as the
reason is recorded. What is not acceptable is leaving the question unexamined
now that it is finally answerable.

### mysqlclient stays — settled 2026-08-02, and the reason is not the obvious one

`mysqlclient==1.4.6` builds fine on 3.10, so nothing forces the question, and it
is tempting to read it as leftover from the Django MySQL backend now that the
site runs on PostgreSQL. It is not. **`tools/pgloader/verify.py` and
`verify_data.py` both import `MySQLdb`**, because they read both engines side by
side — loading a dump uses the `mysql` CLI and converting it uses pgloader, a
standalone tool, and **only the verification needs the Python driver.**

Dropping it would not break the conversion. It would break the *checking* of the
conversion, which is strictly worse, and **nothing would go red** — neither tool
is in the test suite, so the failure would surface during Step 21's cutover
maintenance window. Step 11 task 05 is where those two tools found four defects
nothing else caught, and Step 21 runs the conversion again on a fresh snapshot
whose data nobody has verified yet.

The pin, the Dockerfile's two apt packages (`default-libmysqlclient-dev`,
`default-mysql-client`) and the `mysql` Compose profile are all load-bearing for
this same reason. As of 2026-08-02 all four points of use carry comments saying
so. **This task must not remove any of them** — its job here is to confirm the
comments survived tasks 01–05 intact.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Suggested order" item 4; the mysqlclient section)
- `.agents/planning/2026-07-04-modernizing-sg101/research/upgrade-path.md`
  (the dependency table)
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (for the psycopg evaluation)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump `psycopg2` past the 2.9.9 cap and delete the Python-3.7 justification
   from its comment.
2. Bump `celery` and `kombu` to the 5.3 line, then **remove the
   `importlib-metadata` cap and its comment** — the shim it works around is
   fixed in kombu 5.3.
3. Verify Celery end to end after the bump, not just at import: the search
   indexing tasks, the Beat schedule including the Sunday 03:30 reconcile sweep,
   and the Redis transport.
4. Re-check `six`'s requirers. Keep the pin if any remain and correct the
   comment; do not unpin something that would then float.
5. **Evaluate psycopg 3** and record the decision with its reasoning, whichever
   way it goes. If adopting, it is its own change with its own verification —
   not a line edit alongside these bumps.
6. Confirm `mysqlclient`, the two apt packages and the `mysql` Compose profile
   are still present and still commented. Do not remove them.
7. Every pin comment must describe a constraint that is still true. A comment
   citing Python 3.7 or Django 3.2 after this task is a defect.
8. Keep `requirements.txt` and `requirements-docker.txt` consistent with each
   other.

## Dependencies
- Task 05 (Django 4.2, green) — psycopg 3 support requires it
- Task 01 (Python 3.10) — the interpreter caps lift from it
- Redis and Celery running, for verification

## Implementation Approach
1. Do `celery`/`kombu`/`importlib-metadata` as one change; they are a single
   chain and verifying them together is the point.
2. Exercise Celery for real — queue an indexing task, confirm Beat's schedule
   loads, confirm the worker logs land where the reconcile sweep expects
   (`search/reconcile.py` uses `logging.getLogger('search')` precisely because
   `get_task_logger()` reparents onto `celery.task` and misses `logs/search.log`).
3. Bump `psycopg2` separately and re-run the suite; a driver bump deserves its
   own green run even within the same task.
4. Audit `six`'s requirers with the dependency tree, not from memory.
5. Evaluate psycopg 3 last, and write the decision down before implementing it —
   if it is adopted at all.
6. Re-read every comment in both requirements files and correct the stale ones.

## Acceptance Criteria

1. **Interpreter-Held Caps Lifted**
   - Given Python 3.10
   - When `psycopg2`, `celery` and `kombu` are inspected
   - Then each is past the cap that Python 3.7 imposed, and no comment still
     cites 3.7 as the reason

2. **The Second-Order Cap Is Gone**
   - Given kombu on the 5.3 line
   - When `requirements-docker.txt` is inspected
   - Then the `importlib-metadata` pin and its explanatory comment are removed,
     and Celery starts without the `entry_points().get()` failure the cap
     existed to prevent

3. **Celery Works End to End**
   - Given the bumped celery/kombu
   - When a search indexing task is queued and Beat's schedule is loaded
   - Then the task runs, the worker logs to `logs/search.log`, and the Sunday
     03:30 reconcile sweep is present in the schedule

4. **six Is Correctly Handled**
   - Given the post-bleach dependency tree
   - When `six`'s requirers are enumerated
   - Then the pin is kept with a corrected comment if requirers remain, or
     removed if none do — and the comment matches reality either way

5. **psycopg 3 Decision Recorded**
   - Given Django 4.2, which supports it
   - When the evaluation is complete
   - Then a recorded decision exists with its reasoning, and if psycopg 3 is
     adopted, the search app's query behavior is verified against the Step 12
     measurements rather than assumed

6. **mysqlclient Survived**
   - Given the completed task
   - When the pin, the Dockerfile apt packages and the Compose `mysql` profile
     are inspected
   - Then all are present and all still carry the comment explaining that
     `tools/pgloader/verify*.py` needs them for Step 21

7. **No Stale Pin Comments**
   - Given both requirements files
   - When every comment is read
   - Then none justifies a pin by a constraint that no longer exists

8. **Suite Green and Checks Clean**
   - Given the aligned dependencies
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check` and `makemigrations --check` are clean

## Metadata
- **Complexity**: Medium
- **Labels**: Dependencies, Celery, psycopg, Pins, Step 13
- **Required Skills**: Python dependency resolution, Celery/kombu configuration,
  PostgreSQL drivers
