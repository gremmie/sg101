# Task: The upload modal's file list: choose up to 10, see thumbnails, remove any

## Description
Turn the upload modal's single file input into a list a member builds before
uploading: choose images (more than once if they like), see each as a
thumbnail with its name, remove any, capped at 10. This task builds the list
only. Uploading the list is task 03, so until then Upload keeps sending one
file through today's path, or is wired to the first file only, whichever
keeps the tree working.

## Background
Today `uploads.js` hands the modal to `image_form.js`, a single-form flow
shared with the hot-link modal. A batch does not fit that flow, so the upload
modal gets its own code in `uploads.js` and **hot-link stays on
`image_form.js`, unchanged.**

A browser's file input cannot remove one file from its selection, and a
second choice replaces the first. So the list is ours: each `change` event
adds its files to a JavaScript array and clears the input, and the array is
what gets shown and later uploaded.

Thumbnails are drawn by the browser from the file on disk:
`URL.createObjectURL(file)` gives an `<img>` a `blob:` URL, and CSS shrinks it.
Nothing is read into JavaScript or uploaded to preview it. Each URL must be
released with `URL.revokeObjectURL` when its file leaves the list or the
modal resets, or the browser keeps the file referenced until the page
closes. Browsers apply EXIF orientation by default, so portraits come out
upright.

`accept="image/*"` only filters the dialog; a member can still pick a text
file. A non-image, or a HEIC file in a browser that can't decode it (Chrome
and Firefox on desktop), fails to load as an `<img>`. It must show a plain
placeholder, not a broken-image icon, and stay in the list. The server
decides, per file, in task 03.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (R9, the `post_box/uploads.js (#16)` section)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2 task 02 for the module layout; step 4 for the modal Sass and test patterns; task 01's HEIC finding)
- `sg101/static/js/v3/post_box/` (`uploads.js`, `image_form.js`, `status.js`, `post_box.js`)
- `sg101/templates/core/v3/post_box_modals.html` (`#upload-modal`)
- `news/tests/test_browser.py` (`SubmitUploadTestCase`) and `core/tests/browser.py`

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. The modal's input gains `accept="image/*" multiple`, and a list element
   below it. Update the modal's explanatory text for several images, fixing
   "placed your post" while there.
2. Each choice appends to the list. The input is cleared after each change,
   so the same file can be chosen again after being removed.
3. **Cap of 10.** Choosing past it keeps the first ones up to 10 and shows a
   message saying how many were left out.
4. Each list entry shows a thumbnail (object URL, fixed size, cropped with
   `object-fit: cover`), the file name, and a remove button with an
   accessible label naming the file.
5. A thumbnail that fails to load is replaced by a placeholder.
6. Object URLs are revoked on remove and on modal reset (the function
   `initUploads` returns, called as the modal opens).
7. Styling goes in the v3 Sass under `sg101/scss/`; rebuild with
   `npm run build:css` in `sg101/` and commit `main.min.css` with it.
8. The list works at about 375 px wide.
9. Hot-link behaves exactly as before; its existing tests pass unchanged.
10. Code comments describe the code, never the plan's step numbers.

## Dependencies
- Task 01 (its HEIC finding may change the placeholder's wording).
- Step 2's post box modules; Playwright browser tests (`make test-browser`).

## Implementation Approach
1. Write the browser tests first against `#upload-modal` on news submit,
   using Playwright's `set_input_files` with generated image bytes:
   choosing 12 keeps 10 and says so; choosing twice adds rather than
   replaces; removing a file removes its entry; a text file shows the
   placeholder.
2. Change the template, then `uploads.js`: an array of entries, each holding
   its `File`, its object URL and its list element.
3. Add revocation, checked in a test by stubbing `URL.revokeObjectURL` and
   counting calls.
4. Sass, rebuild, check at phone width.
5. Mutation-verify each browser test (drop the cap, skip the clear, skip the
   revoke) and record each in STATUS.

## Acceptance Criteria

1. **Choices add up**
   - Given the upload modal with 2 images in its list
   - When 3 more are chosen
   - Then the list holds 5

2. **The cap**
   - Given an empty list
   - When 12 images are chosen
   - Then the list holds the first 10 and a message says 2 were left out

3. **Remove**
   - Given a list of 3
   - When the second entry's remove button is pressed
   - Then the list holds the other 2 and that file's object URL is revoked

4. **A file that can't be drawn**
   - Given a text file chosen in the modal
   - When its thumbnail fails to load
   - Then a placeholder shows in its place, with the file name, and it stays in the list

5. **Reset**
   - Given a list of files
   - When the modal is closed and opened again
   - Then the list is empty and every object URL it held was revoked

6. **Hot-link untouched**
   - Given the hot-link modal
   - When its existing tests run
   - Then they pass unchanged

7. **Tests seen to fail; suite and gate**
   - Given each new browser test
   - When what it guards is broken
   - Then it fails; restored, `make test-browser`, the full suite and the deprecation gate (separate run) pass

## Metadata
- **Complexity**: Medium
- **Labels**: Post box, uploads, JavaScript, ES modules, Sass, browser tests, #16
- **Required Skills**: DOM APIs (File, object URLs), Playwright, Sass, accessibility
