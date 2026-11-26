# Task: Walk the one-design site and ship `base.html`'s retirement

## Description
Check on the dev stack that the site renders as before with one base
template, and that no page loads Blueprint, jQuery 1.11 or markItUp. Then
tick step 12, merge, hand Brian the deploy, and close #18 or narrow it.

## Background
**The plan's demo:**

- `git grep base.html` finds no template that extends it.
- No page loads Blueprint, jQuery 1.11 or markItUp.
- The home page, a forum topic, news and a profile render as before.

**The walk.** Headless Chromium at 360 and 1280 px, as an anonymous visitor
and as a member. Pages:

- the home page
- the forums index and a topic
- the news index and a story
- a member's profile
- the post box pages: news submit, a forum reply, a download, a poll's
  comments
- the calendar's event page (`gcalendar.css` changed in task 02)
- the PM compose page (jQuery UI autocomplete)
- the profile editor (jQuery UI datepicker)

For each page, record:

- every requested script and stylesheet URL, none of them `blueprint`,
  `base.css`, `markitup` or jQuery 1.11
- no page errors
- no horizontal overflow
- the sidebar blocks present: POTD, poll, contest, donations, birthdays,
  countdown

Open the post box's smiley picker and preview on one page each.

**This walk only reads, mostly.** Topic views bump `view_count`, and reading
creates `ForumLastVisit`/`TopicLastVisit` rows. Record them before the walk
and put them back afterwards, as step 9 task 04 did. Probe sessions log in
through `settings.AUTHENTICATION_BACKENDS[0]` and are deleted afterwards.
Keep the ORM out of the Playwright block. Check `.env` for `DEBUG_TOOLBAR`.
Don't submit the post box.

**Screenshots stay out of the repository** (Brian, 2026-11-03). Save them in
the session scratchpad and hand Brian their paths.

**#18.** Read it first (`gh issue view 18`). The plan says: close it, or
narrow it to what remains. That's jQuery itself, which Foundation needs, and
replacing jQuery UI's datepicker and autocomplete. Draft the comment and let
Brian choose before posting.

**Shipping.**

- Run the full suite once, under the deprecation gate (`AGENTS.md`).
- Tick step 12 in `implementation/plan.md` and record it in `STATUS.md`,
  carrying forward what is still open (#41, #42, #43, steps 13-15).
- Merge `main` into the branch, push, and check CI. Watch it in a separate
  Bash call run in the background, using the full SHA. Only
  `conclusion=success` is a pass.
- Fast-forward `main` to the branch and push, after Brian says to. Check CI
  again.
- **Brian deploys** (`git pull`, then `make prod-up`; there are no
  migrations). This session doesn't ssh to leopard. **Static files
  changed**: the deploy's `collectstatic` must drop nothing a live page
  needs. Brian checks the home page, a topic, news and a profile live, with
  the browser console open.
- Close or narrow #18 after his live check. Delete the branch, remote and
  local, when he says to.

The branch is `retire-base-html`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 12 demo and integration)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 9 task 04: a read-only walk and its cleanup)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. A walk of the pages above at 360 and 1280 px, anonymous and member,
   recording each page's requested assets, page errors, overflow and sidebar
   blocks.
2. No request for Blueprint, `base.css`, markItUp or jQuery 1.11 on any page.
3. The smiley picker, preview, datepicker and autocomplete still work.
4. The dev database left as found, or what remains recorded.
5. The full suite passes under the deprecation gate.
6. Step 12 ticked and recorded. CI green on the branch and on `main`.
7. Brian deploys, `STATUS.md` records the deploy and his live check, and
   #18 is closed or narrowed as he chooses.

## Dependencies
- Tasks 01-03.
- The dev stack running, with a recent production snapshot.

## Implementation Approach
1. Check `.env`, choose the subjects by id, and record what the walk could
   change. Write the probe in the scratchpad.
2. Walk the pages, run the demo's greps, and exercise the four widgets.
3. Hand Brian the screenshots and anything found. Stop for his answers, and
   fix what he asks for with tests.
4. Clean up and diff. Run the full suite under the gate, and tick the step.
5. Leave the docs unstaged for review. Commit, merge `main` in, push and
   check CI, after Brian says to. Then the fast-forward, Brian's deploy, and
   #18.

## Acceptance Criteria

1. **No page loads the old design**
   - Given the walked pages at both widths, anonymous and member
   - When their requests are recorded
   - Then none is for Blueprint, `base.css`, markItUp or jQuery 1.11, and none has a page error

2. **The site renders as before**
   - Given the home page, a topic, news and a profile
   - When each is compared with today's
   - Then the header, sidebar blocks and content are the same, with no horizontal overflow

3. **The widgets still work**
   - Given the post box, PM compose and the profile editor
   - When the smiley picker, preview, autocomplete and datepicker are used
   - Then each works

4. **The walk leaves no trace**
   - Given the end of the walk
   - When the dev database and the working tree are checked
   - Then the recorded state matches, and no screenshot is in the repository

5. **Step 12 ships**
   - Given the suite passing under the gate and CI green
   - When Brian deploys `main`
   - Then step 12 is ticked, `STATUS.md` records the deploy and his live check, and #18 is closed or narrowed

## Metadata
- **Complexity**: Medium
- **Labels**: base.html, V3 design, review, Playwright, release
- **Required Skills**: Playwright for Python, Docker Compose, git
