# Task: Split topic and move topic on V3

## Description
Move the two topic-level moderator forms, `mod_split_topic.html` and
`move_topic.html`, from `base.html` to `v3/base.html`.

## Background
**The views**, both in `forums/views/main.py`, login required:

| View | URL | Refused |
|---|---|---|
| `mod_topic_split` | `/forums/mod/topic/split/<id>/` | a non-moderator is **redirected**, not refused (`test_split_by_non_moderator_redirects_without_splitting`); keep it |
| `mod_topic_move` | `/forums/mod/topic/move/<id>/` | 403 |

**Split** renders `SplitTopicForm` (new topic title, forum) with
`form.as_table`, two submit buttons, `split-selected` ("Split Selected
Posts") and `split-at` ("Split At Selected Post"), then every post of the
topic in a table: author, a link icon, date, **the post's IP address**, the
post's HTML, and a `post_ids` checkbox on every post but the first. The form
raises "Please select some posts" with none checked, and "Please select only
one post to split the topic at" for `split-at` with more than one. The
template's `custom_js` block emits `{{ form.media }}`, which is empty for
these fields; drop it, and say so.

**How split shows its posts is Brian's choice.** A long topic is a long
page. Options to show him: the topic page's post cards with a checkbox, or a
compact list (author, date, an excerpt). Show the choices on a real topic at
360 and 1280 before building one. Whichever he picks, the IP stays visible
to moderators, and the post HTML is the cached `post.html`, as today.

**Move** renders `MoveTopicForm` (one forum select) with `form.as_p` in a
fieldset whose legend names the topic, and a "Move Topic" button; on success
it redirects to the topic.

Both pages get the V3 crumb, an `<h2>`, and V3 form markup, as the posting
forms did in step 8 (`forums/v3/post_form.html` and #47's tighter fieldset).
Render fields individually if `as_table` or `as_p` doesn't sit well in
Foundation's grid.

**The step 9 "old page" tests.** After task 01, `move_topic` is the last
example left in `test_unconverted_pages_stay_on_the_old_design`; this task
converts it, so drop it there. Task 03 replaces the test.

**Existing tests**: `ModTopicActionTests` (`test_moderation.py`): move,
split-selected, split-at, and the non-moderator redirect. Keep them passing.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 10)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 03, #47)
- `sg101/templates/forums/v3/post_form.html`, `display_post_v3.html`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Both templates extend `v3/base.html`; both views pass `'V3_DESIGN': True`.
2. Split keeps both buttons, a checkbox on every post but the first, each
   post's date and IP, and both validation errors.
3. Move keeps its one select, the topic's name, and the redirect to the
   topic.
4. The permission behaviour is unchanged: split redirects a non-moderator,
   move refuses one with a 403.

## Dependencies
- Task 01 (the step 9 old-page tests are narrowed there first).

## Implementation Approach
1. Show Brian the split options on a real topic; settle the layout.
2. Write the tests first: both pages on `v3/base.html`; split shows the IP
   and no checkbox on the first post; both validation errors render; move
   names the topic. Watch them fail.
3. Convert the templates and views.
4. Check both pages on dev at 360 and 1280.
5. Run the forums tests, then the full suite once, under the gate.
6. Mutation-check each new test, restore byte-identical, and leave the work
   unstaged for review.

## Acceptance Criteria

1. **Both pages are V3**
   - Given a moderator and a topic with several posts
   - When they open split and move
   - Then each extends `v3/base.html` with the V3 crumb

2. **Split still splits**
   - Given two posts checked and a new title and forum
   - When the moderator chooses Split Selected Posts, or one post and Split At Selected Post
   - Then the posts move to a new topic as today

3. **Split explains a bad selection**
   - Given no posts checked, or two with Split At
   - When the moderator submits
   - Then the matching error is shown and nothing is split

4. **Move still moves**
   - Given a destination forum
   - When the moderator submits
   - Then the topic is in that forum and the browser is on the topic

5. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, moderation, forms
- **Required Skills**: Django views, forms and templates, Foundation 6
