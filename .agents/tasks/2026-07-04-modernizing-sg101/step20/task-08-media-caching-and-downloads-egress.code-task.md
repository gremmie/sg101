# Task: Cache `/media` at the Edge, and Measure What `downloads` Costs

## Description
Set Cloudflare cache rules for the media the VM serves from its own disk, and
measure the egress the `downloads` category actually generates before accepting
that it stays there.

## Background
The design has Cloudflare serving cached media in front of both S3 and the VM's
disk. Nothing has been configured to make that happen, and nothing has been
measured to say whether it matters.

**The plan names one category specifically:** *"`downloads` (716 MP3 rows) is the
one category worth measuring egress on before leaving it on disk."* MP3s are the
largest individual files the site serves, and they are the one case where the VM's
bandwidth allowance, rather than its disk, could be the binding constraint.

**The decision this measurement feeds is already made in one direction.** Media
stays on the VM's disk — the R2 direction was reversed on 2026-08-15 and user
photos went back to the existing S3 bucket. So this measurement is not choosing a
storage backend; it is deciding whether edge caching is sufficient to make disk
storage viable, and surfacing the number before cutover rather than discovering it
in a bandwidth bill.

**Measure before recording.** A guess at MP3 egress reads identically to a
measurement once it is written down. jaguar's Apache access logs are the source
for what has actually been served, and they are subject to the retention limits
recorded in the plan — which is a reason to take this measurement early.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§3.2 — Cloudflare serving cached media from both S3 and the VM disk)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/hosting.md` — VM
  bandwidth allowances and object storage egress pricing

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Measure `downloads` egress from jaguar's Apache access logs: request count,
   bytes served, and the distribution over time.
2. State the retention window the measurement covers, and whether it includes a
   representative peak.
3. Compare the measured figure against the target VM's bandwidth allowance and
   record the headroom.
4. Configure Cloudflare cache rules for `/media`, with TTLs chosen per category —
   avatars and `downloads` do not change at the same rate.
5. Verify caching from the response headers rather than from the dashboard.
6. Record the measurement in `STATUS.md` with its date and source, so a later
   reader can tell a measurement from an estimate.

## Dependencies
- Access to jaguar's Apache access logs, within their retention window
- Task 04 — the proxy that serves `/media` on the new VM
- Cloudflare zone configuration access

## Implementation Approach
1. Take the measurement first; the cache rules are shaped by what it says.
2. Compute both the raw egress and what it would be with an effective edge cache,
   and state the assumed hit rate rather than burying it.
3. Configure the cache rules per media category.
4. Verify with `cf-cache-status` on a real request, on a second request for the
   same asset, since the first populates the cache.

## Acceptance Criteria

1. **`downloads` egress is measured, not estimated**
   - Given jaguar's Apache access logs
   - When `downloads` traffic is summed
   - Then request count and bytes served are recorded with the window they cover

2. **The headroom against the VM allowance is stated**
   - Given the measured egress and the target VM's bandwidth allowance
   - When they are compared
   - Then the margin is recorded, along with the cache hit rate assumed

3. **Media is cached at the edge**
   - Given the cache rules are configured
   - When a media asset is requested twice through Cloudflare
   - Then the second response reports a cache hit in `cf-cache-status`

4. **TTLs differ by category where the change rate differs**
   - Given the configured rules
   - When they are reviewed
   - Then each category's TTL is justified by how often that category changes

5. **The measurement is findable later**
   - Given `STATUS.md`
   - When the media section is read
   - Then the figure, its date and its source are recorded

## Metadata
- **Complexity**: Low
- **Labels**: Cloudflare, Caching, Media, Measurement, Production Hardening
- **Required Skills**: Log analysis, Cloudflare cache rules, HTTP caching semantics
