# Task: Django 5.1 → 5.2 LTS (Rung 3) — Target Reached ⭐

## Description
Move Django from 5.1 to **5.2 LTS** with the interpreter held at 3.12, and bump
`django-debug-toolbar` to the 7.x line, which this rung both requires and
unblocks.

**This is the rung the whole plan has been climbing toward.** The ladder that
started at Django 1.9.13 on Python 2.7 ends here: `1.9 → 1.11 → 2.2 → 3.2 → 4.2
→ 5.2`, on PostgreSQL, on Python 3.12. When this task is green the site is on
its target stack.

It also has one forward-looking obligation: produce the **6.0 deprecation
inventory** as a written handoff, the way Step 13 task 05 handed the 5.x
inventory to this step.

## Background
**5.2.17 is the current patch on the line.** Django 6.0 and 6.1 now exist and
are explicitly out of scope — 5.2 is the LTS, it is what the plan targets, and
6.0 requires Python 3.12+, which task 01 has already put us on. The point of
recording a 6.0 inventory here is that the next person to consider that jump
should start from a list rather than a survey.

**`django-debug-toolbar` must move on this rung and could not move before it.**
The pin comment at `requirements_dev.txt:11-15` names this exact moment as its
trigger:

> 6.3.0 is the newest release that still supports Django 4.2: 7.0 requires
> Django >= 5.2, so this pin moves again at the 5.2 rung and not before.

7.1.0 is the current release. **A pin whose comment names a future step as its
trigger is a small piece of scheduling that actually worked** — the same pattern
that brought coverage and the toolbar itself along in Step 13 task 06. Update
the comment to describe the new reality rather than leaving it pointing at a
rung that has happened.

**Two things about the toolbar that are load-bearing and easy to break while
bumping it:**

1. **Its middleware position is deliberate**, and now commented as such. It sits
   *after* `CommonMiddleware`, not at index 0, because index 0 wraps index 1:
   prepending it routes `APPEND_SLASH` redirects through the Redirects Panel.
   Measured during Step 13 task 06 — `/forums` answers 301 from the current
   position and a 200 interstitial from index 0.
2. **`local.py` must not mutate `base.py`'s settings objects in place.** Step 13
   task 06 found that `from base import *` binds base's own list and dict
   objects, so `MIDDLEWARE.insert()` was editing live settings — 105 errors once
   the toolbar shipped a model. It was fixed by copying, with a
   mutation-verified test behind it. If the 7.x install order changes anything
   here, fix it by copying, not by reintroducing the mutation.

**And one thing that will mislead a smoke test:** `/admin/` answers **302**, not
200. A 200 there is the toolbar's Redirects Panel standing in for the redirect,
a dev-only artifact of `INTERCEPT_REDIRECTS` that has already corrupted one
smoke result on this project.

**The vendored `tagging` fork remains the highest-probability breaker.**
`tagging/models.py:178-186` reaches into `queryset.query.get_compiler()`,
`compiler.compile(queryset.query.where)` and `compiler.get_from_clause()` and
string-builds raw SQL. It broke at 4.0 (`smart_text`) and at 4.2
(`FullResultSet`), upstream is dead, and only the news tag cloud reaches it.
Exercise that page on real data.

**5.2's headline feature — composite primary keys — is not adopted here.** This
site's models are single-column-pk throughout, `DEFAULT_AUTO_FIELD` is pinned to
`AutoField` deliberately (Step 10, to keep 32-bit pks and avoid schema churn),
and a version bump is not the place to take on a new feature.

### The 6.0 inventory, and how to produce one that is worth having

Step 13 task 05 set the standard, and it is worth meeting rather than
approximating. That handoff was trustworthy because it had two independent legs:

1. **The suite run under a gate proven to fire** — both warning categories as
   errors, message-based ignores, and each category demonstrated to abort on a
   live warning *before* any result was recorded.
2. **A static sweep for the known removals**, because a suite only covers what
   it exercises. This is the leg that makes an empty inventory mean something.
   An inventory backed only by a green run is a statement about test coverage.

