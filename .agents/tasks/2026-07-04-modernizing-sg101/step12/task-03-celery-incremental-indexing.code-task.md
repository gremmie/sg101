# Task: Keep the Index Fresh via Celery Signals

## Description
Wire the eight source models to the search index so ordinary site activity keeps
it current: a `post_save` / `post_delete` handler queues a Celery task on
transaction commit, and that task writes or removes the row.

This task also owns the **privacy boundary**. Private-category content must never
enter the index, in either direction — a category that becomes private must lose
its rows, and one that becomes public must gain them.

Both halves of this task are places where a bug is silent. A missed index write
produces content that simply cannot be found, with no error anywhere; a missed
exclusion puts restricted content in front of people who would get a 403 clicking
through. The plan singles these two out as the most likely and most costly
failures in Step 12.

## Background
**Every index write goes through Celery — no exceptions, and no inline path.**
This was reconsidered during design and deliberately settled: indexing a post
costs milliseconds and at 4–5 posts a day nobody would feel a synchronous write,
but with indexing inline in `save()` a bug in vector building breaks *posting*.
That coupling is unacceptable on a site one person maintains. Through Celery the
post succeeds, the index lags, and the fix is a reindex rather than an outage.
A sync/async split was rejected for creating two code paths for one job.

**The non-negotiable detail:**

```python
transaction.on_commit(lambda: reindex_document.delay(ct_id, pk))
```

Never `.delay()` directly in `save()`. The worker can pick the task up before the
transaction commits, read a row that does not exist yet, and index nothing — an
intermittent, load-dependent bug that is miserable to diagnose. Queueing on
commit also gives correct rollback behavior for free: the transaction rolls back,
no task fires.

**There is no author-rename fan-out to build** (revised 2026-07-27, superseding
an earlier design that made it a task of its own). `username` is immutable —
written once at activation, `accounts/utils.py:20` — and full names are indexed
only on the `bio.UserProfile` document, so a profile rename rebuilds exactly one
row through the ordinary path. Do not build a fan-out task, and do not reintroduce
`get_full_name` into content documents; see `search-design.md` §3 for the full
reasoning and the measured numbers.

**Private categories, concretely.** Production has five forum categories, four
public and one gated: `Kahunas`, restricted by group membership — 487 topics and
19,088 posts, about 4% of the forums. The indexer keys off `Category.groups`
being non-empty. There is no access key on the row and no per-user query branch;
the content is simply absent, and is therefore unfindable by search *even for the
members allowed to read it*. That is a known, accepted tradeoff.

**A category's privacy is not a fixed property of the data.** Groups can be added
to or removed from a category at any time through the admin, so `Category` needs
its own handler that reindexes or purges the whole category's topics and posts.
This is the exclusion's second direction and the easier half to forget.

**Registering `post_delete` changes how bulk deletes perform.** Django uses a
"fast delete" path — a single `DELETE` with no per-object work — only when no
signal receivers are registered for the model. Attaching a `post_delete` receiver
to `forums.Post` disables that path, so deleting a topic with hundreds of posts
starts collecting every object and firing a signal per row. Correct, but slower,
and the forums' moderation and spam tools are where it will show. Verify their
behavior at realistic sizes rather than assuming.

**Sweep the other seven documents for equivalent visibility rules.** This is
expected to be a non-issue — news, downloads and weblinks hold submissions in
separate `Pending*` models, so the indexed models should contain approved content
only — but the design asks that it be confirmed rather than assumed.

**Tests are unaffected by the Celery choice:** `CELERY_TASK_ALWAYS_EAGER` is
already set, so tasks execute inline under test. Note that this makes the
`on_commit` ordering bug *invisible* to a naive test — a test that passes under
eager execution proves nothing about commit ordering. Use
`django.test.TestCase.captureOnCommitCallbacks` to assert the queueing actually
happens on commit.

