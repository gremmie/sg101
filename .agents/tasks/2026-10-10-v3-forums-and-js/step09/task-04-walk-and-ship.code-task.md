# Task: Walk forums release 2 and ship it

## Description
Walk every page of forums release 2 on the dev stack as an anonymous visitor,
a member and a moderator, at phone and desktop widths, and run the step's
demo. Then tick step 9, merge the release branch into `main`, and hand Brian
the deploy.

## Background
**Release 2's pages** (design §4.4): `topic_list` (unread, unanswered,
active), `post_list` (mine, a member's), and `manage_topics` (favorites,
subscriptions). Seven URLs:

| URL | Signed in |
|---|---|
| `/forums/unread/` | required |
| `/forums/unanswered/` | optional |
| `/forums/topic/active/30/` | optional |
| `/forums/my-posts/` | required |
| `/forums/posts/<username>/` | required |
| `/forums/favorites/` | required |
| `/forums/subscriptions/` | required |

Anonymous requests to the five that need a login go to
`/accounts/login/?next=`, which is V3 too.

**The plan's demo:** as a member with favorites and subscriptions, walk all
seven URLs and remove a favorite. Also choose each entry in the forum query
box from one of these pages and land on it: that box moved to `nav.js` on
these pages in tasks 01-03.

**The probe must not perturb what it measures** (step 8 task 05 is the
worked example).

- Take a snapshot first (`tools/pg_snapshot.sh`).
- Choose subjects by id, not by anything the walk changes. The demo member
  needs favorites and subscriptions; if none has both, add them and remove
  them afterwards.
- Opening the unread list, or a topic from it, touches `ForumLastVisit` and
  `TopicLastVisit`; removing a favorite writes. Record the walking members'
  read-tracking rows, favorites and subscriptions before, diff after, and put
  back what changed.
- Use no ORM inside the Playwright block. Probe sessions log in through
  `settings.AUTHENTICATION_BACKENDS[0]`, and are deleted after;
  `last_login` stays unchanged. Check `.env` for `DEBUG_TOOLBAR`.
- Note in `STATUS.md` what the walk left in the dev database, if anything.

**Screenshots stay out of the repository** (Brian, 2026-11-03). Save them in
the session scratchpad and hand Brian their paths.

**Nothing deferred changes in this release**, so the worker check of step 8
task 05 isn't needed. If tasks 01-03 turned out to touch deferred work, check
it with the worker running.

**Shipping.**

- Run the full suite once, under the deprecation gate (`AGENTS.md`).
- Tick step 9 in `implementation/plan.md` and record it in `STATUS.md`,
  carrying forward what is still open (#41, #42, #43, steps 13-15, and the
  moderator's header overflow at 360).
- Merge `main` into the branch, push, and check CI. Watch it in a separate
  Bash call run in the background, using the full SHA. Only
  `conclusion=success` is a pass.
- Fast-forward `main` to the branch and push, after Brian says to. Check CI
  again.
- **Brian deploys** (`git pull`, then `make prod-up`, or `make prod-deploy`
  if the release has migrations; it shouldn't). This session doesn't ssh to
  leopard. Delete the branch, remote and local, when Brian says to.
- After the deploy, Brian checks live, and `STATUS.md` records that.

The plan's branch name is a placeholder; release 1 used
`v3-forums-release-1`, so `v3-forums-release-2`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 9 demo and integration)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 05: the release 1 walk and its cleanup)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. A headless Chromium walk of the seven URLs, at 360 and 1280 px, as
   anonymous, member and moderator, recording for each page that it extends
   `v3/base.html`, has no page errors, and has no horizontal overflow.
2. The demo, run end to end, with each step's result recorded.
3. No release 2 template extends `base.html`, and `forum_query.js` is gone.
4. The dev database left as found, or what remains recorded.
5. The full suite passes under the deprecation gate.
6. Step 9 ticked in the plan and recorded in `STATUS.md`. CI green on the
   branch and on `main`.
7. Brian deploys, and `STATUS.md` records the deploy and his live check.

## Dependencies
- Tasks 01-03.
- The dev stack running, with a recent production snapshot.

## Implementation Approach
1. Take the snapshot, check `.env`, choose the subjects by id, and record the
   state the walk could change. Write the probe in the scratchpad.
2. Walk the pages by role and width, then run the demo.
3. Hand Brian the screenshots and anything found. Stop for his answers, and
   fix what he asks for with tests.
4. Clean the dev database and diff it against the record. Run the full suite
   under the gate. Tick the step.
5. Leave the docs unstaged for review. Commit, merge `main` in, push and
   check CI, after Brian says to. Then the fast-forward of `main`, and Brian's
   deploy.

## Acceptance Criteria

1. **Release 2 is V3 throughout**
   - Given the seven URLs
   - When each is opened by anonymous, member and moderator at 360 and 1280 px
   - Then each extends `v3/base.html` (or redirects to the V3 login), with no page errors and no horizontal overflow

2. **The demo works end to end**
   - Given a member with favorites and subscriptions on dev
   - When they walk all seven URLs and remove a favorite
   - Then each page works, and the favorite is gone from the list

3. **The forum query box works on the new pages**
   - Given one of the release 2 pages
   - When each entry is chosen and Go is clicked
   - Then the browser lands on that entry's page

4. **The walk leaves no trace**
   - Given the end of the walk
   - When the dev database and the working tree are checked
   - Then the recorded state matches, and no screenshot is in the repository

5. **Release 2 ships**
   - Given the suite and the gate passing and CI green
   - When Brian deploys `main`
   - Then step 9 is ticked, and `STATUS.md` records the deploy and his live check

## Metadata
- **Complexity**: Medium
- **Labels**: forums, V3 design, review, Playwright, release
- **Required Skills**: Playwright for Python, Docker Compose, git
