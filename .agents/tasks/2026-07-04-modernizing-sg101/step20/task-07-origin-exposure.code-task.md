# Task: Author the Origin Firewall Ruleset

## Description
Restrict the new VM's web ports to Cloudflare's published ranges over both IPv4
and IPv6, **in the hosting provider's firewall, driven by a script from one range
list in the repo** (decided 2026-09-23 — see *Decided* below). This task produces
the range file, the provider-neutral tooling around it, and the verification and
emergency-open procedures. **The provider adapter and applying it need the
provider and the VM, and are Step 21's.**

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
against `INPUT` — which is what the original requirements 1 and 4 read as, and what ufw's
ordinary syntax produces — would be present, valid, and would filter nothing.
Traffic from any source address would still reach Apache. **The failure mode is a
firewall that looks correct and is not**, which is the worst available outcome
for this task and is invisible to a review that only reads the rules.

**Consequence for the original requirement 3 (SSH), and it cuts the other way.** `sshd` is a host
process, so administrative access *is* on `INPUT`. The two paths are genuinely
separate chains: restricting the published 443 does not touch SSH, and the
lockout risk that requirement guarded against is smaller than it looks — but only
once the separation is understood, and it is not stated anywhere in this file.
*(Both paragraphs describe host rules, which the provider firewall chosen below
does not use; kept because they are why `DOCKER-USER` was not chosen.)*

**The design was not chosen here, deliberately.** There are at least two shapes —
rules in the `DOCKER-USER` chain, which Docker traverses before its own
published-port rules and never rewrites; or binding the publish to a host-local
address and terminating externally by some other means. They have different
failure modes and different interactions with Cloudflare's ranges, and picking
one is Brian's call on evidence, not a detail to settle while writing rules.
*(Chosen 2026-09-23, and it was neither of these — see the next section.)*

### Decided 2026-09-23: the provider's firewall, driven from the repo

