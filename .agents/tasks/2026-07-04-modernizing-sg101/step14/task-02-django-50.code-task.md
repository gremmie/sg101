# Task: Django 4.2 → 5.0 (Rung 1)

## Description
Move Django from the 4.2 LTS line to 5.0 with the interpreter held at 3.12. One
variable, one rung, suite green before moving on — the doctrine that has held
since Step 6.

This is the first rung of the last ladder. It is also the rung where the
deprecation gate has to be rebuilt and re-proven, because 5.0 re-parents
Django's warning classes the same way 4.2 did.

## Background
**The 5.x inventory handed over from Step 13 task 05 is EMPTY, and that is a
measured result rather than an absent one.** 821 tests passed on 4.2 under a
gate proven to fire, and a static sweep for the known 5.0/5.1 removals backs it
up, since a suite only covers what it exercises. All of these are **zero** in
this tree: `length_is`, `ifequal`, `make_random_password`, `get_storage_class`,
`assertQuerysetEqual`/`assertFormsetError` legacy signatures,
`CryptPasswordHasher`, `CIText`/`CICharField`, the transitional div form
renderers, `USE_L10N`, `index_together`, and `django.utils.timezone.utc`.

**Treat an empty inventory as a hypothesis, not a guarantee.** Step 13's task 04
was handed a worklist of 8 apps that turned out to be already dead, and the same
rung still produced a real finding the list never had. An empty inventory says
where not to look first; it does not say the rung is free.

**Three 5.0 items that touch this codebase, all pre-paid or measured to zero:**

1. **`USE_TZ` defaults to `True` in 5.0.** Inert here — `sg101/settings/base.py:46`
   sets `USE_TZ = True` explicitly, which Step 13 task 09 landed along with the
   whole aware-datetime conversion. Confirm the setting is still explicit rather
   than relying on the new default; an explicit setting is what makes the
   `production.py`/`local.py` modules independent of the Django version.
2. **Unqualified `{{ form }}` renders `div.html` instead of `default.html`.**
   **Zero surface, measured:** the six whole-form renders in this project are all
   explicit — `{{ form.as_p }}` in `forums/move_topic.html`, `forums/show_form.html`,
   `comments/comment_form.html`, `bio/avatar.html` and `bio/member_search.html`,
   and `{{ form.as_table }}` in `forums/mod_split_topic.html` — and explicit
   renderers are unaffected by the default change. The one `as_table` is
   correctly wrapped in a `<table>` at `mod_split_topic.html:15`, so it is not a
   repeat of the `mod_forum.html` defect task 04 fixed, where `<tr>` markup was
   being emitted into a `<div>` and silently discarded by the browser.
3. **`<h1 id="site-name">` becomes `<div id="site-name">`.** This is the one
   real change in the rung and it is ours to make. 5.0 changed admin branding
   for accessibility — the page's `<h1>` should be the content title, not the
   site name. **Our override at `sg101/templates/admin/base_site.html:33` still
   emits `<h1 id="site-name">`**, so after the bump the admin has two `<h1>`
   elements per page and the stylesheet is targeting a tag the rest of the admin
   no longer uses. This was found during Step 13 task 05 and recorded so it
   would not be rediscovered here.

**The dashboard mechanism itself is safe the whole way up.**
`{% block nav-global %}`, which `base_site.html` uses to hang the moderation
dashboard in the header, exists in the same place inside `{% block header %}` in
4.2.30, 5.0.14, 5.1.15 **and** 5.2.17 — checked by grepping each release's
`admin/base.html` rather than assumed. The layout fix from commit `1b968a4`
(`#dashboard` with `flex-basis: 100%`, `#header { flex-wrap: wrap }`) has three
tests behind it; they should keep passing, and if they do not, that is a finding
rather than a test to adjust.

### The vendored `tagging` fork is where to look first

