# Task: fail2ban on the New Host, Banning at Cloudflare's Edge — with an Unban That Works

## Description
Rebuild fail2ban on the VM so bans on the site's auth log are pushed into the
Cloudflare IP list `block_list`, which a WAF rule already drops at the edge.
**Fix the defect that makes jaguar's list grow without limit**, move from the
Global API Key to a narrowly-scoped API token, clear out the entries already
stranded on the list, and prove the whole cycle: a ban appears on the list, and
disappears when it expires.

**Enable it only after runbook B3's real-client-IP check has passed on the VM.**
In the other order it bans Cloudflare.

## Background
**Why it matters.** `STATUS.md` (*IDENTIFIED 2026-08-30 … it is fail2ban*)
dates the edge blocking to 2025-08-10: `mod_remoteip` enabled at 13:47,
`block_list` created at 15:34, the WAF rule `(ip.src in $block_list)` at 15:38.
Spam registrations fell from 14.5/month to ~1.25 and stayed there. **The
registration form is not what holds that floor; this is.** It is host
configuration plus Cloudflare credentials, so nothing in the repo brings it
across. Brian also recalls the wiki drawing much higher load before fail2ban
started banning its abusers.

**jaguar's setup, read 2026-09-24** (fail2ban **0.8.11**, `/etc/fail2ban/jail.local`):

| jail | matches | maxretry / findtime | bantime | action |
|---|---|---|---|---|
| `sg101-auth` | `ERROR (?:Login\|Register) failure from \[<HOST>\]` in `auth.log` | 6 / 600 s | 600 s | cloudflare |
| `sg101-reg` | `CRITICAL Accounts/registration: Honeypot filled \[<HOST>\]` in `auth.log` | 1 / 600 s | 14 days | cloudflare |
| `wiki-abuse` | 403/404/500/503 in the wiki's access log | 6 / 600 s | 5 days | cloudflare |
| `ssh` | stock | stock | 14 days | iptables |
| `postfix` | stock | 1 / 600 s | 14 days | iptables-allports |

Over the ~4 weeks of `fail2ban.log*` on the box: `wiki-abuse` 225 bans / 246
unbans, `sg101-reg` 2 unbans. The two messages still come from the code:
`antispam/decorators.py:29` and `accounts/forms.py:123`.

**Why the list only grows — found 2026-09-24 in `action.d/cloudflare.conf`.**
`actionunban` does look up the item ID before deleting, as the Lists API
requires. But the lookup is a single
`GET …/rules/lists/<list_id>/items` **with no `cursor` and no `per_page`**, and
Cloudflare paginates that endpoint (`per_page` up to 500, `result_info.cursors`
to continue — read from Cloudflare's API docs 2026-09-24). Once the list is
longer than one page, an IP on a later page is not found, the action prints
`id for <ip> cannot be found` and **exits 0**, fail2ban logs the unban as done,
and the entry stays for good. Each stranded entry makes the list longer, which
strands more — so it grows without limit. **Not yet confirmed against the live
list**; comparing its item count with the jails' active bans would confirm it.
Three smaller defects in the same file:
- **No `curl --fail` anywhere.** A 4xx or 5xx from Cloudflare exits 0, so a
  refused ban or unban looks like success.
- **0.8 keeps no ban database and `actionstop` is empty**, so every IP banned at
  the moment of a restart is stranded too.
- **Global API Key** (`X-Auth-Email` + `X-Auth-Key`), which can do anything on
  the account, stored on an end-of-life box. (Its `[Init?family=inet6]` block is
  syntax 0.8 ignores and misspells `cf_target` anyway; harmless.)

**The fix:** look the IP up with the endpoint's `search` parameter (IP lists
match by prefix), select the exact match with `jq`, delete by ID, `--fail` on
every call, and authenticate with an API token scoped to editing the account's
filter lists.

**What carries over, and what does not.** `wiki-abuse` goes: the wiki is
retired. `postfix` goes: nothing on the VM listens for mail (task 04). `ssh`
depends on the firewall's SSH setting from task 03 — if SSH is open to anywhere,
keep a local jail. **A local ban works for `sshd`**, a host process whose
packets pass the VM's `INPUT` chain, and **would not work for the web ports**,
which Docker forwards before `INPUT` — which is why the site's jails ban at
Cloudflare.

