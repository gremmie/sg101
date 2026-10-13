# Task: Every post box on the modules, and the old script deleted

## Description
Move the ten remaining post box pages to task 02's entry module, drop jQuery
Form from all eleven, and delete `sg101/static/js/v3/post_box.js`. Remove the
leftovers in the shared post box templates that only the old script used.
Prove the two-post-box page in a browser test, check a production-style
`collectstatic`, and walk the demo pages by hand. This completes step 2, which
merges and deploys together with step 1.

## Background
After task 02, `news/submit_news.html` runs the modules and the other pages
still load `js/jquery.form.min.js` and `js/v3/post_box.js`.

**Eleven templates load `post_box.js`** (the plan says twelve; measured
2026-10-12 with `grep -rl 'js/v3/post_box.js' . --include='*.html'`):
`bio/edit_profile.html`, `contests/contest_detail.html`, `downloads/add.html`,
`downloads/download_detail.html`, `gcalendar/event.html`,
`messages/compose.html`, `messages/view_message.html`, `news/story.html`,
`news/submit_news.html` (done in task 02), `polls/poll_detail.html`,
`potd/view.html`. All are under `sg101/templates/`.

**jQuery Form is loaded by fifteen**: those eleven, plus four forum templates
(`forums/topic.html`, `new_topic.html`, `new_post.html`, `edit_post.html`).
Only `post_box.js` calls jQuery Form (`ajaxForm`, `clearForm`) among the
non-minified scripts under `sg101/static/js`. So on the eleven pages jQuery
Form goes with the post box. **The four forum templates are out of scope.**
They're on the old design and are rewritten in step 8. Check there whether
their copy is still dead, rather than here.

`bio/edit_profile.html` has **two** post boxes (`profile_text` and
`signature`) sharing one set of modals. That's the case the active post box
exists for. It also loads `js/bio.js` and `js/timezone.js`, which use jQuery
and stay.

Several of these pages also carry `comments.js`, `rating.js` or similar
jQuery scripts, which stay. Removing jQuery Form must not break them. Each
page needs checking that nothing else on it called jQuery Form.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2, §7.2, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 2 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (task 02's notes)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Before changing anything, re-measure the template lists above. Record any
   difference.
2. On each of the ten pages, replace the `jquery.form.min.js` and
   `js/v3/post_box.js` tags with the entry `<script type="module">`, as task
   02 did on news submit. Change nothing else on those pages.
3. Delete `sg101/static/js/v3/post_box.js`. Remove whatever in
   `core/v3/post_box.html` and `core/v3/post_box_modals.html` only the old
   script used. Check that `core/tests/test_static.py` still passes: it fails
   on any template naming a static file that no longer exists.
4. Don't delete `js/jquery.form.min.js`. The four forum templates still load
   it until step 8.
5. A browser test on `bio/edit_profile`: with the caret placed in the
   **second** post box (signature), hot-link or upload inserts into the
   signature and leaves `profile_text` unchanged; then the same with the first.
6. A production-style `collectstatic` (`sg101.settings.production`, as the
   Dockerfile runs it) into a temporary directory. Check that the hashed
   `post_box.js` imports hashed names of its siblings and of `core/http.js`,
   and that each named file exists.
7. Comments describe the code, never this plan's step numbers.

## Dependencies
- Tasks 01 and 02.

## Implementation Approach
1. Re-measure the template lists.
2. Write the two-post-box browser test against `edit_profile` as it is today
   (old script). The active-post-box behaviour exists today, so it should pass
   before the switch, apart from the at-cursor assertion.
3. Switch the ten pages, delete the old script, and remove its template hooks.
4. Run the browser tests. Mutation: make the entry module record the first
   post box instead of the clicked one, and see the two-post-box test fail;
   restore.
5. Production-style `collectstatic`, and read the hashed entry file.
6. Manual walk in a browser at phone and desktop widths (design §7.3), with
   the console and network panels open: news submit, profile edit, message
   compose and a comment form (for example a news story). On each: toolbar,
   preview, hot-link and upload. Record what was checked.
7. Run `make test-browser`, the full suite, and the deprecation gate as its own
   run.

## Acceptance Criteria

1. **No page loads the old script**
   - Given the templates after the change
   - When searched for `js/v3/post_box.js`
   - Then none name it, the file is gone, and `core/tests/test_static.py` passes

2. **jQuery Form is gone from the post box pages only**
   - Given the eleven post box templates
   - When searched for `jquery.form`
   - Then none load it, and the four forum templates still do

3. **The right post box receives the insertion**
   - Given `bio/edit_profile` with two post boxes
   - When the caret is in one and an image is hot-linked or uploaded
   - Then only that textarea changes, at its caret

4. **Production hashes the imports**
   - Given `collectstatic` under `sg101.settings.production`
   - When the hashed entry module is read
   - Then each import names a hashed file that exists in the output

5. **The demo pages work in a browser**
   - Given news submit, profile edit, message compose and a news story's comment form
   - When toolbar, preview, hot-link and upload are each used at phone and desktop widths
   - Then each works, the console shows no errors, and the network panel shows no `jquery.form.min.js`

6. **Suite, gate and CI**
   - Given the change
   - When the suite runs, then the gate as its own run, then CI on push
   - Then all are green

## Metadata
- **Complexity**: Medium
- **Labels**: JavaScript, ES modules, post box, templates, Playwright, static files, manual testing
- **Required Skills**: Django templates and staticfiles, Playwright for Python, browser devtools
