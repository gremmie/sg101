# Task: The moderate-forum page on V3, with `check_all.js` replacing `forums_mod.js`

## Description
Move `mod_forum.html`, the page where a moderator sticks, locks, deletes and
moves a forum's topics in bulk, from `base.html` to `v3/base.html`. Its
master checkbox moves to the shared `check_all.js` from step 9, and
`forums_mod.js` is deleted.

## Background
**The view**, `mod_forum` (`forums/views/main.py`), at
`/forums/mod/forum/<slug>/`, login required; a member who can't moderate the
forum gets a 403. It lists the forum's topics with `create_topic_paginator`
and renders the old `forums/pagination.html` into **`page_nav`**, twice. A
POST with checked `topic_ids` and one of `sticky`, `lock`, `delete` or
`move` (with a `MoveTopicForm` destination) acts on those topics and
redirects to the page. A move with no destination shows the form's error.

**The template today** (`sg101/templates/forums/mod_forum.html`): a
five-column table (topic with sticky and lock icons, replies, author, last
post, a checkbox column headed "Select" with the master box), `page_nav`
above and below, then a control bar: Toggle Sticky, Toggle Lock, Delete,
then "Move To:" and the forum select. A template comment explains why the
select is rendered as a bare field, not a whole form; keep that reasoning
(`test_the_move_control_is_a_bare_select` pins it).

**The master checkbox.** `forums/static/js/forums_mod.js` (jQuery): the
master `#forums-master-topic` ticks or unticks every `.forums-topic_check`,
and unticking a topic unticks the master. `sg101/static/js/v3/forums/check_all.js`
(step 9) does exactly this, found by `data-check-all` and `data-check-item`;
its `data-none-checked` and `data-confirm` are opt-in, so this page can use
the checkbox half alone (STATUS, step 9 task 03). **No `mod.js`**: Brian
agreed 2026-11-25 that `check_all.js` replaces `forums_mod.js`, and the
plan's bullet is updated to match. Whether Delete should ask first is a
question for Brian, not a default: today it doesn't.

**The page number is probably lost on a POST: measure it.** The form posts
to `action="."`, which drops the query string, and `get_page_num` reads only
`GET`. So the hidden `page` input appears to be ignored, and a bulk action on
page 3 redirects to page 1. Confirm this with a test or a dev probe before
reporting it; then show Brian and let him decide whether to fix it here.

**Follow step 9's lists** for the table: `forum-table`, the V3 topic icons
(`forums/v3/topic_icons_tag.html`), `forums/v3/last_post_info.html`, V3
pagination (`core/v3/pagination.html`) above and below, the V3 crumb, an
`<h2>`, the checkbox column as `.forum-table-check` (step 9 task 03). Which
columns stay on a phone, and where the control bar sits, are Brian's
choices: show him the page at 360 and 1280 before settling them.

**The tests that use this page as the "old page" example**,
`test_old_pages_keep_the_old_fragments` and
`test_unconverted_pages_stay_on_the_old_design` (`test_views.py`), fail by
design once it converts. Task 03 replaces them with a static check that no
forum template extends `base.html`; here, drop `mod_forum` from them and
leave `move_topic` until task 02. **The old fragment templates stay** for
step 12, which deletes them with `V3_DESIGN`.

**Existing tests**: `ModForumBulkTests` (`test_moderation.py`): 403 for a
non-moderator, renders for a moderator, the four bulk actions, the bare
select, and the move error. Keep them passing.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 10)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 9 tasks 01 and 03)
- `sg101/templates/forums/manage_topics.html`, `topic_list.html` (the V3 tables)
- `forums/tests/test_browser.py` (`ManageTopicsBrowserTestCase`, the master checkbox tests)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `mod_forum.html` extends `v3/base.html`; `mod_forum` passes
   `'V3_DESIGN': True` and no longer renders `page_nav`.
2. The page uses V3 pagination, the V3 crumb, topic icons and last post
   info, and loads `check_all.js`; it no longer loads `forums_mod.js`.
3. `forums/static/js/forums_mod.js` is deleted, and nothing references it.
4. The four bulk actions act on exactly the checked topics, and a move with
   no destination still shows the error.
5. A member who can't moderate the forum still gets a 403.

## Dependencies
- Step 9: `check_all.js` and the `.forum-table-check` column.

## Implementation Approach
1. Write the tests first: the page on `v3/base.html` with V3 pagination and
   no `page_nav`; `check_all.js` loaded and `forums_mod.js` not; the file
   gone. A browser test of the master checkbox on this page, as a
   moderator. Watch them fail.
2. Convert the template and the view; delete `forums_mod.js`.
3. Measure the page-number behaviour on POST and report it.
4. Show Brian the page at 360 and 1280, and settle the phone columns and the
   control bar with him.
5. Run the forums tests, then the full suite once, under the gate.
6. Mutation-check each new test, restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **The page is V3**
   - Given a moderator of a forum
   - When they open its moderate page
   - Then it extends `v3/base.html`, with V3 pagination and no `page_nav`

2. **The master checkbox works**
   - Given the page with several topics
   - When the master is ticked, then one topic is unticked
   - Then every box was ticked, and unticking one unticks the master

3. **The bulk actions still act on the checked topics**
   - Given two topics checked
   - When the moderator toggles sticky, toggles lock, moves or deletes
   - Then exactly those two change

4. **`forums_mod.js` is gone**
   - Given the repository after this task
   - When it is searched for `forums_mod.js`
   - Then the file doesn't exist and nothing references it

5. **Members are still refused**
   - Given a member who can't moderate the forum
   - When they open the page
   - Then they get a 403

6. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, moderation, JavaScript
- **Required Skills**: Django views and templates, Foundation 6, Playwright for Python