**Where the logs are.** Django writes `var/log/django/auth.log` in the checkout
(bind-mounted from the containers) with format
`%(asctime)s %(levelname)s %(message)s`. fail2ban runs on the host and reads it
there. It rotates under task 03's logrotate, so the jail must follow rotation.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10 — production hardening & deployment)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *Cloudflare dated,
  and 35% of the layer measurement had no client IPs*; the fail2ban
  identification from the audit log
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — B3
- Cloudflare API: Lists items (list, create, delete; bulk operation status)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Confirm the leak before building on it:** the live `block_list` item count
   against the active bans across jaguar's Cloudflare jails, and how many items
   carry the `fail2ban` comment and are older than the longest bantime (14
   days). Record the numbers.
2. fail2ban from the distribution's current packages on the VM, with a
   persistent ban database (default since 0.9).
3. A Cloudflare action in the repo (e.g. `fail2ban/action.d/`), alongside the
   jail and filter files, installed onto the host. The token is not in the repo:
   it goes in a root-only file on the host (e.g. under `/etc/fail2ban/`).
4. `actionban` adds `{"ip": "<ip>", "comment": "fail2ban"}` with `--fail`.
   `actionunban` finds the item with `search=<ip>`, matches it exactly, deletes by
   ID, fails loudly if the delete is refused, and handles "not found" in a way
   that is logged rather than silent.
5. Measure how Cloudflare stores an IPv6 address on this list, and make the
   exact match compare against that form, not the form fail2ban holds.
6. The API calls to add and delete are asynchronous bulk operations. Check
   whether two in quick succession conflict, and handle it if they do.
7. Jails: `sg101-auth` and `sg101-reg` with jaguar's thresholds unless Brian
   changes them; `ssh` according to the firewall decision. Filters checked with
   `fail2ban-regex` against real lines from the new host's `auth.log`.
8. The API token can edit the account's filter lists and nothing else.
9. A one-time cleanup of stranded entries: only `fail2ban`-commented items older
   than the longest bantime. **jaguar writes to the same list until it is shut
   down**, so either fix jaguar's `actionunban` the same way (Brian's box; his
   call) or run the cleanup again after shutdown.
10. **Not enabled until B3 passes on the VM.** B3's order is stated in the
    runbook; make this task's record point at it.

## Dependencies
- Task 03 (VM, stack, logrotate) and runbook B3 passed through a test hostname
- Cloudflare account access to create the scoped token
- Brian, for requirement 9's choice and for any threshold change

## Implementation Approach
1. Take the measurements in requirement 1 first.
2. Write the action against the list API and exercise it from Brian's machine
   with a test address from a documentation range (`192.0.2.0/24`,
   `2001:db8::/32`): add, look up, delete, and look up on a later page.
3. Mutation-test the lookup: put the test IP beyond the first page of results
   and check the old action misses it and the new one finds it.
4. Install on the VM, run `fail2ban-regex`, enable after B3, then trigger a
   `sg101-auth` ban from a phone's mobile connection (real IP, not Brian's
   home address), watch the IP appear on the list, and wait out the 600 s ban.
5. Run the cleanup; record before and after counts.

## Acceptance Criteria

1. **The leak is confirmed or ruled out**
   - Given the live list and jaguar's active bans
   - When they are counted
   - Then both numbers, and the count of stranded `fail2ban` entries, are recorded

2. **Ban and unban complete a full cycle**
   - Given a triggered `sg101-auth` ban on the VM
   - When the ban happens and then expires
   - Then the IP appears on `block_list` and is then gone from it, verified
     against the API, not the fail2ban log

3. **Unban finds entries past the first page**
   - Given a list longer than one page and a test IP beyond the first page
   - When the new `actionunban` runs
   - Then the entry is deleted — and the old action, run the same way, was seen
     to miss it

4. **Refused calls are failures**
   - Given a revoked or wrong token
   - When a ban or unban runs
   - Then fail2ban records the action as failed

5. **Least privilege**
   - Given the new token
   - When it attempts anything other than reading and editing account lists
   - Then Cloudflare refuses it; no Global API Key is on the VM

6. **Stranded entries are cleared**
   - Given the cleanup rule (fail2ban-commented, older than 14 days)
   - When it runs
   - Then the before and after counts are recorded, and nothing without the
     `fail2ban` comment was touched

7. **Filters match the new host's lines**
   - Given real `auth.log` lines from the VM
   - When `fail2ban-regex` runs each filter
   - Then the failure lines match and extract the client's address, not a
     Cloudflare or container address

## Metadata
- **Complexity**: Medium
- **Labels**: fail2ban, Cloudflare, WAF, Security, Anti-spam, Operations
- **Required Skills**: fail2ban, Cloudflare API, Bash, jq, regular expressions
