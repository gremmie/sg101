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

## Status — partially executed 2026-08-17

| Requirement | State |
|---|---|
| 1 — publish DMARC at `p=none` with working `rua` | **done**, verified |
| 2 — wait one reporting cycle | **done** — week ran 2026-08-17 → 08-24, closed by the ninth reading 2026-08-25 |
| 3 — Postmark DKIM + Return-Path | **done**, verified, green in Postmark |
| 5, 6 — SPF rewrite and `~all` | not started; belongs with the task 02 cutover |
| 10, 11 — stale `mail` record, interim FCrDNS relief | **done**; PTR propagated later the same day and the full chain forward-confirms — **Findings 5 and 6 closed** |
| 12 — leave the milter alone | honoured |

**Four records now live** on `surfguitar101.com`: `mail` A (unproxied),
`20260817033844pm._domainkey` TXT, `pm-bounces` CNAME (unproxied), `_dmarc` TXT.
The apex SPF and the legacy `dkim` selector are deliberately unchanged.

**Findings 1, 5 and 6 are confirmed closed from the receiving side** by a
delivered Outlook message, 2026-08-17 — `dmarc=pass action=none` (the first this
domain has produced), `compauth=pass reason=100`, `helo=mail.surfguitar101.com`,
and `dest:I`. Full capture and its limits in
`research/email-header-captures.md`.

**Requirement 2 is satisfied as of 2026-08-25.** The week of aggregate reports
was read across nine sittings, recorded in the planning `STATUS.md` as the first
through ninth readings. Result: **four reporting organizations, eight receiving
domains, one sending source (`173.255.245.115`), and zero messages aligned on
neither mechanism in any window from any reporter.** The one DKIM anomaly, in the
seventh reading, did not recur across the five windows since. Requirement 2 asked
what is currently sending as this domain; the answer is jaguar and nothing else.

**Open before this task can close:** requirements 5–7 at cutover.

**Corrected 2026-08-25, hours after it was written.** This paragraph called
requirement 5 an *ordering requirement* — the claim that under `p=quarantine` a
first Postmark send made before `include:spf.mtasv.net` lands would ride on DKIM
alone. **That is wrong, and requirement 3 in this very document says why.**
Postmark's custom Return-Path is live: `pm-bounces.surfguitar101.com` is a CNAME
to `pm.mtasv.net`, which publishes `v=spf1 include:spf.mtasv.net -all`. SPF is
evaluated against the **envelope sender**, so a Postmark send is checked against
`pm-bounces.surfguitar101.com`, not the apex — it passes there, and
`pm-bounces.surfguitar101.com` is relaxed-aligned with `surfguitar101.com` under
`aspf=r`. **The apex include is not what authorizes Postmark. The CNAME is, and
it has been live and green since 2026-08-17.**

So requirement 5's apex include is defensive rather than load-bearing: it costs
one DNS lookup of the ten available (both includes are flat — `_spf.mx.cloudflare.net`
and `spf.mtasv.net` expand to bare `ip4`/`ip6` with no nesting, so the record uses
2 of 10 with it added) and it covers the case where the Return-Path is later
disabled. Worth publishing. Not a gate on anything.

**This is the fourth occurrence in this document of the failure it already names**
— *"DNS and mail configuration are unusually easy to reason about confidently and
get wrong, because almost nothing in the system reports a disagreement."* The
eighth reading reasoned it, the ninth reading repeated it, and this file recorded
it as a reclassification. None of the three read requirement 3, four hundred lines
below, which had it right on 2026-08-17. [[search-the-artifacts-before-claiming-new]]

**The measurement that settles it, and it has not been taken:** send one Postmark
test message and read `Authentication-Results` at the receiver. If
`smtp.mailfrom=pm-bounces.surfguitar101.com` then the above is confirmed from the
receiving side. If `smtp.mailfrom=pm.mtasv.net` then the Return-Path is not in
effect despite being green, SPF is unaligned, and DKIM alone does carry the
message — the original concern, arrived at for a different reason. **Take the
header before tightening policy, not after.**

The PTR was confirmed at the authoritative nameservers on 2026-08-17 and the
chain forward-confirms. **Postmark account approved 2026-08-17**, so live sending
is no longer gated by account state.

