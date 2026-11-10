# Task: The confirmation pages on V3, and `nav.js` for the forum select boxes

## Description
Move the three confirmation pages, `new_topic_thanks`, `favorite_status` and
`subscription_status`, to `v3/base.html`. Replace the inline `jump_box.js` and
the V3 pages' use of the inline `forum_query.js` with one module, `nav.js`.

## Background
**The confirmation pages** are short: a `forum_navigation` crumb and a
paragraph or two of text with links. They extend `base.html` today. Their views:

| Template | View | Reached by |
|---|---|---|
| `new_topic_thanks.html` | `new_topic_thanks` (`forums/views/main.py`) | the redirect after a new topic |
| `favorite_status.html` | `favorites_status` (`forums/views/favorites.py`) | the redirect after `favorite_topic` (POST) |
| `subscription_status.html` | `subscription_status` (`forums/views/subscriptions.py`) | the redirect after `subscribe_topic` (POST) |

`unfavorite_topic` and `unsubscribe_topic` redirect to the same two status
pages, which show the "removed" wording; test both branches. Each view adds
`'V3_DESIGN': True`. Keep each page's text as it is, unless something reads
wrong on V3; Brian approves any change of wording.

**The select boxes.** Two inline scripts do the same thing: read the selected
`<option>`'s value and go there.

- `forums/jump_box.js` (`#forum-jumpbox-select`, `#forum-jumpbox-button`) is
  included by `forum_index.html` and `topic.html`, both V3.
- `forums/forum_query.js` (`#forum-query-select`, `#forum-query-button`) is
  included by `index.html` (V3) and by `topic_list.html`, `post_list.html`
  and `manage_topics.html`, which are still on `base.html` and move in
  release 2 (step 9).

Both use jQuery's `$(document).ready`. `nav.js`, a module, replaces them on
the V3 pages. **`jump_box.js` is deleted; `forum_query.js` stays** until step 9
converts its last three pages. Record that in `STATUS.md` so step 9 deletes
it. Mark the select and button so the module finds them by a data attribute,
not by the two pairs of ids, and so one module handles both. A `<form>` with
a `submit` handler is fine too, if it keeps working without a click on Go
(Enter in the select). Say which.

**Where `nav.js` lives.** The plan says `forums/static/js/nav.js`. Step 7 put
forum modules in `sg101/static/js/v3/forums/` (Brian), so use that. Static
module imports end in `;`.

**With JavaScript off**, the Go button does nothing today. Not required to
change; note it if a form makes it work for free.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 8; Step 9 for `forum_query.js`)
- `sg101/templates/forums/jump_box.html`, `jump_box.js`, `v3/forum_query.html`, `forum_query.js`
- `sg101/static/js/v3/forums/topic.js` (module conventions)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `new_topic_thanks`, `favorite_status` and `subscription_status` render on
   `v3/base.html` with `V3_DESIGN`.
2. `sg101/static/js/v3/forums/nav.js` sends the browser to the selected
   option's URL, for the jump box and the forum query box.
3. `index.html`, `forum_index.html` and `topic.html` load `nav.js` and no
   longer include `jump_box.js` or `forum_query.js`.
4. `jump_box.js` is deleted. `forum_query.js` stays for the three release 2
   pages, recorded in `STATUS.md`.

## Dependencies
- Step 6: `index.html`, `forum_index.html`, `topic.html` on V3.
- None on tasks 01-03.

## Implementation Approach
1. Write the view tests first: each confirmation page renders on
   `v3/base.html`, with the favorite and subscription pages reached through
   their POST redirects. Write browser tests that choosing a forum and Go
   lands on it, from the jump box on the topic page and from the query box on
   the index. Watch them fail.
2. Convert the three templates and views.
3. Write `nav.js`, change the select markup, load the module, and remove the
   inline includes.
4. Check the pages on dev at 360 and 1280. Run `make test-browser`, the full
   suite, then the deprecation gate, one at a time.
5. Mutation-check: drop `V3_DESIGN` from a view, and break `nav.js`'s
   selector. Each is caught. Restore, and confirm the files are
   byte-identical. Leave the work unstaged for review.

## Acceptance Criteria

1. **The confirmation pages are V3**
   - Given a member who creates a topic, then favorites and subscribes to it
   - When each redirect lands
   - Then each page extends `v3/base.html` and links back to the topic

2. **The jump box goes to the chosen forum**
   - Given the topic page and the forum index
   - When a forum is chosen and Go is clicked
   - Then the browser lands on that forum

3. **The forum query box goes to the chosen list**
   - Given the forums index
   - When a list is chosen and Go is clicked
   - Then the browser lands on it

4. **No V3 forum page has an inline jQuery script for navigation**
   - Given `index.html`, `forum_index.html` and `topic.html`
   - When they render
   - Then neither inline script is in the HTML, and `jump_box.js` no longer exists

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Low
- **Labels**: forums, templates, V3 design, JavaScript
- **Required Skills**: Django views and templates, vanilla JavaScript (ES modules), Playwright for Python
