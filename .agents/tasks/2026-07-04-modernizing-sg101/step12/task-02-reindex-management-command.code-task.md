# Task: Build the Reindex Management Command and Run the Initial Backfill

## Description
Add `manage.py reindex_search`, the bulk path that populates and rebuilds the
search index, then use it to perform the initial backfill of roughly 490,000
documents from the production snapshot.

This runs before the incremental indexing of task 03 on purpose: it exercises all
eight registry entries against real data rather than fixtures, and it leaves a
populated index that tasks 04 and 07 can be developed and measured against.

The command is not scaffolding to be discarded — it is the permanent answer to
"the weights changed" and "the worker was down", both of which require rebuilding
rows that no signal will ever fire for again.

## Background
Task 01 delivers a registry that maps a source object to row values but nothing
that writes rows. This task supplies the bulk writer.

**Corpus, measured against the snapshot:**

| Document | Rows |
|---|---|
| `forums.Post` | 463,221 (less 19,088 in the private category) |
| `forums.Topic` | 35,692 (less 487 private) |
| `bio.UserProfile` | 15,227 |
| `news.Story` | 1,694 |
| `weblinks.Link`, `downloads.Download`, `podcast.Item`, `ygroup.Post` | remainder |

≈490k rows total, 94% of them forum posts. This is the only bulk operation in
Step 12 — steady-state write volume is 134 forum posts in the last 30 days.

**Scale considerations this creates.** A naive object-at-a-time loop over 463k
posts, each rendering a vector and issuing its own `UPDATE`, will be slow enough
to matter and will hold a growing amount of memory if the queryset is not
iterated carefully. Use `iterator()` with a chunk size, `bulk_create` /
`bulk_update` in batches, and `select_related` on the FKs each builder touches
(`user`, `topic`, `submitter`) to avoid a query per row. Measure before and after
rather than assuming.

**Private categories must be excluded here too.** The exclusion is not solely a
signal-time concern — a backfill that indexes `Kahunas` (487 topics, 19,088
posts) puts restricted content in the index in bulk, which is the worst version
of the leak task 03 guards against. The rule keys off `Category.groups` being
non-empty.

**`bio.UserProfile.search_summary` renders a template per profile**
(`bio/models.py:180`), so profiles are the one type where document construction
does real work per row. 15,227 of them is not alarming, but it is the type to
watch if the backfill is slower than expected.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§3 "Architecture", §4 "Corpus, measured")
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q4 — private categories)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a `reindex_search` management command that rebuilds index rows from the
   registry built in task 01.
2. Support **selective rebuilds**, not just a full sweep — at minimum by document
   type (`--model forums.post`), so a weight change affecting one type does not
   require reprocessing all 490k rows. A single-object or single-author filter is
   a reasonable addition if it falls out cheaply.
3. Support a **full rebuild that is safe to re-run**: rows for objects that no
   longer exist must not survive a full pass, and re-running must not duplicate.
4. **Never index private-category content.** Topics and posts in a category with
   groups assigned must be absent from the index after any run.
5. Batch the work — `iterator()` with a chunk size, bulk writes, and
   `select_related` on the FKs each builder dereferences. The command must
   complete the 463k-post table without unbounded memory growth.
6. Report progress and a final count. A run of this size with no output is
   indistinguishable from a hang.
7. Run inside a transaction per batch, not one transaction for the whole sweep —
   a failure at row 400,000 should not discard the first 399,999.
8. Record the measured backfill wall time and the resulting row count per type;
   task 07 needs a baseline to compare query performance against.

## Dependencies
- Task 01 (the `SearchDocument` model, the GIN index, and the registry)
- The converted production snapshot in PostgreSQL, from Step 11 task 03
- Compose defaults to Postgres as of Step 11 task 06

## Implementation Approach
1. Implement the command for one small type first (`news.Story`, 1,694 rows) and
   verify correctness before reaching for scale.
2. Add batching and `select_related`, then run against `forums.Post` and measure.
3. Add the private-category exclusion and verify against `Kahunas` specifically —
   it is the real one in the data, not a synthetic case.
4. Run the full backfill against the snapshot; record timing and per-type counts.
5. Spot-check a sample of rows for correct title, url, date and vector contents.

## Acceptance Criteria

1. **Full Backfill Completes**
   - Given the converted production snapshot
   - When `manage.py reindex_search` runs to completion
   - Then approximately 490,000 rows exist, with per-type counts matching the
     source tables less private-category content, and the wall time is recorded

2. **Private Content Is Absent in Bulk**
   - Given the `Kahunas` category with its 487 topics and 19,088 posts
   - When a full reindex completes
   - Then zero index rows reference any topic or post in that category

3. **Re-running Is Safe**
   - Given a fully populated index
   - When the command runs again
   - Then the row count is unchanged, no duplicates exist, and rows are updated
     rather than accumulated

4. **Stale Rows Are Removed**
   - Given an index row whose source object has since been deleted
   - When a full reindex runs
   - Then that row no longer exists

5. **Selective Rebuild Works**
   - Given a populated index
   - When the command runs restricted to a single document type
   - Then only that type's rows are rebuilt and other types are untouched

6. **Bounded Memory**
   - Given the 463,221-row `forums.Post` table
   - When the command processes it
   - Then it completes without loading the table into memory, and issues a
     bounded number of queries per batch rather than per row

7. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then tests cover the full sweep, the selective sweep, idempotency, stale-row
     removal, and private-category exclusion, and the suite is green

## Metadata
- **Complexity**: Medium
- **Labels**: Search, PostgreSQL, Management Command, Bulk Data, Step 12
- **Required Skills**: Django management commands and ORM bulk operations, query
  optimization, PostgreSQL full-text search