**Three options were compared, not two.** The third — the hosting provider's own
firewall (Linode Cloud Firewall, Lightsail's instance firewall) — was missing from
the list above, and it is the one that dissolves the premise gap: it filters
before a packet reaches the VM, so how Docker routes a published port does not
matter at all.

| | `DOCKER-USER` | Cloudflare Tunnel | **provider firewall (chosen)** |
|---|---|---|---|
| lives | rules on the VM, in the repo | a `cloudflared` service + a Cloudflare tunnel | the provider's dashboard/API, outside the VM |
| per-request cost | negligible (kernel match on new connections) | a userspace hop through `cloudflared` | none on the VM |
| shares task 04's list | yes | moot — nothing public to filter | only if a script pushes it — **hence the script** |
| effect on task 04 | none | reworks it: Apache would only ever see `cloudflared` | none |
| worst failure | a Docker-path subtlety leaves a family unfiltered | `cloudflared` down = **site down** | firewall detached or host changed, nothing on the VM notices |
| emergency open | flush the chain over SSH | re-publish the port and repoint DNS | one dashboard click, reachable even without SSH |
| survives reboot | needs the distribution's persistence, ordered with Docker | a container with a restart policy | nothing on the VM to persist |

**No option was meaningfully slower** at this site's load (6.4M requests in task
08's 56 days, ~1.3/s mean); the choice is on failure modes and upkeep.

**`DOCKER-USER`'s IPv6 half is unverified, and is why it was not chosen:**
depending on the Docker version and daemon settings, IPv6 connections to a
published port may be served by the userland `docker-proxy` through `INPUT`
rather than DNAT'd through `DOCKER-USER`, so the two families could need rules in
different chains. Not measured; recorded so a later revisit starts from it.

**The provider firewall's one weakness — a second copy of the range list outside
the repo — is closed by generating it.** A script, run from Make, pushes the
rules from the same file Apache reads, and can compare what is live against it.

**Decided with it:**

- **One range file, read by both consumers.** The ranges are inline in
  `apache/conf-enabled/remoteip.conf` today. They move to a file of their own
  that Apache reads via `RemoteIPTrustedProxyList` and the firewall script reads
  too, so "shared, not copied" holds by construction rather than discipline.
- **The script runs from Brian's machine, never the VM.** A token on the VM able
  to edit the VM's own firewall lets whoever compromises the VM open it. The
  token is firewall-scoped and lives with Brian.

### Deferred to Step 21, with the provider

The VM provider is not chosen (Step 21), so these wait for it — the constraint is
recorded now, the selection later:

- **The provider adapter** — the part of the script that calls the API. The
  provider-neutral core does not need it.
- **Whether one rule holds all 22 ranges across both families**, or the
  provider's limits split them. Not checked for either candidate.
- **Where SSH is allowed from** — anywhere, or Brian's addresses. Tighter is
  better until a home IP changes; the escape hatch (Linode's Lish console,
  Lightsail's browser SSH) is provider-specific, which is why this waits.
- **Port 80** — the proxy publishes it as well as 443. Allow it from Cloudflare's
  ranges, or drop it, depending on whether the zone's HTTPS redirect means the
  origin never needs to answer plain HTTP. Either way it cannot be left open.

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

**Rewritten 2026-09-23 for the provider-firewall decision.** The previous list
assumed host rules — `INPUT`, and persistence "by the distribution's own
facility" — which the premise gap above had already made wrong and the decision
made moot.

1. **Move the Cloudflare ranges into a file of their own**, IPv4 and IPv6 both,
   carrying the source URLs and the date last verified, and have
   `apache/conf-enabled/remoteip.conf` read it via `RemoteIPTrustedProxyList`.
   Confirm on the running proxy that the real client address is still recorded
   — task 04's behaviour must be unchanged, with the file as its only source.
2. **A check against Cloudflare's published list** (`/client/v4/ips`, or
   `ips-v4` and `ips-v6`) that fails on any difference, run as a Make target.
3. **A provider-neutral plan**: a Make target printing the rule set the file
   implies — inbound 443 (and 80, per Step 21's decision) from the ranges over
   both families, SSH from its chosen source, everything else refused.
4. **Apply and check targets with the provider seam in place** — the targets
   exist and fail clearly with "no provider configured" until Step 21 writes the
   adapter. The script runs from Brian's machine with a firewall-scoped token;
   nothing on the VM holds it.
5. **The verification procedure**, provider-neutral: from a host outside
   Cloudflare, direct connections to the VM's IPv4 and IPv6 addresses on each web
   port must be refused or time out; the same request through Cloudflare must
   succeed; SSH must still connect. State what a correct refusal looks like.
6. **The emergency-open and re-close procedure**, through the Make targets and,
   as the fallback, the provider's dashboard.
7. **Add apply, verify, emergency-open and re-close to `cutover-runbook.md`**
   under *Host preparation*, with the Step 21 decisions marked as open.

## Dependencies
- Task 04 — its range list becomes the shared file; its behaviour must not change
- **Step 21** — the provider, which the adapter, the SSH source, port 80 and the
  rule-size check all wait on, and a provisioned VM to apply to

## Implementation Approach
1. Extract the range file first and prove Apache still reads it: it is the one
   part of this task that can be exercised end to end today.
2. Build the check and the plan against that file; both run with no provider.
3. Leave the provider seam as a clear failure, not a guess at an API.
4. Write both procedures into the runbook, stating plainly that the firewall
   itself is **unexercised** until Step 21.

## Acceptance Criteria

1. **The range list has one source**
   - Given the range file
   - When Apache's trusted-proxy configuration and the firewall plan are read
   - Then both derive from it, with its verification date recorded in it

2. **Task 04 still works from the file**
   - Given the running proxy with the range file in place
   - When a request arrives through a trusted address with `CF-Connecting-IP`
   - Then the application records the client address, as before the move

3. **Drift from Cloudflare is detectable**
   - Given a range file that differs from Cloudflare's published list
   - When the check target runs
   - Then it fails and names the difference

4. **The plan covers both families and SSH explicitly**
   - Given the plan target's output
   - When it is reviewed
   - Then IPv4 and IPv6 ranges both appear for each web port, and the SSH rule
     is stated rather than incidental

5. **The provider seam fails clearly**
   - Given no provider configured
   - When apply or check runs
   - Then it exits non-zero and says what is missing, touching nothing

6. **The procedures are in the runbook, and the unexercised status is recorded**
   - Given `cutover-runbook.md` and the task record
   - When they are read before cutover
   - Then applying, verifying, emergency-opening and re-closing are each written
     down, and the record states the firewall has never been applied to a host

## Metadata
- **Complexity**: Low
- **Labels**: Firewall, Cloudflare, Security, Cutover, Production Hardening
- **Required Skills**: Apache mod_remoteip, cloud provider firewall APIs, IPv6, Cloudflare architecture
