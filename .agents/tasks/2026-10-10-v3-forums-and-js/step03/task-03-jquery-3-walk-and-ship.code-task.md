# Task: Walk the site on jQuery 3, then merge and deploy step 3

## Description
Check by hand the parts of the V3 site that no browser test covers, now that
they run on jQuery 3.7.1. Then close step 3 in the planning documents, merge
`jquery-3` to `main`, and hand over the deploy.

## Background
Research topic 8 loaded these widgets on jQuery 3 without errors but didn't
interact with them, so design §7.3 makes them a manual check at phone and
desktop widths:

- the navigation drilldown and dropdown menus (Foundation's ResponsiveMenu,
  Toggler)
- the Orbit banner
- the home page Cycle slideshow (jQuery Cycle 3.0.3)
- posting a comment on a download, a poll and a photo of the day
  (`comments.js`)

Task 02 changed how every Reveal modal opens, so every post box modal is
walked again with the console open.

Branch practice (Q11): planning and STATUS changes for this step are committed
on `jquery-3`, which merges to `main` when deployed. Deploys are `git pull`
then `make prod-up` on leopard, which Brian runs. Step 3 has no migrations.
The application image has no Node, but this step changes no Sass.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§7.3, §8)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 3 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (tasks 01 and 02's notes)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Walk each item above at phone (about 375 px) and desktop widths on the dev
   stack, with the console and network panels open. Record what was checked,
   and anything other than "works, console clean".
2. Open every post box modal (upload, hot-link, preview, and any others) on
   news submit and `bio/edit_profile`. Confirm task 02's fix holds and the
   console is clean.
3. Confirm the step demo: any V3 page reports `jQuery.fn.jquery === "3.7.1"`,
   and the network panel shows no request to `ajax.googleapis.com`.
4. If posting a comment writes to the dev database, take a snapshot first
   (`tools/pg_snapshot.sh dump <label>`).
5. Tick step 3 in `implementation/plan.md` and close it in the project's
   `STATUS.md`.
6. After Brian approves: merge `jquery-3` to `main`, push, and check CI on both.
   Brian deploys. Record the deploy in STATUS once he confirms the live site.

## Dependencies
- Tasks 01 and 02.

## Implementation Approach
1. Snapshot the dev database if needed.
2. Walk the list at both widths. Then the post box modals.
3. Run `make test-browser`, the full suite, and the deprecation gate as its own
   run, one last time on the branch.
4. Write the step's close in STATUS and tick the plan.
5. Stop for Brian's review. Merge and push when he approves. Watch CI.
6. After Brian deploys, spot-check the live site: one V3 page's jQuery version
   and network panel, and one post box modal.

## Acceptance Criteria

1. **The unwatched widgets work on jQuery 3**
   - Given the dev stack on jQuery 3.7.1
   - When the menus, Orbit, Cycle and comment posting are used at phone and desktop widths
   - Then each works and the console shows no errors

2. **Every post box modal is clean**
   - Given news submit and profile edit
   - When each post box modal is opened and closed
   - Then each works and Chrome logs no `aria-hidden` error or warning

3. **The demo holds**
   - Given any V3 page
   - When it loads
   - Then it reports jQuery 3.7.1 and requests nothing from `ajax.googleapis.com`

4. **The step is closed in the record**
   - Given `implementation/plan.md` and `STATUS.md`
   - When read after the merge
   - Then step 3 is ticked and its close records the walk and the deploy

5. **Merged, deployed, green**
   - Given Brian's approval
   - When `jquery-3` is merged to `main` and pushed
   - Then CI is green and the live site passes the spot check

## Metadata
- **Complexity**: Low
- **Labels**: Manual testing, jQuery, Foundation, release, documentation
- **Required Skills**: Browser devtools, git, the project's deploy path