**It has broken on two of the last three rungs, and it is the only code in the
tree that reaches into Django's private SQL-compiler API.**
`tagging/models.py:178-186` calls `queryset.query.get_compiler()`, then
`compiler.compile(queryset.query.where)`, then `compiler.get_from_clause()`, and
string-builds raw SQL out of the results:

```python
compiler = queryset.query.get_compiler(using=queryset.db)
try:
    where, params = compiler.compile(queryset.query.where)
except FullResultSet:
    where, params = '', []
extra_joins = ' '.join(compiler.get_from_clause()[0][1:])
```

The `FullResultSet` clause is itself the scar from 4.2, where an all-matching
`WHERE` stopped compiling to empty SQL and started raising instead — which 500'd
the news tag cloud. At 4.0 the same file broke on `smart_text`. **Upstream is
dead** (0.5.0 is the final release, 2018), so there is no fix to pull; this
project owns the code, and its retirement — most likely to a PostgreSQL
`ArrayField`, since the content-type indirection exists to tag any model and
this site tags one — is scheduled into Step 19.

**None of this is exercised by an ordinary page load.** Reach the news tag cloud
specifically, on real data, on every rung.

### The warning gate, which must be rebuilt and re-proven here

**This project has now met a lying gate three times.** A filter that does not
bind produces output identical to a real pass, so the failure mode is a step
being certified by a gate that was never watching. The history:

| rung | filter used | what went wrong |
|---|---|---|
| 4.1 | `-W error::django.utils.deprecation.RemovedInDjango50Warning` | silently discarded — Python cannot resolve a dotted category path |
| 4.2 | `-W error::PendingDeprecationWarning` | 4.2 re-parented `RemovedInDjango50Warning` to `DeprecationWarning`, so it caught only half |

**5.0 re-parents again**, on the same schedule: `RemovedInDjango51Warning`
becomes a `DeprecationWarning`, and `RemovedInDjango60Warning` arrives as a
`PendingDeprecationWarning`. The 4.2 gate's shape — both categories, plus
**message-based** ignores — should still be the right shape, but "should still
be" is exactly what was believed the last two times.

The 4.2 gate, as the starting point:

```
python -W error::DeprecationWarning -W error::PendingDeprecationWarning \
  -W 'ignore:SelectableGroups dict interface is deprecated:DeprecationWarning' \
  -W 'ignore:pkg_resources is deprecated as an API:DeprecationWarning' \
  -W 'ignore:Deprecated call to:DeprecationWarning' \
  -W 'ignore:ANTIALIAS is deprecated:DeprecationWarning' \
  manage.py test --noinput --settings=sg101.settings.docker_test
```

**Ignore by message, not by module.** `-W ignore::DeprecationWarning:pkg_resources`
does nothing: the module field is matched against the frame the warning is
*attributed* to after `stacklevel`, not the file it is raised in.

