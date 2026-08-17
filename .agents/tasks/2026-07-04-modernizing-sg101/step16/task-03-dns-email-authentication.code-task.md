# Task: Email Authentication DNS — Audit Findings and Remediation

## Description
Bring `surfguitar101.com`'s email authentication records to a state that a
transactional provider can sign for and that Microsoft will trust. **The audit
half of this task is already done** — it ran on 2026-08-16 against the
authoritative nameservers and its findings are recorded below, so this task
begins at remediation rather than investigation.

The audit was prompted by a suspicion that the domain carried two conflicting
TXT records. **It does not.** It carries something worse: no DMARC record at
all, and a DKIM key half the size current practice expects.

**These changes are made by hand in the Cloudflare dashboard, not by code.**
This task file specifies the exact record values and the verification commands;
applying them is Brian's to run. Nothing here touches the repository except this
document.

## Background

### The audit — measured 2026-08-16
Every value below was read from the authoritative nameserver
(`ada.ns.cloudflare.com`) rather than a resolver cache, so none of it is a
stale-cache artifact.

| Record | Current value |
|---|---|
| Apex `TXT` | `v=spf1 a mx ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 -all` — **exactly one record** |
| `_dmarc` `TXT` | **absent** |
| `dkim._domainkey` `TXT` | `v=DKIM1; p=MIGfMA0…` — valid, **RSA 1024-bit** |
| Apex `MX` | `10 _dc-mx.1431890da307.surfguitar101.com` → `173.255.245.115` |
| Apex `A` | `104.21.53.213`, `172.67.218.217` (Cloudflare proxied) |
| `mail` `A` | `104.21.53.213`, `172.67.218.217` (Cloudflare proxied) |
| `NS` | `ada.ns.cloudflare.com`, `cash.ns.cloudflare.com` |

### Finding 1 — there is no DMARC record. This is the headline.
`_dmarc.surfguitar101.com` returns nothing from the authoritative nameserver.
The belief that SPF/DKIM/DMARC were all configured was two-thirds right: SPF and
DKIM are present and syntactically fine. DMARC was never published.

Two consequences, and the second explains years of confusion:

1. Receivers have no stated policy to apply, so an unauthenticated message
   claiming to be from the domain gets each receiver's default handling rather
   than an instruction from the domain owner.
2. **There has never been any reporting.** DMARC's `rua` aggregate reports are
   the only mechanism that tells a sender *which* receivers are rejecting *which*
   mail and why. Without it, the Microsoft rejections were unobservable from this
   side — which is precisely why the problem has resisted diagnosis for years.
   Publishing DMARC is worth doing for the telemetry alone, before it is worth
   doing for the policy.

Note that Microsoft's May 2025 authentication mandate binds senders above
5,000 messages/day and does **not** apply here — measured volume is ~37/day.
The absence of DMARC is a real defect, but it should not be sold to ourselves as
the sole root cause of the Microsoft rejections. Shared-IP reputation remains
the likelier primary cause, and is what moving to a provider addresses.

### Finding 2 — the DKIM key is 1024-bit
Verified by decoding the published `p=` value:

```
$ dig +short TXT dkim._domainkey.surfguitar101.com | ... | openssl rsa -pubin -noout -text
Public-Key: (1024 bit)
```

1024-bit RSA is below what major receivers now expect; 2048 is the current
norm. This resolves itself for free during the provider move — Postmark issues
2048-bit keys — but the old selector must not be removed while the existing
Postfix instance is still signing with it.

### Finding 3 — the SPF `a` mechanism now authorizes Cloudflare's proxy IPs
When this record was written, `a` meant "the web server, which is also the mail
server." The apex is now Cloudflare-proxied, so `a` resolves to
`104.21.53.213` and `172.67.218.217` — Cloudflare's shared proxy addresses,
which belong to no single customer.

In practice this is inert: Cloudflare's HTTP proxy does not emit mail, so no
message will ever be authorized by it. It is nonetheless wrong, it is a
mechanism nobody intended, and it costs one of SPF's ten permitted DNS lookups.
Remove it.

`mx` is likewise redundant today — it resolves to `173.255.245.115`, the same
address the explicit `ip4:` term already covers. It becomes actively wrong the
moment inbound mail moves to Cloudflare Email Routing, at which point `mx`
would authorize Cloudflare's *inbound* MX hosts to send outbound as this
domain. Remove it too.

