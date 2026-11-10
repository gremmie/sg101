# Task: The post box's video button, the attachment list, and videos that fit a phone

## Description
Add a video button to the post box for forum forms (`{% post_box form.body
video=True %}`), with a video modal and a `post_box/video.js` module that
fetches the embed from `/oembed/fetch/` and adds it to an attachment list
under the post box. Add `{% post_attachments form %}`, which renders that list
on the server for a form that already has attachments. Turn it on for the
topic page's quick reply, and make an attached video fit the post card at
360 px.

## Background
**The design is §4.2, `post_box/video.js`.** The modal takes a URL and POSTs
`q=<url>` to `/oembed/fetch/` (`oembed-fetch_media`). The server answers
`{id, embed}`, or a 400/403 with a text message. The module appends an entry to
`<div data-attachments>` holding:

- the embed HTML, as the server returned it
- a Remove button
- `<input type="hidden" name="attachment" value="<id>">`

The forum forms already read `request.POST.getlist('attachment')`
(`AttachmentProcessor` in `forums/attachments.py`), so the server side of
attaching is unchanged.

**Saved attachments are rendered on the server.** The design (Brian,
2026-10-10) replaces `forums.js`'s second request (to
`/forums/fetch_attachments/` or `/oembed/fetch_saved/`) with
`{% post_attachments form %}`, which renders the same markup `video.js`
creates. It has two sources:

- a POSTed form, re-shown after errors: the ids in
  `form.attach_proc.get_ids()`, in that order, with their `Oembed` rows. Ids
  with no row are skipped.
- an unbound edit form: the instance's `post.attachments`, in `order`.

Both posting forms that need it arrive in task 03. This task builds the tag
and tests it on its own, with a form of each kind.

**The topic page's quick reply has no video button yet.** Its form,
`forums/new_post_form.html`, has an empty `Video Attachments` fieldset with
`<div id="attachment">`, which `forums.js` used to fill. STATUS (step 6 task
03) deferred it to this step. `topic.js` sends the reply as
`new FormData(form)`, so hidden `attachment` inputs inside the form are sent
without any change. After an accepted reply, `topic.js` must also empty the
attachment list, as it empties the textarea. After a failed reply, the list
stays, as the text does.

**Modals.** `core/v3/post_box_modals.html` is one shared set per page. Add the
video modal there, rendered only when the page includes it `with video=True`,
as the design says. Follow `hot_link.js` and `smileys.js` for how a modal
finds the active post box. The video entries belong to the active post box's
form. Use `core/http.js` for the request, and `status.js` for the error
message, not `alert()`. Close the modal on success.

**The toolbar fits 7 buttons at 360 px** (step 6 task 03). The video button is
an eighth that phones can see. Measure the toolbar at 360 with it, and if it
wraps, present the screenshot and options to Brian.

**A video wider than the card on a phone** (Brian, 2026-11-06, STATUS under
step 7 task 01). The embed's `<iframe>` comes from the provider with fixed
`width` and `height` (`OEMBED_MAXWIDTH = 480`, `OEMBED_MAXHEIGHT = 295`), and
the card hides what overflows it. Foundation's `responsive-embed` is already
in the build (`main.scss`, `_settings.scss`). Wrapping each embed in it, or an
equivalent CSS rule on the card's iframes, is the likely fix. The same
markup shows the video in the card (`display_post_v3.html`) and in the
attachment list, so fix both. Measure the iframe's width against the card's at
360 and 1280. A 16:9 ratio suits YouTube; check what `Oembed.type` and the
dev data's providers return before assuming every embed is a 16:9 video.

**Put the module where step 7 put forum modules** (Brian): `video.js` goes
with the post box modules in `sg101/static/js/v3/post_box/`, and is imported
by `post_box.js` or loaded only by pages that ask for video. Say which, and
why. Static module imports must end in `;` (a real-tree test enforces it,
step 2 task 01).

