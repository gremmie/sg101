# Task: Django 4.0 → 4.1 (Rung 2)

## Description
Move Django from the 4.0 line to 4.1 with the interpreter held at 3.10. One
variable, one rung, suite green before moving on.

4.1 is expected to be the cheapest of the three rungs. Treat that as a
hypothesis to test, not a reason to skip verification — Step 10's "no-op" prep
rung was genuinely a no-op, and its rungs each still produced a distinct breaker
that the plan had not predicted.

## Background
**What 4.1 changes that this codebase plausibly touches:**

- **`Model.full_clean()`/form validation**: `ModelForm` fields with a
  `Meta.exclude` interaction and the `Model.save()` signature tightened. The
  site has heavy custom form use across `bio`, `gcalendar`, `accounts`,
  `forums` and `messages`.
- **`django.contrib.postgres` changes** — relevant now in a way they were not
  before Step 11. The `search` app added in Step 12 uses `SearchVector`,
  `SearchQuery`, `SearchRank`, `SearchHeadline` and `SearchVectorField`
  directly. Step 12 task 07 established that `normalization=Value(1)` and the
  `'english'` config are deliberate, load-bearing choices with measured
  consequences. **Any change in ranking behavior across this rung is a
  regression, not an improvement**, and it will not announce itself — Step 12
  task 04 found that `ts_rank` returning a single constant value for exclusion
  queries looked entirely normal from the outside.
- **Async ORM interface additions** — additive, but they change what
  `QuerySet` exposes.
- **`CSRF_COOKIE_MASKED` transitional setting**.

**The search app is the thing to watch on this rung.** It is the newest code in
the tree, it is the only code that talks to PostgreSQL-specific query
constructs, and Step 12 spent nine tasks establishing exactly what its output
should look like. It also has the best regression coverage in the project — 798
tests total, of which the `search` app contributes a large share. Use them.

**Two Step 12 findings worth re-checking by hand after the bump**, because they
were both invisible to a green suite until someone looked:

1. Ranking on a query with an exclusion (`reverb -fender`). Step 12 task 04
   fixed this by ranking on the exclusion-stripped query while filtering on the
   whole one. Confirm the ordering is still meaningful, not just that results
   come back.
2. Headline escaping. `SearchHeadline` rendered directly is stored XSS; the fix
   was sentinels plus escape plus `mark_safe`. Confirm the escaping still holds
   — the assertion that works is "every tag in a result row is one the template
   wrote," not a substring blocklist.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-verification.md`
  (the measured ranking behavior this rung must not change)
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Suggested order" item 3)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to the 4.1 line in both requirements files. Interpreter stays at
   3.10; no other rung in the same change.
2. Resolve every breaker the build and suite surface, each attributable to this
   rung.
3. **Verify `django.contrib.postgres` search behavior did not shift**, beyond
   what the suite asserts — ranking order and headline escaping specifically.
4. Review form and model validation changes against the site's custom forms,
   rather than trusting a green suite alone; form validation is the area 4.1
   tightened and the area this project has the most bespoke code in.
5. `check` and `makemigrations --check` clean; suite green.
6. Record what this rung actually cost. If it was genuinely free, say so
   explicitly — a recorded no-op is a finding, and Step 10 has precedent for it.

## Dependencies
- Task 03 (Django 4.0, green)
- The Step 12 search app and its test suite
- PostgreSQL, from Step 11

## Implementation Approach
1. Bump, build, run the full suite, and collect the failure list before fixing
   anything.
2. Fix breakers one category at a time.
3. Run the search-specific verification by hand: a query with an exclusion, a
   query whose results include user-submitted markup, and a categorical query
   whose per-type counts task 09 established (`backing track` → `Downloads
   (115)` beside `Forum Posts (2,830)`).
4. Exercise the site's most bespoke forms — profile edit, calendar event,
   registration, private message — since form validation is this rung's surface.
5. Smoke the site.

## Acceptance Criteria

1. **Django 4.1 Installed and Running**
   - Given the updated requirements
   - When `django.get_version()` is read in the built image
   - Then it reports 4.1.x on Python 3.10

2. **Search Ranking Is Unchanged**
   - Given the queries measured in Step 12 task 07
   - When each is run before and after the bump
   - Then result ordering is equivalent, and in particular a query containing an
     exclusion still ranks meaningfully rather than returning a constant score

3. **Headline Escaping Still Holds**
   - Given a search result whose source text contains HTML
   - When the result row is rendered
   - Then every tag present is one the template wrote, and no stored markup
     reaches the page live

4. **Per-Type Counts Still Correct**
   - Given a categorical query
   - When the search page renders
   - Then per-type counts sum to the paginator total, and no count collapses to
     1 — the failure mode Step 12 task 09 identified

5. **Custom Forms Still Validate**
   - Given the profile, calendar, registration and private-message forms
   - When valid and invalid input is submitted to each
   - Then acceptance and rejection match pre-bump behavior

6. **Suite Green and Checks Clean**
   - Given Django 4.1
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check` and `makemigrations --check` are clean

7. **Rung Cost Recorded**
   - Given the completed rung
   - When STATUS is updated
   - Then the breakers are named with their fixes, or the rung is explicitly
     recorded as free

## Metadata
- **Complexity**: Medium
- **Labels**: Django 4.1, Upgrade, PostgreSQL Search, Forms, Step 13
- **Required Skills**: Django upgrades and release notes, `django.contrib.postgres`
  full-text search, Django forms validation
