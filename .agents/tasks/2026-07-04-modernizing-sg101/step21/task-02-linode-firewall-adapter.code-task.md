# Task: Write the Linode Cloud Firewall Adapter for `tools/origin_firewall.sh`

## Description
Fill in the provider seam in `tools/origin_firewall.sh` for **Linode Cloud
Firewall**, so `make firewall-apply` pushes the plan to Linode and
`make firewall-check` compares Linode's live rules with it. `apply` **replaces
the whole rule set**; it never adds to it. The adapter can be built and
exercised against a real Linode firewall object before the VM exists, and it
should be.

## Background
Step 20 task 07 chose the provider's firewall over rules on the VM (Docker
forwards published ports before the VM's `INPUT` chain sees them), and built
everything except the part that talks to a provider. `provider()` currently
dies with `no provider configured` / `no <action> support for provider`.
Runbook **B6** carries the rest.

**Provider decided 2026-09-24: Linode, 4 GB shared CPU, in a core compute
region** (see `STATUS.md`, Step 21). Brian knows Linode; jaguar and bobcat
already run there.

**Linode's limits, read 2026-09-24 from Akamai's Cloud Firewall docs:** at most
**25 rules per firewall** (inbound and outbound together), **255 addresses or
ranges per rule**, **15 ports or port ranges per rule**, and a Linode attaches
to **one** firewall at a time. So all 22 Cloudflare ranges (15 IPv4, 7 IPv6)
fit in **one** rule for 443, and the whole plan is at most three inbound rules
(443, 80 if `allow`, 22). The question B6 left open — "whether one rule holds
all 22 ranges" — is answered by the docs; confirm it on the real API.

**The replace requirement is load-bearing.** The emergency-open procedure is a
dashboard click that adds a rule; re-closing is `firewall-apply`. Only an apply
that replaces the rule set removes that emergency rule, and `firewall-check`
passing is what proves it did.

**The API, to confirm against Linode's API reference before relying on it:**
`GET` and `PUT /v4/networking/firewalls/{firewallId}/rules`, where the `PUT`
replaces the firewall's inbound and outbound rules and policies with the
request body. A rule is roughly `{"action": "ACCEPT", "protocol": "TCP",
"ports": "443", "addresses": {"ipv4": [...], "ipv6": [...]}, "label": ...}`,
alongside `inbound_policy` and `outbound_policy`. The token needs only the
Firewalls read/write scope.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10 — production hardening & deployment)

**Additional References (if relevant to this task):**
- `.agents/tasks/2026-07-04-modernizing-sg101/step20/task-07-origin-exposure.code-task.md`
  — § *Decided 2026-09-23*, why the provider's firewall
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — § Step 20 task 07,
  the mutation table and the `pipefail` bug
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — B6
- Linode API reference, Cloud Firewall endpoints

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. `FIREWALL_PROVIDER=linode` selects the adapter. It also needs the firewall's
   ID (e.g. `FIREWALL_LINODE_ID`) and a token (e.g. `LINODE_TOKEN`), both from
   the environment. It refuses clearly if either is missing, and never prints
   the token.
2. `apply` builds one request body from the same data `plan` prints — same
   ranges, same port 80 and SSH decisions — and `PUT`s it. Inbound policy
   `DROP`; outbound policy `ACCEPT` with no outbound rules, matching `plan`'s
   "Outbound is not restricted."
3. `check` `GET`s the live rules and compares them with the body `apply` would
   send, **normalized** (address order, and any canonical form Linode applies
   to addresses), then reports `OK` or names what differs, as `ranges-check`
   does. Exit 0 on match, 1 on difference, 2 on error — the convention the
   script already uses.
4. Any HTTP error is a failure with Linode's error message shown: `curl -f` or
   an explicit status check. A refused call must never look like success.
5. Keep the script's existing guarantees: `apply` still refuses while
   `FIREWALL_SSH_FROM` or `FIREWALL_HTTP` is unset, and a malformed ranges line
   still stops everything.
6. The script keeps running only from Brian's machine. Nothing in this task puts
   a token or the script on the VM.
7. Update B6 in `cutover-runbook.md` with the variables Linode needs, and remove
   the "write it" wording.

## Dependencies
- A Linode account token scoped to Firewalls read/write only
- `curl` and `jq` on Brian's machine (`jq` 1.7.1 is present, checked 2026-09-24)
- No VM: a Cloud Firewall can be created on its own, attached to nothing

## Implementation Approach
1. Split building the request body into its own function that prints JSON, so
   it can be checked without the network.
2. Write `apply` and `check` against a base URL that can be overridden, so they
   can be run against a local stub as well as `api.linode.com`.
3. Mutation-test the way task 07 did: for each property, break it and see the
   check fail — drop a range, add a stray one, add an extra rule (the
   emergency-open case), change a port, change the inbound policy.
4. Then, with Brian's token, create a scratch firewall attached to nothing,
   `apply`, `check`, add a rule by hand in the dashboard, and confirm `check`
   reports it and a second `apply` removes it. Delete the scratch firewall
   afterwards, or keep it as the one the VM attaches to in task 03. **If the
   Linode already exists**, its firewall was created with it (inbound drop, SSH
   only — runbook B6) and can be the test subject instead, as long as the SSH
   rule survives every `apply`: set `FIREWALL_SSH_FROM` to match it.

## Acceptance Criteria

1. **Plan and request agree**
   - Given the ranges file and a set of settings
   - When the request body is built
   - Then it holds exactly the ranges and ports `plan` prints for those
     settings: 443 from all 22 ranges, 80 and 22 as decided, inbound policy DROP

2. **Apply replaces rather than adds**
   - Given a live firewall with an extra hand-added rule
   - When `apply` runs
   - Then the extra rule is gone and `check` reports OK

3. **Check detects drift in every direction**
   - Given each mutation: missing range, stray range, extra rule, changed port,
     changed inbound policy
   - When `check` runs against it
   - Then it exits 1 and names the difference, and each mutation was seen to
     fail before being trusted

4. **Errors are failures**
   - Given a bad token or a wrong firewall ID
   - When `apply` or `check` runs
   - Then it exits non-zero with Linode's error, and the token does not appear in
     the output

5. **Existing guards still hold**
   - Given `FIREWALL_SSH_FROM` unset, or a malformed ranges line
   - When `apply` runs
   - Then it refuses before any request is sent

6. **Exercised against the real API**
   - Given a scratch Linode Cloud Firewall attached to nothing
   - When apply, a hand edit, check, and apply again are run
   - Then each result is recorded in `STATUS.md`, including whether one rule held
     all 22 ranges

## Metadata
- **Complexity**: Low
- **Labels**: Firewall, Linode, Cloudflare, Shell, Production Hardening
- **Required Skills**: Bash, REST APIs with curl, jq, mutation testing