**What the clean week does not cover.** Every observation in all nine readings is
the legacy `dkim` selector on jaguar's IP — the path being retired. The Postmark
selector `20260817033844pm` has appeared in no auth result in any window. These
reports are evidence that task 10's repairs worked; they are no evidence about
Postmark, and the first window after cutover needs reading with the same
attention as the first window ever did.

**Three claims in this document were corrected on 2026-08-17** — Findings 2, 7a
and 8, each marked in place. All three were inferences recorded as findings; none
had been measured. Finding 7a has since been **confirmed by capture**, which is
the intended end state: flag the inference, then go and measure it. That is the
third occurrence of the same failure in this one document, so it is worth naming
as a property of the work rather than a run of bad luck: **DNS and mail
configuration are unusually easy to reason about confidently and get wrong,
because almost nothing in the system reports a disagreement.**

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
5,000 messages/day and does **not** apply here — measured volume is ~30/day
(re-measured 2026-08-17; the margin is three orders of magnitude either way).
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
norm. The old selector must not be removed while the existing Postfix instance
is still signing with it.

**CORRECTED 2026-08-17 — this does *not* resolve itself on the move.** The
paragraph above used to end "This resolves itself for free during the provider
move — Postmark issues 2048-bit keys." **Postmark issued a 1024-bit key.**
Measured from the key it published for `surfguitar101.com`:

```
$ printf -- '-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----\n' "$p" \
    | openssl rsa -pubin -noout -text | head -1
Public-Key: (1024 bit)
```

216 base64 characters, DER header `30 81 9f`. A 2048-bit key is 392 characters
and opens `MIIBIjAN`. The new selector is exactly the same strength as the old
one.

**Not a blocker and not on the critical path.** 1024-bit RSA still validates
everywhere and meets Google's and Yahoo's published minimums — it is below
current norms, not below current requirements — and key strength was never
implicated in the Microsoft rejections, which are Findings 5, 6 and 1. Worth
asking Postmark whether a 2048-bit rotation is offered; not worth blocking on.

*One incidental benefit: at 224 characters the whole TXT value fits in a single
DNS string, so it needs no splitting. A 2048-bit key exceeds the 255-byte limit
and must be published as two quoted strings, which is its own source of error.*

*The process failure is the familiar one — a vendor's behaviour was assumed,
then recorded as fact in three places, none of them measured. Same shape as the
milter inference in Finding 7, and it survived longer because nothing about it
looked like a guess.*

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
  plausibility.

  **CORRECTED 2026-08-17, then CONFIRMED by capture the same day.** This bullet
  used to end "Resolved by requirement 11's `myhostname` change, or by the move."
  **Both are false.** Django stamps its own `Message-ID` in
  `EmailMessage.message()` from `DNS_NAME` = `socket.getfqdn()` on the
  **application** host — not Postfix's `myhostname`, and not anything the SMTP
  provider controls. The header therefore survives both the interim fix and the
  Postmark migration; closing it needs the app host's FQDN changed or a
  Django-side override.

  **Established by format, not by value** — see
  `research/email-header-captures.md`, capture 2. A delivered Outlook message
  shows `<20260817235321.1920.52741@jaguar.deathofagremmie.com>`, which is
  `YYYYMMDDHHMMSS.pid.randrange(100000)` — the signature of Python 2.7's
  `email.utils.make_msgid()`. **Postfix's Message-ID would embed its queue ID**,
  and that queue ID appears elsewhere in the same message (`with ESMTP id
  0F0BD586565`) but not in the Message-ID.

  *The value alone would have proved nothing: `myhostname` was deliberately left
  as `jaguar.deathofagremmie.com`, so both hypotheses predicted that domain would
  still appear. A probe both hypotheses predict is not a probe.* Cosmetic either
  way — a plausibility signal, not an authentication check.
- `Date:` carries a `-0000` offset (meaning "local offset unknown") while the
  `Received` header shows `-0500`. Valid, occasionally penalized, cosmetic.

**None of Findings 5–7 survive the move.** Postmark owns the sending IP, its PTR,
the HELO, the canonicalization and the signing key, and aligns DKIM to
`surfguitar101.com`. They generate no remediation work here beyond the optional
interim relief in requirement 11.

