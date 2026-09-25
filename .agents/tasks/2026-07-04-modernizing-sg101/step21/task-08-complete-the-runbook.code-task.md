# Task: Complete the Cutover Runbook — Sequence, Timings, Smoke Checklist, Rollback

## Description
Close the four gaps `cutover-runbook.md` lists about itself, so it can be
followed on the day without deciding anything: put the entries in order with
timings from the rehearsal, write a current smoke checklist, write a rollback
procedure that says what happens to data written on the new host, and remove the
"Step 20 is unfinished" gap, which is no longer true.

## Background
The runbook was started 2026-09-06 to collect cutover-day actions that had been
spread across four files. It holds actions and pointers, never reasoning, and
every entry has a source. Its closing section, *Known gaps in this list*, reads:

- **The smoke checklist is not here.** A Step 13 version exists in
  `STATUS-archive-steps-01-15.md`; whether it is still current is unchecked.
- **No rollback procedure** beyond "keep jaguar warm and flip DNS back". What
  that means for data written to the new host during the window is undecided.
- **Step 20 is unfinished** — no longer true: Step 20 closed 2026-09-23.
- **Ordering and timings are absent.** Sections are grouped by phase, not
  sequenced.

**Rollback is the hard one, and it is a decision.** After the DNS flip, members
post, register and upload on the new host. A DNS flip back to jaguar makes
jaguar's MySQL authoritative again, and everything written since is not in it.
The choices lie between "rollback only within the first N hours, and anything
written is lost, announced" and "carry the new rows back", which needs tooling
that does not exist in the Postgres → MySQL direction. It also depends on how
C0 left jaguar: frozen read-only, so it cannot quietly accept writes either.
**Brian decides**; this task sets out the options and what each costs.

**The Postmark and Cloudflare sides need a rollback line too:** the maintenance
mechanism on the new host is Cloudflare-side (C0 notes it must be in place
before D2), and the firewall's emergency open is in B6.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§6 — error handling, safety & rollback)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md`
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS-archive-steps-01-15.md`
  — the Step 13 smoke checklist
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — task 07's timings

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. A numbered sequence from "a week before" to "jaguar off", placing every A–D
   entry, with durations from task 07 where measured and marked estimates where
   not. The window's expected length and a stop point (the time after which
   the window is abandoned and jaguar is unfrozen).
2. A go/no-go list before the DNS flip: what must be true, each item checkable
   in one command or one look.
3. A smoke checklist current to the modern stack: the Step 13 list rechecked
   item by item, apps pruned since removed, and what `tools/prod_smoke.sh`
   already covers referenced rather than repeated. It covers reads, the writes a
   member makes (post, PM, registration, photo upload), search, mail, the
   calendar, and the worker picking up tasks (C4a).
4. Rollback options with their cost in lost data and effort, Brian's choice, and
   the procedure for the chosen one — including announcing it to members.
5. Where the maintenance notice comes from on each host, and in what order they
   switch.
6. Entries added by tasks 01–07 are placed in sequence; the *Known gaps* section
   says only what is still true.
7. The runbook stays actions and pointers. Any reasoning this task produces goes
   in `STATUS.md` and is linked.

## Dependencies
- Task 07 (timings and the corrections it made)
- Brian, for the rollback decision

## Implementation Approach
1. Read the whole runbook and the Step 13 checklist before changing either.
2. Draft the sequence from task 07's record; mark every unmeasured duration.
3. Put the rollback options to Brian; write the chosen procedure.
4. Walk the finished runbook as a dry read with Brian, and fix what doesn't
   make sense out of order.

## Acceptance Criteria

1. **Every entry has a place and a time**
   - Given the runbook
   - When read top to bottom
   - Then every entry appears in the sequence with a measured or marked
     estimated duration

2. **The smoke checklist is current**
   - Given the modern stack
   - When each checklist item is compared with the code
   - Then no item refers to a removed app or path, and each member-facing write
     is covered

3. **Rollback is decided and written**
   - Given Brian's choice
   - When the rollback section is read
   - Then it states the cutoff, what data is lost or carried, the steps, and the
     notice to members

4. **The gaps section is true**
   - Given the finished runbook
   - When *Known gaps* is read
   - Then it lists only what is still open

## Metadata
- **Complexity**: Medium
- **Labels**: Cutover, Runbook, Rollback, Documentation, Planning
- **Required Skills**: Operations planning, technical writing