**Browser tests make no outside request.** Use an `Oembed` row that already
exists, so `fetch_media` answers from the database (the plan says so). For
errors, answer the request with Playwright's `page.route`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2 `post_box/video.js`, §4.4)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/ (the post box and forums.js topics)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 6 task 03: toolbar at 360; step 7 tasks 01-02: the card and `topic.js`)
- `forums/static/js/forums.js` (today's behaviour, to replace)
- `sg101/static/js/v3/post_box/hot_link.js`, `smileys.js`, `status.js`
- `core/tests/browser.py` (`BrowserTestCase`)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `{% post_box field video=True %}` renders a video button. Without
   `video=True` the toolbar is unchanged.
2. `post_box_modals.html` renders the video modal only when included with
   `video=True`.
3. `video.js` POSTs `q` to `/oembed/fetch/`, appends an entry (embed, Remove
   button, hidden `attachment` input) to the active form's
   `[data-attachments]`, and shows the server's message in the modal on error.
4. Remove takes the entry, and its hidden input, out of the form.
5. `{% post_attachments form %}` renders one entry per attachment, in order,
   in `video.js`'s markup, from the POSTed ids or the edited post.
6. The topic page's quick reply has the video button. Its attachments are
   sent, and the list is emptied after an accepted reply and kept after a
   failed one.
7. At 360 px, an attached video is no wider than its card, on the topic page
   and in the attachment list.

## Dependencies
- Step 2's post box modules, step 4's smiley modal (the active post box
  pattern), and step 7's `topic.js`.
- An `Oembed` row in the test database for the browser tests.

## Implementation Approach
1. Write the template tag tests first: `post_box` with and without
   `video=True`; `post_attachments` for a POSTed form (with an unknown id
   among the known ones) and for an edit form, checking order. Watch them
   fail.
2. Write the browser tests: adding a video puts its `attachment` id in a quick
   reply's request; removing it means the id isn't sent; a fetch error shows
   in the modal; the list is empty after an accepted reply; at 360 the iframe
   fits the card.
3. Build the tags, the modal, `video.js`, and the `topic.js` change.
4. Fix the embed width in Sass, and rebuild `main.min.css`.
5. Check the topic page on dev at 360 and 1280. Run `make test-browser`, the
   full suite, then the deprecation gate, one at a time.
6. Mutation-check: drop the `video=True` condition, send the reply without
   the attachments, skip clearing the list, reverse the attachment order, and
   remove the width rule. Each is caught. Restore, and confirm the files are
   byte-identical. Leave the work unstaged for review.

## Acceptance Criteria

1. **The button appears only where asked for**
   - Given `post_box` with and without `video=True`
   - When each is rendered
   - Then only the first has the video button, and only a page including the modals `with video=True` has the video modal

2. **Adding a video sends its id with a reply**
   - Given a member on a topic page and an existing `Oembed` row
   - When they add its URL in the video modal and quick-reply
   - Then the request carries that row's id as `attachment`, the post shows the video, and the attachment list is empty

3. **Removing a video means it isn't sent**
   - Given a video added to the list
   - When it is removed and the reply is sent
   - Then the request has no `attachment`

4. **Errors show in the modal**
   - Given `/oembed/fetch/` answers 400 with a message
   - When a member adds a URL
   - Then the message shows in the modal, with no `alert()`, and the list is unchanged

5. **Saved attachments render in order**
   - Given a POSTed form with three ids, one unknown, and an edit form for a post with two attachments
   - When `post_attachments` renders each
   - Then the first shows the two known entries in posted order, and the second shows both in `order`

6. **Videos fit a phone**
   - Given a post with a video attachment
   - When the topic page is shown at 360 px
   - Then the iframe is no wider than its card

7. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: High
- **Labels**: forums, post box, JavaScript, ES modules, template tags, oembed, Sass
- **Required Skills**: Vanilla JavaScript (ES modules, fetch, FormData), Django template tags, Foundation 6 Reveal, Playwright for Python
