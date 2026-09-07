# Task: Remove the Vendored django-tagging App

## Description
Delete the vendored `tagging` package, drop its two tables, and remove the last
references to it. This is the retirement the plan has carried since Step 13 task
03; task 05 already moved the site off it, so nothing here changes what a page
renders.

**This task is deliberately separate from task 05 and deliberately small.** Task
05's equivalence check needs the old tables alive to compare against; once that
has passed, the deletion is one revertible commit that touches nothing a reader
can see.

## Background

### Why the app is going
`tagging` was vendored into the repo during Step 13 task 03 (see
`tagging/__init__.py`) because `django-tagging==0.5.0` imports `smart_text`,
which Django 4.0 removed — the import failure aborted `django.setup()`, so zero
tests ran. Vendoring kept that rung to one variable; **it was never an
endorsement.** 0.5.0 is the final release, upstream stopped in 2018, and the
fork has needed hand-fixing on two further rungs since: Django 4.2 made an
all-matching `WHERE` raise `FullResultSet` instead of compiling to empty SQL,
which 500'd the news tag cloud, and `Query.add_filter()` changed arity.

### What is still referencing it after task 05
Verified against the tree on 2026-09-07; task 05 will have cleared the first
group, and this task should confirm that rather than assume it:

- `sg101/settings/base.py:163` — `'tagging'` in `INSTALLED_APPS`
- `tagging/` — the package itself, including `tagging/migrations/0001_initial.py`,
  `0002_on_delete.py`, `0003_adapt_max_tag_length.py`
- `news/tests/test_tag_queries.py` — 57 lines
- `sg101/templates/fixed/colophon.html:14`

### Two admin pages disappear, and that is a decision
`tagging/admin.py` registers **both** `Tag` and `TaggedItem`, so
`/admin/tagging/tag/` and `/admin/tagging/taggeditem/` exist today and go with
the app.

**Neither is a loss, and one is a trap being removed.** The `Tag` rename form
half-applies: the join table follows so every page renders the new name, but each
story's own `news_story.tags` column keeps the old string, and saving any one of
those stories afterwards silently reverts it alone. Merging two tags is not
possible at all — the unique index on `name` refuses it. Both measured
2026-09-07; the detail is in `STATUS.md` § "Step 19 Phase C task 04". Task 07
provides a correct rename and merge as management commands.

### `test_tag_queries.py` is deleted, not ported
Its docstring says what it is for: these queries "are the only place in the
project that reaches into Django's SQL compiler and builds a statement by hand,
so they are the part of the fork most exposed to Django's internals moving
underneath it." **When the fork goes, its subject goes.** The *behaviour* it
covers — tag usage counts feeding the cloud — is covered by task 05's cloud
tests, and this task should check that it is before deleting the file rather
than deleting it and assuming.

### The colophon is a live page
`sg101/templates/fixed/colophon.html:14` credits django-tagging with a link to
`http://code.google.com/p/django-tagging/`, dead for years. The line has been
carried in the plan since 2026-08-04 specifically so it would not be lost.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — § "Step 19 Phase C
  task 04" for the decision, and the Phase B wiki sections for the
  archive-then-remove shape this follows
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase C]` django-tagging block
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Confirm nothing reads the tables before dropping them.** A fresh sweep for
   `tagging`, `TaggedItem`, `TagField` and `tagging_tags` across `*.py` and
   `*.html`, not a re-reading of this task file's list. Task 05 may have left
   something, and a stale inventory is how a "small" deletion becomes an outage.

2. **A migration in `news` drops `tagging_tag` and `tagging_taggeditem`**, after
   `'tagging'` leaves `INSTALLED_APPS`. Deleting an app whose tables remain leaves
   two orphan tables and three orphan `django_migrations` rows; the migration must
   clear the `tagging` rows from `django_migrations` too, or a later
   `makemigrations --check` and a fresh `migrate` on Step 21's converted snapshot
   will disagree about what has been applied.

3. **The drop is irreversible in practice and should say so.** The reverse can
   recreate empty tables; it cannot recreate the data, because task 05's data
   migration is what holds the recovery path. State that in the migration rather
   than writing a reverse that looks like a restore and is not.

4. **Delete `tagging/` in full**, its `INSTALLED_APPS` entry, and
   `news/tests/test_tag_queries.py`.

5. **Update `sg101/templates/fixed/colophon.html:14`.** The credit is no longer
   accurate — the site no longer uses django-tagging — so the entry comes out
   rather than getting a fresher URL. Check the surrounding punctuation: it is a
   comma-joined list and removing an item mid-list is how a stray comma ships to
   a live page.

6. **No shipped comment mentions the step number.** Per `CODEASSIST.md`, comments
   describe the code, not the plan.

## Dependencies
- Task 05, complete and verified — the site must already be running on the array
- `tools/pg_snapshot.sh dump <label>` before the drop migration is applied
- Step 21's cutover runs `migrate` against a freshly converted snapshot, so the
  migration must be correct from zero as well as from the current state

## Implementation Approach
1. Snapshot the database.
2. Sweep the tree for remaining references and fix or confirm each.
3. Remove `'tagging'` from `INSTALLED_APPS`, delete the package and the test file.
4. Write the drop migration, including the `django_migrations` cleanup.
5. Fix the colophon and read the rendered line.
6. Run the suite, the gate, `makemigrations --check`, and a migrate-from-zero on a
   scratch database.

## Acceptance Criteria

1. **Nothing references the app**
   - Given the working tree after the deletion
   - When it is swept for `tagging`, `TaggedItem`, `TagField` and `tagging_tags`
     across Python and templates
   - Then the only matches are unrelated words (`{% load ... _tags %}` modules,
     `message.tags`), each one checked rather than assumed

2. **The tables and their migration history are gone**
   - Given the applied migration
   - When the database is inspected
   - Then `tagging_tag` and `tagging_taggeditem` do not exist and no
     `django_migrations` row names the `tagging` app

3. **A fresh database reaches the same state**
   - Given an empty scratch database
   - When `migrate` runs from zero
   - Then it completes without the `tagging` app present, and
     `makemigrations --check` reports no missing migrations

4. **The colophon renders correctly**
   - Given the deletion
   - When `/fixed/colophon/` is loaded in a browser
   - Then django-tagging is not credited, the surrounding list reads correctly,
     and no stray comma or double space is left behind

5. **The site is unchanged where it should be**
   - Given the same converted production database
   - When the cloud, a common tag page, a rare tag page, a story page, the news
     index and an archive month are compared against task 05's output
   - Then every page is identical — this task changes no rendered content

6. **The suite and the gate are green**
   - Given the full suite and, separately, the deprecation gate on `docker_test`
   - When both are run in the container
   - Then both pass, with `test_tag_queries.py` gone and the count reduced by
     exactly the tests that file held

## Metadata
- **Complexity**: Medium
- **Labels**: news, tagging, pruning, migration, vendored-fork, Step 19 Phase C
- **Required Skills**: Django migrations and app removal, PostgreSQL DDL, careful dependency sweeping
