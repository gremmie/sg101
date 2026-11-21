# Task: "My posts" and a member's posts on V3

## Description
Move `post_list.html`, the template behind "my posts" and a member's posts,
from `base.html` to `v3/base.html`. `_user_posts` sets `V3_DESIGN`, uses the
V3 pagination fragment, and stops rendering `page_nav`. The forum query box
becomes the V3 one, driven by `nav.js`.

## Background
**The views**, in `forums/views/main.py`, both login required, both through
`_user_posts`:

| View | URL | Title |
|---|---|---|
| `my_posts` | `/forums/my-posts/` | "My Posts" |
| `posts_for_user` | `/forums/posts/<username>/` | "Posts by <username>"; the username matches case-insensitively |

`_user_posts` lists the target user's posts newest first, only in the forums
the *requesting* user can see, paginated with `create_post_paginator` (20 a
page). Like the topic lists it renders `forums/pagination.html` into
`page_nav`; on V3, include `core/v3/pagination.html` above and below the list
and drop `page_nav`.

**Each post today** is a `<dt>` with three links, the forum, the topic, and
the post's date (`forum_date`, in the reader's time zone) linking to the post
in context, then a `<dd>` with `post.html|safe`, the post's cached rendered
HTML (AGENTS.md: rendering is at save time, so nothing here re-renders).

**On V3**, give each post a card with that forum › topic › date line as its
header and the body below. Use the post card's shared class (`sg101-card`
and its divider, step 6 task 02) so the colours and spacing match the topic
page, but this is not the topic page's `display_post_v3.html`: no author
column, no post tools. Brian settles the look at the screenshot review;
record his choices in `STATUS.md`. The empty case stays "No posts found."

**The forum query box**: include `forums/v3/forum_query.html` and load
`nav.js` as a module, as task 01 does. Do not include
`forums/forum_query.js`, and do not delete it yet: `manage_topics.html` still
uses it until task 03.

**Existing tests**: `test_views.py` has `test_posts_for_user`,
`test_posts_for_user_differing_case` and a third around line 157. Keep them
passing.

**Embedded content in a post body**, such as a video's `<iframe>`, is
rendered HTML from the database and may be wide. Check a post with a video
and one with a wide image at 360, and that the page doesn't scroll sideways.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 9)
- `sg101/templates/forums/display_post_v3.html` and `sg101/scss/_sg101.scss` (the card's classes)
- `sg101/templates/core/v3/pagination.html`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `post_list.html` extends `v3/base.html`; `_user_posts` passes
   `'V3_DESIGN': True`.
2. The page includes `core/v3/pagination.html` above and below the list, and
   `_user_posts` no longer builds `page_nav`.
3. Each post is a card with a header linking to its forum, its topic, and the
   post in context, and the post's cached HTML as its body.
4. The page includes `forums/v3/forum_query.html` and loads `nav.js`, and
   not `forum_query.js`.
5. A Sass change, if any, is committed with its rebuilt `main.min.css`, and
   the forums tests that pin CSS pass (memory: CSS changes need the suite).

## Dependencies
- Step 8: `nav.js`, `forums/v3/forum_query.html`, the V3 crumb.
- None on tasks 01 and 03.

## Implementation Approach
1. Write the view tests first, for both URLs: renders on `v3/base.html` with
   `V3_DESIGN`; one card per post, newest first, with the three links; the
   forum query box with `nav.js` and without the inline script; "No posts
   found." for a member with none; a post in a forum the requester can't see
   is left out. Watch them fail.
2. Convert the template and `_user_posts`.
3. Check both pages on dev at 360 and 1280, including a post with a video.
4. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
5. Mutation-check: drop `V3_DESIGN`; reverse the order; drop the link to the
   post in context. Each is caught. Restore, and confirm the files are
   byte-identical. Leave the work unstaged for review, with screenshot paths
   for Brian.

## Acceptance Criteria

1. **Both post lists are V3**
   - Given a member with posts
   - When they open "my posts", and another member's posts
   - Then each page extends `v3/base.html`, with the V3 crumb, the V3 forum query box and `nav.js`

2. **Each post links to where it lives**
   - Given a post in the list
   - When the page renders
   - Then its card header links to its forum, its topic, and the post in context, with the date in the reader's time zone

3. **Only visible forums are listed**
   - Given a post in a forum the requester can't see
   - When the requester opens that member's posts
   - Then the post is not listed

4. **No sideways scroll on a phone**
   - Given a post with a video and one with a wide image
   - When the page is viewed at 360 px
   - Then the page does not scroll sideways

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Low
- **Labels**: forums, templates, V3 design
- **Required Skills**: Django views and templates, Foundation 6, Sass
