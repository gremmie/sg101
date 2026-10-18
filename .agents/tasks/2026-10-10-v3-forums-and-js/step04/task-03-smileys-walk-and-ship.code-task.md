# Task: Walk the smiley picker, then merge and deploy step 4

## Description
Check the smiley picker by hand where the tests don't reach, run the step's
demo, close step 4 in the planning documents, merge `smileys` to `main`, and
hand over the deploy. Then close GitHub issue #9.

## Background
Tasks 01 and 02 add the picker and insertion, each with tests. What they
don't cover: how the six-button toolbar and an 85-smiley modal look at phone
width, lazy loading in a browser other than Chromium (task 01 measured only
Chromium), and the picker on every page that includes the post box modals.

Branch practice (Q11): planning and STATUS changes for this step are
committed on `smileys`, which merges to `main` when deployed. Deploys are
`git pull` then `make prod-up` on leopard, which Brian runs. Step 4 has no
migrations. If any Sass changed, `npm run build:css` in `sg101/` and commit
the built `main.min.css` with it: the application image has no Node.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§7.3, §8)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 4 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (tasks 01 and 02's notes; step 3 task 03's walk probe, which hides the dev debug toolbar)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. **The demo:** on news submit, insert three smileys at different points,
   preview, and all three render as images.
2. At about 375 px and desktop width: the toolbar's buttons fit on one row,
   the modal scrolls and its Done button is reachable, and the console is
   clean. Walk the picker on news submit, profile edit (both boxes), message
   compose and one comment form. At desktop width, drag the picker aside,
   click into the post to move the cursor, and add smileys there; compare
   with the old forums' "more smileys" window, which it is meant to match.
3. In Firefox or Safari (Brian's browser, by hand): the network panel shows
   no smiley image requests until the modal opens.
4. If anything writes to the dev database, take a snapshot first
   (`tools/pg_snapshot.sh dump <label>`).
5. Tick step 4 in `implementation/plan.md` and close it in `STATUS.md`.
6. After Brian approves: merge `smileys` to `main`, push, and check CI on
   both. Brian deploys. Record the deploy once he confirms the live site.
7. Close #9 with a comment naming the commit, after asking Brian.

## Dependencies
- Tasks 01 and 02.

## Implementation Approach
1. Snapshot the dev database if needed. Run the demo, then the walk at both
   widths.
2. Run `make test-browser`, the full suite, and the deprecation gate as its
   own run, one last time on the branch.
3. Write the step's close in STATUS and tick the plan.
4. Stop for Brian's review. Merge and push when he approves. Watch CI.
5. After Brian deploys, spot-check the live site: insert a smiley and preview it.

## Acceptance Criteria

1. **The demo holds**
   - Given news submit on the dev stack
   - When three smileys are inserted at different points and previewed
   - Then all three render as images

2. **It fits and works at both widths**
   - Given each post box page walked
   - When the picker is opened, used and closed at phone and desktop widths
   - Then the toolbar fits, the modal scrolls to Done, and the console shows no errors

3. **Lazy outside Chromium**
   - Given Firefox or Safari
   - When a post box page loads and the picker is then opened
   - Then smiley images are requested only after it opens

4. **The step is closed in the record**
   - Given `implementation/plan.md` and `STATUS.md`
   - When read after the merge
   - Then step 4 is ticked and its close records the walk and the deploy

5. **Merged, deployed, green, closed**
   - Given Brian's approval
   - When `smileys` is merged to `main` and pushed
   - Then CI is green, the live site passes the spot check, and #9 is closed

## Metadata
- **Complexity**: Low
- **Labels**: Manual testing, smileys, release, documentation, #9
- **Required Skills**: Browser devtools, git, the project's deploy path, gh