### Finding 8 — inbound mail currently bypasses the proxy, by design
`_dc-mx.1431890da307.surfguitar101.com` is a Cloudflare-generated unproxied
hostname that lets MX reach the Linode origin. It is not a misconfiguration. It
is the record that gets replaced when inbound cuts over to Email Routing.

`mail.surfguitar101.com` resolving to proxy IPs is a leftover: it cannot serve
as an SMTP hostname in that state. Harmless, worth cleaning up.

**CORRECTED 2026-08-17 — the trigger was the MX *target* being proxied, not the
apex, and the record dissolved itself when that was fixed.** This section
originally said the alias existed "while the apex A record stays proxied." The
zone's MX row has always pointed at `mail.surfguitar101.com`; because *that*
name was orange-clouded, Cloudflare could not serve it as an MX target and
substituted the generated `_dc-mx` alias in its answers. Grey-clouding `mail.`
under requirement 11 removed the need for the indirection, and the authoritative
MX answer changed on its own within the hour:

```
before:  10 _dc-mx.1431890da307.surfguitar101.com.   → 173.255.245.115
after:   10 mail.surfguitar101.com.                  → 173.255.245.115
```

**Nothing was edited to make that happen and inbound mail is unaffected** — both
names resolve to the same Linode box, and `_dc-mx` still resolves as well. The
zone's MX row still reads `mail.surfguitar101.com`, confirmed in the panel. The
change is an improvement: MX, HELO and PTR now converge on one real, unproxied
hostname, which is the configuration a receiver expects.

**Consequence for task 06:** its requirement 6 and its acceptance criterion both
speak of replacing "the `_dc-mx.<hash>` record." That record is no longer what MX
resolves to, so those need rewording — see the note added there.

