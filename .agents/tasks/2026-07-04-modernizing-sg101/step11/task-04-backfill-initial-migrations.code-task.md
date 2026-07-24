# Task: Backfill Initial Migrations for the 21 Unmigrated Apps

## Description
Twenty-one of SG101's twenty-six apps have no `migrations/` package at all. Their
tables date from the pre-1.7 `syncdb` era and have never had a migration trail.
Generate initial migrations for all of them, verify those migrations describe the
schema that actually exists, and mark them applied with `--fake-initial`.

This produces **no schema change**. It is bookkeeping: recording what is already
there. That property is what makes it safe to do inside the engine-swap step, and
it must be preserved — if this task alters the database, something has gone
wrong.

## Background
Django gained migrations in 1.7 (2014); SG101 dates to 2009. When the project
reached 1.7, only five apps ever had migrations generated. The rest were left as
**unmigrated apps**, which Django still supports indefinitely — there is no
deprecation machinery around `run_syncdb` or `unmigrated_apps` in Django 3.2.

**Apps with migrations (5):** `comments` (2), `countdown` (2), `downloads` (2),
`forums` (3), `news` (8). Plus Django's own and third-party `tagging`.

**Apps without migrations (21):** `accounts`, `antispam`, `bandmap`, `banners`,
`bio`, `bulletins`, `contests`, `core`, `donations`, `elsewhere`, `gcalendar`,
`messages`, `oembed`, `podcast`, `polls`, `potd`, `shoutbox`, `smiley`,
`user_photos`, `weblinks`, `ygroup`.

**Why this cannot be deferred past Step 11:**

`run-syncdb` only ever *creates* tables that do not exist. It never *alters* one.
So a model change in an unmigrated app reaches a fresh database automatically —
which is why the 567 tests pass — and reaches an existing database **never**. The
only way to change one of those 21 schemas in production has been a hand-written
`ALTER TABLE`.

Step 12 adds `SearchVectorField` and GIN indexes to the searchable models, and
**four of the seven are unmigrated**: `bio`, `weblinks`, `podcast`, `ygroup`
(`forums`, `news`, `downloads` have migrations). Those are real columns and real
indexes on tables holding real data. Step 12 is the forcing function.

**Why the verification matters more than the generation.** The project has relied
on `makemigrations --check` as a CI gate since Step 9's `c76f920`. That gate is
blind here: a blanket `makemigrations` **deliberately skips apps with no
migrations package** — it only considers an app's models if the app is named
explicitly on the command line. Verified on this codebase:

```
$ makemigrations --check --dry-run   → No changes detected  (exit 0)
$ makemigrations elsewhere --dry-run → Create model InstantMessenger
                                       Create model SocialNetwork … (all 5)
```

So for 21 of 26 apps, `models.py` and the real schema could have drifted apart at
any point in fifteen years and no tool would have said a word. Generating an
initial migration from `models.py` and checking it against the converted
Postgres tables **is** the schema-parity audit — the first this schema has ever
had. Any drift found is worth knowing regardless of the engine change.

**Scope boundary.** Generating initial migrations is not the same as refactoring
schema. The `elsewhere` app's `post_migrate` seeding hook and its possible
`network_id`→FK change are **real** schema/data changes and remain deferred to
Step 19, along with pruning the triage apps. This task records the current shape
of things and nothing more.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-stack.md`
  (what Step 12 will need to add to `bio`, `weblinks`, `podcast`, `ygroup`)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 10 §elsewhere — why its rework is deferred, and the migration-hygiene
  work in Step 9's `c76f920`)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Generate an initial migration for each of the 21 unmigrated apps.
2. **Diff each generated migration against the real converted Postgres schema**
   from task 03 — column names, types, nullability, defaults, indexes, unique
   constraints, and foreign keys. This is the core of the task, not a formality.
3. Produce a written drift report: for every difference between what `models.py`
   describes and what the tables actually contain, record the difference, decide
   whether the model or the database is correct, and state the resolution.
   **Do not silently reconcile drift by editing whichever side is more
   convenient.** Surface it.
4. Apply the migrations with `--fake-initial` against the converted database and
   confirm the tables are untouched — same columns, same indexes, same row
   counts before and after.
5. Confirm a fresh database built purely from migrations (no `--run-syncdb`)
   produces a schema equivalent to the converted one. Two build paths, one
   result.
6. Once every app has migrations, `makemigrations --check` becomes a meaningful
   whole-project gate for the first time. Confirm it is clean and note in the CI
   configuration that its coverage is now complete.
7. Do not change any model's fields to make migration generation tidier. If a
   model looks wrong, report it; fixing it is separate work.
8. Watch for the Python 2 bytes-literal problem Step 9 hit in `c76f920`
   (`verbose_name=b'…'` producing phantom `AlterField` operations on Python 3).
   Newly generated migrations should not reintroduce it.

## Dependencies
- Task 01 (Postgres running, schema creatable on an empty database)
- Task 03 (converted production database to diff against — the migrations must
  be verified against *real* tables, not just a freshly synced one)

## Implementation Approach
1. Generate initial migrations app by app, reviewing each for obvious
   misreadings of the models before moving on.
2. Build the comparison: introspect the converted Postgres schema and compare it
   field by field against what the generated migrations describe.
3. Write the drift report and get the resolutions agreed before applying
   anything.
4. Apply with `--fake-initial`; verify the database is byte-for-byte unchanged.
5. Build a fresh database from migrations alone and compare it to the converted
   one to prove the two paths agree.
6. Confirm the now-meaningful `makemigrations --check` gate is clean.

## Acceptance Criteria

1. **Every App Has Migrations**
   - Given the 26 apps
   - When the task is complete
   - Then all 26 have a `migrations/` package with an initial migration, and none
     relies on `run-syncdb` any more

2. **Drift Report Exists and Is Resolved**
   - Given the comparison between generated migrations and the converted schema
   - When the task is complete
   - Then every discrepancy is recorded with a decision and a rationale, and none
     has been silently absorbed by editing one side to match the other

3. **Faking Changes Nothing**
   - Given the converted database before applying `--fake-initial`
   - When the migrations are applied
   - Then the schema and row counts are identical afterwards, demonstrated by a
     before/after comparison rather than asserted

4. **Both Build Paths Agree**
   - Given a fresh database built from migrations alone, with no `--run-syncdb`
   - When its schema is compared to the converted production database
   - Then they are equivalent, with any remaining difference explained

5. **Suite Green on Both**
   - Given the migrations are in place
   - When the full suite runs against a migrations-built database
   - Then all 567 tests pass (5 skipped)

6. **`makemigrations --check` Now Means Something**
   - Given all 26 apps have migrations
   - When `makemigrations --check` runs
   - Then it reports no changes, and this is recorded as now covering the whole
     project rather than 5 of 26 apps

7. **No Schema Refactoring Smuggled In**
   - Given the diff of this task's changes
   - When reviewed
   - Then it contains only generated migrations and documentation — no model
     field changes, no `elsewhere` FK rework, no app pruning

## Metadata
- **Complexity**: High
- **Labels**: Database, Migrations, Schema Audit, Technical Debt, PostgreSQL,
  Step 11
- **Required Skills**: Django migrations internals, `--fake-initial` semantics,
  PostgreSQL schema introspection, careful diffing
