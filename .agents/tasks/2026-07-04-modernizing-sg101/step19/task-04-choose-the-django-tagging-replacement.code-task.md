# Task: Measure the Tag Read Path and Choose django-tagging's Replacement

## Description
Decide what replaces vendored `django-tagging`, on a measurement rather than on
taste. **This task changes no schema and moves no data.** Its output is a
decision recorded in `STATUS.md` and the numbers behind it; the implementation
becomes task 05, written once the answer is known.

The two candidates have different schemas — one keeps the `TaggedItem` join
table and its content-type indirection, the other deletes both — so writing an
implementation task now would mean writing it for a design nobody has chosen.
That is the reasoning Phase 0 used, applied inside the phase: shrinking and
settling work before generating task files is cheaper than generating tasks for
work that turns out not to exist.

## Background

### Why the library is being retired
`tagging` was vendored during Step 13 task 03 (see `tagging/__init__.py`). 0.5.0
is the final release, upstream stopped in 2018, and it did not import on Django
4.0. **Vendoring was the move that kept the 4.0 rung to one variable, not an
endorsement**, and the plan has carried the retirement ever since.

### The surface, fully mapped as of 2026-08-04
**Only the `news` app uses it:**
- `TagField` on `Story` — `news/models.py:9`
- `Tag` / `TaggedItem` in `news/views.py` and `news/utils.py`
- the `tagging_tags` templatetags in `sg101/templates/news/story.html` and
  `story_summary.html`
- the `/news/tags/` and `/news/tag/<name>/` routes

**Live data: 1,006 tags across 4,561 tagged items.**

### The two candidates, and why the choice is not obvious
- **`django-taggit`** — the maintained like-for-like. Keeps the generic foreign
  key and content-type machinery.
- **A PostgreSQL `ArrayField` with a GIN index** — the more interesting option,
  because that machinery is sized for tagging *any* model and this site tags
  exactly one. The whole `TaggedItem` join table and its content-type
  indirection exist to support a generality nothing here uses.

Either way it is a schema change plus a data migration for the 4,561 rows, which
is why it was never a version-rung item.

### What the plan says to measure
*"Measure the tag-page query cost before choosing; `/news/tag/<name>/` is the
read path that would change shape most."* That is the whole brief for this task.

### An ordering constraint this decision releases
`research/collation-audit.md` holds a tag-cloud finding that is **about
`tagging_tag.name`** — a table the `ArrayField` option deletes. The plan's
ordering rule is explicit: *"Do not record a decision about a table you may
delete."* So the tag-cloud half of the collation audit stays blocked until this
lands, and this task's record should say which way it went for that reader.

### One thing to fix whichever way it goes
`sg101/templates/fixed/colophon.html:14` credits django-tagging with a link to
`code.google.com/p/django-tagging/`, dead for years. **It is a live page.**
Carry it into task 05 rather than losing it.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase C]` block on retiring `django-tagging`, including the mapped surface
- `.agents/planning/2026-07-04-modernizing-sg101/research/collation-audit.md` —
  the tag-cloud finding this unblocks
- `news/views.py`, `news/utils.py`, `news/models.py`, `tagging/`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Measure `/news/tag/<name>/` as it runs today**, on real data in the
   container against the converted production database — query count, the SQL
   emitted, and wall time for a common tag and a rare one. `facebook`-scale and
   single-item tags behave differently and both are on the site.

2. **Measure `/news/tags/`**, the tag cloud, on the same basis. It is the other
   read path and it aggregates across all 1,006 tags.

3. **Model both candidates against the same data** rather than reasoning about
   them. A throwaway `ArrayField` column populated from the existing
   `TaggedItem` rows, with a GIN index, is enough to get real numbers for the
   same two queries; `taggit`'s shape is close enough to the current one that its
   query profile can be measured from the existing schema.

4. **Record what each option costs beyond query time** — the migration's shape,
   what happens to `Tag` as an addressable object (`/news/tag/<name>/` resolves
   by name today), whether tag rename or merge is possible afterwards, and what
   admin support each retains.

5. **State the risk each carries.** `ArrayField` ties the feature to PostgreSQL,
   which this project has already committed to; `taggit` carries a dependency
   whose maintenance is someone else's, which is the situation being escaped.

6. **Put the choice to Brian with the numbers**, and record the answer in
   `STATUS.md` as a decision record with its date, in the shape Phase 0 used.

7. **Change nothing else.** No dependency added or removed, no model touched, no
   migration written. Any throwaway column created for measurement is dropped
   before the task closes.

## Dependencies
- The converted production database, for real tag distribution
- `django.test.utils.CaptureQueriesContext` or `assertNumQueries` for query
  counting
- Brian, for the decision

## Implementation Approach

1. Establish the tag distribution — how many stories per tag, at the head and the
   tail of the 1,006.
2. Measure both read paths on the current schema.
3. Build the throwaway `ArrayField` + GIN model of the same data and measure the
   equivalent queries.
4. Write up both options with numbers, migration shape, and what each gives up.
5. Put the choice, record the answer, and note in the collation audit that its
   tag-cloud half is now unblocked and which way.

## Acceptance Criteria

1. **The current read paths are measured, not estimated**
   - Given the converted production database
   - When `/news/tag/<name>/` and `/news/tags/` are exercised
   - Then query counts, the emitted SQL and timings are recorded for a common tag
     and a rare one

2. **Both candidates are measured against the same data**
   - Given the same 1,006 tags and 4,561 tagged items
   - When the equivalent queries are run against an `ArrayField` + GIN model and
     against the join-table shape
   - Then the two are compared on numbers from this database, not from
     documentation

3. **The non-performance consequences are written down**
   - Given each candidate
   - When the write-up is read
   - Then it says what happens to tag addressability, rename and merge, admin
     support, and the migration's shape

4. **The decision is recorded**
   - Given the completed measurement
   - When `STATUS.md` is read
   - Then a dated decision record names the choice, the numbers it rests on, and
     the option not taken with the reason

5. **The blocked audit is released**
   - Given the decision
   - When `research/collation-audit.md`'s tag-cloud finding is read
   - Then it says whether `tagging_tag` survives, so that finding can be settled

6. **Nothing shipped changed**
   - Given the task is complete
   - When the working tree is diffed
   - Then no model, migration, dependency or template has changed, and any
     throwaway measurement column is gone

7. **The suite is green**
   - Given the full test suite under the deprecation gate on `docker_test`
   - When it is run in the container
   - Then it passes, unchanged from before the task

## Metadata
- **Complexity**: Medium
- **Labels**: news, tagging, django-tagging, ArrayField, GIN, measurement, decision, Step 19 Phase C
- **Required Skills**: PostgreSQL indexing and query analysis, Django ORM query profiling, schema design