On 5.2, `RemovedInDjango60Warning` should already be a `DeprecationWarning` and
`RemovedInDjango61Warning` should arrive as a `PendingDeprecationWarning` —
**verify that rather than assuming it**, since the re-parenting schedule is the
mechanism that has broken this project's gate three times.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 14; and Step 15+ for what consumes the 6.0 inventory)
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-verification.md`
  (the measured search behavior that must survive to the target stack)
- `.agents/planning/2026-07-04-modernizing-sg101/research/upgrade-path.md`
  (the ladder this rung completes)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump Django to **5.2 LTS** (5.2.17 current) in both requirements files.
   Interpreter stays at 3.12.
2. Bump `django-debug-toolbar` to the 7.x line and **rewrite its pin comment** —
   the current one describes a constraint that this rung dissolves.
3. Verify the toolbar's middleware position is unchanged and still deliberate,
   and that `local.py` still copies rather than mutates `base.py`'s settings
   objects. The mutation-verified test from Step 13 task 06 must still pass.
4. Resolve every breaker the build and suite surface.
5. **Exercise the news tag cloud on real data** — the vendored `tagging`
   compiler code, third rung running.
6. Verify `django.contrib.postgres` search behavior did not shift: ranking
   order, per-type counts, headline escaping.
7. `check`, `check --deploy` and `makemigrations --check` clean; suite green.
8. **Produce the 6.0 deprecation inventory** with both legs — a gate proven to
   fire on this rung, and a static sweep for the known 6.0 removals — and write
   it into STATUS as a handoff. If it is empty, say so and say what backs the
   claim.
9. Run the **full Step 13 smoke checklist** on real production-snapshot data,
   including both password-reset flows, the admin, search, feeds, and the celery
   worker and beat.

## Dependencies
- Task 03 (Django 5.1, green)
- Task 01 (Python 3.12) — 5.2 supports 3.10–3.13, so this is not strictly
  required, but it is the stack the demo is defined against
- A PostgreSQL snapshot taken before any DB-writing work
  (`tools/pg_snapshot.sh dump <label>`)

## Implementation Approach
1. Bump Django alone first, and get the suite green, before touching the
   toolbar. Two changed variables is what this project's rung doctrine exists to
   avoid — and the toolbar is a dev dependency, so it cannot be what makes the
   site work.
2. Then bump the toolbar and verify the dev server, the panels, and the
   middleware ordering behavior.
3. Reach the news tag cloud.
4. Verify search by replaying the standing query probe on 5.1 and 5.2 against
   the same database, comparing totals, per-type counts and top-20 ordering with
   rank to 10 decimal places — the method that has caught nothing three rungs
   running, which is the result it is there to produce.
5. Build the 6.0 inventory: prove the gate, run the suite under it, then sweep
   statically for the known removals.
6. Run the full smoke checklist and capture the demo.

## Acceptance Criteria

1. **Django 5.2 LTS Installed and Running**
   - Given the updated requirements
   - When `django.get_version()` is read in the built image
   - Then it reports 5.2.x on Python 3.12, against PostgreSQL

2. **Debug Toolbar Bumped and Working**
   - Given `django-debug-toolbar` on the 7.x line
   - When the dev server is loaded with `DEBUG=True`
   - Then the toolbar renders, its SQL panel works, and its pin comment
     describes the current constraint rather than the one this rung removed

3. **Toolbar Middleware Position Preserved**
   - Given the bumped toolbar
   - When `/forums` is requested
   - Then it answers 301, not a 200 interstitial — confirming the toolbar still
     sits after `CommonMiddleware` rather than at index 0

4. **Settings Are Still Copied, Not Mutated**
   - Given `local.py`
   - When the settings modules are imported
   - Then `base.py`'s list and dict objects are unmodified, and the
     mutation-verified test from Step 13 task 06 passes

5. **The News Tag Cloud Renders**
   - Given real tag data on 5.2
   - When the news tag cloud is requested
   - Then it renders with correct counts, verified by reaching the page

6. **Search Is Unchanged on the Target Stack**
   - Given the standing query probe
   - When it is replayed on 5.1 and 5.2 against the same database
   - Then totals, per-type counts and top-20 ordering including rank compare
     equal, and headline escaping still holds

7. **Suite Green and Checks Clean**
   - Given Django 5.2
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass, and `check`, `check --deploy` and
     `makemigrations --check` are clean

8. **The 6.0 Inventory Exists and Is Backed**
   - Given the completed rung
   - When the inventory is written into STATUS
   - Then it names both legs — a gate demonstrated to fire on a live 6.0
     warning, and a static sweep for the known removals — and an empty result is
     stated as a finding with its evidence, not left implicit

9. **Target Stack Demonstrated**
   - Given the completed rung
   - When SG101 is run locally on real production-snapshot data
   - Then the site serves on **Django 5.2 LTS / Python 3.12 / PostgreSQL** with
     working search, working feeds, both password-reset flows, and a clean
     celery worker and beat — the step's demo

10. **CI Green**
    - Given the pushed branch
    - When the GitHub Actions workflow runs
    - Then it builds and the suite passes on the target stack

## Metadata
- **Complexity**: Medium
- **Labels**: Django 5.2 LTS, Upgrade, Target Stack, debug-toolbar, Deprecation
  Inventory, Step 14
- **Required Skills**: Django upgrades and release notes, Python warnings
  filters, `django.contrib.postgres` full-text search, Django settings layout
