# Task: Screenshot the three ported pages for Brian's review, and settle the phone toolbar

## Description
Take screenshots of the forums index, a forum's topic list and a topic page,
at phone and desktop widths, as an anonymous visitor, a member and a
moderator. Include the post box toolbar at 360 px with seven buttons. Brian
reviews them and decides the look and whether the toolbar fits. His decisions
are recorded before step 7 starts, and any change he asks for is made in this
task.

## Background
Q6 settled that the `v3-dev` pages are ported rather than redesigned, and
that Brian sees them before the remaining forum pages are built on the same
look (R12). This is that review.

**The toolbar question (R11).** The post box toolbar has 12 buttons. At phone
width today it shows 6: link, smiley, hot-link, upload, preview and help (the
rest are `hide-for-small-only`). Step 8 adds a video button for the forums,
making 7. Whether 7 fit on one line at 360 px was estimated from defaults,
never measured (idea-honing Q8). Measure it now. **The video button doesn't
exist yet, so add a temporary stand-in for the screenshot and don't commit
it.**

**Screenshots stay out of the repository (Brian, 2026-11-03).** They show
dev data, which is members' real names, avatars and posts, and `.agents/` is
published with the repository. Save them in the session scratchpad and hand
Brian their paths. `STATUS.md` records his decisions and the toolbar
measurement in words.

**The forum tables overflow at tablet widths, an open decision for this
review (Brian, 2026-11-04).** Task 01 fixed phone widths, but from 640 to 1024
px the forum's topic list scrolls sideways, by up to 309 px on `gear`. The
measurements, and one remedy measured but not applied, are in `STATUS.md` under
step 6 task 01. Shoot 640 and 1024 as well, so Brian decides with those in
front of him.

The dev debug toolbar overlays the phone menu. It is hidden unless `.env` has
`DEBUG_TOOLBAR=True`, so check `.env` before shooting. Probe sessions log in
through `settings.AUTHENTICATION_BACKENDS[0]`, not `ModelBackend`. The dev
stack serves `MEDIA_ROOT` (`sg101/urls.py`) and the test server doesn't, but
whether avatars, badges and smileys appear depends on what the dev media holds.
Check one page by eye before shooting all 18, and note any missing images
for Brian so he doesn't read them as a fault in the design.

This task deploys nothing. The branch continues through steps 7 and 8.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§2.4 R12, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/idea-honing.md (Q6 on the review, Q8 on the toolbar count)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (earlier walk probes: hiding the debug toolbar, logging a probe in)
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 6 demo and gate)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. With a headless Chromium probe against the dev stack, screenshot each of
   the three pages at 360 px and at a desktop width (1280 px), as anonymous,
   member and moderator: 18 full-page screenshots.
2. Choose subjects by something the probe doesn't change: a forum with more
   than one page of topics, and a topic with more than one page of posts,
   picked by id. The member should be one who can reply. The moderator should
   moderate that forum.
3. Screenshot the reply box's toolbar at 360 px with a temporary seventh
   phone button. Measure whether it wraps (the toolbar's height, and each
   item's top offset), not only how it looks.
4. Save everything under the session scratchpad. Nothing from it goes into the
   repository.
5. Write Brian's decisions into `STATUS.md`: the look, the toolbar fit and,
   if it doesn't fit, what he chooses instead.
6. Make any change he asks for, with tests where the change has behaviour.
   Re-shoot what it affects.
7. Tick step 6 in `implementation/plan.md` and record it in `STATUS.md`. Run
   the full suite and then the deprecation gate on the branch.

## Dependencies
- Tasks 01 and 02.
- The dev stack running, with a recent production snapshot loaded.

## Implementation Approach
1. Check `.env` for `DEBUG_TOOLBAR`, pick the subjects, and write the probe
   in the scratchpad.
2. Shoot the 18 page screenshots and the toolbar, and record the toolbar's
   measurements.
3. Remove the stand-in button and confirm `git status` shows no change from
   it.
4. Hand Brian the screenshot paths with a short note per page: anything that
   looks wrong, and anything `v3-dev` left unfinished that step 7 will add.
5. Stop for his decisions. Record them, and make and verify the changes.
6. Run the full suite, then the deprecation gate. Leave the work unstaged for
   review.

## Acceptance Criteria

1. **Every page, width and role is covered**
   - Given the three ported pages
   - When the probe runs
   - Then there are 18 page screenshots in the scratchpad, each named by page, width and role

2. **The toolbar fit is measured**
   - Given the reply box at 360 px with seven phone buttons
   - When the toolbar is measured
   - Then `STATUS.md` records whether it stays on one line, with the numbers

3. **No screenshot or stand-in reaches the repository**
   - Given the end of the task
   - When `git status` and the diff are checked
   - Then no image, no member data, and no stand-in button are in the working tree

4. **Brian's decisions are recorded before step 7**
   - Given Brian's review
   - When he decides on the look and the toolbar
   - Then `STATUS.md` records each decision, and every change he asked for is made and re-shot

5. **The step closes green**
   - Given the branch at the end of step 6
   - When the full suite and then the deprecation gate run
   - Then both pass

## Metadata
- **Complexity**: Low
- **Labels**: forums, V3 design, review, Playwright, screenshots
- **Required Skills**: Playwright for Python, responsive layout measurement
