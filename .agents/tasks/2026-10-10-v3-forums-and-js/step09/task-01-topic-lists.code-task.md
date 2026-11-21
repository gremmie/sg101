# Task: The unread, unanswered and active topic lists on V3

## Description
Move `topic_list.html`, the template behind the unread, unanswered and active
topic lists, from `base.html` to `v3/base.html`. Its three views set
`V3_DESIGN`, use the V3 pagination fragment, and stop rendering `page_nav`.
The page's forum query box becomes the V3 one, driven by `nav.js`.

## Background
**The three views**, all in `forums/views/main.py`, render
`forums/topic_list.html`:

| View | URL | Notes |
|---|---|---|
| `unread_topics` | `/forums/unread/` | login required; `unread: True` |
| `unanswered_topics` | `/forums/unanswered/` | open to anonymous visitors |
| `active_topics` | `/forums/topic/active/<num>/` | open to anonymous visitors; `num` is clamped to 10..50 |

Each renders `forums/pagination.html` into a `page_nav` string because the
old template shows it twice. On V3, include `core/v3/pagination.html` twice
instead, as `forum_index.html` does, and drop `page_nav` and its
`render_to_string` from these three views. **`mod_forum` also renders
`forums/pagination.html` into `page_nav`. Leave it alone:** step 10 converts
it, and the old fragment stays until then.

**The table.** Start from `forum_index.html`'s `forum-table`: the topic cell
with `topic_icons` and the page range, Replies, Author and Views hidden below
medium (`show-for-medium`), and Last Post. Add a **Forum** column, which
the old page has as its first column, linking to the topic's forum. Decide
where the forum shows on a phone, where the other columns are hidden, and say
which in `STATUS.md`. On the unread list, **a topic's title links to
`forums-topic_unread`** ("jump to first unread"), and to the topic otherwise.
Keep that. The empty row's text stays "No topics meet your search criteria."

**"Mark All Forums Read"** shows only on the unread list, and only when it
has topics. It posts to `forums-catchup_all`. Make it a Foundation button, as
the forum index's "Mark All Topics Read" is.

**The forum query box.** The V3 version is `forums/v3/forum_query.html`,
marked with `data-forum-nav` and driven by `sg101/static/js/v3/forums/nav.js`
(step 8 task 04). Include it in place of the old `forums/forum_query.html`,
and load `nav.js` as a module in `custom_js`, as `index.html` does. Do not
include `forums/forum_query.js` here. **Do not delete `forum_query.js` or the
old `forum_query.html` yet:** `post_list.html` and `manage_topics.html` still
use them until tasks 02 and 03.

**The crumb** is `{% forum_navigation title %}`, as today. Check that
`navigation_tag` renders the V3 crumb on this page (it chooses on
`V3_DESIGN`, as the release 1 pages showed).

**Three existing tests use the unanswered list as their example of an old
page**, and fail by design once it is V3. Point each at a page that is still
old rather than deleting what it guards:

- `test_old_pages_keep_the_old_fragments` checks that the old variants of
  `topic_icons_tag`, `last_post_info` and `forum_query` are used there, with
  their old icons. `mod_forum`, which it also requests, stays old until step
  10. Choose an old page that still renders those fragments, or narrow the
  test to what an old page still shows.
- `test_unconverted_pages_stay_on_the_old_design` lists it with two
  moderator pages. Drop it from the list.
- `ForumNavTestCase.test_old_pages_keep_the_inline_forum_query_script`
  checks that an old page still gets `forum_query.js`. Point it at a manage
  page until task 03 deletes the script.

`test_unread.py` covers `get_unread_topics` and the unread journeys. Keep
them passing.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 9)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 04: `nav.js` and `forum_query.js`)
- `sg101/templates/forums/forum_index.html` (the V3 topic table)
- `sg101/templates/core/v3/pagination.html`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `topic_list.html` extends `v3/base.html`; `unread_topics`,
   `unanswered_topics` and `active_topics` pass `'V3_DESIGN': True`.
2. The page includes `core/v3/pagination.html` above and below the table, and
   the three views no longer build `page_nav`.
3. The table has a Forum column, and the unread list's titles link to
   `forums-topic_unread`.
4. "Mark All Forums Read" shows only on a non-empty unread list.
5. The page includes `forums/v3/forum_query.html` and loads `nav.js`, and
   not `forum_query.js`.

## Dependencies
- Step 8: `nav.js`, `forums/v3/forum_query.html`, the V3 crumb, and
  `forum_index.html`'s table.
- None on tasks 02 and 03.

## Implementation Approach
1. Write the view tests first, one per URL: renders on `v3/base.html` with
   `V3_DESIGN`; the forum query box once, with `nav.js` and without the inline
   script; the Forum column's link; the unread title link; the catch-up button
   present on a non-empty unread list and absent on the others and on an
   empty one; pagination links on a second page. Watch them fail.
2. Convert the template and the three views.
3. Check the pages on dev at 360 and 1280, signed in and not.
4. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
5. Mutation-check: drop `V3_DESIGN` from a view; link unread titles to the
   topic; show the catch-up button on every list. Each is caught. Restore,
   and confirm the files are byte-identical. Leave the work unstaged for
   review.

## Acceptance Criteria

1. **The three lists are V3**
   - Given the unread, unanswered and active topic URLs
   - When each is requested (the unread list by a member)
   - Then it extends `v3/base.html`, shows the V3 crumb and the V3 forum query box, and loads `nav.js`

2. **Unread titles jump to the first unread post**
   - Given a member with an unread topic
   - When they open the unread list
   - Then the topic's title links to `forums-topic_unread`, and on the other lists titles link to the topic

3. **The catch-up button is where it was**
   - Given the unread list with topics, the unread list empty, and the other lists
   - When each renders
   - Then "Mark All Forums Read" appears only on the first, and posts to `forums-catchup_all`

4. **Pagination is V3**
   - Given more topics than fit on a page
   - When page 2 is requested
   - Then the V3 pagination shows above and below the table, and the view passes no `page_nav`

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Low
- **Labels**: forums, templates, V3 design
- **Required Skills**: Django views and templates, Foundation 6
