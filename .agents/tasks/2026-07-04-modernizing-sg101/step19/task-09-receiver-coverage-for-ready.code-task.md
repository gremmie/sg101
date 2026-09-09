# Task: Cover the Signal Wiring in `downloads`, `potd` and `weblinks`

## Description
Add tests that fail when each app's `ready()` stops running. Three apps register
their signal receivers there and the suite does not notice when that wiring
disappears — it goes green with the receivers gone and the site quietly stops
maintaining its own denormalized state.

**This task adds tests and changes no application code.** If it turns out a
receiver is wrong, that is a separate finding and a separate commit.

## Background

### The gap, and where it came from
⚠️ **Measured during the Django 4.1 rung — Step 13 task 04, 2026-08-04** (the
plan said 5.0 until 2026-09-08; the table is in
`STATUS-archive-steps-01-15.md` § "Step 13 task 04"). That rung removed
`default_app_config` from eight apps, and the removal's failure shape is silent:
4.1 does not error on `default_app_config`, it stops reading it. Had any app kept
its config somewhere other than `apps.py`, `ready()` would never have run, its
receivers would never have registered, and nothing would have raised.

So each app was mutation-tested by neutering its `ready()`:

| app | suite verdict with `ready()` neutered |
|---|---|
| bio | FAILED (154 errors) |
| forums | FAILED (2 failures, 1 error) |
| antispam | FAILED (2 failures) |
| wiki | FAILED (1 failure) |
| **downloads** | **OK — not caught** |
| **potd** | **OK — not caught** |
| **weblinks** | **OK — not caught** |

Recorded as a pre-existing hole that rung happened to measure, deliberately not
fixed inside a version bump. `wiki` has since been removed in Phase B; the three
uncaught apps remain.

### What is actually unprotected
Each `ready()` is a single import, and everything hangs off it:

- **`downloads/apps.py:7`** → `downloads/receivers.py`, three connections:
  - `on_download_save` (`post_save`, `Download`) — recomputes `Category.count`
    from `Download.public_objects`; on create it updates the parent category
    only, otherwise every category, because a download can be moved between them
  - `on_download_delete` (`post_delete`, `Download`) — recomputes the parent
    category's count **and deletes the uploaded file** (`file.delete(save=False)`)
  - `on_pending_download_delete` (`post_delete`, `PendingDownload`) — deletes the
    uploaded file
- **`potd/apps.py:9`** → `potd/receivers.py`, two connections:
  - `on_photo_save` (`post_save`, `Photo`) — `Sequence.objects.insert_photo(pk)`
  - `on_photo_delete` (`post_delete`, `Photo`) — `Sequence.objects.remove_photo(pk)`
- **`weblinks/apps.py:8`** → `weblinks/receivers.py`, two connections:
  - `on_link_save` (`post_save`, `Link`) — recomputes `Category.count`
  - `on_link_delete` (`post_delete`, `Link`) — recomputes `Category.count`

All connections use a `dispatch_uid`, so re-importing the module does not
double-register — which is why the mutation is *removing* `ready()`'s body rather
than importing the receivers a second time.

### Why this is worth doing now rather than at cutover
Two of the three effects are not recoverable by re-running something. A missed
`Category.count` update is fixable by a recount; a **file that was not deleted**
leaves orphaned uploads accumulating on the VM's disk, and `potd`'s sequence
drifting means the photo of the day repeats or skips. Step 21 moves this code to
a new host and Step 20 rebuilds the container; both are places where an app
config can silently stop loading.

### What "covered" has to mean here
**A test that passes today and still passes with `ready()` neutered is not
coverage of this.** The suite already exercises these models; that is precisely
why the gap went unnoticed for three rungs. Every test this task adds must be
seen to fail with the wiring removed, and the neutering — not a monkeypatched
receiver — is the mutation, because it is the exact effect of the config not
loading. A passing test proves nothing here until it has been seen to fail, and
to fail for the right reason.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS-archive-steps-01-15.md` —
  § "Step 13 task 04" for the original mutation table and the silent-failure shape
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase D]` `ready()` block and Phase D's Tests line
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Re-run the mutation first and confirm the gap is still real.** Three rungs
   and a phase of pruning have happened since it was measured. If an app is now
   caught, say so and drop it rather than adding a test for a hole that closed.

