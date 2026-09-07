# Task: rename_tag and merge_tags Management Commands

## Description
Add two management commands that rename a tag across every story that carries it,
and merge one tag into another. **Both are new capability, not restored
capability** — the system being retired could not do either correctly.

## Background

### What the old system actually did, measured rather than assumed
`tagging/admin.py` registered `Tag`, so `/admin/tagging/tag/` offered a rename
form. Measured on 2026-09-07 in a rolled-back transaction against the converted
production database:

```
BEFORE            /news/tag/video/ -> 57 stories   /news/tag/clips/ -> 0

AFTER THE RENAME  /news/tag/video/ -> 0            /news/tag/clips/ -> 57
   story 634   page shows clips,eliminators    column holds 'eliminators video'
   story 717   page shows chicchi,clips        column holds 'chicchi video'

AFTER STORY 634 IS SAVED (its tags untouched)
   /news/tag/video/ -> 1 story      /news/tag/clips/ -> 56 stories
```

The rename applied to all 57 stories at once — and left every one of them holding
the *old* string in `news_story.tags`, because the rename never touched the
denormalized column. **Saving any of those stories afterwards silently reverted
it alone**, recreating `video` and splitting the set across two tag pages, with
no error anywhere. A renamed tag did not revert in one go; it eroded, one story
at a time, over however many years it took for those stories to be edited. (Only
8 of 1,694 stories have been edited in the last two years, so the erosion is
slow. It is also permanent: nothing heals it.)

**Merging was not possible at all** — renaming a tag onto an existing name hit
the unique index: `duplicate key value violates unique constraint
"idx_600078_name"`.

### Why the ArrayField makes both correct and trivial
There is no second copy of the tag string to go stale, so each operation is one
statement against one column:

```sql
UPDATE news_story SET tags = array_replace(tags, 'video', 'clips');
```

Merge is the same statement plus a de-duplication, because a story carrying both
`show` and `release` would otherwise end up with `release` twice.

### Scope
`Story` and `PendingStory` both carry tags (`news/models.py:51`, inherited from
`StoryBase`), so both commands operate on both models. `PendingStory` is empty
today — 0 rows — but it is not empty by design, and a command that silently
skipped it would be wrong the first time a submission was pending.

**`FORCE_LOWERCASE_TAGS` behaviour must be preserved.** Every one of the 1,001
live tags is lowercase with no case variants; a command that let `Video` into the
data would create a tag no URL resolves, since the tag page lowercases what it
looks up.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — § "Step 19 Phase C
  task 04", for the rename measurement above and the tag distribution
- `search/management/commands/reindex_search.py` — the house shape for a
  management command in this project
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **`rename_tag <old> <new>`** — renames across `Story` and `PendingStory`,
   lowercasing both arguments the way a save would.

2. **`merge_tags <source> <destination>`** — folds `source` into `destination`,
   **de-duplicating** any story that carried both. A story ending up with the same
   tag twice is the failure this command exists to avoid.

3. **`rename_tag` refuses a rename that is really a merge.** If `<new>` is already
   in use, the command must say so and point at `merge_tags` rather than quietly
   producing duplicates. This is the case the old admin form raised an
   `IntegrityError` on, and the friendly version of that refusal.

4. **Both report what they changed** — the number of stories touched per model,
   and nothing if there were none. A command that prints nothing on a typo'd tag
   name is indistinguishable from one that worked.

5. **Both run in a transaction**, so a failure part-way leaves the tag as it was.

6. **A `--dry-run` on both**, reporting the counts without writing. These operate
   on production content with no admin undo behind them.

7. **Tests, mutation-verified**, per `CODEASSIST.md`. The cases that matter: a
   story carrying both tags in a merge, a tag that does not exist, a rename onto
   an existing name, `PendingStory` rows included, case normalization, and
   `--dry-run` writing nothing.

## Dependencies
- Task 05, complete — the commands operate on the `ArrayField`
- PostgreSQL `array_replace` / `array_remove`, or the ORM equivalent

## Implementation Approach
1. Write the tests first, including the duplicate-on-merge case.
2. Implement `rename_tag`, including the refusal when the target exists.
3. Implement `merge_tags` with de-duplication.
4. Add `--dry-run` to both and confirm it writes nothing.
5. Exercise both against the converted production database on a snapshot, then
   restore.

## Acceptance Criteria

1. **A rename reaches every story and nothing reverts**
   - Given 57 stories tagged `video`
   - When `rename_tag video clips` runs and one of those stories is then saved
     with its tags untouched
   - Then all 57 stories carry `clips`, none carries `video`, and the save changes
     nothing — the erosion the old admin form caused does not occur

2. **A merge de-duplicates**
   - Given a story carrying both `show` and `release`
   - When `merge_tags show release` runs
   - Then the story carries `release` exactly once, and no story anywhere carries
     `release` twice

3. **A rename onto an existing tag is refused**
   - Given `release` already in use
   - When `rename_tag show release` runs
   - Then the command exits with an error naming `merge_tags` and changes nothing

4. **Both models are covered**
   - Given tagged rows in `Story` and in `PendingStory`
   - When either command runs
   - Then both models are updated and the report names the count for each

5. **Case is normalized**
   - Given `rename_tag Video Clips`
   - When it runs
   - Then it behaves exactly as `rename_tag video clips` and stores `clips`

6. **`--dry-run` writes nothing**
   - Given either command with `--dry-run`
   - When it runs
   - Then it reports the counts it would change and the database is byte-identical
     afterwards

7. **An unknown tag is reported, not silently ignored**
   - Given a tag no story carries
   - When either command names it
   - Then the command says so and exits non-zero

8. **The suite and the gate are green, and the tests have teeth**
   - Given the full suite and, separately, the deprecation gate on `docker_test`
   - When both are run in the container
   - Then both pass, and a mutation battery shows each new test failing on a
     deliberate defect with the restored files byte-identical

## Metadata
- **Complexity**: Low
- **Labels**: news, tagging, management-command, ArrayField, Step 19 Phase C
- **Required Skills**: Django management commands, PostgreSQL array functions, TDD with mutation verification
