# Task: Move News Tagging onto a PostgreSQL ArrayField

## Description
Implement task 04's decision: replace `django-tagging`'s `TagField` with a
PostgreSQL `ArrayField` on the news models, migrate the live tag data onto it,
and move every read path across.

**The vendored `tagging` app stays installed and both its tables stay populated
when this task ends.** That is deliberate and it is what makes the task
verifiable: the old and new shapes can be run side by side against the same
1,208 stories and required to agree. Deleting the app is task 06.

## Background

### The decision this implements
Recorded in `STATUS.md` § "Step 19 Phase C task 04 — `django-tagging` is
replaced by a PostgreSQL `ArrayField`, DECIDED 2026-09-07", with the
measurements under it. Two answers came out of it, both Brian's:

- **A PostgreSQL `ArrayField` with a GIN index**, not `django-taggit`. The
  deciding argument is referential integrity, not speed — see the orphans below.
- **The join table is the migration's source of truth**, not `news_story.tags`.

**The performance argument runs the other way and this task should not claim
otherwise.** In raw SQL the join table is *faster* on a common tag — 0.26 ms
against 0.96 ms for `tags @> ARRAY['release']`, because at 567 of 1,694 rows the
tag is 33% selective and the planner ignores the GIN index in favour of a
sequential scan. The `ArrayField` wins at the ORM level because it deletes two
round trips per tag page and the Python that assembles them, not because the
query is quicker. The GIN index earns its place at the tail of the distribution,
where a rare tag is a 0.023 ms bitmap scan.

### The surface, verified against the tree on 2026-09-07
- `news/models.py:51` — `tags = TagField()` on `StoryBase`, so **both `Story` and
  `PendingStory` are tagged**. The plan said the site tags one model; it tags two.
- `news/views.py:184` `tags()` — the cloud, via `Tag.objects.cloud_for_model`.
- `news/views.py:194` `tag()` — the tag page, via `get_object_or_404(Tag,
  name__iexact=...)` then `TaggedItem.objects.get_by_model(...)`.
- `news/utils.py:26` — `attach_extra_attrs` bulk-loads `TaggedItem` rows and hangs
  a `tag_list` on each story.
- `sg101/templates/news/story.html:52` — `{% tags_for_object story as story_tags %}`.
- `sg101/templates/news/story_summary.html:77` — `{% if story.tag_list %}`.
- `sg101/templates/news/tag_index.html:14` — renders `tag.name` and
  `tag.font_size`.
- `search/documents.py:256` — `body_text(obj.short_text, obj.long_text, obj.tags)`,
  the one consumer outside `news`.
- `news/tests/test_tag_queries.py`, `news/tests/test_display_views.py:76,83,94`.

### Live data, measured 2026-09-07 and not what the plan carried
**1,001 tags across 3,931 join rows on 1,208 stories** — not the 1,006/4,561 the
plan has said since 2026-08-04. The difference is **630 orphaned rows**: 616
pointing at `news_pendingstory` rows that no longer exist and 14 at deleted
stories. The mechanism is `news/admin.py:85` — `_approve_story` ends with
`pending_story.delete()`, and django-tagging registers no delete handler, so
every story ever approved left its pending tag rows behind.

**The orphans are not migrated and the reverse migration does not recreate
them.** Their targets do not exist; there is nothing to attach them to.

Also measured, and each one bears on this task:
- **Every one of the 1,001 live tags is lowercase, with no case variants.**
  `FORCE_LOWERCASE_TAGS = True` (`sg101/settings/base.py:196`) is what does it,
  and `news/tests/test_display_views.py:94` already pins it.
- **The longest `tags` string is 251 characters of the column's 255** (story 635,
  2011, twenty tags). The array has no such cap; this is a constraint being
  removed, not a limit to reproduce.
- **The maximum tag length is 36 characters** and the maximum tag count on one
  story is 20.

### Two stories where the two sources disagree
```
story 1539 (2021-10-31)   column: jay-poisön    join table: jay-poison
story 1730 (2024-10-12)   column: thálasses     join table: thalasses
```
MySQL's accent-insensitive unique index on `tagging_tag.name` matched a later
accented submission to an ASCII tag that already existed. **The MySQL snapshot
holds the same bytes, so this is production data and not a conversion artifact.**
The decision is to take the join table's spelling, which is what every page
renders today, so the migration produces no visible change. The accented forms
survive only in the admin edit box and the search index — which is why a reindex
is part of this task.

