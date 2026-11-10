# Task: Make V3's `.quiet` grey everywhere

## Description
Give V3's `.quiet` class Blueprint's grey (`color: #666`) as well as its
smaller size, so it means the same on both designs. Screenshot every V3 page
that uses it before and after, check the contrast on both post card colours,
and put to Brian whether the post card's own grey classes fold back into
`quiet`.

## Background
Brian decided on 2026-11-09 that V3's `.quiet` goes grey everywhere, as
Blueprint's does. Today it is only

```scss
.quiet {
   font-size: smaller;
}
```

in `sg101/scss/_sg101.scss`. Step 7 task 01 made the post card's quiet text
grey with classes of its own, because changing `.quiet` reaches other pages:
`.forum-post-author-details`, `.forum-post-edited` and the signature rule
(STATUS, step 7 task 01).

**Pages using `.quiet` on V3**, found by grepping the templates on this branch:

- `forums/topic.html`
- `ygroup/v3/post.html` and `ygroup/v3/thread.html`
- `potd/view.html`
- `store/base.html`

Grep again before starting. Steps 6 and 7 changed templates since this list was
made, and an included fragment may use the class without the page itself
having it. Old-design pages (`base.html`) use Blueprint's rule and are out of
scope.

**The v3 stylesheet is a committed build artifact.** Change the Sass, run
`npm run build:css` in `sg101/`, and commit both.

**Screenshots stay out of the repository** (Brian, 2026-11-03). They show
members' names and posts. Save them in the session scratchpad and hand Brian
their paths. `STATUS.md` records his decision in words.

**The fold-back is Brian's decision; don't choose.** Once `.quiet` is grey,
the card's three grey classes might become `quiet` plus whatever is left of
them (size, spacing, the rule). Measure the computed colour and size of each
before and after and present the options with a recommendation.

**Contrast.** The post cards alternate two background colours
(`:nth-child(even)`, step 6 task 02). Compute the WCAG contrast ratio of
`#666` on each and on the page background. If one falls under 4.5:1 for
normal text, say so with the numbers. Don't pick a different grey without
Brian.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 8, the `.quiet` bullet)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 7 task 01: the card's grey classes, and task 03's open question)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. `.quiet` in `_sg101.scss` sets `color: #666` and keeps `font-size: smaller`.
2. `main.min.css` is rebuilt from the Sass and committed with it.
3. Before and after screenshots of every V3 page that uses `.quiet`, at 360
   and 1280 px, in the session scratchpad.
4. Contrast ratios of `#666` on both card colours and on the page background,
   recorded in `STATUS.md`.
5. Brian's decision on the fold-back recorded in `STATUS.md` and carried out,
   with the card's existing browser tests still passing.

## Dependencies
- Step 7: the post card's grey classes.
- The dev stack running, with the CSS build tooling (`npm` in `sg101/`).

## Implementation Approach
1. Grep the templates for `quiet` and list the V3 pages it reaches.
2. Write a browser test that `.quiet` text on a V3 page computes to
   `rgb(102, 102, 102)`, and watch it fail.
3. Shoot the "before" set, change the Sass, rebuild, and shoot the "after" set.
4. Compute the contrast ratios. Present screenshots, ratios and the fold-back
   options to Brian. Stop for his answer.
5. Make what he chooses, then run the full suite and the deprecation gate, one
   at a time. Leave the work unstaged for review.

## Acceptance Criteria

1. **`.quiet` is grey on V3**
   - Given a V3 page with `.quiet` text
   - When a browser renders it
   - Then the text computes to `rgb(102, 102, 102)` and is smaller than its parent's text

2. **The test is seen to fail**
   - Given the new browser test
   - When run against the Sass without the colour
   - Then it fails, and passes once the colour is back

3. **The built CSS matches the Sass**
   - Given the Sass change
   - When `npm run build:css` runs again
   - Then `main.min.css` is unchanged from what is committed

4. **Brian's decision is recorded and made**
   - Given the screenshots, contrast ratios and fold-back options
   - When Brian decides
   - Then `STATUS.md` records it and the card's classes follow it

5. **Nothing from the review reaches the repository**
   - Given the end of the task
   - When `git status` is checked
   - Then no screenshot is in the working tree

## Metadata
- **Complexity**: Low
- **Labels**: V3 design, Sass, accessibility, screenshots
- **Required Skills**: Sass, Foundation 6, Playwright for Python, WCAG contrast
