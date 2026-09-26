# Task: Run the Cutover

## Description
Move SurfGuitar101.com to the new host by following `cutover-runbook.md` as
task 08 left it: the pre-window checks, the maintenance window, the DNS flip,
and the first checks after it. **The runbook is the procedure; this task is
doing it and recording what happened.** Anything the runbook got wrong on the
day is corrected in the runbook as well as recorded.

## Background
This is the moment the modernization reaches production. Until now the repo and
the live site have differed — jaguar has served the Python 2.7 / Django 1.8 code
throughout — and `AGENTS.md` says so. After the flip the site runs Django 5.2 /
Python 3.12 / PostgreSQL 16 on the Linode, behind Cloudflare, with jaguar kept
warm as the fallback task 08 defined.

**Things specific to the day, which the rehearsal does not cover:**
- **Undo the rehearsal's safety blocks.** Task 07 ran with mail blocked and the
  calendar key removed or pointed at a scratch calendar. The real stack needs
  the real Postmark token and the real calendar key back, and C4a's restart so
  the worker and beat read them.
- **Pre-window items with a lead time:** A4 (DMARC readings go daily about a week
  before) and A5 (the jaguar-side email baseline — the only chance to take it).
- **A2 re-runs the production working-copy audit** (`hg status`, `hg diff` on
  jaguar), since production stayed live on the old code the whole time.
- **A3 is done:** Brian deleted the 32 pending `gcalendar` rows in production
  (reported 2026-09-26, date not recorded). The rehearsal snapshot confirms it
  (task 07a, requirement 4a). If it was not confirmed there, count pending events
  in the final snapshot before the site opens.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10; §6 — rollback)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — all of it
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — task 07's timings
  and task 08's rollback decision
- `.agents/planning/2026-07-04-modernizing-sg101/research/dmarc-readings.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. A date and time chosen with Brian, at a low-traffic hour, announced to
   members beforehand.
2. Every A entry done before the window, and recorded.
3. The window follows the runbook's sequence; start and end times of each step
   are recorded next to task 07's figures.
4. The go/no-go list is checked before the DNS flip. A "no" means following the
   rollback procedure, not improvising.
5. The DNS change is made at a low TTL, in Cloudflare, and nothing else in the
   zone changes with it. After it, exactly one `v=spf1` per apex, MX unchanged,
   exactly one `v=DMARC1`.
6. D1 (one real message, read with headers: `dkim=pass d=surfguitar101.com`,
   `spf=pass`) and B9 (the `/media` cache rule serving `HIT` from the new origin)
   done the same day.
7. fail2ban (task 06) enabled once B3 is seen passing on live traffic, if it was
   not already enabled on the test hostname.
8. The cutover commit is tagged, and the final MySQL snapshot archived beside
   the pristine one (checksummed). Both are preconditions for task 11.
9. `plan.md` and `STATUS.md` both updated the same day. `AGENTS.md`'s
   "nothing is deployed" statement is now false; correct it here rather than
   waiting for task 10's full review.

## Dependencies
- Tasks 01–08
- Brian, throughout: this is his production site and his DNS

## Implementation Approach
1. Walk through the runbook together the day before.
2. Keep a running log in the session with exact times; write it into
   `STATUS.md` afterwards.
3. Stop at the stop point task 08 defined, if it comes.

## Acceptance Criteria

1. **The site serves from the new host**
   - Given the DNS flip
   - When `curl -sI https://surfguitar101.com/` runs from outside
   - Then it returns 200 with a `cf-ray` header, and the request appears in the
     VM's Apache log with the client's real address

2. **Nothing written during the window was lost**
   - Given C0 froze writes on jaguar before the final snapshot
   - When the newest post, PM, registration and photo on jaguar are looked up on
     the new host
   - Then each is present, with its file where it has one

3. **Mail and calendar are live again**
   - Given the rehearsal's blocks were removed
   - When a real notification is triggered and a calendar event approved
   - Then the message is delivered with passing authentication, and the event
     appears on the real calendar

4. **The record is complete**
   - Given the window has ended
   - When `STATUS.md` is read
   - Then each step's time, anything that deviated from the runbook, and the tag
     and snapshot checksum are recorded

## Metadata
- **Complexity**: High
- **Labels**: Cutover, Deployment, DNS, Cloudflare, Production
- **Required Skills**: Operations, PostgreSQL, Docker Compose, Cloudflare,
  incident handling
