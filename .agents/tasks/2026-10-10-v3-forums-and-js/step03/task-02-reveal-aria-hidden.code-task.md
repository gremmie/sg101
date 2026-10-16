# Task: Stop Reveal hiding the open modal from assistive technology

## Description
When any Reveal modal opens, Foundation sets `aria-hidden="true"` on `<body>`
and on the overlay that holds the modal it then focuses. Chrome refuses both,
logging an error and a warning on every post box modal. Fix it so that, while
a modal is open, neither `<body>` nor any ancestor of the focused modal has
`aria-hidden="true"`, and `aria-hidden` is restored as it was on close.
**How to fix it is not decided.** Measure first, bring Brian the options, and
implement the one he chooses.

## Background
Found in step 2 task 03's manual walk (STATUS, 2026-10-14). The post box
modules set neither `aria-hidden` nor focus. Both settings are in the vendored
`sg101/static/js/v3/foundation.min.js`, which is Foundation **6.2.0**'s
`dist/foundation.min.js` plus task 01's patch, not 6.3.1 (only the Sass is
6.3.1; `STATUS.md`, step 3 task 01):

- `open` calls `t("body")…attr("aria-hidden", …)`, which Chrome refuses as an
  **error**.
- `_makeOverlay` creates `.reveal-overlay` with `aria-hidden="true"`, and the
  modal is moved inside it. Chrome refuses that as a **warning**, because the
  element receiving focus is inside it.

Brian put the fix into step 3 on 2026-10-14 (`59400010`), since step 3 already
patches `foundation.min.js`. There is no Foundation upgrade (Q12, Q13): even
if 6.9.0 fixed it, the fix is a patch to the vendored 6.2.0. Compare
Reveal in 6.2.0 with 6.9.0, not 6.3.1 with 6.9.0.

The plan names three measurements to make before choosing:
- whether Foundation 6.9.0 changed this upstream. Its fix shows the intent.
- what Firefox and Safari do with `aria-hidden` on `<body>`, where Chrome
  refuses it
- whether the overlay needs to be hidden from assistive technology at all,
  or `inert` on the page behind it does that job

A second patch to the vendored file, recorded in the vendor README next to
task 01's, is the likely shape, but it isn't decided.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.3, §7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 3, "Reveal's `aria-hidden`")
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 2 task 03's manual walk)
- .agents/planning/2026-10-10-v3-forums-and-js/research/foundation-upgrade.md

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Make the three measurements and record each with its source: Foundation's
   6.9.0 code or changelog for Reveal, the browser behaviour (spec text, MDN, or
   a probe in a real browser), and what `inert` covers.
2. **Stop and present the options to Brian** with a recommendation, before
   implementing. Don't pick one yourself.
3. Implement the chosen fix. If it patches `foundation.min.js`, record it in
   `sg101/static/js/vendor/README.md` next to task 01's patch: what changed and
   why.
4. Browser test: with a post box modal open, `<body>` and every ancestor of
   the modal lack `aria-hidden="true"`, and Chrome logs no console error or
   warning about `aria-hidden`. After the modal closes, `<body>` has the
   `aria-hidden` state it had before.
5. The fix applies to every Reveal modal, not only the post box's, because
   Reveal is shared.
6. Comments describe the code, never this plan's step numbers.

## Dependencies
- Task 01: jQuery 3 and the patched `foundation.min.js` already in place, and
  the vendor README to add to.

## Implementation Approach
1. Reproduce: open the upload modal on news submit in Playwright and capture
   Chrome's console messages. Both should appear.
2. Make the three measurements.
3. Write up the options and a recommendation for Brian. Wait for his choice.
4. Write the browser test, and see it fail on today's code.
5. Implement the fix.
6. Mutations, restoring after each: put back Reveal's `aria-hidden` on
   `<body>`, and the test fails; put back the overlay's `aria-hidden`, and the
   test fails.
7. Run `make test-browser`, the full suite, and the deprecation gate as its own
   run.

## Acceptance Criteria

1. **The choice was Brian's**
   - Given the three measurements, recorded
   - When the options are presented with a recommendation
   - Then Brian chooses, and STATUS records the choice and its reason

2. **Nothing hides the open modal**
   - Given a post box modal open
   - When `<body>` and the modal's ancestors are read
   - Then none has `aria-hidden="true"`, and Chrome logs no `aria-hidden` error or warning

3. **Closing restores the page**
   - Given a modal opened and then closed
   - When `<body>` is read
   - Then its `aria-hidden` state is what it was before the modal opened

4. **The test can fail**
   - Given the browser test
   - When each of Reveal's two `aria-hidden` settings is put back in turn
   - Then the test fails each time

5. **Suite, gate and CI**
   - Given the change
   - When the suite runs, then the gate as its own run, then CI on push
   - Then all are green

## Metadata
- **Complexity**: Medium
- **Labels**: JavaScript, Foundation, accessibility, ARIA, Playwright
- **Required Skills**: ARIA and `inert`, reading minified JavaScript, Playwright for Python
