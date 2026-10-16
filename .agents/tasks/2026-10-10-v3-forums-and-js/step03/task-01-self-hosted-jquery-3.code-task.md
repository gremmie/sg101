# Task: jQuery 3.7.1 and jQuery UI 1.13.3, served from the site

## Description
Every V3 page loads jQuery 3.7.1 from the site's own static files instead
of Google's 2.2.4, and jQuery UI moves from Google's 1.11.0 to a self-hosted
1.13.3. Two small fixes go with it: Foundation 6.2.0's JavaScript calls an API jQuery 3
removed, and `comments.js` calls another. Browser tests prove that Foundation,
the datepicker and the autocomplete still behave as they do on 2.2.4.

## Background
Research topic 8 (`research/jquery3.md`) swapped jQuery in a headless
browser across eight V3 pages and found exactly what breaks:

- **Foundation's JavaScript (6.2.0; the task first said 6.3.1) calls
  `$(window).load(function …)`** once, in its
  triggers utility. jQuery 3.0 removed `.load(handler)`, so the call throws,
  the rest of `foundation.min.js`'s init is skipped, and **no Reveal modal
  opens**. Fix: in `sg101/static/js/v3/foundation.min.js` change
  `(window).load(function` to `(window).on("load",function`. There is exactly
  one occurrence (re-counted 2026-10-15).
- **jQuery UI 1.11.0's autocomplete** calls `.offset()` on `window`, which
  jQuery 3 rejects (`getClientRects`). The menu appears at the page's top-left
  (0, 0). Fix: jQuery UI 1.13.3. With both fixes, every page probed matched
  2.2.4 exactly.
- **`comments/static/js/comments.js:26`** calls `.size()`, removed in 3.0. It
  runs only after a comment is posted, which the probe didn't do. Fix:
  `.length`.

Facts about today's tree (checked 2026-10-15):
- `sg101/templates/v3/base.html:277` loads
  `https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js`.
- `sg101/settings/base.py`'s `GPP_THIRD_PARTY_JS['jquery-ui']` and
  `GPP_THIRD_PARTY_CSS['jquery-ui']` name Google's 1.11.0 JS and `redmond`
  theme. `core/templatetags/script_tags.py` (`script_tags`, `js_tags`,
  `css_tags`) renders them. `core/tests/test_static.py` checks every local
  path in both dicts exists, so local paths are covered automatically.
- **V3 users of `jquery-ui`:** `bio/edit_profile` (datepicker, `bio/static/js/bio.js`),
  `gcalendar/event` (datepicker, `gcalendar/static/js/gcalendar.js`),
  `bio/member_search` and `messages/compose` (autocomplete,
  `sg101/static/js/v3/autocomplete.js`).
- **Old-design users of the same entry:** `forums/topic`, `new_topic`,
  `new_post` and `edit_post` extend `base.html`, which loads Google's jQuery
  1.11.1 (`GPP_THIRD_PARTY_JS['jquery']`). `forums.js` and `forums_mod.js`
  call no jQuery UI widget, so they appear to load it without using it. jQuery
  UI 1.13 supports jQuery 1.8 and newer. Brian approved (2026-10-15) changing
  the one entry for both designs, with a no-errors check on these four pages,
  rather than a separate legacy entry.
- **The old design's `jquery` 1.11.1 entry is untouched.** It goes in step 12.
- `sg101/static/js/vendor/` doesn't exist yet.
- `bio/tests/test_browser.py` and `news/tests/test_browser.py` have docstrings
  saying the tests need outbound access to Google's CDN. That stops being true.
- `news/tests/test_browser.py`'s `test_upload_button_opens_the_upload_modal`
  is step 1's modal test.
- The deprecated APIs that still work in 3.7.1 (`.bind`, `jQuery.trim`, event
  shorthands) are **not** changed. They matter only for jQuery 4.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.3, §7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/jquery3.md (what breaks, and the probe that proved the fixes)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 3)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Vendor into `sg101/static/js/vendor/`:
   - `jquery-3.7.1.min.js`
   - `jquery-ui-1.13.3/`: `jquery-ui.min.js`, and the `redmond` theme's CSS
     and the images it references
   Download each from its official source (code.jquery.com or the jQuery UI
   release archive). Check the jQuery file against the SRI hash jQuery
   publishes for it.
