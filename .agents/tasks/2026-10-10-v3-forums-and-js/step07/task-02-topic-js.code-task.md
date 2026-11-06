# Task: `topic.js` — quick reply, flag and delete without jQuery

## Description
Write `forums/static/js/topic.js`, an ES module that runs the V3 topic page:
quick reply, flag, delete, and the delete-topic confirm. It replaces what
`forums.js` does on the old page, with every request through `core/http.js`
and its messages shown in a callout instead of `alert()`.

## Background
**On this branch, replies are lost.** The reply form posts to `.`, which
`topic_index` ignores; `forums.js` is what turned the submit into quick reply,
and step 6 left it off the V3 page (STATUS, step 6 task 02). So "drop
`forums.js` from the topic page" in the plan is already done. This task puts
the behaviour back.

**The server side needs no change.** The endpoints and their replies, from
`forums/views/main.py`:

| Feature | Endpoint | Sends | Success | Failure |
|---|---|---|---|---|
| Quick reply | `POST /forums/quick-reply/` | `body`, `topic_id`, `attachment` (repeated) | 200, one rendered `display_post_v3.html` | 400 with the form's first error as text; 403 text for not signed in, no permission, or spam |
| Flag | `POST /forums/flag-post/` | `id` | 200 text, a thank-you | 403 or 400 text |
| Delete | `POST /forums/delete-post/` | `id` | 200 text | 403, 400 or 404 |
| Delete topic | the moderator form's submit | | | |

`core/http.js`'s `postForm` sends the CSRF token and `X-Requested-With`,
times out, and throws `RequestError` with a message fit to show, including a
short text body. That covers every failure above, so use it, as
`post_box/uploads.js` and `preview.js` do.

**What `forums.js` does that this must keep** (design §4.4, §5):

- **Quick reply:** disable the button and relabel it while posting. On
  success, append the returned card to `#forum-topic-post-container`, clear
  the textarea, and enable the button. The card's colour comes from
  `:nth-child` (step 6), so no class juggling. **On failure, keep the text**:
  show the message, re-enable the button. `forums.js` also reset the video
  attachment list both ways (`initAttachments`). The list is step 8's, so
  send whatever `attachment` inputs the form holds (none, for now) and leave
  resetting them to step 8.
- **Flag:** keep the `confirm()` and its wording. Show the server's reply in
  a callout on that post, success or failure.
- **Delete:** keep `confirm('Are you sure you want to delete this post?')`.
  On success, show the reply and fade the post (`post-<id>`) out. If it was
  the topic's only post, the server deleted the topic too; check what the old
  page did then and match it.
- **Delete topic:** keep its `confirm()` on `#forum-mod-del-topic`, wording
  unchanged.

**Attach the handlers by delegation on the container**, not per button. A
card appended by quick reply then has working flag and delete buttons
without rebinding. `forums.js` bound them once at load, so a quick-replied
post's tools did nothing until a reload. Say so in STATUS as a fix, not
parity.

**One callout, or one per post?** The post box has `status.js`
(`showStatus`, `hideStatus`). Reuse it if it fits. The callout for flag and
delete should sit on the post it concerns, so a member reading page 3 sees it
where they clicked.

**Load the module where it's needed.** `topic.html` loads the post box only
when `last_page and can_reply`, but flag and delete appear on every page, and
the delete-topic confirm for moderators. Load `topic.js` on every topic page
with `type="module"`. `forums.js` stays: the old-design posting forms use it
until step 8.

**Browser tests open `confirm()` dialogs.** Playwright dismisses dialogs by
default, so a test that doesn't handle one sees the cancel path. Accept with
`page.on('dialog', ...)` set up before the click (STATUS, step 5 task 03: an
`expect_file_chooser` raced a fast key press; `page.on` set up first did not).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.1 `core/http.js`, §4.4, §5 error handling)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/playwright.md (the browser test setup)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2's module loading and import rules; step 5's dialog and file-chooser races)
- `forums/static/js/forums.js` (today's behaviour, lines 1 to 90)
- `sg101/static/js/v3/core/http.js`, `sg101/static/js/v3/post_box/status.js`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `forums/static/js/topic.js`, an ES module with no jQuery, loaded on every
   V3 topic page as `type="module"`. Relative imports end in `.js` (step 2's
   real-tree test enforces it).
2. Every request through `core/http.js`'s `postForm`.
3. Quick reply posts `body`, `topic_id` and any `attachment` inputs, appends
   the returned card, clears the textarea on success, keeps it on failure,
   and shows failures without `alert()`.
4. Flag and delete keep `confirm()`, show the server's reply in a callout on
   the post, and work on a card added by quick reply.
5. Delete fades out `post-<id>` on success.
6. The delete-topic confirm on `#forum-mod-del-topic`.
7. No `alert()` anywhere in the module.

## Dependencies
- Task 01: the card's `data-post-id` buttons and `post-<id>` anchors.
- Step 2: `core/http.js` and the post box modules.
- Step 6: `:nth-child` card colours and `#forum-topic-post-container`.

## Implementation Approach
1. Write the browser tests first, under `@tag('browser')` on
   `BrowserTestCase`, and watch them fail on the branch:
   - Quick reply appends a post, which takes the next card colour, and the
     box is empty after.
   - A rejected reply (an empty body, or one the server refuses) leaves the
     text in the box and shows the message.
   - Flag, accepted, shows the server's reply in a callout on that post.
   - Delete as a moderator removes the post.
   - Flag works on a post that quick reply just added.
2. Write `topic.js`, and load it from `topic.html`.
3. Try it on dev as a member and a moderator: reply, flag, delete, cancel each
   `confirm()`.
4. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
5. Mutation-check (the plan names the first): break the append, clear the box
   on failure, bind flag per button instead of by delegation, and drop the
   module's `<script>` tag. Each is caught. Restore, and confirm the files are
   byte-identical.

## Acceptance Criteria

1. **Quick reply appends and clears**
   - Given a member on the last page of a topic
   - When they submit a reply through the reply box
   - Then the new post appears at the end with the next card colour, the box is empty, and the page didn't reload

2. **A failed reply keeps the text**
   - Given a reply the server refuses
   - When it is submitted
   - Then the text is still in the box, the message is shown on the page, and the button works again

3. **Flag answers in a callout**
   - Given a signed-in member who accepts the confirm
   - When they flag a post
   - Then the server's reply shows in a callout on that post, with no `alert()`

4. **Delete removes the post**
   - Given a moderator who accepts the confirm
   - When they delete a post
   - Then the post is removed from the page and from the database

5. **Tools work on a quick-replied post**
   - Given a post just added by quick reply
   - When its flag button is used
   - Then it flags that post

6. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, JavaScript, ES modules, fetch, Playwright
- **Required Skills**: modern JavaScript (modules, fetch, event delegation), Playwright for Python
