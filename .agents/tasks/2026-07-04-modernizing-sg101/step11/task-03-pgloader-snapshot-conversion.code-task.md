# Task: Convert the Production Snapshot from MySQL to PostgreSQL with pgloader

## Description
Convert the real production database snapshot from MySQL to PostgreSQL using
`pgloader`, producing a repeatable, documented procedure rather than a one-off
manual run. The output of this task is both a converted database to develop
against and the conversion script that will be re-run at cutover (Step 21).

Correctness of the *data* is verified in task 05. This task owns getting the
conversion to run cleanly and reproducibly, including the encoding and sequence
problems known to be waiting.

## Background
The Dockerized MySQL 5.7 `db` service holds the production snapshot
(`snapshots/sg10120260712.sql.bz2`, git-ignored), originally dumped from **MySQL
5.5.62** on the legacy Ubuntu 14.04 box. **91 tables.**

**Scale** — forum posts are the only large table:

| Table | Rows |
|---|---|
| `forums_post` | 463,221 |
| `forums_topic` | 35,692 |
| `auth_user` | 15,227 |
| `news_story` | 1,694 |

`pgloader` is the right tool for `forums_post`; Django `dumpdata`/`loaddata` is
too slow and memory-hungry at that size, though it remains useful for
cross-checking small tables in task 05.

**Encoding — the known trap.** 83 tables are `utf8` (3-byte,
`utf8_general_ci`), but **8 tables are `latin1` (`latin1_swedish_ci`)**:

```
bandmap_bandentry        contests_contest         contests_contest_contestants
contests_contest_winners countdown_event          django_migrations
messages_flag            user_photos_photo
```

These must be transcoded latin1→UTF8 on load by declaring the source encoding to
pgloader, or the result is mojibake.

**All eight tables are in scope.** `contests`, `countdown`, and `bandmap` were
open questions in `app-triage.md`; the project owner **confirmed on 2026-07-24
that all three are kept**, so there is no pruning shortcut here — every latin1
table must be transcoded correctly. `messages_flag` and `user_photos_photo` are
the most live of the eight, but none may be treated as throwaway.

There is **no `utf8mb4` anywhere**, so 4-byte characters (emoji) cannot be stored
today. Moving to Postgres `UTF8` is a genuine capability upgrade, not just a
port.

**Other watch-items** from the research: `AUTO_INCREMENT` → sequences must be
reset to the correct values after load or the first insert collides; MySQL
`tinyint(1)` → boolean mapping; zero dates (`0000-00-00`) that MySQL 5.5 allowed
and Postgres will reject outright.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (tooling comparison, charset findings, watch-items — read in full)
- `.agents/planning/2026-07-04-modernizing-sg101/research/app-triage.md`
  (keep/prune status of `contests`, `countdown`, `bandmap`)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Produce a **checked-in, re-runnable pgloader command file** — not a shell
   history. It will be run again at cutover against a fresher snapshot, so it
   must be idempotent from a known starting state and take the source/target
   connection details as configuration.
2. Run pgloader from a container so no host installation is required, consistent
   with the project's Docker-first approach.
3. Declare the source encoding per table (or per table set) so the 8 latin1
   tables transcode correctly to UTF8 while the 83 utf8 tables are unaffected.
4. Reset all sequences to `MAX(id) + 1` after load. Verify by inserting a row
   into a representative table and confirming no primary-key collision.
5. Handle `0000-00-00` zero dates explicitly. Decide and document the mapping
   (NULL, a sentinel date, or a pre-conversion cleanup in MySQL) rather than
   letting pgloader choose silently.
6. Capture and review the full pgloader summary output — row counts per table
   and any rejected rows. **A non-zero rejection count must be investigated and
   explained, never accepted as noise.**
7. Document the procedure in `DOCKER.md` (or a dedicated doc it links to) so it
   can be followed at cutover without reconstructing this task's reasoning.
8. Do not modify the MySQL snapshot in place. If pre-conversion cleanup is
   needed, script it against a copy so the original stays pristine.
9. **Widen the three narrow email columns to match `models.py`** — owner
   decision 2026-07-24, taken on the schema drift audit. `accounts_illegalemail
   .email`, `accounts_pendinguser.email`, and `podcast_channel.owner_email` are
   `varchar(75)` in production where the models say 254; Django widened
   `EmailField` in 1.8 and these three never got it, because their apps had no
   migrations to carry the change. pgloader derives widths from the MySQL
   source, so this needs an explicit step or the drift carries into Postgres.
   Prefer a hand-written `AlterField` migration re-asserting each field over a
   pgloader `CAST` rule: it is engine-agnostic, survives a re-run of the
   conversion, applies equally to the MySQL database if wanted, and leaves the
   reason in the migration history. It is a no-op for `makemigrations --check`,
   since the model state does not change. See
   `research/schema-drift-audit.md` §2.

## Dependencies
- Task 01 (running Postgres service, driver, settings)
- Task 04 (every app has migrations; run before this one — see STATUS.md)
- The production snapshot loaded into the MySQL `db` service

## Implementation Approach
1. Write a first-pass pgloader command file covering schema and data; run it and
   read the summary carefully.
3. Iterate on type mappings, encoding declarations, and zero-date handling until
   the run is clean with zero unexplained rejections.
4. Add sequence resets and verify with a real insert.
5. Re-run the whole thing from an empty Postgres database to prove
   reproducibility.
6. Document the procedure for cutover.

## Acceptance Criteria

1. **Conversion Runs Clean and Reproducibly**
   - Given an empty Postgres database and the MySQL snapshot
   - When the checked-in pgloader command file is run
   - Then it completes with zero unexplained rejected rows, and running it again
     from an empty database produces the same result

2. **Latin1 Tables Transcode Correctly**
   - Given all 8 latin1 tables
   - When the conversion completes
   - Then non-ASCII characters render correctly in Postgres in **every one of
     them**, verified by comparing specific rows containing non-ASCII text
     against the MySQL source — not by assuming. If a table contains no
     non-ASCII text to compare, say so explicitly rather than passing it silently

3. **Sequences Are Correct**
   - Given the converted database
   - When a new row is inserted into a representative table
   - Then it receives the next available primary key with no collision, and
     every sequence is confirmed to be at `MAX(id) + 1`

4. **Zero Dates Handled Deliberately**
   - Given the `0000-00-00` dates present in the legacy dump
   - When the conversion runs
   - Then each is mapped according to a documented, deliberate decision, and no
     row is silently dropped because of one

5. **Procedure Is Documented for Cutover**
   - Given the documentation produced
   - When someone follows it at Step 21 with a fresher snapshot
   - Then they can complete a conversion without reconstructing this task's
     reasoning

6. **Original Snapshot Untouched**
   - Given the conversion is complete
   - When the MySQL snapshot and `db` service are inspected
   - Then they are unmodified and the application can still be pointed back at
     MySQL (R17 fallback intact)

## Metadata
- **Complexity**: High
- **Labels**: Database, PostgreSQL, Data Migration, pgloader, Encoding, Step 11
- **Required Skills**: pgloader, MySQL and PostgreSQL administration, character
  encodings, SQL