2. `sg101/static/js/vendor/README.md` lists each file with its version, source
   URL and SHA-256. It also records the hand edit to
   `sg101/static/js/v3/foundation.min.js`: what changed, why (jQuery 3 removed
   `.load(handler)`), and that the file is otherwise Foundation 6.2.0's
   release. Task 02 adds a second entry there.
3. `v3/base.html` loads jQuery with `{% static %}`. Both `jquery-ui` entries in
   `settings/base.py` name the local files.
4. Apply the Foundation patch and the `comments.js` fix.
5. Browser test: a V3 page (news submit will do) reports
   `jQuery.fn.jquery === "3.7.1"`, and no request goes to
   `ajax.googleapis.com` while it loads. Record requests with Playwright's
   `page.on('request')`.
6. Browser tests: the datepicker on `bio/edit_profile` and the autocomplete
   menu on `bio/member_search` appear directly under their inputs, judged by
   bounding boxes (the widget's top within a few pixels of the input's bottom,
   and horizontally aligned with it). The autocomplete needs a matching member
   in the test database.
7. Update the two browser-test docstrings that mention Google's CDN.
8. Load each of the four old-design forum pages in a browser after the change
   and record whether any page error appears. Report anything other than none
   to Brian before going on.
9. Comments describe the code, never this plan's step numbers.

## Dependencies
- Steps 1 and 2 (Playwright, `BrowserTestCase`, the modal test). Both deployed.

## Implementation Approach
1. Re-check the facts above against the tree. Record any difference.
2. Write the version/no-Google test and the datepicker and autocomplete tests
   first, and run them against today's tree. The version test fails. The
   position tests should pass on 2.2.4 and 1.11.0, which shows they measure
   the right thing.
3. Vendor the files, write the README, switch `v3/base.html` and the two
   settings entries, and apply the Foundation patch and the `comments.js` fix.
4. Run the browser tests. Then the mutations, restoring after each:
   - revert the Foundation patch: the modal test fails
   - point `jquery-ui` back at 1.11.0 (Google's copy is fine for this check):
     the autocomplete test fails, with the menu at (0, 0)
5. Load the four old-design forum pages and check for page errors.
6. Post a comment on a news story in the dev stack and check the number
   `comments.js` writes.
7. Run `make test-browser`, the full suite, and the deprecation gate as its own
   run.

## Acceptance Criteria

1. **V3 pages run self-hosted jQuery 3.7.1**
   - Given any V3 page
   - When it loads in a browser
   - Then `jQuery.fn.jquery` is `"3.7.1"` and no request goes to `ajax.googleapis.com`

2. **Foundation's init survives jQuery 3**
   - Given the patched `foundation.min.js`
   - When the post box's upload button is clicked
   - Then the upload modal opens, and with the patch reverted the modal test fails

3. **jQuery UI widgets sit under their inputs**
   - Given `bio/edit_profile` and `bio/member_search` on jQuery UI 1.13.3
   - When the date field is focused and a member name is typed
   - Then the datepicker and the menu each appear directly under their input, and on 1.11.0 the autocomplete test fails

4. **The vendored files are accounted for**
   - Given `sg101/static/js/vendor/README.md`
   - When each listed file's SHA-256 is recomputed
   - Then it matches, and the README records the Foundation edit

5. **Old-design forum pages are unharmed**
   - Given the four forum pages on jQuery 1.11.1 with jQuery UI 1.13.3
   - When each loads in a browser
   - Then no page error appears

6. **Comment numbering works**
   - Given a news story's comment form
   - When a comment is posted
   - Then the new comment's number appears with no console error

7. **Suite, gate and CI**
   - Given the change
   - When the suite runs, then the gate as its own run, then CI on push
   - Then all are green

## Metadata
- **Complexity**: Medium
- **Labels**: JavaScript, jQuery, jQuery UI, Foundation, static files, Playwright
- **Required Skills**: jQuery and jQuery UI, Django staticfiles and templates, Playwright for Python
