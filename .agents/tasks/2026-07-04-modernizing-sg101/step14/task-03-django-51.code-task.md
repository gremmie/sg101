# Task: Django 5.0 → 5.1 (Rung 2)

## Description
Move Django from the 5.0 line to 5.1 with the interpreter held at 3.12. One
variable, one rung.

5.1 is where the deprecations 4.2 announced actually get removed, so on paper it
is the rung with the most surface. In this tree every one of those removals
measured zero, which makes this primarily a **verify-and-record** rung — with
two exceptions that are worth real attention.

## Background
**What 5.1 removes, and what each is worth here.** All of these were swept
statically on 4.2 during Step 13 task 05 and came back **zero**:

| removal | count in this tree |
|---|---|
| `django.contrib.postgres.fields.CIText`, `CICharField`, `CIEmailField`, `CITextField` | 0 |
| `index_together` | 0 |
| `BaseUserManager.make_random_password` | 0 |
| `length_is` template filter | 0 |
| `django.core.files.storage.get_storage_class` | 0 |
| `DEFAULT_FILE_STORAGE` / `STATICFILES_STORAGE` settings | 0 — `STORAGES` adopted at `sg101/settings/production.py:33` |

**The `CIText` zero is not luck, and the reason is worth knowing before someone
re-introduces it.** Step 11's task 02 found `CITextField` already deprecated and
routed the case-insensitive uniqueness work to `__iexact` plus a functional
index instead. `detailed-design.md` and `research/database-migration.md` both
recommended `CITEXT` at the time and were corrected at that step's close-out.
This rung is where that decision pays; do not let a 5.1 breakage tempt anyone
back toward it, because the class is simply gone.

**The `STORAGES` zero has a caveat.** `STORAGES` is set in `production.py` and
nowhere else, and `production.py` is loaded by nothing except `check --deploy`.
That is exactly the configuration that let `MemcachedCache` sit broken in the
same file for a rung and a half. **Run `check --deploy` on this rung, and do not
treat a green suite as covering the production settings module.**

### The two things that actually deserve attention

**1. The vendored `tagging` fork.** It has broken on two of the last three
rungs, and it is the only code in the tree reaching into Django's private
SQL-compiler API — `tagging/models.py:178-186` calls
`queryset.query.get_compiler()`, `compiler.compile(queryset.query.where)` and
`compiler.get_from_clause()`, then string-builds raw SQL from the results. The
`except FullResultSet` clause is the 4.2 scar; `smart_text` was the 4.0 one.
Upstream is dead, so there is nothing to pull — this project owns it, and its
retirement is scheduled into Step 19. **Nothing but the news tag cloud reaches
this code**, so exercise that page specifically, on real data.

**2. `Model.save()` and `asave()` positional arguments are deprecated in 5.1.**
Not removed — removal is 6.0 — so what this rung produces is warnings, and the
gate turns warnings into failures. **Measured: this looks like a non-item, and
the measurement is worth recording because the grep is misleading.** Searching
for positional `.save(` calls returns ten hits, and **every one of them is
`PIL.Image.save()` or `FieldFile.save()`, not `Model.save()`**:

- `bio/forms.py:131`, `core/images/upload.py:108,150`, `potd/models.py:73`,
  and four in `core/tests/images/imagemakers.py` — all PIL.
- `bio/views.py:148` — `FieldFile.save(name, content, save=False)`.

Neither signature is affected. Let the gate settle it rather than the grep,
since a positional `Model.save()` reached through a helper would not match
either pattern.

**New in 5.1 and deliberately not adopted here:** `LoginRequiredMiddleware`
would be a site-wide access-control change, not an upgrade concern, and this
site is mostly public. `{% querystring %}` and PostgreSQL connection pools are
likewise improvements rather than obligations. **A version bump is not the place
to adopt new features** — the same reasoning that kept the `elsewhere` schema
refactor out of the 3.0 rung in Step 10.

### The gate