### A defect this closes without being asked to
Renaming a tag in the admin today (`/admin/tagging/tag/`) half-applies: the join
table follows immediately, so all 57 stories tagged `video` render the new name,
but each story's `news_story.tags` column keeps the old string. **Saving any one
of those stories afterwards silently reverts it alone**, recreating the old tag
and splitting the set across two tag pages, with no error anywhere. Measured on
2026-09-07 in a rolled-back transaction. It erodes slowly — only 8 of 1,694
stories have been edited in the last two years — but it never heals.

**The `ArrayField` removes the mechanism**: there is no second copy of the tag
string to go stale. Do not write a separate fix for it; note in the commit that
it is closed here.

### Where `calculate_cloud` lives
The font sizes on `/news/tags/` come from `tagging/utils.py:250`
(`calculate_cloud`, `_calculate_thresholds`, `_calculate_tag_weight`, and the
`LOGARITHMIC`/`LINEAR` constants). **`tagging/` is deleted in task 06, so that
logic has to move into `news/` here** or the cloud loses its font sizes one task
later. It is roughly forty lines and it has no dependency on the `Tag` model —
it reads `.count` and sets `.font_size` on whatever objects it is handed.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — § "Step 19 Phase C
  task 04", the decision record, the measurements, and the ten-item brief this
  task expands
