# Task: Verify Converted Data Integrity and Smoke the Live Site on Postgres

## Description
Prove that the Postgres database produced by task 03 actually holds the
production data — correctly, completely, and in a form the running application
behaves normally against. This is the task that earns the right to trust the
conversion.

Task 03 established that the conversion *runs*. This one establishes that its
*output is right*.

## Background
The plan's stated done-criterion for Step 11 is "suite green on Postgres;
row counts/data verified vs. MySQL snapshot" (design §C5), and the risk register
is explicit that a converted database must not be trusted before counts and
content are checked (§"DB engine port").

Two properties of this project make verification more important than usual:

- **Test coverage does not cover engine behavior.** The suite has always run on
  sqlite, so MySQL-specific and Postgres-specific behavior has never been under
  test. A green suite is necessary but not sufficient evidence here.
- **The large table is the important one.** `forums_post` holds 463,221 rows —
  the site's actual value. Spot-checking a handful of rows in small tables proves
  little about it.

Step 6 produced a durable lesson worth applying: a green unit suite did not catch
17 broken management commands, which only surfaced when the live Celery worker
and beat ran real scheduled jobs. Boot the full stack, not just the test runner.

`dumpdata`/`loaddata` was rejected as the conversion tool for scale reasons, but
remains useful *here* as an independent cross-check on small tables — a second
opinion produced by a different code path than pgloader's.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§C5 done-criteria, §risk register "DB engine port")

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (expected row counts from the Step 1 snapshot analysis)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 1 smoke-checklist content; Step 6's worker/beat lesson)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Compare row counts for **all 91 tables** between the MySQL source and the
   Postgres target, not a sample. Any difference must be explained, including
   differences that look benign.
2. Verify these known counts from the Step 1 analysis survive the conversion:
   `forums_post` 463,221 · `forums_topic` 35,692 · `auth_user` 15,227 ·
   `news_story` 1,694.
3. Spot-check content across data types that conversions commonly damage:
   non-ASCII text (especially in the transcoded latin1 tables), long-form post
   bodies with markup, dates and datetimes including any that were zero dates,
   booleans that were MySQL `tinyint(1)`, decimals in `donations`, and NULL
   versus empty-string distinctions.
4. Verify foreign-key integrity — no orphaned references introduced by load
   ordering — and that Postgres's constraints are actually enforced rather than
   merely declared.
5. Cross-check a sample of small tables using Django `dumpdata` against both
   engines and diffing the output, as an independent check on pgloader.
6. Run the full test suite against the **converted production database**, not
   just an empty schema. This is a different exercise from task 01.
7. Run the full manual smoke checklist against the converted database with the
   whole stack up: site, forums, news, podcast, links, admin, both password-reset
   flows, and the debug toolbar. Boot the **Celery worker and beat** and confirm
   scheduled tasks run clean — per the Step 6 lesson, the unit suite will not
   catch what they catch.
8. Exercise **write** paths, not only reads. Create a post, upload a photo, send
   a private message. Sequence and constraint problems surface on insert, and a
   read-only smoke would miss them entirely.
9. Record the verification results durably enough to be repeated at cutover.

## Dependencies
- Task 03 (the converted database)
- Task 04 (migrations applied, so the schema is in its final Step 11 state)
- Task 02 (case-insensitivity fixes, so identity behavior is correct during smoke)

## Implementation Approach
1. Script the all-tables row-count comparison so it can be re-run at cutover.
2. Work through the content spot-checks by data-type category, keeping a record
   of what was checked and what was found.
3. Run the `dumpdata` cross-check on a representative set of small tables.
4. Run the suite against the converted database.
5. Bring up the full stack and work the smoke checklist, including writes and
   the worker/beat.
6. Write up the results.

## Acceptance Criteria

1. **All Row Counts Match**
   - Given the MySQL source and the converted Postgres database
   - When all 91 tables are compared
   - Then every count matches, or each difference is explained with a documented
     reason

2. **Known Counts Confirmed**
   - Given the Step 1 baseline figures
   - When the converted database is queried
   - Then `forums_post` = 463,221, `forums_topic` = 35,692, `auth_user` = 15,227,
     and `news_story` = 1,694

3. **Content Survives Intact**
   - Given rows containing non-ASCII text, markup, dates, booleans, decimals, and
     NULLs
   - When compared between engines
   - Then values are equivalent, with particular attention to the transcoded
     latin1 tables and to NULL-versus-empty-string distinctions

4. **Referential Integrity Holds**
   - Given the converted database
   - When foreign-key relationships are checked
   - Then no orphaned references exist and constraints are enforced

5. **Independent Cross-Check Agrees**
   - Given `dumpdata` output from both engines for a sample of small tables
   - When diffed
   - Then they agree, or differences are explained as known serialization
     variation rather than data loss

6. **Suite Green on Real Data**
   - Given the converted production database
   - When the full suite runs against it
   - Then all 567 tests pass (5 skipped)

7. **Live Stack Smokes Clean, Including Writes**
   - Given the full stack running against the converted database
   - When the smoke checklist is worked through
   - Then all pages serve, both password-reset flows work, the Celery worker and
     beat run scheduled tasks without error, and newly created content (a post,
     a photo, a private message) saves and displays correctly

8. **Verification Is Repeatable**
   - Given the recorded results and scripts
   - When cutover arrives at Step 21
   - Then the same verification can be re-run against a fresher snapshot without
     redesigning it

## Metadata
- **Complexity**: Medium
- **Labels**: Database, Data Integrity, Verification, PostgreSQL, Smoke Testing,
  Step 11
- **Required Skills**: SQL across both engines, Django ORM and `dumpdata`, manual
  QA discipline, Celery operations
