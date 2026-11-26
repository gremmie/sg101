# Task: Remove the shoutbox app

## Description
Remove the `shoutbox` app and everything that calls it: its package, URLs,
templates, static files and setting entry, its place in the admin dashboard,
the shout deletion in `deactivate_spammer`, and its include in the old
`base.html`.

## Background
**What references the shoutbox** (measured on `main` at `95ce0681`):

| Where | What |
|---|---|
| `shoutbox/` | the app: models (`Shout`, `ShoutFlag`), views, forms, admin, `shoutbox_tags`, one migration, static `css/shoutbox.css`, `css/shoutbox_app.css`, `js/shoutbox_app.js` |
| `sg101/templates/shoutbox/` | six templates; three extend `base.html` |
| `sg101/urls.py` | `path('shout/', include('shoutbox.urls'))` |
| `sg101/settings/base.py` | `'shoutbox'` in `INSTALLED_APPS` |
| `sg101/templates/base.html` | `{% load shoutbox_tags %}`, `css/shoutbox.css`, `js/shoutbox.js`, `{% shoutbox %}` |
| `core/templatetags/custom_admin_tags.py` | imports `ShoutFlag`, counts `flagged_shouts` |
| `sg101/templates/core/admin_dashboard.html` | the `flagged_shouts` condition and its "Shouts" line |
| `antispam/utils.py` | `deactivate_spammer`: `user.shout_set.all().delete()` |
| `antispam/tests/test_utils.py` | makes a `Shout` and asserts it is deleted |
| `core/tests/templatetags/test_custom_admin_tags.py` | patches `ShoutFlag.objects.count`, asserts "Shouts: 9" |

**`js/shoutbox.js` doesn't exist.** `base.html` has loaded a missing file;
remove the reference with the rest. `base.html` itself stays until step 12:
take out only the shoutbox lines.

**The tables must be dropped first.** Like the flatpages removal (`fdb9b5f5`,
#33): `migrate shoutbox zero` runs on leopard against the deployed code,
while the app is still installed, before this is deployed. Say so in the
commit message, as that commit did. Task 03 does it.

**Search before deleting**: grep the repository (templates, Python, static,
`tools/`, fixtures, `AGENTS.md` and `.agents/summary/`) for `shout`
case-insensitively, and account for every hit. Docs that describe the app as
current are updated; the planning record keeps its history.

**Tests to keep passing**: the admin dashboard tag test, and
`deactivate_spammer`'s, each with the shout parts removed.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, item 3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 11)
- `git show fdb9b5f5` (the flatpages removal: the shape and the commit message)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `shoutbox/` and `sg101/templates/shoutbox/` are deleted; `'shoutbox'` is
   out of `INSTALLED_APPS` and `/shout/` out of the URL conf.
2. `base.html` has no shoutbox tag, CSS or script.
3. The admin dashboard and its tag have no shouts line or `ShoutFlag`.
4. `deactivate_spammer` no longer touches shouts and still does everything
   else.
5. `makemigrations --check` is clean.
6. A case-insensitive grep for `shout` finds only the planning record and the
   archive.

## Dependencies
- Task 01: the archive is committed first.

## Implementation Approach
1. Write the tests first: `/shout/` and `/shout/view/history/` 404; the
   dashboard renders without a shouts line; `deactivate_spammer` still
   deactivates the account and deletes its posts and comments. Watch the 404
   tests fail.
2. Remove the app and its references; update the two existing tests.
3. Run `makemigrations --check`, the affected apps' tests, then the full
   suite once under the gate.
4. Mutation-check the new tests, restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **The shoutbox URLs are gone**
   - Given the URL conf after this task
   - When `/shout/` and `/shout/view/history/` are requested
   - Then each answers 404

2. **The admin dashboard has no shouts**
   - Given flagged posts and no shoutbox
   - When the dashboard renders
   - Then it shows the other lines and no "Shouts" line

3. **Deactivating a spammer still works**
   - Given a stranger with posts and comments
   - When `deactivate_spammer` runs
   - Then the account is inactive with spammer status, and its posts and comments are gone

4. **No migration is missing**
   - Given the app removed
   - When `makemigrations --check` runs
   - Then it reports no changes

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Low
- **Labels**: shoutbox, removal, cleanup
- **Required Skills**: Django apps, URL conf, templates