5.0's gate (task 02) should carry over unchanged in shape, since 5.1's
re-parenting moves `RemovedInDjango60Warning` from `PendingDeprecationWarning`
to `DeprecationWarning` and both categories are already errors. **Re-prove it
anyway.** The cost of a probe is a minute; the cost of a gate that has stopped
binding is a rung certified by nothing, which has happened three times on this
project. Point a probe at a live `RemovedInDjango60Warning` and watch it abort.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
  (why `CITEXT` was rejected in favor of `__iexact` plus a functional index)
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-verification.md`
  (the measured search behavior no rung may change)
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 13 task 05: the static sweep behind the zeros above)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to the 5.1 line (5.1.15 is the line's final patch) in both
   requirements files. Interpreter stays at 3.12; no other rung in the same
   change.
2. Re-prove the deprecation gate fires on this rung before trusting a green run
   under it.
3. Resolve every breaker the build and suite surface, each attributable to this
   rung.
4. **Exercise the news tag cloud on real data** and confirm the vendored
   `tagging` compiler code still produces correct SQL under 5.1.
5. Run `check --deploy` and confirm `production.py` still imports and its
   `STORAGES` block is still valid — the suite does not cover this file.
6. Verify `django.contrib.postgres` search behavior did not shift: ranking
   order, per-type counts, and headline escaping.
7. `check`, `check --deploy` and `makemigrations --check` clean; suite green.
8. Record what this rung cost. Given the inventory, an explicitly recorded no-op
   is a likely and perfectly good outcome — Step 13 task 04 is the precedent.

## Dependencies
- Task 02 (Django 5.0, green)
- The vendored `tagging/` app and the news tag cloud
- The Step 12 search app and its suite

## Implementation Approach
1. Bump, build, run the full suite, and collect the failure list before fixing
   anything.
2. Re-prove the gate, then run the suite under it.
3. Reach the news tag cloud before anything else — it is the highest-probability
   breaker and it does not announce itself from the home page.
4. Run `check --deploy`.
5. Verify search by hand as well as by suite.
6. Smoke the site, worker and beat.

## Acceptance Criteria

1. **Django 5.1 Installed and Running**
   - Given the updated requirements
   - When `django.get_version()` is read in the built image
   - Then it reports 5.1.x on Python 3.12

2. **The Gate Still Fires**
   - Given the carried-over deprecation filter
   - When a live `RemovedInDjango60Warning` is raised under it
   - Then the run aborts, demonstrated on this rung rather than inherited from
     the last

3. **The News Tag Cloud Renders**
   - Given real tag data on 5.1
   - When the news tag cloud is requested
   - Then it renders with correct counts, and the SQL the vendored `tagging`
     compiler code builds is still valid — verified by reaching the page, not by
     a green suite

4. **Production Settings Still Import**
   - Given 5.1's removal of `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE`
   - When `check --deploy` runs
   - Then `production.py` imports cleanly and its `STORAGES` block is accepted

5. **No Positional `Model.save()` Warnings**
   - Given 5.1's deprecation of positional arguments to `save()`/`asave()`
   - When the suite runs under the gate
   - Then no such warning is raised, confirming the ten positional `.save(`
     call sites are all PIL and `FieldFile` as measured

6. **Search Is Unchanged**
   - Given the queries measured in Step 12 and re-verified at each rung since
   - When each is run before and after the bump
   - Then totals, per-type counts and top-20 ordering are equivalent, and
     headline escaping still holds

7. **Suite Green and Checks Clean**
   - Given Django 5.1
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check`, `check --deploy` and
     `makemigrations --check` are clean

8. **Rung Cost Recorded**
   - Given the completed rung
   - When STATUS is updated
   - Then the breakers are named with their fixes, or the rung is explicitly
     recorded as free

## Metadata
- **Complexity**: Medium
- **Labels**: Django 5.1, Upgrade, Vendored tagging, PostgreSQL Search, Step 14
- **Required Skills**: Django upgrades and release notes, Django ORM/SQL
  compiler internals, `django.contrib.postgres` full-text search
