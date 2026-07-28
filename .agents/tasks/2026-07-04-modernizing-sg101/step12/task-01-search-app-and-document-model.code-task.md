# Task: Create the `search` App, the `SearchDocument` Model, and the Document Registry

## Description
Create the foundation for PostgreSQL full-text search: a new `search` app holding
one denormalized `SearchDocument` model with a GIN-indexed `tsvector`, and a
registry that knows how to turn each of the eight searchable source objects into
one such row.

This task builds **no UI and no signals** — nothing writes rows automatically
yet. It delivers the table, the index, and a pure function per document type that
maps a source object to the values of a row. Tasks 02 and 03 supply the two ways
rows actually get written (bulk and incremental).

Everything downstream depends on the shape decided here, and the stored vector is
the expensive thing to change — revising weights means recomputing every one of
~490k rows. Get this right before anything else is built on it.

## Background
Step 4 deleted the Xapian/Haystack stack but left its artifacts, so what to index
is documented rather than guessed. `sg101/templates/search/indexes/*/*.txt`
records exactly which fields each document contained, and every source model
still carries the `search_title` / `search_summary` properties that define how a
result row displays.

**Why one table rather than a `SearchVectorField` per model.** Results are a
single blended list, relevance-ordered and *paginated*, across eight types. A
global ordering cannot be assembled by querying eight models and merging in
Python — page 2 would require fetching every match from every model first. One
table with one vector, one GIN index and one `ORDER BY` gives ordering and
pagination directly. This supersedes an earlier sketch in `plan.md` that proposed
per-model vector fields.

**Denormalize the display fields.** `title`, `summary`, `url` and `date` are
copied onto the row so a result page renders from this table alone, with no N+1
fan-out across eight models to show ten results.

**The eight documents**, with their recovered index contents:

| Document | Title (A) | Body (B) | Author (C) |
|---|---|---|---|
| `forums.Topic` | `name` | — | `user.username` |
| `forums.Post` | `topic.name` | `body` | `user.username` |
| `news.Story` | `title` | `short_text`, `long_text`, `tags` | `submitter.username` |
| `bio.UserProfile` | `user.username`, `user.get_full_name` | `location`, `occupation`, `interests`, `profile_text`, `signature`, linked site names/URLs | *(is the author)* |
| `weblinks.Link` | `title` | `url`, `description` | `user.username` |
| `downloads.Download` | `title` | `description` | `user.username` |
| `podcast.Item` | `title` | `subtitle`, `summary`, `keywords` | `author` (a text field, not a FK) |
| `ygroup.Post` | `title` | `msg` | — |

**Author full names are deliberately absent from content documents** (revised
2026-07-27 — see `search-design.md` §3, "Index maintenance"). `username` is
immutable, written once at activation (`accounts/utils.py:20`), so embedding it
carries no maintenance cost. `first_name`/`last_name` are user-editable via
`bio.EditUserForm`, and embedding those in content documents would make one
profile edit rebuild up to 25,768 rows. They are indexed **only on the
`bio.UserProfile` document**, where the author *is* the document and a rename
touches exactly one row. Do not reintroduce `get_full_name` into the other seven
builders.

**A gotcha in the existing contract:** `bio.UserProfile.search_summary`
(`bio/models.py:180`) renders `search/indexes/bio/userprofile_text.txt` — the
index template — so the *display* summary and the *indexed* text are currently
the same string. `forums.Topic.search_summary` returns `u''`. Decide deliberately
what each document's stored `summary` should be rather than assuming
`search_summary` is right for all eight.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§3 "Architecture" — the table, the weighting, and why one table)
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q3 what's searchable, Q5 addendum on author names, Q8 score scaling)
- `sg101/templates/search/indexes/*/*.txt` — the recovered per-document field
  lists, and the authority on what each document contained

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Create a new Django app, `search`, added to `INSTALLED_APPS` alongside
   `django.contrib.postgres` (confirm whether the latter is already installed;
   `SearchVectorField` and `GinIndex` require it).
2. Define `SearchDocument` with: a generic pointer (`content_type` FK +
   `object_id`) to the source object, `search_vector` (`SearchVectorField`),
   `title`, `summary`, `url`, `date`, and **`indexed_at`** (see requirement 9).
   Add a **unique constraint on (`content_type`, `object_id`)** so a document
   maps to exactly one row and reindexing is idempotent.
