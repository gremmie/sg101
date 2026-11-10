# Task: New topic, new post and edit post on V3, and `forums.js` removed

## Description
Move the three posting pages, `new_topic`, `new_post` (with `?quote=`) and
`edit_post`, to `v3/base.html`, with the post box, the video button and their
saved attachments. Port the new-topic "Quick Search" off `forums.js`. Then
delete `forums.js`, the `fetch_attachments` and `fetch_saved_media` views and
their URLs, and the hidden form fields that existed only to feed them. Fix the
`KeyError` an unknown attachment id raises when a post is saved.

## Background
**Today all three pages extend `base.html`** and render the form through
`{% show_form %}` (`forums/show_form.html`): markItUp, `jquery.form`,
`forums.js`, and the old image dialogs. `v3-dev` never converted them, so
there is no port to start from. Build them on `v3/base.html` with
`{% post_box form.body video=True %}`, `{% post_attachments form %}` (task 02),
`core/v3/post_box_modals.html` included `with video=True`, and `post_box.js`.
Each view adds `'V3_DESIGN': True` to its context, as every V3 view does
(design §4.4). `forum_navigation` and the other forum tags then choose their
V3 variants.

**What each page holds:**

| Page | View | Form | Extras |
|---|---|---|---|
| `new_topic.html` | `new_topic` | `NewTopicForm` | subject; sticky and locked for moderators; Quick Search |
| `new_post.html` | `new_post` | `PostForm` | `?quote=<id>` fills the body; "locked" or "no permission" text when `can_post` is false |
| `edit_post.html` | `edit_post` | `PostForm(instance=…)` | the post being edited shown above the form; subject when it is the first post |

Show the post on `edit_post` with `display_post_v3.html`, as the topic page
does. `display_post.html` loses its last user here: delete it if nothing else
includes it, and say so. `show_form` and `show_form.html` lose theirs too;
delete them likewise. Grep both static trees and every template first.