### Finding 4 — the record count suspicion was unfounded, and why it looked true
There is one TXT record at the apex. The two TXT records that exist are the SPF
at the apex and the DKIM at `dkim._domainkey` — two records at two different
names, which is correct and required. The failure mode worth guarding against
is two records *at the same name*: a domain with two apex `v=spf1` strings is a
`permerror` at every receiver, which fails harder than publishing no SPF at all.
That is not the situation here, and the acceptance criteria below re-assert it
after the edits so a second record cannot be introduced by accident.

### Finding 5 — reverse DNS does not forward-confirm, and Cloudflare's proxy is why
**This is the likeliest primary cause of the Microsoft rejections.** Measured
2026-08-16:

```
PTR for 173.255.245.115           →  surfguitar101.com
forward lookup surfguitar101.com  →  104.21.53.213, 172.67.218.217  (Cloudflare)
```

The pair does not match. Forward-confirmed reverse DNS — resolve the connecting
IP's PTR, then resolve that name forward and require the original IP back — is
checked by essentially every large receiver, and weighted heavily by Microsoft.
This fails on every message the server sends.

**It used to pass.** Before the site went behind Cloudflare's proxy,
`surfguitar101.com` resolved to `173.255.245.115` and the pair confirmed. Making
the apex A record proxied — a change to *web* hosting, with no apparent
connection to mail — silently broke it. Nothing logs this, no bounce names it,
and the two events are far enough apart in time to defeat correlation. That is
why years of re-checking SPF and DKIM syntax found nothing: the records were
never the problem.

### Finding 6 — the HELO hostname does not resolve to the sending host either
`myhostname = jaguar.deathofagremmie.com`, and `smtpd_banner = $myhostname`, so
that is the name the server greets with. It resolves to `104.21.11.151` /
`172.67.166.93` — Cloudflare proxy addresses, not `173.255.245.115`. The domain
carrying the mail server's own identity has **no MX record and no SPF record**,
and Brian has confirmed it is otherwise stale and unused.

So the greeting name and the PTR name are both wrong, in the same way, for the
same underlying reason.

### Finding 7 — DKIM **is** signing and passing. An earlier claim here was wrong.
This section previously asserted that `smtpd_milters = inet:localhost:88888`
meant the milter was unreachable and mail was going out unsigned. **A real
message header disproved it.** Captured from a contact-form notification
delivered 2026-08-12:

```
DKIM-Signature: v=1; a=rsa-sha256; c=simple/simple; d=surfguitar101.com; s=dkim;
Authentication-Results: mx.google.com;
    dkim=pass header.i=@surfguitar101.com header.s=dkim header.b=CnijwesJ;
    spf=pass (…designates 173.255.245.115 as permitted sender)
```

Signing works, the signature validates, and it is aligned to
`surfguitar101.com`. The 1024-bit key of Finding 2 is in active use, not dormant.

**Why the impossible port works — hypothesis, not yet verified.** 88888 exceeds
the 16-bit port space, but `88888 − 65536 = 23352`. If Postfix and OpenDKIM both
parse the value and truncate it the same way, both land on 23352 and connect to
each other successfully. The configuration is wrong in a way that is
self-consistent on both sides, which is why it has worked for years. Confirm
with `ss -lntp | grep 23352` and the `Socket` line in `opendkim.conf` if it
matters — but it does not matter for this step, since the milter is being
decommissioned either way.

**The methodological point, recorded because it cost a correction across three
documents:** the config value was measured; the consequence was *inferred* from
it and written up as a finding. Inferring "therefore unsigned" from "therefore
unreachable" skipped the one cheap observation — a message header — that settles
it directly. The uncertainty was flagged in the original text, which is why the
error was caught, but flagging an inference does not make it a measurement.

### What Findings 5–7 mean together
With DKIM eliminated, every message leaving `173.255.245.115` presents this way:

| Check | Result |
|---|---|
| Forward-confirmed reverse DNS | **fails** (Finding 5) |
| HELO hostname resolves to sender | **fails** (Finding 6) |
| DMARC policy published | **absent** (Finding 1) |
| DKIM | passes, but on a 1024-bit key with `simple/simple` canonicalization |
| SPF | passes |

**This narrows the diagnosis rather than weakening it.** The same captured header
independently corroborates two other findings:

- Gmail wrote `Received: from jaguar.deathofagremmie.com ([173.255.245.115])` —
  with an **empty parenthetical where the reverse-DNS name belongs**. Gmail
  renders `from HELO (ptr-name [ip])` when it can confirm reverse DNS. It could
  not. That is Finding 5 observed from the receiving side.
- `Authentication-Results` carries `dkim=` and `spf=` but **no `dmarc=` clause
  at all**, because there is no policy to evaluate. That is Finding 1 observed
  from the receiving side.

