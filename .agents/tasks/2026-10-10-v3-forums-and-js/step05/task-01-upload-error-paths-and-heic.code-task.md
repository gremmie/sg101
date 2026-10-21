# Task: Close the upload view's error-path tests, and measure HEIC

## Description
Give `upload_ajax_v3` a view test for the one error path still untested, a
member over the daily upload limit, and find out what the server does with a
HEIC photo. The result decides whether the post box needs anything for HEIC.
That decision is Brian's.

## Background
Step 5's server half (R10) was pulled forward into step 2: `upload_ajax_v3`
(`user_photos/views.py`) already puts every message in `error_msg`, as plain
text, and the exception path returns a generic sentence and logs the
traceback. `user_photos/tests/test_upload_views.py` (`UploadAjaxV3Tests`)
covers not logged in, not AJAX, uploads disabled, an exception in save, and
a file that is not an image. **The over-quota path has no view test.**
`rate_limit_user` (`user_photos/forms.py`) raises a `ValidationError` from
`UploadForm.clean()` after `USER_PHOTOS_RATE_LIMIT` (50 a day) is used up.
The message reaches `error_msg` through the form-errors branch, but no test
proves that. `test_forms.py`'s `test_rate_limit` covers the hot-link form,
not this view.

HEIC: `UploadForm.image_file` is a Django `ImageField`, validated by Pillow
12.3.0, and `pillow-heif` is not installed. So a HEIC file is **probably**
rejected as "Upload a valid image." That is unmeasured. iOS Safari usually
converts HEIC to JPEG when a photo is chosen from the library, so phones may
never send one, but a Mac's Finder will.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.2, R9, R10)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2 task 02, where R10 landed)
- .agents/planning/2026-10-10-v3-forums-and-js/research/upload-timing.md
- AGENTS.md (logging is disabled in test settings; the enable-and-restore dance)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a view test to `UploadAjaxV3Tests`: a member over the limit posts a
   valid image and gets a 400 whose `error_msg` is the quota message, as
   plain text. Use a real `UploadForm` and Redis-backed limit if the test
   settings allow it (e.g. `override_settings(USER_PHOTOS_RATE_LIMIT=(0, 60))`),
   rather than mocking `rate_limit_user` away: mocking it would not prove
   the message's path to `error_msg`.
2. Mutation-verify it: break the path (for example, drop non-field errors
   from the `errors` list in the view) and see the test fail, then restore.
3. Check that the test's Redis key does not leak into other tests.
4. Measure HEIC with a real HEIC file (from Brian's phone or a Mac export;
   never committed if it is a personal photo): post it to `upload_ajax_v3`
   on the dev stack and record the status and `error_msg`. Also record
   what the browser reports as the file's `type` in Chrome and Safari on
   macOS.
5. Record the findings in `STATUS.md` and present the options to Brian:
   leave as is, reject with a clearer message naming HEIC, or accept it
   (`pillow-heif`, a new dependency). Do not choose for him.

## Dependencies
- The dev stack (`docker compose up -d`).
- A HEIC sample file.

## Implementation Approach
1. Read `UploadAjaxV3Tests` and copy its setup and `AJAX` headers.
2. Write the over-quota test and run it. Mutate, see it fail, restore.
3. Run the HEIC probe against the dev stack, with
   `USER_PHOTOS_LOCAL_UPLOAD=True` so nothing reaches S3.
4. Write the STATUS section and stop for Brian's choice.

## Acceptance Criteria

1. **The quota message reaches the member**
   - Given a member who has used up the daily upload limit
   - When they post a valid image to `upload_ajax_v3`
   - Then the response is 400 and `error_msg` is the quota message, as plain text

2. **The test is seen to fail**
   - Given the view with non-field errors dropped from `error_msg`
   - When the over-quota test runs
   - Then it fails, and passes again once the view is restored

3. **HEIC is measured, not assumed**
   - Given a real HEIC file
   - When it is posted to `upload_ajax_v3` on the dev stack
   - Then its status, `error_msg` and the browsers' reported `type` are recorded in STATUS

4. **The HEIC decision is Brian's**
   - Given the measurement
   - When the task closes
   - Then STATUS lists the options and Brian's choice; any change it needs is scheduled, not made silently

5. **Suite and gate**
   - Given the branch
   - When the full suite and the deprecation gate run as separate runs
   - Then both pass

## Metadata
- **Complexity**: Low
- **Labels**: Uploads, tests, error messages, HEIC, #16
- **Required Skills**: Django test client, Redis, Pillow, mutation testing