**Two of those four ignores should now be dead, and a dead ignore is dead
config.** The `ANTIALIAS` cause was removed by Step 13 task 07, and
`SelectableGroups` cannot fire on 3.12 at all. Drop any ignore that no longer
matches anything, and verify it by removing it and seeing the run stay green —
this project's lesson from `production.py`'s template block is that config
reproducing something already true is invisible in review.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`
  (Step 13 task 05: the gate's derivation, the re-parenting table, and the empty
  5.x inventory)
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-verification.md`
  (the measured search behavior no rung may change)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to the 5.0 line (5.0.14 is the line's final patch) in both
   requirements files. Interpreter stays at 3.12; no other rung in the same
   change.
2. **Rebuild the deprecation gate for 5.0 and prove both halves fire before
   trusting a single result from it.** Point one probe at a live
   `RemovedInDjango51Warning` and another at a live `RemovedInDjango60Warning`,
   and confirm each aborts the run. A gate that has not been demonstrated to
   fail is not evidence.
3. Drop any gate ignore whose cause no longer exists, and demonstrate it is dead
   rather than assuming it.
4. Change `sg101/templates/admin/base_site.html:33` from `<h1 id="site-name">`
   to `<div id="site-name">`, and check the accompanying CSS in the same file
   still targets the element it means to.
5. Confirm `USE_TZ` remains explicitly set rather than inherited from 5.0's new
   default.
6. Verify the moderation dashboard still renders on its own row in the admin
   header, and that the three tests from `1b968a4` still pass.
7. **Exercise the news tag cloud on real data**, which is the only thing that
   reaches `tagging/models.py`'s compiler code, and confirm the `FullResultSet`
   handling still matches how 5.0 compiles an all-matching `WHERE`.
8. `check`, `check --deploy` and `makemigrations --check` clean; suite green.
   **`check --deploy` matters**: it is the only thing that loads
   `production.py`, and that module was silently unimportable for a rung and a
   half during Step 13.
9. Record what this rung actually cost. If it was free, say so explicitly.

## Dependencies
- Task 01 (Python 3.12, green)
- The Step 12 search app and its suite
- PostgreSQL, from Step 11

## Implementation Approach
1. Bump, build, run the full suite, and collect the failure list before fixing
   anything.
2. Build the new gate and prove it fires, in both categories, before running it
   in anger.
3. Fix breakers one category at a time.
4. Make the `site-name` change and look at the rendered admin, including
   `/admin/login/` — the one admin page an anonymous visitor sees, and the page
   whose theme toggle task 05 had to restore by hand.
5. Verify search behavior by hand as well as by suite: a query with an exclusion
   still ranks across distinct values rather than collapsing to a constant, and
   headline escaping still holds.
6. Smoke the site, worker and beat.

## Acceptance Criteria

1. **Django 5.0 Installed and Running**
   - Given the updated requirements
   - When `django.get_version()` is read in the built image
   - Then it reports 5.0.x on Python 3.12

2. **The Gate Is Proven Before It Is Trusted**
   - Given the rebuilt deprecation filter
   - When a live `RemovedInDjango51Warning` and a live `RemovedInDjango60Warning`
     are each raised under it
   - Then each aborts the run as an error, demonstrated and recorded — and only
     then is a green run under that gate treated as meaningful

3. **No Dead Ignores Survive**
   - Given the gate's ignore list
   - When each entry is removed in turn
   - Then any entry whose removal leaves the run green is deleted rather than
     kept "just in case"

4. **Admin Branding Uses a div**
   - Given the 5.0 admin
   - When any admin page is rendered
   - Then `site-name` is a `<div>`, the page has exactly one `<h1>`, and the
     branding still displays correctly

5. **The Moderation Dashboard Still Sits on Its Own Row**
   - Given the admin header on 5.0
   - When a staff user loads an admin page
   - Then the dashboard renders below the branding rather than beside the user
     tools, and the three layout tests pass unchanged

6. **Timezone Handling Is Unchanged**
   - Given 5.0's new `USE_TZ` default
   - When the settings are loaded
   - Then `USE_TZ` is still explicitly `True` in `base.py`, and displayed times
     across the site match the pre-bump capture

7. **Search Is Unchanged**
   - Given the queries measured in Step 12 and re-verified at each rung since
   - When each is run before and after the bump
   - Then totals, per-type counts and top-20 ordering are equivalent, and an
     exclusion query still ranks across distinct values

8. **Suite Green and Checks Clean**
   - Given Django 5.0
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check`, `check --deploy` and
     `makemigrations --check` are clean

9. **Rung Cost Recorded**
   - Given the completed rung
   - When STATUS is updated
   - Then the breakers are named with their fixes, or the rung is explicitly
     recorded as free

## Metadata
- **Complexity**: Medium
- **Labels**: Django 5.0, Upgrade, Deprecation Gate, Admin Templates, Step 14
- **Required Skills**: Django upgrades and release notes, Python warnings
  filters, Django admin template overrides
