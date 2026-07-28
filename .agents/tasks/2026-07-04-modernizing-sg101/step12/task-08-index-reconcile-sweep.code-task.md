# Task: Weekly Index Reconcile Sweep (Reporting Only)

## Description
Add a Celery Beat job that compares the search index against the source tables
once a week and **reports** any drift it finds — documents missing from the index,
orphaned rows whose source is gone, and documents whose source has been edited
since it was indexed.

**It does not repair anything.** That is deliberate, and the point of the task: the
incremental indexing built in task 03 is supposed to make drift impossible, and
this job exists to find out whether that is true. Auto-repair becomes a small
change once there is evidence about what drift actually looks like — building it
now would mask exactly the bugs worth finding.

## Background
Task 03's design accepts one cost: if the Celery worker is down or a task is lost,
the index goes stale and **nothing says so**. This job removes the silence.

**A reconcile does not mean a rebuild.** Task 02's command recomputes ~490k
vectors and exists for weight changes. This job computes nothing — it compares
sets and timestamps in SQL and reports the difference. Its cost scales with the
*drift it finds*, not with the size of the corpus, so on a healthy system it does
essentially no work.

**Measured cost of the dominant term.** Scanning `id, update_date` for every row
of `forums_post` — 463,222 rows, 94% of the corpus, in a 417 MB table:

```
Seq Scan on forums_post  (rows=463222)
Execution Time: 170.122 ms
```

The full eight-type sweep is roughly two anti-joins per type against a ~490k-row
index table. Expect **one to three seconds** end to end. Weekly is free; the
interval could be far tighter if it ever proved useful.

**The data supports timestamp comparison.** Seven of the eight document types
carry an `update_date`, and every one is `db_index=True` — `forums.Post:289`,
`forums.Topic:191`, `news.Story:53`, `downloads:62`, `weblinks:42`,
`podcast:55`, `bio.UserProfile:107`. The eighth, `ygroup.Post`, has no
modification timestamp because it is the imported Yahoo Group archive: frozen
content that cannot drift. Handle it with the set comparison only, and say so in
a comment rather than leaving the asymmetry to be rediscovered.

`SearchDocument.indexed_at` (task 01) is the other half of the comparison.

**Three kinds of drift, all detectable in SQL:**

| Drift | Detection |
|---|---|
| Missing | source row with no index row |
| Orphaned | index row whose source is gone |
| Stale | `indexed_at` < source `update_date` |

**What this actually protects against**, so the scope stays honest: a downed or
wedged worker, a lost task, a flushed Redis, a bug in the indexing path, and
snapshot reloads or direct database surgery. It does **not** exist to paper over
bulk ORM operations — a check of `forums/`, `news/`, `downloads/`, `weblinks/`,
`podcast/`, `ygroup/` and `bio/` found no `.update()`, `bulk_create` or
`bulk_update` against any indexed model, so signals see every application write
today. If that changes, this job is what will notice.

**Private categories are drift too, in the direction that matters most.** An
index row for a `Kahunas` topic or post is a privacy failure, not a staleness
one. The sweep should report those separately and prominently rather than
folding them into a count of missing documents.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§3 "Index maintenance" — the accepted staleness cost this job addresses)
- `.agents/tasks/.../step12/task-03-celery-incremental-indexing.code-task.md`
  (the write path whose correctness this job measures)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a Celery task that reconciles all eight document types and reports its
   findings. Schedule it **weekly** on Beat.
2. Detect all three drift kinds — missing, orphaned, stale — per document type.
   For `ygroup.Post`, detect missing and orphaned only, since it has no
   `update_date`; note the reason in a comment.
3. Do the comparison **in SQL**, as anti-joins between the index table and each
   source table. Do not pull PK sets into Python and diff them there — that
   defeats the whole cost argument.
4. **Report only. Repair nothing.** No writes to `SearchDocument` from this task.
5. Report **private-category rows separately** from ordinary drift. Any index row
   pointing at content in a category with groups assigned is a privacy defect and
   must be surfaced as such.
6. Log to the `search` logger from task 04 — at `INFO` when clean, at `WARNING`
   when any drift is found, so it is greppable in `logs/search.log` next to the
   query lines. Include per-type counts and a bounded sample of offending IDs;
   do not log 400,000 primary keys.
7. Confirm the queries use indexes rather than degrading into nested-loop joins
   over 463k rows, and record the measured runtime of a real sweep.
8. Make it runnable on demand as a management command as well as on the schedule
   — a job you cannot run by hand when you suspect a problem is much less useful.

## Dependencies
- Task 01 (`SearchDocument`, including `indexed_at`)
- Task 03 (the write path that stamps `indexed_at`; drift is meaningless without it)
- Task 04 (the `search` logger and its `search.log` handler)
- Celery Beat, running since Step 10

## Implementation Approach
1. Write the three detection queries for one type and check their plans with
   `EXPLAIN ANALYZE` against the full index before generalizing.
2. Generalize across the registry from task 01, special-casing `ygroup.Post`.
3. Add the private-category check as its own query with its own report line.
4. Wire up logging and the management-command entry point, then the Beat schedule.
5. Run it against the fully backfilled index and record the runtime and the
   baseline drift — which should be zero.
6. Prove it detects real drift: stop the worker, make changes, restart, and
   confirm the sweep reports exactly what was missed.

## Acceptance Criteria

1. **A Clean Index Reports Clean**
   - Given a fully backfilled index with the worker running normally
   - When the sweep runs
   - Then it reports zero drift of all three kinds and logs at `INFO`

2. **Missing Documents Are Detected**
   - Given index rows deleted directly from the database
   - When the sweep runs
   - Then exactly those documents are reported missing, with per-type counts

3. **Orphaned Rows Are Detected**
   - Given an index row whose source object has been deleted behind the signals
   - When the sweep runs
   - Then that row is reported as orphaned

4. **Stale Documents Are Detected**
   - Given a source object edited while the worker was stopped
   - When the worker restarts and the sweep runs
   - Then that document is reported stale via `indexed_at` < `update_date`

5. **Private-Category Rows Are Reported Separately**
   - Given an index row pointing at content in a category with groups assigned
   - When the sweep runs
   - Then it is reported distinctly from ordinary drift and logged at `WARNING`

6. **Nothing Is Repaired**
   - Given an index with drift of every kind
   - When the sweep runs
   - Then the drift still exists afterwards and no row was written, updated or
     deleted

7. **Cost Is as Expected**
   - Given the full ~490k-row index
   - When a sweep runs
   - Then it completes in seconds, its queries use indexes rather than scanning
     repeatedly, and the measured runtime is recorded

8. **Runnable on Demand**
   - Given a suspicion of drift between scheduled runs
   - When the operator invokes the management command
   - Then the same sweep runs and reports identically

9. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then each drift kind has a test that seeds the condition and asserts it is
     reported, a clean index is asserted to report clean, the report-only
     guarantee is asserted, and the suite is green

## Metadata
- **Complexity**: Medium
- **Labels**: Search, Celery Beat, Data Integrity, Monitoring, Observability,
  Step 12
- **Required Skills**: SQL anti-joins and query plans, Celery Beat scheduling,
  Django ORM and management commands, PostgreSQL performance analysis
