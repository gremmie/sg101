# Task: Check the phone banner fix on dev and on Brian's phone, and ship it

## Description
Confirm on the dev stack that the phone banner shows when the layout
narrows, have Brian check it on his phone (landscape, then upright), then
tick step 13, merge, and hand Brian the deploy.

## Background
**The plan's demo:** in dev tools' phone view, the banner shows without a
reload. **Brian, on his phone:** open a page in landscape, turn it upright,
and the banner shows. The landscape-to-portrait case was inferred, never
seen (task 01's background), so Brian's check is the first time anyone
sees it.

**The dev walk** is headless Chromium against the dev server, read only:

- A few V3 pages (the home page, the forums index, a topic, a profile),
  loaded at 1280, narrowed to 402, 375 and 360, then widened back to 1280.
- At each narrow width: the banner's height, the logo visible, the bullets
  and the next button working, no page error, no horizontal overflow.
- At 1280 again: the banner hidden, the desktop header as before.
- Screenshots in the session scratchpad, never the repository.

Viewing a topic bumps its `view_count`, and a member's visits create
`ForumLastVisit` and `TopicLastVisit` rows. Walk anonymously, or record and
restore those as step 12 task 04 did. Check `.env` for `DEBUG_TOOLBAR`.

**Brian's phone check** needs the dev server reachable from the phone: the
Mac's LAN address on port 8000 (step 5 task 04 did this). Make sure
`ALLOWED_HOSTS` admits it on dev, and say what to open.

**Shipping.**

- Run the full suite once, under the deprecation gate (`AGENTS.md`).
- Tick step 13 in `implementation/plan.md` and record it in `STATUS.md`,
  carrying forward what is still open (#41, #42, #43, #50, steps 14 and 15).
- Push the branch and check CI. Watch it in a separate Bash call run in the
  background, using the full SHA. Only `conclusion=success` is a pass.
- Merge `main` into the branch if it has moved. Fast-forward `main` to the
  branch and push **only when Brian explicitly says to update `main`**.
  Check CI again.
- **Brian deploys** (`git pull`, then `make prod-up`; no migrations). This
  session doesn't ssh to leopard. Brian checks live on his phone. Record
  the deploy and his check in `STATUS.md`; delete the branch, remote and
  local, when he says to.

The branch is `orbit-remeasure`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 13 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 5 task 04: the phone check on the LAN; step 12 task 04: a read-only walk and its cleanup)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. A headless walk recording, for each page and width, the banner's height,
   the logo's visibility, the next button, page errors and overflow.
2. Brian's phone check, landscape to portrait, recorded.
3. The dev database left as found, or what remains recorded.
4. The full suite passes under the deprecation gate.
5. Step 13 ticked and recorded. CI green on the branch and on `main`.
6. Brian deploys, and `STATUS.md` records the deploy and his live check.

## Dependencies
- Task 01.
- The dev stack running.

## Implementation Approach
1. Check `.env`, write the probe in the scratchpad, and walk.
2. Give Brian the LAN address and what to do; stop for his result.
3. Run the full suite under the gate, tick the step, and leave the docs
   unstaged for review.
4. Commit and push after Brian says to; then `main`, the deploy and the
   live check.

## Acceptance Criteria

1. **The banner shows after narrowing, on every walked page**
   - Given the walked pages loaded at 1280
   - When each narrows to 402, 375 and 360
   - Then the banner is taller than 0 with the logo visible, with no page error or overflow

2. **A real phone turned upright shows the banner**
   - Given Brian's phone in landscape on a dev page
   - When he turns it upright
   - Then the banner shows without a reload

3. **The walk leaves no trace**
   - Given the end of the walk
   - When the dev database and the working tree are checked
   - Then nothing has changed, and no screenshot is in the repository

4. **Step 13 ships**
   - Given the suite passing under the gate and CI green
   - When Brian deploys `main`
   - Then step 13 is ticked, and `STATUS.md` records the deploy and his phone check

## Metadata
- **Complexity**: Low
- **Labels**: Orbit, responsive, review, Playwright, release
- **Required Skills**: Playwright for Python, Docker Compose, git
