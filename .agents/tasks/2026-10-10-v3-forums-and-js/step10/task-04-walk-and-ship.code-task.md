# Task: Walk forums release 3 and ship it

## Description
Walk the seven moderator pages on the dev stack as an anonymous visitor, a
member and a moderator, at phone and desktop widths, and run the step's
demo. Then tick step 10, merge the release branch into `main`, hand Brian the
deploy, and close #17.

## Background
**Release 3's pages** (design §4.4):

| Page | URL |
|---|---|
| `mod_forum` | `/forums/mod/forum/<slug>/` |
| `mod_split_topic` | `/forums/mod/topic/split/<id>/` |
| `move_topic` | `/forums/mod/topic/move/<id>/` |
| `post_ip` | `/forums/post/ip/<post_id>/` |
| `stranger` | `/forums/stranger/<post_id>/` |
| `spammer` | `/forums/spammer/<post_id>/` |
| `spammer_nailed` | `/forums/spammer/nailed/<spammer_id>/` |

All seven need a login, so an anonymous request goes to
`/accounts/login/?next=`, which is V3. A member gets each page's refusal: a
403, a redirect (split), or the page's own sentence (stranger, spammer).

**The plan's demo:** as a moderator, bulk-lock two topics, split a topic,
move one, and mark a stranger as legitimate. Every page is V3. **The spammer
button is not pressed**: it deactivates an account and deletes its posts.
Its page is opened, not submitted.

**The demo writes, so do it on things made for it.** Unlike release 2's walk,
lock, split, move and promote all change data:

- Take a snapshot first (`tools/pg_snapshot.sh`).
- Make a demo topic with a few posts in a forum chosen by id, by a member
  chosen by id, before the walk; split it, and move one of the halves. Delete
  both topics afterwards through `forums.views.main._delete_topic`, as step 8
  task 05 did, and put back the author's `forum_post_count` (#42).
- Lock two **existing** topics chosen by id, then lock them again to unlock
  them; record their `locked` and `update_date` before and after.
- For the stranger: choose a member with stranger status and a post, by id.
  Record their `UserProfile.status` (and anything else promotion writes:
  read `spam.stranger` first) and put it back.
- Record the walkers' `ForumLastVisit` and `TopicLastVisit` rows, the
  forums' counts and `last_post`, the topics' view counts, and `last_login`;
  diff after; put back what changed. Redis's post and topic counts go up
  with the demo topic and don't come down (#43): rebuild with `rebuild_redis
  --noinput` afterwards.
- Use no ORM inside the Playwright block. Probe sessions log in through
  `settings.AUTHENTICATION_BACKENDS[0]`, and are deleted after;
  `last_login` stays unchanged. Check `.env` for `DEBUG_TOOLBAR`.
- Note in `STATUS.md` what the walk left in the dev database, if anything.

**Deferred work.** Promotion, deactivation and the moderator actions may
queue tasks (mail to the admin on deactivation, search index updates). Read
what each path queues before the walk; if any does, restart the worker
first, as step 8 task 05 did, and check its log.

**Screenshots stay out of the repository** (Brian, 2026-11-03). Save them in
the session scratchpad and hand Brian their paths.

**Shipping.**

- Run the full suite once, under the deprecation gate (`AGENTS.md`).
- Tick step 10 in `implementation/plan.md` and record it in `STATUS.md`,
  carrying forward what is still open (#41, #42, #43, steps 11-15).
- Merge `main` into the branch, push, and check CI. Watch it in a separate
  Bash call run in the background, using the full SHA. Only
  `conclusion=success` is a pass.
- Fast-forward `main` to the branch and push, after Brian says to. Check CI
  again.
- **Brian deploys** (`git pull`, then `make prod-up`, or `make prod-deploy`
  if the release has migrations; it shouldn't). This session doesn't ssh to
  leopard. Close #17 after his live check, and delete the branch, remote
  and local, when he says to.
- After the deploy, Brian checks live, and `STATUS.md` records that.

The branch is `v3-forums-release-3`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.4, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 10 demo and integration)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 8 task 05 and step 9 task 04: the walks and their cleanup)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. A headless Chromium walk of the seven pages, at 360 and 1280 px, as
   anonymous, member and moderator, recording for each page that it extends
   `v3/base.html` (or redirects to the V3 login, or refuses), has no page
   errors, and has no horizontal overflow.
2. The demo, run end to end, with each step's result recorded.
3. No forum template extends `base.html`, and `forums_mod.js` is gone.
4. The dev database left as found, or what remains recorded.
5. The full suite passes under the deprecation gate.
6. Step 10 ticked in the plan and recorded in `STATUS.md`. CI green on the
   branch and on `main`.
7. Brian deploys, `STATUS.md` records the deploy and his live check, and #17
   is closed.

## Dependencies
- Tasks 01-03.
- The dev stack running, with a recent production snapshot.

## Implementation Approach
1. Take the snapshot, check `.env`, choose the subjects by id, make the demo
   topic, and record the state the walk could change. Write the probe in the
   scratchpad.
2. Walk the pages by role and width, then run the demo.
3. Hand Brian the screenshots and anything found. Stop for his answers, and
   fix what he asks for with tests.
4. Clean the dev database and diff it against the record. Run the full suite
   under the gate. Tick the step.
5. Leave the docs unstaged for review. Commit, merge `main` in, push and
   check CI, after Brian says to. Then the fast-forward of `main`, and Brian's
   deploy.

## Acceptance Criteria

1. **Release 3 is V3 throughout**
   - Given the seven pages
   - When each is opened by anonymous, member and moderator at 360 and 1280 px
   - Then each extends `v3/base.html`, or redirects to the V3 login, or refuses as today, with no page errors and no horizontal overflow

2. **The demo works end to end**
   - Given a moderator, a demo topic, two existing topics and a stranger
   - When they bulk-lock two topics, split the demo topic, move a half, and promote the stranger
   - Then each change happens, and every page in the path is V3

3. **The walk leaves no trace**
   - Given the end of the walk
   - When the dev database, Redis and the working tree are checked
   - Then the recorded state matches, and no screenshot is in the repository

4. **Release 3 ships**
   - Given the suite passing under the gate and CI green
   - When Brian deploys `main`
   - Then step 10 is ticked, `STATUS.md` records the deploy and his live check, and #17 is closed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, V3 design, moderation, review, Playwright, release
- **Required Skills**: Playwright for Python, Docker Compose, git