So the surviving explanation for the Microsoft-specific rejections is the
FCrDNS/HELO pair plus the missing DMARC — and the split between receivers now
makes sense. **Gmail accepted this message without complaint**, because Gmail
weights SPF and DKIM heavily and both pass. Microsoft weights connecting-IP
reputation and reverse DNS far more heavily, and that is precisely where this
server fails. A domain that passes at Gmail and fails at Outlook is the expected
signature of an FCrDNS problem, not a contradiction of one.

### Finding 7a — two smaller defects visible in the same header
- **`c=simple/simple` canonicalization.** The strictest option: any whitespace or
  header rewriting in transit invalidates the signature. `relaxed/relaxed`
  tolerates the small rewrites that forwarders and list servers routinely make.
  Not a live failure here, but unnecessary fragility. Moot after the move —
  Postmark signs with its own policy.
- **`Message-ID: <…@jaguar.deathofagremmie.com>`.** The Message-ID is stamped
  with the dead domain rather than `surfguitar101.com` — a third place the stale
  hostname leaks, after HELO and PTR. Some filters check Message-ID domain
  plausibility. Resolved by requirement 11's `myhostname` change, or by the move.
- `Date:` carries a `-0000` offset (meaning "local offset unknown") while the
  `Received` header shows `-0500`. Valid, occasionally penalized, cosmetic.

**None of Findings 5–7 survive the move.** Postmark owns the sending IP, its PTR,
the HELO, the canonicalization and the signing key, and aligns DKIM to
`surfguitar101.com`. They generate no remediation work here beyond the optional
interim relief in requirement 11.

### Finding 8 — inbound mail currently bypasses the proxy, by design
`_dc-mx.1431890da307.surfguitar101.com` is a Cloudflare-generated unproxied
hostname that lets MX reach the Linode origin while the apex A record stays
proxied. It is not a misconfiguration. It is the record that gets replaced when
inbound cuts over to Email Routing.

`mail.surfguitar101.com` resolving to proxy IPs is a leftover: it cannot serve
as an SMTP hostname in that state. Harmless, worth cleaning up.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 16's guidance; Step 20's Cloudflare front; Step 21's cutover)
- Postmark, "How do I verify a domain?" — the DKIM selector and Return-Path CNAME
- Postmark's free DMARC monitoring service, for the `rua` destination

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Publish DMARC first, in monitor mode, before any other change.** Standing up
   reporting before the migration means the migration itself is observable.
   ```
   _dmarc.surfguitar101.com  TXT  "v=DMARC1; p=none; rua=mailto:<report-address>; fo=1"
   ```
   `p=none` changes no receiver behavior; it only requests reports. The `rua`
   destination must be a mailbox that actually receives — Cloudflare Email
   Routing can forward it, or point it at a DMARC report analyzer. Postmark
   operates a free one, which is the low-effort choice given the provider
   decision.

2. **Let at least one full reporting cycle elapse at `p=none`** (aggregate
   reports arrive daily) before tightening policy. Reading one week of reports
   costs a week and is the only way to learn what is currently sending as this
   domain.

3. **Add Postmark's DKIM and Return-Path records** using the selector Postmark
   assigns in its dashboard. Do not copy a selector from any guide, including
   this one. The Return-Path `CNAME` to `pm.mtasv.net` is optional for delivery
   but wanted here: it gives SPF alignment in addition to DKIM alignment, and it
   is how Postmark collects bounces.

4. **Do not remove the existing `dkim` selector until Postfix stops signing.**
   Both selectors coexisting is normal and correct during a migration; a message
   carries the selector that signed it. Removing the old one early breaks
   verification for mail already in flight.

5. **Rewrite the SPF record in two stages.** During the transition, while
   Postfix still sends:
   ```
   v=spf1 ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 include:spf.mtasv.net ~all
   ```
   After cutover, when nothing but Postmark sends:
   ```
   v=spf1 include:spf.mtasv.net -all
   ```
   Both drop `a` and `mx` per Finding 3.

6. **Soften to `~all` for the duration of the cutover, then restore `-all`.** The
   current `-all` is a hard fail: a wrong record does not degrade, it bounces
   registration confirmations outright. `~all` makes a mistake during the window
   recoverable and observable via the DMARC reports from requirement 1. Restore
   `-all` once reports show clean authentication. **Do not leave it at `~all`.**

7. **Note that Postmark passes SPF without the include.** Per Postmark's own
   documentation, mail sent through them evaluates SPF against their
   Return-Path domain, so the `include:spf.mtasv.net` term is not strictly
   required. It becomes load-bearing only once requirement 3's custom
   Return-Path CNAME is in place. Adding it is harmless either way; knowing why
   it is there prevents it being removed later as apparent clutter.

