# Task: Upload the list one file at a time, inserting each image code as it lands

## Description
Make Upload send the modal's list to `upload_ajax_v3` one request at a time,
in order. Each success inserts its image code at the cursor and marks the
entry ✓; each failure marks it ✗ with the server's reason and the queue
carries on. A summary line ends the batch.

## Background
Task 02 built the list. The design sends files **sequentially**, not in
parallel: each upload resizes, thumbnails and makes two S3 PUTs
(research/upload-timing.md), the server's limit is 50 a day, and
order matters because codes are inserted in the order chosen. A request
that fails says why in `error_msg` (R10, in since step 2), and
`core/http.js`'s `postForm` already turns that into the thrown error's
message.

Insertion uses `insertAtCursor(textarea, '![image](url)', { ownLine: true })`
from `editor.js`. Each insertion moves the cursor past the inserted code,
so successive codes land in order without extra bookkeeping. Check that
this holds if the member clicks elsewhere in the post mid-batch, and record
what happens.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (R9, the `post_box/uploads.js (#16)` sequence diagram)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/upload-timing.md
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2 task 02: `http.js` and `error_msg`)
- `sg101/static/js/v3/core/http.js`, `sg101/static/js/v3/post_box/editor.js`
- AGENTS.md (slow uploads and the Cloudflare buffering rule; 30 s gunicorn timeout)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Upload with an empty list shows "Please choose a file to upload." as now.
2. Upload sends each queued entry in list order, one `POST` at a time
   (`FormData` with `image_file` and the CSRF token, via `postForm`).
3. On success: insert the code at the cursor, mark the entry ✓.
   On failure: mark it ✗ and show the server's reason beside it; continue.
4. While the batch runs: Upload is disabled and shows a busy label with
   progress (for example "Uploading 3 of 8…"); remove is disabled on entries
   already sent or in flight; choosing more files is disabled.
5. When the batch ends: a summary line, for example "8 of 10 added", using
   `status.js`'s success style when all succeeded and its failure style
   otherwise. Uploaded entries leave the list; failed ones stay, so the
   member can remove them or retry.
6. A network failure (no response) marks that entry ✗ with a generic message
   and the queue continues.
7. Object URLs of entries that leave the list are revoked.
8. Code comments describe the code, never the plan's step numbers.

## Dependencies
- Task 02 (the list).
- `upload_ajax_v3` and `UploadForm`; uploads stored locally in tests
  (`SubmitUploadTestCase` uses a temporary `MEDIA_ROOT`, never S3).

## Implementation Approach
1. Write the browser tests first on news submit:
   - 3 files, the middle one not an image: 2 image codes in the textarea in
     order, the middle entry ✗ with "Upload a valid image…", summary "2 of 3
     added".
   - A file removed before Upload is never sent (count requests with
     Playwright's request listener).
   - Upload is disabled while a batch runs (hold a response with
     `page.route` and assert, then release).
2. Implement the queue as an `async` loop over a snapshot of the list.
3. Mutation-verify each test (parallel sends with `Promise.all`, stop on
   first failure, skip the remove check) and record each in STATUS.
4. Try a slow upload by hand on the dev stack (throttled in devtools) to
   see the progress label and the disabled controls.

## Acceptance Criteria

1. **Codes land in order**
   - Given 3 images in the list and the cursor in the post
   - When Upload is pressed
   - Then 3 image codes are inserted, each on its own line, in list order

2. **A failure says why and the rest go on**
   - Given 3 files, the middle one not an image
   - When Upload is pressed
   - Then the first and third codes are inserted, the middle entry shows ✗ with the server's reason, and the summary reads "2 of 3 added"

3. **One at a time**
   - Given 3 files and a held first response
   - When Upload is pressed
   - Then only 1 request is in flight until it completes, and Upload is disabled throughout the batch

4. **Removed means not sent**
   - Given 3 files with one removed before Upload
   - When Upload is pressed
   - Then exactly 2 requests are made

5. **Retry what failed**
   - Given a finished batch with a failed entry still listed
   - When the member removes it, adds another image and presses Upload
   - Then only the new image is sent

6. **Tests seen to fail; suite and gate**
   - Given each new browser test
   - When what it guards is broken
   - Then it fails; restored, `make test-browser`, the full suite and the deprecation gate (separate run) pass

## Metadata
- **Complexity**: Medium
- **Labels**: Post box, uploads, JavaScript, async, browser tests, #16
- **Required Skills**: async JavaScript, fetch/FormData, Playwright request interception
