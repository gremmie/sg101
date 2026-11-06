# Task: Walk the finished topic page, settle the icons and the phone layout, and close step 7

## Description
Walk the step's demo on the dev stack: read a topic, follow a permalink,
quick-reply, flag a post, and as a moderator delete one, at phone and desktop
widths. Screenshot the post card for Brian's review of the two decisions tasks
01 left open, the tool icons and where the PM and email links go on phones.
Make the changes he asks for, then tick step 7.

## Background
The plan's demo for step 7: on dev data, read a topic, follow a permalink,
quick-reply, flag a post, and as a moderator delete one, with no page reload
and no `alert()`.

**Decisions waiting for this review:**

- **The icons.** Task 01 used `fi-*` icons provisionally and listed them.
- **The phone layout.** Task 01 placed the PM and email links where phones
  can see them, since the author card is hidden below medium.
- **The flag button for anonymous visitors**, if task 01 didn't settle it.

Present each with the screenshots that show it, and a recommendation.

**The probe must not perturb what it measures.** Flagging emails the admins
and stores a `FlaggedPost`, and deleting removes a real post from the dev
copy of production's data. Pick a subject by id, not by something the walk
changes. Make the post the walk deletes, and the reply it adds, on a topic
chosen for it, and delete what the walk added once it's done. Note in STATUS
what the walk left in the dev database, if anything.

**Screenshots stay out of the repository (Brian, 2026-11-03).** They show
members' names, avatars and posts. Save them in the session scratchpad and
hand Brian their paths. `STATUS.md` records his decisions in words.

The dev debug toolbar overlays the phone menu; check `.env` for
`DEBUG_TOOLBAR` first. Probe sessions log in through
`settings.AUTHENTICATION_BACKENDS[0]`, not `ModelBackend`.

This task deploys nothing. Forums release 1 ships at the end of step 8.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§2.4 R14, §7.3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 7 demo)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 6 task 03's probe, how to log a probe in)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. With a headless Chromium probe against the dev stack, walk the demo at 360
   and 1280 px, as a member and as a moderator. Record for each action
   whether it worked, with no page reload and no `alert()`.
2. Screenshot the post card at both widths for each role, and the card of a
   stranger's post as a moderator.
3. Save everything under the session scratchpad. Nothing from it goes into the
   repository.
4. Record Brian's decisions in `STATUS.md`, make each change he asks for, with
   tests where the change has behaviour, and re-shoot what it affects.
5. Tick step 7 in `implementation/plan.md` and record it in `STATUS.md`.
   Carry forward anything found and not done.
6. Run the full suite and then the deprecation gate on the branch.

## Dependencies
- Tasks 01 and 02.
- The dev stack running, with a recent production snapshot loaded.

## Implementation Approach
1. Check `.env`, choose the subjects by id, and write the probe in the
   scratchpad.
2. Walk the demo, then shoot the cards.
3. Hand Brian the screenshot paths with the open decisions and a
   recommendation for each. Stop for his answers.
4. Record them, make and verify the changes, and remove what the walk added
   to the dev database.
5. Run the full suite, then the deprecation gate. Leave the work unstaged for
   review.

## Acceptance Criteria

1. **The demo works end to end**
   - Given the dev stack and a member and a moderator
   - When the probe reads a topic, follows a permalink, quick-replies, flags, and deletes
   - Then each works with no page reload and no `alert()`, at 360 and 1280 px

2. **Brian's decisions are recorded and made**
   - Given the screenshots and the open decisions
   - When Brian decides
   - Then `STATUS.md` records each decision, and every change he asked for is made and re-shot

3. **Nothing from the walk reaches the repository**
   - Given the end of the task
   - When `git status` and the diff are checked
   - Then no image and no member data are in the working tree

4. **The step closes green**
   - Given the branch at the end of step 7
   - When the full suite and then the deprecation gate run
   - Then both pass, and step 7 is ticked in the plan

## Metadata
- **Complexity**: Low
- **Labels**: forums, V3 design, review, Playwright, screenshots
- **Required Skills**: Playwright for Python, responsive layout measurement