*Worth keeping as a pattern: a generated workaround record is evidence that
something upstream is misconfigured. Reading it as "by design" was half right —
it was Cloudflare's design, compensating for a proxy setting that should not have
been on a mail hostname.*

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 16's guidance; Step 20's Cloudflare front; Step 21's cutover)
- Postmark, "How do I verify a domain?" — the DKIM selector and Return-Path CNAME
- Cloudflare **DMARC Management** (zone → Email), for the `rua` destination.
  *Postmark's own DMARC service was the original pick here; it has been spun out
  as `dmarcdigests.com` and is no longer free — see requirement 1.*

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Publish DMARC first, in monitor mode, before any other change.** Standing up
   reporting before the migration means the migration itself is observable.
   ```
   _dmarc.surfguitar101.com  TXT  "v=DMARC1; p=none; rua=mailto:<report-address>; fo=1"
   ```
   `p=none` changes no receiver behavior; it only requests reports.

   **DONE 2026-08-17.** Published via **Cloudflare DMARC Management** (zone →
   Email), which generates the record and parses the XML into a dashboard, free:
   ```
   v=DMARC1; p=none; rua=mailto:00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net
   ```
   Verified authoritatively: exactly one record at `_dmarc`, TTL 300. **The
   reporting cycle in requirement 2 starts from this date.**

   **The `rua` destination is not a free choice, which this requirement did not
   say.** RFC 7489 §7.1: when `rua` names a mailbox outside the policy domain's
   own organizational domain, receivers must first look up
   `<policy-domain>._report._dmarc.<rua-domain>` and send only if it publishes a
   `v=DMARC1` record. So the obvious fallback — point `rua` at a personal Gmail —
   is **not reliable**: Google publishes no such authorization for arbitrary
   senders, and a strict receiver drops the reports silently. Reports vanishing
   without a trace is the precise failure this requirement exists to prevent.
   Three destinations do work:
   - an analyzer service, which publishes the authorization record for its
     customers (Cloudflare's does; this is what was used);
   - any address **on `surfguitar101.com` itself** — same organizational domain,
     so no authorization lookup happens at all;
   - both, comma-separated, if a self-owned backup channel is wanted.

   **Postmark's free DMARC service no longer exists as such.** The in-app "Set up
   DMARC" button now opens `dmarcdigests.com`, a separate product: 14-day trial,
   then **$14/month per domain**. Rejected — it nearly doubles this step's running
   cost ($15 Postmark + $14) for a reporting UI on a domain sending ~30/day, and
   Cloudflare's built-in tool is free and already authoritative for the zone. If
   the richer analysis is ever wanted, start that trial **at cutover**, not
   before, so its 14 days cover the window where the reports actually matter.

2. **Let at least one full reporting cycle elapse at `p=none`** (aggregate
   reports arrive daily) before tightening policy. Reading one week of reports
   costs a week and is the only way to learn what is currently sending as this
   domain.

   **DONE 2026-08-25.** Clock started 2026-08-17 and the mandatory week was up
   2026-08-24. Nine readings, recorded in the planning `STATUS.md`: four
   reporting organizations, eight receiving domains, one sending source, zero
   messages aligned on neither mechanism. Two facts worth carrying forward from
   the week rather than from this record: **windows gain reports and never revise
   them** — Microsoft files exactly one window late, observed on 08-21, 08-22 and
   08-23, so any window's newest count is a floor — and **Yahoo files one report
   per receiving domain**, which is why a count of reports overstates
   organizations and understates receivers.

3. **Add Postmark's DKIM and Return-Path records** using the selector Postmark
   assigns in its dashboard. Do not copy a selector from any guide, including
   this one. The Return-Path `CNAME` to `pm.mtasv.net` is optional for delivery
   but wanted here: it gives SPF alignment in addition to DKIM alignment, and it
   is how Postmark collects bounces.

   **DONE 2026-08-17.** Selector `20260817033844pm._domainkey` (TXT) and
   `pm-bounces` (CNAME → `pm.mtasv.net`). Both verified authoritatively, both
   green in Postmark on the second attempt — Postmark briefly caches a failed
   lookup, so one retry is expected and is not a sign of a bad record.

   **The CNAME must be grey-clouded.** Cloudflare defaults new CNAMEs to proxied,
   and a proxied Return-Path resolves to Cloudflare's addresses instead of
   Postmark's; verification then fails without naming the proxy as the cause.
   Confirm by resolving the full chain — `pm-bounces` must reach Postmark's AWS
   addresses (`3.151.x`, `3.13.x`), never `104.21.x`/`172.67.x`. This is the same
   proxy-breaks-mail mechanism as Findings 5, 6 and 8.

   **Watch the two columns.** Postmark's table lists `pm-bounces` under *Hostname*
   and `pm.mtasv.net` under *Add this value*; they are easy to transpose. Entering
   the target as the name creates `pm.mtasv.net.surfguitar101.com`, because
   Cloudflare appends the zone to anything that is not the bare apex — a record
   that resolves fine and verifies never.

4. **Do not remove the existing `dkim` selector until Postfix stops signing.**
   Both selectors coexisting is normal and correct during a migration; a message
   carries the selector that signed it. Removing the old one early breaks
   verification for mail already in flight.

   **There is a third signer this file never listed: `cf2024-1`.** It is not
   new to the project — task 06 has carried it since 2026-08-23, as one of the
   five records in Cloudflare's **Add missing records** bundle and as Phase 1's
   Defect 1 — but this document's selector inventory predates it and said two
   where there are three.
   Cloudflare DKIM-signs the mail it forwards as
   `d=surfguitar101.com; s=cf2024-1`, and
   `cf2024-1._domainkey.surfguitar101.com` resolves to a 2048-bit
   Cloudflare-managed key. So this domain has three selectors in service, not
   two: `dkim` (legacy, 1024-bit, Postfix), `20260817033844pm` (Postmark), and
   `cf2024-1` (Cloudflare, forwarded mail).

   It needs no action here — the record is published on both zones and the key
   is Cloudflare's, shared across customer zones, not ours to rotate or remove.
   It never appears in a DMARC report for this domain because forwarded mail
   carries the *original sender's* `header.from`, so this domain's DMARC is not
   what gets evaluated on it. Task 06 found the selector by reading a delivered
   message on 2026-08-23; a raw message on 08-25 is what showed it actually
   signing.

5. **Rewrite the SPF record in two stages.** During the transition, while
   Postfix still sends:
   ```
   v=spf1 ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 include:spf.mtasv.net include:_spf.mx.cloudflare.net ~all
   ```
   After cutover, when nothing but Postmark sends:
   ```
   v=spf1 include:spf.mtasv.net include:_spf.mx.cloudflare.net -all
   ```
   Both drop `a` and `mx` per Finding 3. Both use **3 of the 10 permitted DNS
   lookups** in the transition form and 2 after cutover: `spf.mtasv.net` and
   `_spf.mx.cloudflare.net` are flat, expanding to bare `ip4`/`ip6` with no
   nesting.

   **Corrected 2026-08-25 — both records above previously omitted
   `include:_spf.mx.cloudflare.net`, and publishing either as written would have
   broken forwarded mail.** Cloudflare Email Routing applies **SRS**: it rewrites
   the envelope sender of every message it forwards into this domain, e.g.
   `SRS0=zJrw=sg=alerts.comcast.net=dmarc-support@surfguitar101.com`. The
   receiver therefore evaluates SPF **against `surfguitar101.com`** for mail this
   domain did not originate, and it passes only because Cloudflare's forwarding
   IP falls inside that include. Measured from a raw message 2026-08-25: Gmail
   returned `spf=pass ... designates 104.30.10.185 as permitted sender` against
   the SRS envelope, and `104.30.10.185` is inside `104.30.0.0/19` from
   `_spf.mx.cloudflare.net`.

   **The blast radius is every forwarding alias** — `admin@`, `abuse@`,
   `postmaster@`, `brian@` — **including the DMARC reports themselves, which
   arrive through `admin@surfguitar101.com`.** Deleting the include would break
   the pipeline that would otherwise report the breakage. Note also that this
   failure needs no policy change to bite: an SPF hard fail on the SRS envelope
   stands on its own, under `p=none` as much as under `p=quarantine`.

   **Why it was missed.** The include was read as belonging to *inbound* mail,
   since Email Routing is a forwarding service, and an inbound feature has no
   business in an outbound policy record. SRS is what makes that wrong: a
   forwarder re-sends under the forwarding domain's name, which makes it an
   outbound sender for this domain. Full derivation in the planning `STATUS.md`,
   tenth reading.

   **This was known and not carried across.** Task 06's Phase 1 account, written
   2026-08-23, states that *"Cloudflare's SRS rewrite lands in
   `@surfguitar101.com`, so Email Routing does need your SPF authorization"*, and
   the live apex record was fixed that day on exactly that basis. Requirement 5
   was never updated to match, so this file spent two days prescribing a record
   that would undo a fix another file had already made. **The defect was not that
   SRS was unknown. It was that two documents disagreed and the executable one
   was wrong.**

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
    requirement 11, which needs exactly that name. **DONE 2026-08-17**, as
    requirement 11's first step.

11. **Interim relief for Findings 5 and 6. TAKEN 2026-08-17** — cutover is more
    than two weeks out (Steps 17–21 all follow this one), so the gate was met.
    - Repoint `mail.surfguitar101.com` to `173.255.245.115` as an **unproxied**
      (grey-cloud) A record. **Done; verified authoritative and at two public
      resolvers.** Side effect: it dissolved the `_dc-mx` alias — Finding 8.
    - Set the Linode reverse-DNS entry for `173.255.245.115` to
      `mail.surfguitar101.com`, so the PTR forward-confirms. **Done; verified.**
      Linode warns propagation takes up to an hour and it took roughly that —
      check at `*.akam.net`, which serves the reverse zone, because the old PTR's
      300s TTL means a resolver answer cannot distinguish "not applied" from
      "cached".
    - Align the outbound HELO. **Done; verified with `postconf`.**

    **Use `smtp_helo_name`, not `myhostname` — corrected 2026-08-17.** This step
    used to read "Set Postfix `myhostname = mail.surfguitar101.com` so HELO
    agrees, and check `/etc/mailname` and `mydestination` for consequences." That
    works but drags in avoidable risk, and the live config shows why:

    ```
    inet_protocols = ipv4
    myhostname     = jaguar.deathofagremmie.com
    mydestination  = jaguar.deathofagremmie.com, localhost.deathofagremmie.com, , localhost
    /etc/mailname  = surfguitar101.com
    ```

    `mydestination` is a list of **literals**, not the usual `$myhostname, …`
    form. Changing `myhostname` would therefore leave the new name absent from
    `mydestination`, and Postfix delivers its own generated mail to
    `double-bounce@$myhostname`; with `mail.surfguitar101.com` now resolving to
    this same box, that produces `loops back to myself`. Repairing it means also
    editing local delivery routing on a server carrying 20 live aliases — real
    exposure, for a fix that is throwaway by design.

    `smtp_helo_name` governs exactly one thing: the name Postfix presents in EHLO
    when connecting **outbound**. That is precisely Finding 6, and nothing else
    moves. One line in `main.cf`, then `postfix reload`:
    ```
    smtp_helo_name = mail.surfguitar101.com
    ```
    Leave `myhostname`, `mydestination` and `/etc/mailname` untouched. (The empty
    element in `mydestination` is an inert leftover; Postfix skips it.)

    **`inet_protocols = ipv4` closes the IPv6 question.** Postfix cannot send over
    IPv6, so one PTR is sufficient — no AAAA on `mail.`, no second reverse-DNS
    entry. This matters because Microsoft effectively requires a valid PTR on the
    v6 path too, and the SPF record's `ip6:` term made it look as though that path
    was in use. It is not, and that term has been inert throughout.

12. **Do not touch the milter.** Per Finding 7 it is working — signing and
    validating — despite an out-of-range port that both sides evidently
    truncate identically. Changing it can only break a working signer on a
    server being decommissioned.

13. **~~Publish SPF at the HELO name, not only at the apex.~~ DONE 2026-08-20** —
    verified at both authoritative nameservers, one SPF record at the name, apex
    untouched, and **delivery-verified at Gmail the same evening** —
    `spf=pass smtp.helo=mail.surfguitar101.com` on a real null-sender message.
    Note for step 9: the pass it produces is *aligned* only because `aspf`
    defaults to relaxed — observed, not assumed, in that same message's
    `dmarc=pass ... header.from=surfguitar101.com` — so tightening `p=` is safe
    but adding `aspf=s` would send this class back to failing. Original text
    follows. Added 2026-08-18
    from the first DMARC reports, which showed 4 of 65 messages failing both
    mechanisms. Requirements 5–7 all describe the apex record, and
    **null-sender mail never consults it**: a bounce has an empty envelope
    sender, so SPF falls back to the HELO identity (RFC 7208 §2.3) — now
    `mail.surfguitar101.com`, which requirement 10 published as an A record
    only. No TXT there means the result is `none`, never `pass`, so a bounce
    has no aligned pass available from SPF. It has none from DKIM either,
    because Postfix does not apply milters to internally generated bounces
    (`internal_mail_filter_classes` is empty by default, confirmed with
    `postconf -d`). Publish:
    ```
    mail.surfguitar101.com.  TXT  "v=spf1 ip4:173.255.245.115 -all"
    ```
    This is the only DMARC-relevant record that is *not* about site mail, which
    is why it was missed: every other requirement here reasons about the mail
    the application sends. **Its lifetime is the old host's** — once inbound
    moves to Cloudflare Email Routing and the new VM keeps no local bounce
    traffic, the record retires with the box that needed it.

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
- ~~**Given** the new DKIM key is decoded with `openssl rsa -pubin -noout -text`
  **Then** it reports 2048 bits, not 1024~~ — **withdrawn 2026-08-17: Postmark
  issued a 1024-bit key, so this criterion can never pass.** See Finding 2. It
  rested on an assumption about the vendor, not a measurement, and it should not
  be carried as an open failure.
- **Given** the PTR for `173.255.245.115` queried at the authoritative
  nameservers for `245.255.173.in-addr.arpa` (Akamai `*.akam.net`, not a resolver
  cache) **Then** it returns `mail.surfguitar101.com`, and that name forward-
  resolves to `173.255.245.115` — forward-confirmed reverse DNS, closing
  Finding 5
- **Given** `postconf smtp_helo_name` on the Linode box
  **Then** it returns `mail.surfguitar101.com`, matching the PTR — closing
  Finding 6
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
- **Partially executed**: 2026-08-17 — see Status above. Findings 2, 7a and 8
  corrected in place the same day.
