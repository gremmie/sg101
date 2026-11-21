# Task: Favorites and subscriptions management on V3, the master checkbox as a module, and `forum_query.js` deleted

## Description
Move `manage_topics.html`, the template behind managing favorite and
subscribed topics, from `base.html` to `v3/base.html`. Replace its inline
jQuery with a shared ES module for a master checkbox, which step 10's
moderator page will reuse. With this page converted, nothing uses
`forum_query.js` or the old `forum_query.html`; delete both.

## Background
**The views**, both login required, both render `forums/manage_topics.html`:

| View | URL | Title |
|---|---|---|
| `manage_favorites` (`forums/views/favorites.py`) | `/forums/favorites/` | "Favorite Topics" |
| `manage_subscriptions` (`forums/views/subscriptions.py`) | `/forums/subscriptions/` | "Topic Subscriptions" |

Each lists the user's topics, newest update first, 20 a page, with its own
`DiggPaginator`. A POST removes the checked topics (`delete_ids`) and
redirects back to the list. Both views also accept **`delete_all`**, which
clears the list, but **the template has no control that sends it**. Keep
the branch as it is, and don't add a button for it unless Brian asks; note
it in `STATUS.md`.

The template uses the old `forums/pagination.html` include directly (not
`page_nav`). Use `core/v3/pagination.html`. It posts the current page number
in a hidden `page` input, which the views ignore; keep or drop it, and say
which.

**The inline script today** (jQuery, in `custom_js`):

- `#master_check` checks or unchecks every `.topic_box`.
- On submit, with nothing checked, `alert("Please select some topics to
  remove.")` and cancel; otherwise `confirm("Are you sure you wish to remove
  the selected topics from your list?")`.

`forums/static/js/forums_mod.js`, used by `mod_forum.html` (step 10), does
the master half too, and one thing more: **unticking a topic unticks the
master**. The new module does both.

**The shared module.** The plan says step 9's checkboxes reuse the master
checkbox behaviour "through step 10's `mod.js`, or a shared module if it
lands first". Step 9 lands first, so write the shared module here, in
`sg101/static/js/v3/` (choose the path and name with Brian; step 7 put forum
modules in `sg101/static/js/v3/forums/`). Mark the master and its boxes with
data attributes rather than ids or classes, so `mod_forum` can use it
unchanged. Keep the submit check and the confirmation, in this page's own
code or the module's, and keep the wording; Brian approves any change.
Static module imports end in `;`.

**With JavaScript off**, the form posts whatever is checked, with no
confirmation, as today.

**Deleting `forum_query.js`.** After this task, `topic_list.html` (task 01),
`post_list.html` (task 02) and this page all use `forums/v3/forum_query.html`
and `nav.js`. Delete `sg101/templates/forums/forum_query.js` and
`sg101/templates/forums/forum_query.html`, and grep that nothing references
either. `ForumNavTestCase.test_old_pages_keep_the_inline_forum_query_script`
fails by design and is deleted with them (STATUS, step 8 task 04); replace it
with a test that the template no longer exists, as step 8 did for
`jump_box.js`. **`forums/pagination.html` stays** for `mod_forum`.

**Existing tests**: `forums/tests/test_subscriptions.py` covers listing and
deleting for both pages, and `delete_all` (`test_manage_*_lists_and_deletes`,
`test_manage_*_delete_all`). Keep them passing.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4, `mod.js`)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Steps 9 and 10)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 04: `forum_query.js`)
- `forums/static/js/forums_mod.js`, `sg101/templates/forums/mod_forum.html`
- `sg101/static/js/v3/forums/nav.js`, `topic.js` (module conventions)
- `forums/tests/test_browser.py` (`ForumNavBrowserTestCase`, the browser test pattern)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `manage_topics.html` extends `v3/base.html`; `manage_favorites` and
   `manage_subscriptions` pass `'V3_DESIGN': True`.
2. The page uses `core/v3/pagination.html` and `forums/v3/forum_query.html`
   with `nav.js`.
3. A shared master-checkbox module, found by data attributes: the master
   checks or unchecks every box, and unticking a box unticks the master.
4. Submitting with nothing checked warns and doesn't post; otherwise the
   confirmation is asked, with today's wording.
5. `forum_query.js` and the old `forum_query.html` are deleted, and nothing
   references them.
6. The removal POSTs still remove exactly the checked topics.

## Dependencies
- Tasks 01 and 02: the last two other users of `forum_query.js`.
- Step 8: `nav.js` and `forums/v3/forum_query.html`.

## Implementation Approach
1. Write the tests first. View tests for both URLs: renders on
   `v3/base.html` with `V3_DESIGN`; the module loaded; no inline jQuery; the
   forum query box with `nav.js`; the old `forum_query.js` and
   `forum_query.html` templates don't exist. Browser tests: the master checks
   all and unchecks all; unticking one unticks the master; submit with none
   checked shows the warning and doesn't post; dismissing the confirmation
   doesn't post; accepting it removes exactly the checked topics. Watch them
   fail.
2. Write the module, convert the template and the two views, and delete the
   two old templates.
3. Check both pages on dev at 360 and 1280.
4. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
5. Mutation-check: the master doesn't uncheck; unticking a box leaves the
   master ticked; the empty-selection check removed; the confirmation
   skipped. Each is caught. Restore, and confirm the files are byte-identical.
   Leave the work unstaged for review.

## Acceptance Criteria

1. **Both manage pages are V3**
   - Given a member with favorites and subscriptions
   - When they open each manage page
   - Then it extends `v3/base.html`, with the V3 crumb, the V3 forum query box and V3 pagination

2. **The master checkbox checks all**
   - Given a manage page with several topics
   - When the master is ticked, then unticked, and then one topic is unticked after ticking the master
   - Then every box follows the master, and unticking one unticks the master

3. **Removal asks first and removes what's checked**
   - Given two of three topics checked
   - When the member submits and accepts the confirmation
   - Then exactly those two are removed and the list is shown again

4. **Nothing posts by mistake**
   - Given nothing checked, or the confirmation dismissed
   - When the member submits
   - Then nothing is posted and the list is unchanged

5. **`forum_query.js` is gone**
   - Given the repository after this task
   - When it is searched for `forum_query.js` and the old `forum_query.html`
   - Then neither file exists and nothing references them

6. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, JavaScript
- **Required Skills**: Django views and templates, vanilla JavaScript (ES modules), Playwright for Python