- `.agents/planning/2026-07-04-modernizing-sg101/research/collation-audit.md` —
  § "`tagging_tag` does not survive", the accent-folding finding and the
  ordering decision that carries over
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase C]` django-tagging block
- `elsewhere/migrations/0004_seed_networks.py` — the house shape for a reversible
  data migration, from Phase C task 03
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **`tags` becomes an `ArrayField` on `StoryBase`** —
   `ArrayField(models.CharField(max_length=50), default=list, blank=True)` — with
   a `GinIndex` on `Story` and on `PendingStory`. `StoryBase` is abstract, so the
   index belongs on the concrete models.

2. **Two migrations in `news`, and they are separate.** A schema migration adding
   the column and the index, then a data migration populating it from
   `tagging_taggeditem` for both content types (`news.story` and
   `news.pendingstory`). Separating them keeps a failed backfill from taking the
   schema change with it, and it is the shape Phase C tasks 01–03 used.

3. **The data migration is reversible**, rebuilding `tagging_tag` and
   `tagging_taggeditem` from the arrays. **It will not restore the 630 orphans**,
   and the migration should say so in a comment rather than leaving the next
   reader to discover the row count changed.

4. **The tag page runs two queries and preserves both of its current behaviours.**
   `Story.objects.filter(tags__contains=[tag_name.lower()])` — `.lower()` is what
   reproduces today's `name__iexact`, and it is faithful because every live tag is
   lowercase. The 404 for an unknown tag moves onto the paginator's count rather
   than a `Tag` lookup, so it costs no extra query.

5. **The cloud runs one query** — `unnest` plus `GROUP BY`, ordered by the tag —
   feeding the ported `calculate_cloud`. The template needs objects carrying
   `.name`, `.count` and `.font_size`.

6. **`attach_extra_attrs` loses its `TaggedItem` query entirely.** The tags arrive
   on the story row; `story.tag_list` should become `story.tags` at the call
   sites rather than being synthesised to keep the old name alive.

7. **`search/documents.py:256`**: `obj.tags` is a list now. **A reindex is
   required** — the two accented stories change in the index — and
   `reconcile_search` should be clean afterwards.

8. **The admin's tag box moves to commas, with help text and a validator.**
   **Brian's call 2026-09-07: no custom form field.** `ArrayField.formfield()`
   already returns a `SimpleArrayField` with a `','` delimiter, existing values
   render comma-separated with no code, and `'surf, reverb , twang'` parses to
   three tags with the surrounding whitespace stripped. Two additions, both one
   line, neither needing a custom field or widget:

   - **`help_text` on the model field**, which Django surfaces in the admin and
     wires to the input with `aria-describedby`. It is the only thing standing
     between twelve years of space-separated habit and a junk tag.
   - **A validator on the inner `CharField` rejecting a tag containing a space.**
     This matters because the failure is silent: measured 2026-09-07, typing
     `surf reverb twang` **validates** and stores one tag named
     `surf reverb twang` — which no URL resolves and which appears alone in the
     cloud. The validator turns that into an error message.

   **The validator cannot reject existing data**: 0 of the 1,006 tags contain a
   space, and no story's `tags` column ever used django-tagging's quoted
   multi-word syntax. If it is unwanted, it is one line to drop; the help text is
   not.

9. **The vendored `tagging` app is not touched.** It stays in `INSTALLED_APPS`,
   its tables stay populated, and `news/tests/test_tag_queries.py` keeps passing.
   That is what the equivalence check in AC 1 runs against.

10. **Mutation verification is required** for the new tests, per `CODEASSIST.md`:
    a deliberate defect per test, the expected test seen to fail, restore, and the
    restored file byte-identical.

## Dependencies
- The converted production database, for the equivalence check
- `tools/pg_snapshot.sh dump <label>` before the migration is applied
- `django.contrib.postgres` (already in `INSTALLED_APPS` since Step 12)
- `manage.py reindex_search` and `reconcile_search`
- `django.test.utils.CaptureQueriesContext` / `assertNumQueries` for the query
  counts in AC 3

## Implementation Approach
1. Snapshot the database.
2. Port `calculate_cloud` and its helpers into `news/`, with tests, before
   anything depends on them.
3. Add the field, the index and the two migrations; apply them and check the row
   counts against the join table before writing any view code.
4. Move the read paths across one at a time — cloud, tag page, `attach_extra_attrs`,
   templates, search document — running the equivalence check after each.
5. Add the admin form field.
6. Port the tests, mutation-verify them, run the suite and the gate.
7. Reindex, reconcile, and walk the pages in a browser.

## Acceptance Criteria

1. **The two shapes agree on the real data**
   - Given the converted production database with `tagging` still installed and
     both its tables populated
   - When the cloud and the tag pages are produced from the array and from the
     join table and compared
   - Then all 1,001 tags match on name, count, font size **and order**, and the
     story sets match for a common tag (`release`, 567), a mid tag (`video`, 57)
     and a rare tag (`thalasses`, 2)

2. **The migration moves the live rows and only the live rows**
   - Given 3,931 live join rows across 1,208 stories, and 630 orphans
   - When the data migration runs
   - Then 1,208 stories carry a non-empty array totalling 3,931 tag entries over
     1,001 distinct tags, and no orphan is represented anywhere

3. **The query counts drop as measured**
   - Given the rewritten views
   - When each page is exercised under `assertNumQueries`
   - Then `/news/tag/<name>/` runs 2 queries (from 4), `/news/story/<id>/` runs 1
     (from 2), `/news/date/` and `/news/archive/<y>/<m>/` run 2 (from 3), and
     `/news/tags/` still runs 1

4. **The tag page's two current behaviours survive**
   - Given a mixed-case tag in the URL and, separately, a tag no story carries
   - When each is requested
   - Then the mixed-case URL resolves to the lowercase tag and renders its
     stories, and the unknown tag returns 404 rather than an empty page

5. **The migration reverses**
   - Given the applied data migration
   - When it is reversed on a restored snapshot
   - Then `tagging_tag` and `tagging_taggeditem` hold the 1,001 tags and 3,931
     live rows, the 630 orphans are absent, and the difference is stated in the
     migration rather than left to be discovered

6. **The admin box takes commas, says so, and refuses the old habit**
   - Given a story edited in the admin
   - When `surf, reverb, twang` is typed into the tag box and saved
   - Then three tags are stored and the box redisplays them comma-separated
   - And when `surf reverb twang` is typed instead
   - Then the form raises a validation error naming the space rather than storing
     one three-word tag
   - And the field's help text tells the editor to use commas

7. **Search is reindexed and consistent**
   - Given the migration has run
   - When `reindex_search` completes and `reconcile_search` runs
   - Then the sweep is clean, stories 1539 and 1730 index the ASCII spellings,
     and a search for a tag term still matches the stories carrying it

8. **The suite and the gate are green, and the tests have teeth**
   - Given the full suite and, separately, the deprecation gate on `docker_test`
   - When both are run in the container
   - Then both pass with the new tests included, and a mutation battery shows
     each new test failing on a deliberate defect and the restored files
     byte-identical

9. **The pages are correct in a browser, not only in the suite**
   - Given the site running in the container
   - When `/news/tags/`, a common and a rare tag page, a story page, the news
     index and an archive month are walked
   - Then tags render and link correctly, the cloud's font sizes still vary, and
     the admin tag box round-trips

## Metadata
- **Complexity**: High
- **Labels**: news, tagging, ArrayField, GIN, data-migration, search, admin, Step 19 Phase C
- **Required Skills**: PostgreSQL arrays and GIN indexing, Django data migrations, Django ORM query profiling, Django admin form fields, TDD with mutation verification
