# Task: Author the Origin Firewall Ruleset

## Description
Write and review the ruleset that will restrict the new VM's HTTPS port to
Cloudflare's published ranges over both IPv4 and IPv6. **Applying it needs the
provisioned VM and is handed to the cutover runbook** — this task produces the
rules, the verification procedure and the emergency-open procedure.

## Background
An origin behind Cloudflare is only protected if it refuses direct connections.
While the origin answers on its own address, every edge protection — the WAF rule,
the rate limits, the IP block list fail2ban maintains — can be bypassed by
addressing the VM directly, and `CF-Connecting-IP` trust becomes meaningless
because the peer is no longer necessarily Cloudflare.

**This was recorded as Step 20's during Step 16**, with the note that closing it
*"belongs to the new VM"*, and that Step 16 task 06 removed the reason the
exposure existed — Email Routing leaves the VM with no MX and no public mail name,
so nothing else needs to reach it from the open internet.

**Scope corrected 2026-09-12: no VM is provisioned.** The host *shape* was decided
2026-08-15, but nothing exists to firewall, and Step 20's premise is that it is
exercisable locally. The rules can be authored and reviewed now; they cannot be
applied or genuinely verified until Step 21. Splitting the task is more honest
than pretending the second half can happen here.

**This task and task 04 are two halves of one boundary.** Task 04 decides which
peers may assert a client address; this one decides which peers may connect at
all. Neither is sufficient alone, and **they must share one range list** rather
than maintaining two that can drift apart.

**⚠️ PREMISE GAP found 2026-09-21: this file predates the stack it has to
firewall, and reads as though Apache were a host process.** It was generated
2026-09-12. Task 03 landed on 2026-09-19 and put Apache in a **container**, which
changes where the rules have to live — not merely how they are written.

Measured from `docker-compose.prod.yml` rather than assumed: **exactly one
service publishes anything.** `proxy` publishes `80:80` and `443:443`, with no
address prefix, so both bind `0.0.0.0`. `web`, `worker`, `beat`, `postgres` and
`redis` declare no `ports:` at all and are reachable only on the compose network.
The entire public surface is the proxy container's two ports.

**That is the case where a host firewall silently does nothing.** Docker
publishes a port by inserting DNAT rules into `nat/PREROUTING`; the packet is
then *forwarded* to the container and never traverses `INPUT`. A ruleset written
against `INPUT` — which is what requirements 1 and 4 read as, and what ufw's
ordinary syntax produces — would be present, valid, and would filter nothing.
Traffic from any source address would still reach Apache. **The failure mode is a
firewall that looks correct and is not**, which is the worst available outcome
for this task and is invisible to a review that only reads the rules.

**Consequence for requirement 3, and it cuts the other way.** `sshd` is a host
process, so administrative access *is* on `INPUT`. The two paths are genuinely
separate chains: restricting the published 443 does not touch SSH, and the
lockout risk requirement 3 guards against is smaller than it looks — but only
once the separation is understood, and it is not stated anywhere in this file.

**The design is not chosen here, deliberately.** There are at least two shapes —
rules in the `DOCKER-USER` chain, which Docker traverses before its own
published-port rules and never rewrites; or binding the publish to a host-local
address and terminating externally by some other means. They have different
failure modes and different interactions with Cloudflare's ranges, and picking
one is Brian's call on evidence, not a detail to settle while writing rules.

**This is the same failure as task 04's**, one task later: a task file written
before the task it depends on carried a premise that had since become false.
**Re-read a task file's premises against what has landed since it was written**,
not only its requirement list.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — Step 16 task 03's
  *Open* register, where the origin-exposure question was recorded and deferred
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — where the
  application half of this task lands

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

**Read the premise-gap note in *Background* before this list.** Requirements 1
and 4 are written as though Apache were a host process; it is a container, and a
ruleset on `INPUT` would filter none of its published traffic.

1. Author a ruleset restricting inbound 443 to Cloudflare's published ranges,
   **IPv4 and IPv6 both**, in a form that can be applied to the VM unchanged —
   and in a chain that actually sees traffic DNAT'd to a published container
   port, which `INPUT` does not.
2. Source the ranges from the same verified list task 04 uses; a single source for
   both is the point, and drift between them is the failure mode.
3. Keep administrative access (SSH) reachable, and state explicitly by what means.
4. Make the rules survive a reboot, in the mechanism the chosen distribution uses.
5. Write the verification procedure — what to connect from, over which protocol,
   and what a correct refusal looks like.
6. Write the emergency-open and re-close procedure, so a cutover-day debugging
   need is not improvised under pressure.
7. Add the apply-and-verify steps to `cutover-runbook.md` under *Host
   preparation*.

## Dependencies
- Task 04 — shares the Cloudflare range list and its verification
- A provisioned VM, for the application half only — which is why that half is in
  the runbook

## Implementation Approach
1. Reuse task 04's verified range list.
2. Write the rules for the distribution the VM will run, including the IPv6 table,
   which is the half most often forgotten.
3. Review them by reading, since they cannot be exercised: state plainly in the
   task record that this ruleset is **unexercised** until Step 21.
4. Write both procedures — verification and emergency open — into the runbook.

## Acceptance Criteria

1. **The ruleset covers both protocols**
   - Given the authored rules
   - When they are reviewed
   - Then inbound 443 is restricted over IPv4 and IPv6, and the IPv6 table is
     present rather than assumed

2. **The range list is shared, not copied**
   - Given task 04's configuration and this ruleset
   - When their trusted ranges are compared
   - Then they derive from one verified source with a recorded verification date

3. **Administrative access is preserved and stated**
   - Given the ruleset
   - When SSH access is traced through it
   - Then the path is explicit rather than incidental

4. **The rules persist across a reboot by design**
   - Given the ruleset and its installation mechanism
   - When the mechanism is reviewed
   - Then persistence is handled by the distribution's own facility, not a
     start-up script that can silently fail

5. **Both procedures are in the runbook**
   - Given `cutover-runbook.md`
   - When *Host preparation* is read
   - Then applying, verifying, emergency-opening and re-closing the firewall are
     each written down

6. **The unexercised status is recorded**
   - Given the task record
   - When it is read before cutover
   - Then it states plainly that these rules have never been applied to a running
     host

## Metadata
- **Complexity**: Low
- **Labels**: Firewall, Cloudflare, Security, Cutover, Production Hardening
- **Required Skills**: Linux firewalling (nftables/ufw), IPv6, Cloudflare architecture