3. Add a **`GinIndex` on `search_vector`** via `Meta.indexes`, plus whatever
   index the ordering and type-filtering need — `ORDER BY rank, -date` and
   filtering by `content_type` are the two query shapes task 04 will issue.
4. Build the vector with `setweight`: **A** title, **B** body, **C** author
   username. On `bio.UserProfile` put username *and* full name at A, profile
   fields at B. Use the `'english'` search configuration (task 07 revisits this).
5. Implement a **registry**: one entry per document type, each able to produce
   the full set of row values (`title`, `summary`, `url`, `date`, and the
   weighted vector) from a source instance. Prefer a declarative registration
   over an eight-branch conditional — tasks 02 and 03 both iterate it, and task
   07 measures per-type.
6. Reuse the existing `search_title` / `search_summary` / `get_absolute_url`
   contracts where they give the right answer; where they do not (see the
   `bio`/`forums.Topic` gotcha above), state the deviation in a comment.
7. `date` must be each document's own natural date (`creation_date`,
   `pub_date`, etc.) — it is the recency tiebreak, so it must be populated for
   every type, with a documented choice for any type lacking an obvious one.
8. Do **not** register signal handlers or write any rows in this task.
9. Add **`indexed_at`** — a timestamp set on every write, recording when the row
   was last rebuilt. It is not used by anything in tasks 01–07; it exists so that
   task 08's reconcile sweep can find documents whose source has been edited
   since they were indexed, by comparing it against the source's `update_date`.
   Include it now rather than later: adding a column afterwards means a migration
   plus a backfill against ~490k rows. Index it if the reconcile query shape
   needs it — task 08 determines that; a plain column is the default.

## Dependencies
- PostgreSQL 16 and Django 3.2 from Step 11 (`SearchVectorField`, `GinIndex`,
  and `SearchRank(normalization=...)` all require Django ≥ 3.1 / PG ≥ 11)
- All 26 apps have migrations as of Step 11 task 04, so a fresh database builds

## Implementation Approach
1. Create the app and its migration; verify the GIN index and unique constraint
   actually appear in the generated SQL (`sqlmigrate`), not just the model.
2. Implement the vector builder and one registry entry — `news.Story` is a good
   first pick: small, has all three weight levels, and only 1,694 rows.
3. Add the remaining seven entries, using the recovered index templates as the
   authority on field lists.
4. Write tests that build a document per type from a fixture object and assert
   the weight labels land where intended.

## Acceptance Criteria

1. **Table and Index Exist as Specified**
   - Given a fresh database and `manage.py migrate`
   - When the schema is inspected
   - Then `SearchDocument` exists with a GIN index on `search_vector` and a
     unique constraint on (`content_type`, `object_id`)

2. **Every Document Type Builds**
   - Given one saved instance of each of the eight source models
   - When the registry builds a row for each
   - Then all eight produce a non-empty `search_vector`, a non-empty `title`, a
     resolvable `url`, and a non-null `date`

3. **Weights Are Applied Correctly**
   - Given a `forums.Post` whose topic name, body, and author username contain
     distinguishable terms
   - When the vector is built and inspected
   - Then the title term carries weight A, the body term B, and the username C

4. **Profile Documents Weight the Author as the Title**
   - Given a `bio.UserProfile` for a user with a full name set
   - When its vector is built
   - Then username and full name both carry weight A, and location / occupation
     / interests / profile text carry B

5. **Full Names Are Absent from Content Documents**
   - Given a `forums.Post`, `forums.Topic`, `news.Story`, `weblinks.Link`, or
     `downloads.Download` by a user with a full name set
   - When the vector is built
   - Then the full name does not appear in it, and the username does

6. **Reindexing Is Idempotent**
   - Given a document already indexed
   - When the same object is indexed again
   - Then the existing row is updated in place and no duplicate row is created,
     and `indexed_at` advances to the time of the rebuild

7. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then every registry entry has a test covering its title, summary, url, date
     and weighting, and the suite is green

## Metadata
- **Complexity**: High
- **Labels**: Search, PostgreSQL, Full-Text Search, Data Model, Step 12
- **Required Skills**: PostgreSQL full-text search (`tsvector`, `setweight`, GIN),
  Django ORM and migrations, `django.contrib.postgres`, content types framework
