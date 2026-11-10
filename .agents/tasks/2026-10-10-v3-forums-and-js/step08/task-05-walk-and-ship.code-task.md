# Task: Walk forums release 1, check subscription mail with a real worker, and ship it

## Description
Walk every page of forums release 1 on the dev stack as an anonymous visitor,
a member and a moderator, at phone and desktop widths, and run the step's
demo. Check that a reply's subscription email is sent by a real Celery
worker. Then tick step 8, merge `v3-forums-release-1` into `main`, and hand
Brian the deploy.

## Background
**Release 1's pages** (design §4.4): `index`, `forum_index`, `topic`,
`display_post_v3`, `new_topic`, `new_post`, `edit_post`, `new_topic_thanks`,
`favorite_status`, `subscription_status`, plus the fragments they include.
The plan's integration note: nothing in release 1 still loads `base.html`.

**The plan's demo:** start a topic with a video, reply with a quote, edit the
reply to add a second video, then favorite and subscribe from the topic page.
Every page in that path is V3.

**Subscription mail is deferred work.** `CELERY_TASK_ALWAYS_EAGER` hides
worker faults by construction (AGENTS.md), so the suite can't show it. On the
dev stack, with the worker running, subscribe a second member to the topic,
reply as the first, and confirm the worker ran the task and the mail was sent
(the worker's log, and wherever dev's mail backend puts mail). Check
`sg101/settings/dev.py` for the backend first.

**The probe must not perturb what it measures.**

- Choose subjects by id, not by anything the walk changes.
- Make the topic the walk posts to, and delete what it added when done.
- Viewing a post touches `ForumLastVisit` for its forum too (step 7 task 03).
  Record every forum the walk opens, and restore those rows from the
  `before-forums-review` snapshot if they changed.
- Note in `STATUS.md` what the walk left in the dev database, if anything.

Answer writes with `page.route` where a write isn't the thing being checked,
and use no ORM inside the Playwright block. Probe sessions log in through
`settings.AUTHENTICATION_BACKENDS[0]`. The dev debug toolbar overlays the
phone menu; check `.env` for `DEBUG_TOOLBAR`.

**Screenshots stay out of the repository** (Brian, 2026-11-03). Save them in
the session scratchpad and hand Brian their paths.

**Shipping.**

- Run the suite and the deprecation gate, separately, one at a time (they
  share `test_sg101`).
- Tick step 8 in `implementation/plan.md` and record it in `STATUS.md`,
  carrying forward what is still open (#41, steps 13-15, `forum_query.js` for
  step 9).
- Merge `main` into the branch, push, and check CI. Watch it in a separate
  Bash call run in the background, using the full SHA. Only
  `conclusion=success` is a pass.
- Fast-forward `main` to the branch and push, after Brian says to. Check CI
  again.
- **Brian deploys.** Hand him the commands (`git pull`, then `make prod-up`,
  or `make prod-deploy` if the release has migrations), and the branch delete
  commands. This session doesn't ssh to leopard or delete branches.
- After the deploy, Brian checks live, and `STATUS.md` records that.

The branch carries steps 6-8. Its history with `main` includes the
2026-11-05 revert and revert-of-revert (`91c4628f`, `54e53361`); it merges
into `main` normally, with no extra revert (STATUS).

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 8 demo and integration)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 7 task 03's walk and its cleanup)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. A headless Chromium walk of every release 1 page, at 360 and 1280 px, as
   anonymous, member and moderator, recording for each page that it extends
   `v3/base.html`, has no page errors, and has no horizontal overflow.
2. The demo path, run end to end, with each step's result recorded.
3. A subscription email sent by a real worker after a reply, recorded in
   `STATUS.md`.
4. The dev database left as found, or what remains recorded.
5. The suite and the deprecation gate pass, run separately.
6. Step 8 ticked in the plan and recorded in `STATUS.md`. CI green on the
   branch and on `main`.
7. Brian deploys, and `STATUS.md` records the deploy and his live check.

## Dependencies
- Tasks 01-04.
- The dev stack running, with its Celery worker and a recent production
  snapshot.

## Implementation Approach
1. Check `.env` and the dev mail backend, choose the subjects by id, and
   write the probe in the scratchpad.
2. Walk the pages by role and width, then run the demo.
3. Check the subscription mail with the worker.
4. Hand Brian the screenshots and anything found. Stop for his answers, and
   fix what he asks for with tests.
5. Clean the dev database. Run the suite, then the gate. Tick the step.
6. Leave the docs unstaged for review. Commit, merge `main` in, push and
   check CI, after Brian says to. Then the fast-forward of `main`, and Brian's
   deploy.

## Acceptance Criteria

1. **Release 1 is V3 throughout**
   - Given every release 1 page
   - When each is opened by anonymous, member and moderator at 360 and 1280 px
   - Then each extends `v3/base.html`, with no page errors and no horizontal overflow

2. **The demo works end to end**
   - Given a member on dev
   - When they start a topic with a video, reply with a quote, edit the reply to add a second video, then favorite and subscribe
   - Then each step works and every page in the path is V3

3. **Subscription mail is sent by the worker**
   - Given a second member subscribed to the topic
   - When the first replies
   - Then the worker runs the notification task and the mail is sent

4. **The walk leaves no trace**
   - Given the end of the walk
   - When the dev database and the working tree are checked
   - Then what the walk added is gone, `ForumLastVisit` rows are as they were, and no screenshot is in the repository

5. **Release 1 ships**
   - Given the suite and the gate passing and CI green
   - When Brian deploys `main`
   - Then step 8 is ticked, and `STATUS.md` records the deploy and his live check

## Metadata
- **Complexity**: Medium
- **Labels**: forums, V3 design, review, Playwright, Celery, release
- **Required Skills**: Playwright for Python, Celery, Docker Compose, git
