# Task: Walk multiple uploads, measure thumbnails on a phone, then merge and deploy step 5

## Description
Run step 5's demo, walk the upload modal where the tests don't reach, and
have Brian try it on a real phone, which decides whether thumbnails need a
canvas downscale. Close step 5 in the planning documents, merge
`multi-upload` to `main`, and hand over the deploy. Then close GitHub issue
#16.

## Background
Tasks 02 and 03 build and test the list and the queue in headless
Chromium, with small generated images. What they don't cover: real
12-megapixel phone photos, a phone's file picker (camera and photo library),
Safari, and slow real uploads through Cloudflare.

**Thumbnails decode the full photo.** Ten phone photos are ten full-size
decodes. Desktops manage this easily; an older phone might be slow or run
short of memory. The fix, if needed, is to draw each photo once onto a
small `<canvas>` and show that instead of the object URL. **Add it only if
the phone measurement calls for it.** Record the measurement either way.

Branch practice (Q11): planning and STATUS changes for this step are
committed on `multi-upload`, which merges to `main` when deployed. Deploys
are `git pull` then `make prod-up` on leopard, which Brian runs. Step 5 has
no migrations unless task 01's HEIC decision added a dependency (then
`make prod-build` is needed too; say so in the hand-over). If any Sass
changed, the built `main.min.css` is committed with it.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (R9, §7.3, §8)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 5 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (tasks 01–03; step 4 task 03's walk probe, which hides the dev debug toolbar)
- AGENTS.md (the Cloudflare request-buffering rule for slow uploads)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **The demo:** on news submit, choose 4 photos and a text file, remove one
   photo, Upload: 3 image codes land at the cursor and the text file shows
   "Upload a valid image…".
2. Walk at about 375 px and desktop width on every page that includes the
   post box modals (news submit, profile edit's boxes, message compose, a
   comment form, a download's page): the list fits and scrolls, controls are
   reachable, the console is clean.
3. With `USER_PHOTOS_LOCAL_UPLOAD=True`, so dev uploads don't reach S3. If
   anything writes to the dev database, snapshot first
   (`tools/pg_snapshot.sh dump <label>`).
4. **Brian, by hand, on a phone** (against the dev stack or, after deploy,
   live): choose 10 photos from the library. Record how long the thumbnails
   take to appear, whether the page stays responsive, and whether any fail.
   Also try Safari on macOS with a HEIC file from Finder.
5. If the phone result is poor, propose the canvas downscale with the
   numbers; Brian decides whether it joins this step or becomes its own.
6. Tick step 5 in `implementation/plan.md` and close it in `STATUS.md`.
7. After Brian approves: merge `multi-upload` to `main`, push, check CI on
   both. Brian deploys. Record the deploy once he confirms the live site.
8. Close #16 with a comment naming the commit, after asking Brian.

## Dependencies
- Tasks 01, 02 and 03.

## Implementation Approach
1. Run the demo, then the walk at both widths with a headless probe.
2. Hand Brian the phone check; record what he reports.
3. Run `make test-browser`, the full suite, and the deprecation gate as its
   own run, one last time on the branch.
4. Write the step's close in STATUS and tick the plan.
5. Stop for Brian's review. Merge and push when he approves. Watch CI.
6. After Brian deploys, spot-check live: upload two images in one batch.

## Acceptance Criteria

1. **The demo holds**
   - Given news submit on the dev stack
   - When 4 photos and a text file are chosen, one photo removed, and Upload pressed
   - Then 3 image codes land at the cursor and the text file's entry shows "Upload a valid image…"

2. **It fits and works at both widths**
   - Given each post box page walked
   - When the upload modal is used at phone and desktop widths
   - Then the list fits, every control is reachable, and the console shows no errors

3. **The phone is measured**
   - Given 10 library photos on Brian's phone
   - When they are chosen in the modal
   - Then STATUS records how the thumbnails behaved, and whether a canvas downscale is needed and what was decided

4. **The step is closed in the record**
   - Given `implementation/plan.md` and `STATUS.md`
   - When read after the merge
   - Then step 5 is ticked and its close records the walk, the phone check and the deploy

5. **Merged, deployed, green, closed**
   - Given Brian's approval
   - When `multi-upload` is merged to `main` and pushed
   - Then CI is green, the live site passes the spot check, and #16 is closed

## Metadata
- **Complexity**: Low
- **Labels**: Manual testing, uploads, mobile, release, documentation, #16
- **Required Skills**: Browser devtools, mobile testing, git, the project's deploy path, gh
