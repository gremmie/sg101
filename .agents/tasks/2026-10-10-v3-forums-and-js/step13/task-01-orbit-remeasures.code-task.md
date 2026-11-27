# Task: The phone banner re-measures when the layout narrows

## Description
Make the phone-width banner (the Orbit in `v3/base.html`) show its slides
when a page that loaded at medium width or wider narrows to small. Prefer
porting an upstream Foundation fix into the vendored file; otherwise
re-measure Orbit from `sg101.js` on Foundation's breakpoint change.

## Background
**The fault, measured** (`STATUS.md`, step 3 task 01 and step 6 task 01).
Foundation 6.2.0's Orbit measures its slides once, at initialisation. The
banner is `hide-for-medium`, so a page loaded at medium or wider measures 0
and leaves `.orbit-container` at `height: 0` and every slide at
`max-height: 0`, still rotating. Loaded at a phone width it shows (94.7 px
at 375, 102 px at 402) and rotates. Loaded at 1280 and narrowed to 375 or
402: 0. **The landscape-to-portrait case is inferred, not seen**: a phone
in landscape is usually 640 px or wider, which is medium.

**What the vendored Orbit binds** (measured 2026-11-26 in
`sg101/static/js/v3/foundation.min.js`): swipe, click, hover and the
previous/next buttons, under `.zf.orbit`. No `resize`, no `resizeme`, no
`mediaquery` handler. `_prepareForOrbit` (which calls `_setWrapperHeight`)
runs from `_init` only.

**The markup** (`sg101/templates/v3/base.html`, "Small screen logo orbit"):
`<div class="orbit hide-for-medium" data-orbit>` with two slides, the logo
(`images/v3-logo.png`, alt "SG101 logo") and the banner
(`images/sg101-celebrating.jpg`), and two bullets. Each slide's row is also
`hide-for-medium`.

**Hand edits to the vendored Foundation** are recorded in
`sg101/static/js/vendor/README.md`, "Hand edits to vendored files
elsewhere", each with what it changes and why. Six so far. A port goes
there too.

**Measure, don't assume, the hidden slide.** Orbit sizes the container to
its tallest slide, but a slide hidden at the moment of measuring measures 0.
The two slides are about 102 px each today, so a short banner shouldn't
show. Check it at the narrowed width.

**Browser tests for what every V3 page shares** live in
`core/tests/test_browser.py` (`PhoneMenuTestCase`, `HeaderAlignmentTestCase`).
The live test server serves static files, so the images load. Two lessons
from earlier steps: measure boxes in one `evaluate` call after the layout
settles (a resize reflows, and two separate `bounding_box()` calls can
straddle it; step 8 task 03), and Playwright reads text from hidden
elements, so assert visibility or size, not text.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 13)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 3 task 01: the Orbit measurements; step 8 task 03: measuring boxes after a resize)
- `sg101/static/js/vendor/README.md` (the hand edits)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Loaded at 1280 and narrowed to 402, the banner is taller than 0 and the
   logo is visible, without a reload.
2. Loaded at 402, the banner is as today: about 102 px, it rotates, and the
   next button works.
3. Narrowed, widened and narrowed again, it still shows.
4. If the fix is a port of upstream Foundation code, it is recorded in the
   vendor README beside the other hand edits. If it lives in `sg101.js`, the
   code says it relies on Orbit internals, acceptable on a pinned, vendored
   6.2.0 that won't be upgraded.
5. No page error at any width, and the existing browser tests still pass.

## Dependencies
- Step 12 shipped (`main` at `37e311e8` or later).
- A branch `orbit-remeasure`, cut from `main` after these task files are
  committed there.

## Implementation Approach
1. **Write the browser test first** in `core/tests/test_browser.py`: load a
   V3 page at 1280, resize to 402, and assert the banner's height is above 0
   and the logo has a box. Run it and watch it fail.
2. **Look for an upstream fix:** read Orbit's source (`js/foundation.orbit.js`)
   in Foundation 6.3, 6.4 and 6.5 for a resize or breakpoint handler. Record
   what each version has, with the version and file, in `STATUS.md`.
3. **Choose.** If an upstream handler exists and fits 6.2.0's Orbit, port the
   smallest piece of it into the vendored file. Otherwise, in `sg101.js`, on
   `changed.zf.mediaquery` when the new size is `small`: clear each Orbit's
   container height and its slides' `max-height` first (the measurement
   reads current heights, and a slide held at `max-height: 0` measures 0),
   then call its `_prepareForOrbit()`. Show Brian the two options if both
   are viable.
4. Add the other two tests (loaded at 402, unchanged; narrow, widen,
   narrow), and check the hidden slide.
5. Run `core`'s tests against the running stack, then the full suite once
   under the gate. Mutation-check (remove the fix: the first test fails;
   skip the clearing step: check whether it still fails), restore
   byte-identical, and leave the work unstaged for review.

## Acceptance Criteria

1. **The banner shows after narrowing**
   - Given a V3 page loaded at 1280 px
   - When the viewport narrows to 402 px
   - Then the banner is taller than 0 and the logo is visible, without a reload

2. **Loading at phone width is unchanged**
   - Given a V3 page loaded at 402 px
   - When it is measured and the next button is pressed
   - Then the banner is about 102 px high and moves to the next slide

3. **Repeated resizing keeps it**
   - Given a page narrowed, widened and narrowed again
   - When the banner is measured
   - Then it is taller than 0 and shows a slide

4. **The test is seen to fail**
   - Given the first test
   - When it runs without the fix
   - Then it fails, and passes with the fix restored

## Metadata
- **Complexity**: Low
- **Labels**: Foundation, Orbit, responsive, JavaScript, Playwright
- **Required Skills**: Foundation 6 plugins, jQuery, Playwright for Python