**The new-topic Quick Search is in `forums.js`** and the plan doesn't place
it. The button beside the subject sends the title to `/search/topics/` (GET,
`q`), which returns an HTML fragment of matching topics with a "hide" control,
rendered under the field. It is `@login_required`. Port it to a module in
`sg101/static/js/v3/forums/` (step 7's location, Brian) using `core/http.js`,
with the error in a `status.js` callout, not `alert()`. The fragment's markup
may need V3 classes; check `search/templates`. `search/urls.py` and
`search/views.py` both say `forums.js` fixes the path: update them to name
the new module.

**Hidden fields to remove.** They told `forums.js` what to fetch:

- `NewTopicForm` adds a `MultipleHiddenInput` `attachment` field when a POST
  had attachments.
- `PostForm` adds a hidden `post_id` field when editing a post that has
  attachments.

`{% post_attachments form %}` renders the list, and its hidden inputs, from
the same data, so these fields would send each id twice. Remove both, and the
comments that describe them. `PostForm` re-shown after errors on `new_post`
loses its attachments today (it has no hidden field); with `post_attachments`
it keeps them.

**The `KeyError`.** `AttachmentProcessor.save_attachments` does
`self.embeds[pk]` for every posted id, but `self.embeds` comes from
`Oembed.objects.in_bulk(self.pks)`, which leaves out ids with no row. An
`attachment` id with no `Oembed` row (forged, or deleted meanwhile) therefore
raises `KeyError` and a 500. Write the failing test first, then skip ids with
no row, in `save_attachments` or by keeping `pks` to the ids `in_bulk` found.
Keep the posted order.

**Deletions, once nothing calls them** (grep both static trees, all
templates, and the tests):

- `forums/static/js/forums.js`
- `forums/views/attachments.py` `fetch_attachments`, and its URL
  `forums-fetch_attachments`
- `oembed/views.py` `fetch_saved_media`, and its URL `oembed-fetch_saved_media`
- the tests of all three, replaced by tests that the URLs now 404

**The "Need help?" link** under Video Attachments points at the fixed topic
`/forums/topic/18843/`, in `new_post_form.html` and `show_form.html`. The plan
leaves it for this step: does it stay a fixed topic now the video button
exists? Ask Brian; don't choose. Options include keeping it, pointing the video
modal's own help text at it, or dropping it.

**Removing jQuery from these pages.** They load `script_tags 'jquery-ui
markitup'` and `jquery.form.min.js` today. `v3/base.html` brings its own
jQuery for Foundation. None of the three needs markItUp or `jquery.form` after
this task.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2 `post_box/video.js`, §4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 8)
- `forums/forms.py`, `forums/attachments.py`, `forums/views/main.py`
- `sg101/templates/forums/show_form.html` (today's form, item for item)
- `forums/static/js/forums.js` (the Quick Search)
- `search/views.py` `search_topics`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `new_topic`, `new_post` and `edit_post` render on `v3/base.html` with
   `V3_DESIGN`, the post box with the video button, and the attachment list.
2. Every field `show_form.html` shows today still shows: subject, body,
   sticky and locked for moderators, and errors on each.
3. `?quote=<id>` fills the body as today.
4. A form re-shown after errors keeps its attachments, in order. An edit
   form shows the post's attachments, with no AJAX request.
5. The Quick Search works from a module, without jQuery or `alert()`.
6. `NewTopicForm`'s hidden `attachment` field and `PostForm`'s `post_id` are
   gone.
7. An unknown `attachment` id is skipped; the post saves with the others.
8. `forums.js`, `fetch_attachments`, `fetch_saved_media` and their URLs are
   deleted, and the URLs 404.
9. Brian's decision on the "Need help?" link is recorded in `STATUS.md` and
   carried out.

## Dependencies
- Task 02: `post_box video=True`, `post_attachments`, `video.js`.
- Step 7: `display_post_v3.html` and `topic.js`.

## Implementation Approach
1. Write the view tests first and watch them fail: each page renders on
   `v3/base.html`; the edit page of a post with attachments contains their
   embeds and hidden inputs; a `new_post` and a `new_topic` re-shown after an
   error keep their attachments; `?quote=` fills the body; the removed URLs
   404; an unknown attachment id saves the post without it.
2. Write the browser tests: the plan's demo path (start a topic with a video,
   reply with a quote, edit to add a second video) posts the right ids; the
   Quick Search shows results under the subject.
3. Build the templates, move the views to V3, port the Quick Search, remove
   the hidden fields, fix the `KeyError`.
4. Delete the old code once grep finds no caller. Ask Brian about the help
   link.
5. Check the three pages on dev at 360 and 1280 as a member and a moderator.
   Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
6. Mutation-check: drop `V3_DESIGN` from a view, put the hidden `post_id` back
   (the edit then sends ids twice), break `?quote=`, and undo the `KeyError`
   fix. Each is caught. Restore, and confirm the files are byte-identical.
   Leave the work unstaged for review.

## Acceptance Criteria

1. **The three pages are V3**
   - Given a member, and a moderator for the sticky and locked fields
   - When each opens new topic, new post and edit post
   - Then each page extends `v3/base.html` and shows the post box with the video button

2. **Editing shows saved videos without a request**
   - Given a post with two attachments
   - When its author opens edit post
   - Then both embeds and their hidden inputs are in the HTML, in order, and no request goes to a removed endpoint

3. **Attachments survive a form error**
   - Given a new topic posted with a video and no subject
   - When the form comes back with the error
   - Then the video is still in the list, once

4. **The demo path works**
   - Given a member on dev
   - When they start a topic with a video, reply with a quote, and edit the reply to add a second video
   - Then each page is V3, and each saved post has the attachments that were sent

5. **An unknown id doesn't break a post**
   - Given a reply POSTed with one known and one unknown `attachment` id
   - When it is saved
   - Then the post saves with the known attachment, and no error is raised

6. **The old endpoints are gone**
   - Given the removed URLs
   - When requested
   - Then each answers 404, and `forums.js` no longer exists

7. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: High
- **Labels**: forums, templates, V3 design, forms, JavaScript, cleanup
- **Required Skills**: Django forms, views and templates, vanilla JavaScript (ES modules), Playwright for Python