**Accepted cost:** a downed worker means a stale index, where a synchronous write
would have kept working. Task 02's command is the manual remedy, and **task 08
adds a weekly reconcile sweep** that makes such staleness visible rather than
silent — but neither is built here, and neither excuses a write path that drops
documents. This task is what correctness depends on; task 08 only reports on it.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§3 "Index maintenance" and "Access and exclusions")
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q4 private content, Q5 and its 2026-07-27 addendum)
- `forums/tests/test_permissions.py` — the existing lock-down of anon / member /
  superuser / group-moderator access to private categories

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a `reindex_document(content_type_id, object_id)` Celery task that builds
   or updates one row via task 01's registry, and a companion that removes one.
2. Register `post_save` / `post_delete` handlers for all eight source models,
   queueing **only** via `transaction.on_commit`. No `.delay()` call may appear
   directly inside a signal handler or model `save()`.
3. The task must tolerate an object that no longer exists by the time it runs
   (deleted between queueing and execution) without raising — this is a normal
   race, not an error.
4. Skip private-category content on write: a topic or post in a category with
   groups assigned must never produce a row.
5. Handle `Category` changes in **both directions**: gaining groups purges that
   category's topics and posts from the index; losing them indexes them. Bulk
   work here should reuse task 02's batching rather than duplicating it.
6. Confirm and record the visibility rules of the other seven documents. If any
   has a moderation or approval state that the indexed model exposes, handle it;
   if none does, state that in a comment so the next reader need not re-derive it.
7. Configure retries/backoff on the task. A transient database blip should not
   silently drop a document from the index.
8. Check the forums' moderation and spam tools against the fast-delete change
   described above — deleting a busy topic must remain acceptably fast and must
   leave no orphaned index rows.
9. Set `indexed_at` (task 01) on every write. Task 08's reconcile sweep depends
   on it being accurate; a write path that forgets to stamp it makes fresh
   documents look stale forever.
10. Do not build the reconcile sweep here — that is task 08.

## Dependencies
- Task 01 (the registry and the `SearchDocument` model)
- Task 02 (batching, reused for whole-category reindex and purge)
- Celery 5.2.7 and Redis, running from Step 10

## Implementation Approach
1. Write the Celery task and prove it works when called directly.
2. Add signal handlers for one model, with a `captureOnCommitCallbacks` test that
   fails if the task is queued outside `on_commit`.
3. Extend to the remaining seven models.
4. Add the `Category` privacy handler and test both directions against a
   `Kahunas`-shaped fixture.
5. Sweep the other seven documents for visibility rules; record the finding.
6. Verify end to end against the running stack — post a forum message, confirm it
   becomes findable; delete it, confirm it stops being findable.

## Acceptance Criteria

1. **Create, Update, Delete Are Reflected**
   - Given an indexed document type
   - When an instance is created, then edited, then deleted
   - Then the index gains a row, the row's content changes, and the row is removed

2. **Queueing Happens on Commit, Not on Save**
   - Given a `post_save` inside an atomic block
   - When the transaction is rolled back
   - Then no indexing task runs and no row is written; and when it commits, the
     task is queued exactly once, asserted via `captureOnCommitCallbacks`

3. **Private Content Never Enters the Index**
   - Given a category with groups assigned
   - When a topic is created in it and a post added to that topic
   - Then no index rows exist for either

4. **Privacy Changes Propagate Both Ways**
   - Given a public category with indexed topics and posts
   - When a group is assigned to it
   - Then all of its rows are removed; and when the group is removed again, its
     topics and posts are indexed once more

5. **Deleted-Before-Run Is Not an Error**
   - Given an indexing task queued for an object that is deleted before the task
     executes
   - When the task runs
   - Then it completes without raising and leaves no row

6. **Posting Cannot Be Broken by Indexing**
   - Given a deliberately failing document builder
   - When a user posts to the forums
   - Then the post is saved successfully and the failure is confined to the task

7. **Visibility Sweep Recorded**
   - Given the other seven document types
   - When the task is complete
   - Then each has a recorded finding on whether it can expose unapproved or
     moderated content, with handling added where one does

8. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then all eight types have create/update/delete coverage, both privacy
     directions are covered, and the suite is green

## Metadata
- **Complexity**: High
- **Labels**: Search, Celery, Signals, Access Control, Data Integrity, Step 12
- **Required Skills**: Django signals and `transaction.on_commit`, Celery tasks
  and retries, Django permissions model, PostgreSQL full-text search
