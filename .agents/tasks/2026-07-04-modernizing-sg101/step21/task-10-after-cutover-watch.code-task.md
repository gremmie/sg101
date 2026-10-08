# Task: After Cutover — Mail Proven Live, Two Weeks Watched, Documentation Made True

## Description
The checks that can only be done once the site is live on the new host: run
every mail path for real, watch bounces for two weeks, keep the DMARC readings
daily and then stop them, confirm the edge blocking and the backups on live
traffic, measure Step 17's *after* figure when enough months exist, and
regenerate `.agents/summary/` and review `AGENTS.md` so they describe what
production now is.

## Background
Several earlier steps closed with an item that needed production:

- **D3 — every mail path, live, once.** `tools/email_smoke.py --live` in the
  production `web` container, all ten paths, to addresses Brian owns, **including
  an Outlook or Hotmail inbox**: Gmail accepted this site's mail before any of
  the migration, so it cannot tell success from failure. Read
  `Authentication-Results` in the inbox, not the provider's `250`. So far one
  path to one receiver has been sent. `--live` cannot be undone.
- **D4 — Postmark's bounce dashboard, two weeks from cutover.** This replaced a
  graduated warm-up (dropped 2026-08-20): 11.9% of a year's notification mail goes
  to accounts dormant 3+ years, so early hard bounces are expected, and each
  suppresses its address.
- **DMARC readings** stay daily for about two weeks after the flip (A4), then
  stop, per `research/dmarc-readings.md`. Run `tools/dmarc_fetch.py` before each
  reading.
- **Step 17's *after* measurement:** spam deactivations by month from
  `UserProfile.status`, the same read as `STATUS.md` § *the spam baseline, read
  from the database* (~1.4/month before). It needs several post-cutover months,
  so **this item may stay open after the rest of the task closes**; say so rather
  than holding the task.
- **Email Routing and SPF.** Any change to Email Routing must not let
  Cloudflare's wizard add a second `v=spf1` at an apex — two is a PermError and
  SPF fails for everything the site sends. After any such change: one `v=spf1`
  per apex with the `ip4:`/`ip6:` terms and `-all` intact, MX still
  `route1/2/3.mx.cloudflare.net`, one `v=DMARC1`. Note the apex SPF still names
  **jaguar's** address; whether it should now name the VM's is a question for
  this task (the VM sends through Postmark, not directly). **The `ip6:` term
  authorizes jaguar's whole Linode /64, which is shared**, and a neighbour,
  `2600:3c01::2000:96ff:fe4a:23be`, passed DMARC as this domain on it in
  Google's 09-30 report (twenty-fifth DMARC reading). Drop it or narrow it to
  `/128` here; Brian deferred the change past the cutover on 2026-10-05.
- **`.agents/summary/` was generated 2026-08-27** and describes jaguar, Apache +
  `mod_wsgi`. It became false at the flip. Regenerate with
  `/agent-sops:codebase-summary`, then review `AGENTS.md` — its facts about the
  live site (the `REMOTE_ADDR` path, log retention, the wiki and `fabfile.py`
  notes) change with the cutover.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C8 — email; C10)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — D2–D4
- `.agents/planning/2026-07-04-modernizing-sg101/research/dmarc-readings.md`
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 16 task 07
  (*Still open*), Step 17's spam baseline
- `tools/email_smoke.py` — its docstring on what a green run does not prove

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. All ten mail paths sent live from the production container to Brian's
   addresses, Gmail and Outlook at least; `Authentication-Results` read and
   recorded per path per receiver.
2. Postmark bounces and spam complaints reviewed daily for two weeks; anything
   other than dormant-address hard bounces explained.
3. DMARC readings daily through the two weeks, then the cadence stopped as the
   reading log says.
4. fail2ban seen banning and unbanning on live traffic, with the list's size
   stable rather than growing.
4a. At the end of the two weeks, `make blocklist-clear days=14` on leopard:
   the second stranded-entry cleanup task 06 owes. By then every entry jaguar's
   `wiki-abuse` made before the wiki went (runbook C6) is past fourteen days.
   Before and after counts recorded, as the first run's were.
4b. `web`'s memory read daily: `docker stats --no-stream` for the container,
   and each gunicorn worker's RSS and elapsed time from `ps` inside it, so a
   restart is not mistaken for a plateau. gunicorn runs five workers with no
   `--max-requests`, so nothing recycles them. Starting points: 502–539 MiB in
   the first hour after the flip, **691 MiB** (workers 150–168 MB) on
   2026-10-08 22:30 UTC, 12½ h after the 10:00 UTC reboot. A plateau needs
   nothing; growth that continues past the first few days calls for
   `--max-requests` with jitter, recorded with the readings that show it.
5. The first nightly backups after cutover present in both buckets, and no
   alarm fired (or, if it fired, explained).
6. The apex SPF question settled and recorded; any DNS change followed by the
   three checks above.
7. `.agents/summary/` regenerated and `AGENTS.md` reviewed; every statement
   about the live site now describes the Linode stack.
8. Step 17's after-measurement recorded when the months exist, or left as a named
   open item with a date to revisit.

## Dependencies
- Task 09 (the site is live on the VM)
- Brian's inboxes, Postmark and Cloudflare access

## Implementation Approach
1. D3 in the first days, while D4's watch is running.
2. A short daily check against a fixed list (bounces, DMARC, fail2ban list
   size, backup alarm, `web`'s memory), recorded as one line a day.
3. Regenerate the summary at the end of the two weeks, once nothing is moving.

## Acceptance Criteria

1. **Every mail path authenticates at two receivers**
   - Given the ten paths sent to Gmail and Outlook
   - When the headers are read
   - Then each shows DKIM and SPF passing for `surfguitar101.com`, or the failure
     is recorded and fixed

2. **Two weeks watched**
   - Given the daily checks
   - When the two weeks end
   - Then bounces, DMARC, the block list's size and `web`'s memory each have
     fourteen recorded readings

3. **Edge blocking holds**
   - Given live traffic
   - When the block list is read at the start and end of the two weeks
   - Then its size tracks active bans, not the total bans ever made

4. **The documentation describes production**
   - Given the regenerated summary and the reviewed `AGENTS.md`
   - When they are read
   - Then neither describes jaguar, `mod_wsgi` or MySQL as current

## Metadata
- **Complexity**: Medium
- **Labels**: Email, DMARC, Monitoring, Documentation, Post-Cutover
- **Required Skills**: Email authentication, Postmark, Cloudflare DNS, technical
  writing