2. **Each app gets tests covering the effects its receivers actually produce**,
   not the fact that a receiver is connected. Asserting
   `post_save.has_listeners(Download)` would pass with a receiver that does
   nothing; assert the count, the deleted file and the sequence position.

3. **File deletion is asserted on the storage, not on the model.** `downloads`
   deletes the uploaded file on both `Download` and `PendingDownload` delete.
   Use a temporary `MEDIA_ROOT` so the test neither reads nor writes real media.

4. **`potd`'s sequence is asserted through `Sequence`**, covering both insert on
   save and removal on delete.

5. **`Category.count` is asserted for both `downloads` and `weblinks`**, and for
   `downloads` this includes the move case — an existing download changing
   category updates both categories, which is why the non-create branch
   recomputes all of them.

6. **Every added test is mutation-verified against a neutered `ready()`** and the
   failure is observed, not assumed. Record which test catches which app.

7. **No application code changes in this task.** If a receiver looks wrong,
   report it rather than fixing it here.

8. **No shipped comment mentions the step or phase number.** Per `CODEASSIST.md`,
   comments describe the code, not the plan.

## Dependencies
- The three apps and their receivers, unchanged by this task
- A temporary `MEDIA_ROOT` for the file-deletion assertions
- The suite must be run the way CI does:
  `manage.py test --noinput --settings=sg101.settings.docker_test`

## Implementation Approach
1. Re-run the neutering mutation on all three apps and confirm each is still
   uncaught; drop any that is now caught.
2. Write the `downloads` tests: count on create, count on move, count on delete,
   file removed on `Download` delete, file removed on `PendingDownload` delete.
3. Write the `potd` tests: inserted on save, removed on delete.
4. Write the `weblinks` tests: count on save, count on delete.
5. Neuter each `ready()` in turn and confirm the intended tests fail — and that
   they fail on the assertion, not on an unrelated error.
6. Restore and run the full suite and the deprecation gate.

## Acceptance Criteria

1. **The gap is confirmed before it is filled**
   - Given the tree as it stands
   - When each of the three apps has its `ready()` body removed and the suite run
   - Then the pre-existing result is reproduced, or any app that is now caught is
     named and dropped from this task with the catching test identified

2. **`downloads` counts and files are covered — mutation-verified**
   - Given `downloads.apps.DownloadsConfig.ready()` neutered
   - When the suite is run
   - Then tests fail covering the created count, the moved-category count, the
     deleted count, and the uploaded file surviving a `Download` delete and a
     `PendingDownload` delete

3. **`potd`'s sequence is covered — mutation-verified**
   - Given `potd.apps.PotdConfig.ready()` neutered
   - When the suite is run
   - Then tests fail showing a saved `Photo` absent from the sequence and a
     deleted `Photo` still in it

4. **`weblinks` counts are covered — mutation-verified**
   - Given `weblinks.apps.WeblinksConfig.ready()` neutered
   - When the suite is run
   - Then tests fail showing `Category.count` unchanged on link save and on
     link delete

5. **The failures are for the right reason**
   - Given each neutered run
   - When the failure output is read
   - Then each is an assertion about the effect, not an import error, a missing
     fixture or a collection error — a test that fails for the wrong reason is
     not evidence

6. **No real media is touched**
   - Given the file-deletion tests
   - When they run
   - Then they operate under a temporary `MEDIA_ROOT` and leave nothing behind

7. **The suite and the gate are green with everything restored**
   - Given all three `ready()` methods intact
   - When the suite and, separately, the deprecation gate are run in the container
   - Then both pass and the test count has grown by the tests added

## Metadata
- **Complexity**: Medium
- **Labels**: downloads, potd, weblinks, signals, test-coverage, mutation-testing, Step 19 Phase D
- **Required Skills**: Django signals and AppConfig.ready, Django test fixtures and file storage, mutation-verified testing