8. **Defer the MX change to the inbound-routing task.** Moving MX to Cloudflare
   Email Routing changes where mail is *received* and is independent of who
   sends. Keep the two migrations separable so either can be rolled back alone.

9. **Keep TTLs low through the window.** The apex TXT is currently at 300s,
   which is right. Do not let a longer TTL be set on any record being changed
   until the change has been verified.

10. **Remove or unproxy the stale `mail` A record** — or repurpose it per
    requirement 11, which needs exactly that name.

11. **Optional interim relief, only if cutover is more than ~2 weeks out.**
    Findings 5 and 6 are fixable in about ten minutes and would improve
    deliverability immediately, while the provider migration proceeds:
    - Create `mail.surfguitar101.com` as an **unproxied** (grey-cloud) A record
      pointing at `173.255.245.115`.
    - Set the Linode reverse-DNS entry for `173.255.245.115` to
      `mail.surfguitar101.com`, so the PTR now forward-confirms.
    - Set Postfix `myhostname = mail.surfguitar101.com` so HELO agrees, and
      check `/etc/mailname` and `mydestination` for consequences.

    **Skip this entirely if cutover is imminent** — it is throwaway work on
    infrastructure being retired, and touching the live mail server carries its
    own risk. Judgement call, not a requirement.

12. **Do not touch the milter.** Per Finding 7 it is working — signing and
    validating — despite an out-of-range port that both sides evidently
    truncate identically. Changing it can only break a working signer on a
    server being decommissioned.

## Dependencies
- Postmark account created and the domain added, so the assigned DKIM selector
  and Return-Path target are known (requirement 3).
- A working destination for DMARC aggregate reports (requirement 1).
- Independent of the code tasks in this step; can proceed in parallel. The
  reporting cycle in requirement 2 is the long pole, so **start this task first**.

## Implementation Approach
1. Publish the DMARC record at `p=none` with a working `rua`. Stop.
2. Wait for aggregate reports to begin arriving; read a week of them.
3. Create the Postmark domain; add its DKIM TXT and Return-Path CNAME.
4. Rewrite SPF to the transition form, softened to `~all`.
5. Verify every record with the commands in the acceptance criteria.
6. Cut sending over to Postmark (separate task); confirm via DMARC reports and
   Postmark's own delivery logs.
7. Rewrite SPF to the post-cutover form and restore `-all`.
8. Retire the old `dkim` selector once Postfix is confirmed silent.
9. Escalate DMARC `p=none` → `p=quarantine` → `p=reject`, one step at a time,
   reading reports between each.

## Acceptance Criteria
- **Given** the authoritative nameserver is queried for `_dmarc.surfguitar101.com`
  **When** `dig +short TXT _dmarc.surfguitar101.com @ada.ns.cloudflare.com` runs
  **Then** exactly one record returns, beginning `v=DMARC1;`, with a reachable
  `rua` destination
- **Given** the apex is queried for TXT records
  **When** `dig +noall +answer TXT surfguitar101.com @ada.ns.cloudflare.com` runs
  **Then** exactly one `v=spf1` string is present — never two
- **Given** the rewritten SPF record
  **Then** it contains neither the `a` nor the `mx` mechanism, and stays within
  ten DNS-resolving terms
- **Given** the Postmark dashboard after DNS propagation
  **Then** the domain shows DKIM verified and Return-Path verified
- **Given** the new DKIM key is decoded with `openssl rsa -pubin -noout -text`
  **Then** it reports 2048 bits, not 1024
- **Given** a test message sent through Postmark to a Gmail address
  **When** the received headers are inspected
  **Then** `Authentication-Results` shows `spf=pass`, `dkim=pass`, and
  `dmarc=pass`, with the DKIM `d=` aligned to `surfguitar101.com`
- **Given** one week of DMARC aggregate reports after cutover
  **Then** no legitimate sending source is failing authentication, and only then
  is `-all` restored and policy escalated past `p=none`
- **Given** the old Postfix instance has been confirmed to have stopped sending
  **Then** the legacy `dkim` selector is removed, and not before

## Metadata
- **Complexity**: Medium — individually simple records, but ordered, with a
  mandatory waiting period and a rollback story
- **Labels**: DNS, Email, SPF, DKIM, DMARC, Deliverability, Cloudflare, Postmark, Step 16
- **Required Skills**: SPF/DKIM/DMARC semantics, DMARC aggregate report reading,
  Cloudflare DNS, `dig` against authoritative nameservers
- **Audit performed**: 2026-08-16, against `ada.ns.cloudflare.com`
