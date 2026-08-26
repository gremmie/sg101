# Task: Move Inbound Mail from Postfix Virtual Aliases to Cloudflare Email Routing

## Description
Retire the Postfix instance's inbound role by reproducing its live virtual
aliases as Cloudflare Email Routing rules across two domains, and drop the third
domain entirely. This is what allows the Step 21 VM to ship with no MX record, no
inbound port 25, and no mail server to maintain.

**The alias table converts mechanically — there is no hard part in the mapping.**
The schedule risk was entirely in Cloudflare's destination-verification
requirement, which depended on five other people clicking links in their own
inboxes.

**That risk is largely retired as of 2026-08-22.** The prune in requirement 0
ran: 20 aliases became 12 kept plus the new `no_reply@`, and **six destinations
became two** — Brian, who self-verifies, and Ivan, who has already replied. Todd
has not answered, which gates nothing: verification and MX are independent, so
that zone can sit fully staged with mail still flowing through Postfix until he
does (requirement 3a). What remains is dashboard transcription plus one person's
click.

**Applied by hand in the Cloudflare dashboard. No repository code changes.**

## Background

### The source of truth, dumped from production 2026-08-16
`postconf -n` reports `virtual_alias_domains = deathofagremmie.com
themadeira.net surfguitar101.com` and `virtual_alias_maps =
hash:/etc/postfix/virtual_alias_maps`. That table holds 24 entries; 20 belong to
the two domains that still receive mail.

### The mapping is trivial, and this was worth confirming rather than assuming
Three things would have forced a Cloudflare Worker instead of plain rules,
because Email Routing maps **one pattern to exactly one destination**. The dump
was checked for all three:

- **No alias fans out to multiple destinations.** Every entry is one-to-one.
- **No catch-all** (`@domain`) exists on any of the three domains.
- **No alias points at another alias.** Every destination is an external mailbox.

So the whole migration is plain routing rules. **No Worker is required.**

### The real constraint: 6 destinations, 5 of which are other people's inboxes
Cloudflare will not deliver to a destination address until its owner has clicked
a verification link Cloudflare emails them. The 20 aliases collapse to six
distinct destinations:

| Destination | Owner | Aliases served | Outcome of the 2026-08-22 prune |
|---|---|---|---|
| `bgneal@gmail.com` | Brian — self-verify | 10 | **stays**, now serving 10 of the 13 rules |
| `ipongrac@…` | Ivan | 4 (both domains) | **stays**, 3 of 4 kept — the only third party left |
| `creepyrick@…` | Rick | 3 | **gone** — wants none |
| `dane.carter@…` | Dane | 1 | **gone** |
| `todd4ta@…` | Todd | 1 | **deferred** — undecided, requirement 3a |
| `malfunctioncentral@…` | Patrick | 1 | **gone** |

**Five of the six required someone else to act, which was the entire critical
path — and the prune removed four of them.** What follows is the reasoning that
made the prune worth doing first; it is now history, kept because it is why the
critical path is one person instead of five. A migration that is twenty minutes of dashboard work becomes a week or
more of chasing bandmates, and any destination still unverified when MX flips
means mail to its aliases is refused.

One efficiency worth knowing: **destination verification is per Cloudflare
account, not per zone.** `surfguitar101.com` and `themadeira.net` share
nameservers (`ada`/`cash.ns.cloudflare.com`), so they are the same account, and
`ipongrac@…` — which appears under both domains — is verified once and serves
both. Six verifications total, not twenty.

### `deathofagremmie.com` is dead and does not migrate
It has **no MX record at all**, so it already receives nothing; its four Postfix
aliases have been inert for however long that has been true. Brian confirmed the
domain is stale and unused. It also sits on a **different Cloudflare account** —
nameservers `danica`/`ganz`, against `ada`/`cash` for the other two — so
migrating it would mean a second round of verification for no benefit.

Two loose ends it leaves, both outside this task:
- `myhostname = jaguar.deathofagremmie.com` made this dead domain the Postfix
  HELO identity, which was part of the authentication problem recorded in task 03.
  **Resolved for outbound mail 2026-08-17** by setting `smtp_helo_name =
  mail.surfguitar101.com`; `myhostname` itself was deliberately left alone,
  because `mydestination` holds literals rather than `$myhostname` and changing it
  would disturb local delivery. So the dead domain still appears in `myhostname`,
  `mydestination` and the `smtpd_banner` for *inbound* connections — harmless, and
  it disappears with the box.
- `gremmie@deathofagremmie.com` is a personal-handle address. Dropping mail is
  not the same decision as dropping the domain registration; Brian may want to
  keep the name even with no mail on it.

### `/etc/aliases` is a different mechanism and must not be migrated here
`root`, `brian`, `www-data` → `bgneal@gmail.com`, and `postmaster: root`, are
**local system aliases**: cron output, logrotate, unattended-upgrades. Email
Routing handles mail arriving from the internet and never sees them. They are
reproduced on the new VM by the send-only null client (`msmtp` or Postfix in
satellite mode), not by Cloudflare. Confusing the two is how system mail ends up
silently discarded.

### `no_reply@surfguitar101.com` is absent from the table — replies bounce today
There is no `no_reply@` alias and no catch-all, so Postfix currently rejects mail
to that address with "User unknown in virtual alias table." Since `no_reply@` is
the `From` on contact-form, private-message, flag and email-a-friend mail
(`core/functions.py:85,95` and four other sites), **every member who hits reply
on one of those notifications currently receives a bounce.** That has always been
true and is not a regression, but the migration is the natural moment to decide
it deliberately rather than inherit it.

Recommendation: route `no_reply@` to `bgneal@gmail.com`, optionally behind a
filter. A silently-accepted-and-discarded address is defensible; an address that
bounces the people your own site told to expect mail from it is worse than
either.

### Plus-addressing may not survive
Postfix has `recipient_delimiter = +`, so `brian+anything@` currently resolves.
Cloudflare Email Routing matches rules on the literal address. If any
plus-addressed forms are in real use, test one before cutover; the fallback is a
catch-all rule.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `step16/task-03-dns-email-authentication.code-task.md` — the MX change and the
  SPF/DKIM/DMARC work this coordinates with
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 16; Step 20's Cloudflare front; Step 21's cutover)
- Cloudflare Email Routing limits: 200 verified destinations per account,
  25 MiB max message size, one pattern per rule

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

0. **Prune before migrating — Brian's call, 2026-08-16. DONE 2026-08-22**, see
   the prune section below for what was decided; the rest of this requirement is
   kept because it is the reasoning that made it worth doing first.

   He believed several aliases were no longer used and would confirm with their
   owners. **Do this
   first**, because it is the one action that shortens the critical path:
   every third-party destination that turns out to be dead is one fewer person
   whose click the cutover waits on. The rules cost nothing to create, so the
   saving is entirely in verification.

   Note the leverage is uneven. Dropping `dane@`, `todd@` or `patrick@` removes
   a whole destination each — one fewer person. Dropping any one of
   `hellbenders@`, `meltdowns@` or `volcanos@` saves nothing on its own, since
   all three route to Rick; **only dropping all three removes him from the
   list.** Same for Ivan's four addresses across the two domains. Ask about
   destinations, not addresses.

   The same conversation is the moment to ask whether each person still wants
   the forwarding at all — a band address nobody has read in five years is
   better retired than migrated.

1. **Verify a zone's destinations before touching that zone's MX record.** This
   is the ordering that makes the cutover safe: while Postfix still holds MX,
   mail keeps flowing normally and verification failures cost nothing.

   **Per zone, not across both** (clarified 2026-08-22). MX is a per-domain
   record, so `surfguitar101.com` needs only its own destination — Brian's —
   verified before its flip, and does not wait on `themadeira.net`. After the
   prune that is the difference between one domain being blocked and both.

### THE PRUNE IS DONE — decided 2026-08-22, and it collapsed the critical path

Requirement 0 has been executed. Brian asked all five destination owners; four
answered. **Six destinations became two**, so the only third party left to wait
on is Ivan, who has already replied.

| Owner | Answer | Effect |
|---|---|---|
| Rick | wants none of them | `hellbenders@` `meltdowns@` `volcanos@` dropped — **destination gone** |
| Ivan | keep all but `madeira@surfguitar101.com` | that one dropped; his other three kept — **destination stays** |
| Dane | drop | `dane@` dropped — **destination gone** |
| Patrick | drop | `patrick@` dropped — **destination gone** |
| Todd | no answer yet | **undecided, requirement 3a** — costs nothing, since this zone's MX moves only when Brian says so |

Brian's own calls, needing nobody: **`store@surfguitar101.com` dropped**,
**`brian@themadeira.net` dropped**, `admin@themadeira.net` kept.

`store@` was checked rather than assumed: `/store/` is an "Editor's Choice"
recommendations page whose every item links out to Amazon, John Blair's site or
reverbjunkiesfilm.com. **The site sells nothing itself, there is no order flow,
and the page publishes no address at all.** No reference to `store@` exists
anywhere in the repository outside this file.

**21 rules become 13. Six destinations become two** (three until Todd resolves).

2. **Create these rules on `surfguitar101.com`** (was 11, now 6):

   | Address | Destination | Why it survives |
   |---|---|---|
   | `postmaster@` | `bgneal@gmail.com` | RFC 2142; requirement 4 |
   | `abuse@` | `bgneal@gmail.com` | RFC 2142; requirement 4 |
   | `admin@` | `bgneal@gmail.com` | `DEFAULT_FROM_EMAIL` **and** `SERVER_EMAIL` (`settings/base.py:236,244`) — the From on every site email and on Django's error mail. Also published as a mailto in `potd/view.html:53` |
   | `no_reply@` | `bgneal@gmail.com` | **new** — `GPP_NO_REPLY_EMAIL`, the From on PM, contact-form and flag notifications. Bounces today |
   | `podcast@` | `bgneal@gmail.com` | published as a mailto in `podcast/base.html:27` |
   | `brian@` | `bgneal@gmail.com` | Brian's own |

   **Dropped:** `store@`, `hellbenders@`, `meltdowns@`, `volcanos@`, `madeira@`.

3. **Create these rules on `themadeira.net`** (was 10, now 7):

   | Address | Destination | Why it survives |
   |---|---|---|
   | `postmaster@` | `bgneal@gmail.com` | RFC 2142; requirement 4 |
   | `abuse@` | `bgneal@gmail.com` | RFC 2142; requirement 4 |
   | `admin@` | `bgneal@gmail.com` | Brian's call 2026-08-22 |
   | `madeira@` | `ipongrac@…` | Ivan keeps |
   | `themadeira@` | `ipongrac@…` | Ivan keeps |
   | `ivan@` | `ipongrac@…` | Ivan keeps |
   | `todd@` | `member35@example.com`, unverified | **settled 2026-08-23 — see 3a.** Todd wants it kept at this new address; needs its own verification click |

   **Dropped:** `brian@`, `dane@`, `patrick@`.

3a. **`todd@themadeira.net` — SETTLED 2026-08-23. Todd wants it kept, moved to
   `member35@example.com`.**

   **None of the three options below is what happened.** They all presuppose
   continued silence; he broke it. The rule stays, pointed at a *new* address.

   Two consequences. **This is a new destination, not a re-point** — the Gmail
   address is unverified and needs its own click, so Phase 2 waits on two
   third-party verifications (Ivan's and Todd's) rather than one. And **the
   privacy objection that killed the holding pen is retired**: Todd has said
   where he wants his mail to go, which is the consent the pen would have
   manufactured. Neither verification gates anything until MX moves.

   *The original requirement is kept below, because its reasoning about
   verification and MX being independent is what made waiting free — and that
   reasoning still governs Phase 2.*

3a-original. **`todd@themadeira.net` — UNDECIDED, and deferrable at no cost.**

   **Verifying a destination and changing MX are independent actions**, and
   realising that is what makes this easy (2026-08-22). Verification is a click
   in the destination owner's inbox recording their consent; it publishes no
   DNS, routes no mail, touches Postfix not at all, and never expires. So Ivan
   verifying does **not** oblige anyone to flip `themadeira.net`. The zone can
   sit fully staged — Email Routing enabled, Ivan verified, all seven rules
   created — with MX still pointing at jaguar and every message still arriving
   exactly as it does today, for as long as anyone likes.

   **Therefore the default is simply to wait for Todd**, and it costs nothing
   but patience. The only real deadline is Step 21's cutover, several steps out.

   The three options, for the moment this actually becomes live — which is only
   if Ivan verifies, Todd is still silent, *and* something forces a date:

   - **Wait.** Keep the rule pointed at `todd4ta@…` and leave MX alone. Nothing
     breaks; Postfix keeps receiving. **This is the default.**
   - **Drop `todd@`.** Mail to it bounces, so his correspondents find out and
     reach him another way — the same answer Rick, Dane and Patrick chose, and
     arguably more respectful of his mail than forwarding it.
   - **Holding pen:** point `todd@` at `bgneal@gmail.com`, an already-verified
     destination, and forward by hand until Todd surfaces. **Brian is uneasy
     about this and the objection is sound** — people writing to `todd@` are
     writing to Todd, and he never agreed to Brian reading it. Reserve it for a
     genuine deadline.

   **What must not happen in any case: flipping MX while his destination is
   unverified.** Cloudflare accepts the rule and then silently discards, which
   is worse than bouncing and worse than waiting.

   *(Superseded 2026-08-22: this requirement previously recommended the holding
   pen outright, on the reasoning that Todd would otherwise block everything on
   one person. That reasoning was wrong twice — `themadeira.net` is gated on
   Ivan regardless, so the pen removed no blocker; and it traded away someone
   else's mail privacy to solve a scheduling problem that does not exist.)*

3b. **The eight dropped addresses will bounce, not vanish.** That is the correct
   behaviour — a sender writing to `dane@themadeira.net` finds out rather than
   being ignored — but it is a hard failure at the far end. **If any of those
   band addresses were ever published, tell Rick, Dane and Patrick** so a bounce
   to one of their contacts is not a surprise.

4. **Keep `postmaster@` and `abuse@` on both live domains.** RFC 2142 expects
   them, receivers and registrars check them, and they are the channel by which
   a deliverability problem gets reported to you. Do not prune them as unused.

5. **Do not migrate `deathofagremmie.com`.** Remove it from
   `virtual_alias_domains` when Postfix is decommissioned; make the
   keep-or-release decision on the registration separately.

6. **Coordinate the MX change with task 03.** Enabling Email Routing replaces the
   current MX target with Cloudflare's own MX records. Do this as its own change,
   separable from the outbound Postmark work, so either can be rolled back alone.

   **Updated 2026-08-17 — the MX target is no longer `_dc-mx.<hash>`.** Task 03's
   requirement 11 grey-clouded `mail.surfguitar101.com`, and Cloudflare stopped
   substituting its generated alias: the authoritative answer is now
   `10 mail.surfguitar101.com` → `173.255.245.115`. Same destination, real
   hostname. The rollback value to write down before flipping MX is therefore
   `10 mail.surfguitar101.com`, not the `_dc-mx` name. See task 03, Finding 8.

   **The two zones have different rollback values — measured 2026-08-23, and
   this is the first time `themadeira.net`'s was read.** Every `_dc-mx` note in
   these documents describes `surfguitar101.com`'s hash; the other zone was
   never queried. At `ada.ns.cloudflare.com`:

   ```
   surfguitar101.com   MX  10 mail.surfguitar101.com              -> 173.255.245.115
   themadeira.net      MX  10 _dc-mx.658032ac2d3a.themadeira.net  -> 173.255.245.115
   ```

   `themadeira.net` still carries the generated alias **because
   `mail.themadeira.net` is still proxied** — it answers `104.21.71.48` /
   `172.67.169.122`, Cloudflare's shared proxy addresses. That is exactly the
   mechanism task 03's Finding 8 identified and removed on the other zone by
   grey-clouding `mail.`; it was never done here, so the substitution is still
   in effect. Both zones deliver to the same box today, so nothing is broken —
   but **the value to write down before flipping Phase 2's MX is
   `10 _dc-mx.658032ac2d3a.themadeira.net`**, and copying Phase 1's rollback
   value onto this zone would restore a record that was never its MX.

   *Grey-clouding `mail.themadeira.net` to make the two zones symmetric is
   deliberately **not** proposed. Phase 3 removes this zone's MX entirely, so
   the alias disappears on its own; changing a live MX target's proxy state to
   tidy a record that is about to be deleted is risk with no return.*

   **CONFIRMED 2026-08-23 — the bundle is five records, all-or-nothing, and one
   of them breaks outbound mail.** The Settings page's **Add missing records**
   button offers three MX records, a `cf2024-1._domainkey` TXT, and
   `v=spf1 include:_spf.mx.cloudflare.net ~all` **at the apex** — a second
   `v=spf1` string alongside the existing record, i.e. a `permerror` at every
   receiver (task 03, Finding 4). There is no per-record control. Add the three
   MX records by hand instead.

   **And the panel keeps reporting them missing afterward.** Cloudflare tracks
   records it created itself by ID, so hand-made records read as absent even when
   the values match exactly — pressing the button later would add *duplicate* MX
   records. The display is cosmetic; verify with `dig`, not with the dashboard.

   **Do not let a wizard bundle this.** Cloudflare's email tooling offers to
   update MX as part of other flows — the DMARC Management setup on 2026-08-17
   was checked specifically for this. Publishing Email Routing's MX before the
   six destinations are verified would drop mail to unverified destinations,
   which is the one change in this step that breaks something real.

7. **Reproduce `/etc/aliases` on the new VM as null-client configuration**, not
   as Email Routing rules. **And rewrite the sender as well as the recipients**
   (added 2026-08-18): system mail leaves as `root@<hostname>`, which Postmark
   refuses because it is not a verified sender signature. A `sender_canonical`
   map onto `@surfguitar101.com` is required for any of this mail to be
   accepted — the same fix task 10 applied to the old host, where the identical
   defect had been silently destroying Django's error reports.

   **Verify by making a cron job fail**, not by reading the configuration. A
   null client that discards mail looks exactly like a server with nothing to
   say, which is how the old box lost every root message for years.

8. **Keep Postfix running and able to receive until the new path is verified
   end-to-end.** MX has a TTL and senders cache; mail will arrive at the old box
   for a while after the flip regardless.

## Dependencies
- Both live domains already use Cloudflare DNS — confirmed 2026-08-16 — so no
  nameserver migration is needed. Email Routing is a dashboard toggle.
- Third-party destination verification (requirement 1) gates everything else.
- Independent of the outbound Postmark tasks; sequence them separately.

## Implementation Approach

### The two domains are independent, and after the prune only one of them waits

Each domain is its own Cloudflare zone with its own MX record, so migrating one
touches nothing about the other. **What the prune changed is that
`surfguitar101.com` now has no third-party destination at all**: all six of its
surviving rules point at `bgneal@gmail.com`, because Ivan's
`madeira@surfguitar101.com` was the only external address on it and he is the
one who asked to drop it.

So the domain carrying `admin@`, `no_reply@`, `postmaster@` and the site's whole
mail identity **can be migrated start to finish by Brian alone, today, waiting
on nobody.** Only `themadeira.net` needs Ivan.

Do `surfguitar101.com` first. Besides being unblocked, it is the better
rehearsal: every address on it is Brian's to test by mailing it and watching it
arrive, and any surprise is his to fix immediately rather than discovered on
someone else's mail.

**The constraint is *within* a domain, not between them.** MX is per-zone, so
enabling Email Routing on `themadeira.net` replaces that zone's MX wholesale —
there is no arrangement where `ivan@` is served by Cloudflare while `todd@` is
still served by Postfix. That domain moves as a unit — which is why `todd@` has
to be settled before its MX changes, and why requirement 3a exists.

**But the unit does not have to move at all until Brian says so.** Verification
and MX are independent, so this zone can sit fully staged and verified with mail
still arriving through Postfix indefinitely. Ivan verifying starts no clock.

### Phase 1 — `surfguitar101.com` — ✅ DONE 2026-08-23

**Executed as written, with two additions the steps below did not anticipate.**
Full account in `STATUS.md`. In brief: the **Add missing records** button offered
five records with no per-record control, one of them a second apex `v=spf1`
string, so the three MX records were added by hand. Reading a delivered message
then exposed two deliverability defects — `cf2024-1._domainkey` unpublished
(Cloudflare signs forwarded mail as your domain, and the missing selector made it
`permerror`), and the apex SPF not authorizing Cloudflare's forwarder. **The
second one corrects a claim made in planning**: Cloudflare's SRS rewrite lands in
`@surfguitar101.com`, so Email Routing *does* need your SPF authorization. Both
fixed; a forwarded message now passes DKIM, SPF and DMARC.

**Also learned: Cloudflare's Email Routing DKIM key is shared across customer
zones** — same key as `cf2024-1._domainkey.cloudflare-email.net`, published on a
hypothesis and then confirmed by a test send rather than assumed.


1. Enable Email Routing on the zone, but **do not let it publish MX yet**; see
   requirement 6 on wizards that offer to bundle the change.
2. Add `bgneal@gmail.com` as a destination and verify it — Brian's own inbox,
   so this is immediate.
3. Create all six rules (requirement 2).
4. **Write down the rollback value before touching MX: `10
   mail.surfguitar101.com`.** Not the `_dc-mx` name, which task 03 superseded on
   2026-08-17.
5. Publish Cloudflare's MX as its own deliberate step.
6. Test all six addresses end-to-end from an external mailbox. Every one lands
   in the same inbox, so this is six sends and six checks with nobody to chase.

### Phase 2 — `themadeira.net` — ✅ MX FLIPPED 2026-08-25, 6 of 7 confirmed

**Ivan verified 2026-08-25, the last gate.** All three destinations verified, the
seven rules created, MX flipped, six addresses confirmed end-to-end from an
external mailbox. `todd@` awaits Todd's reply — an outstanding confirmation, not
an observed fault. Full account in the planning `STATUS.md`.

**Two things the steps below did not anticipate.** Cloudflare assigned MX
priorities of **3, 46 and 17**, and 3 beats the `_dc-mx` record's 10 — publishing
it as assigned would have cut mail over on the spot, defeating the
additions-before-deletion ordering. Published `route1` at **15** instead, which
preserves Cloudflare's ranking of its own three hosts. And **`_dc-mx` is not a
record in the panel**: `mail.themadeira.net` is proxied, so Cloudflare substitutes
a generated alias, and the panel row reads `MX 10 → mail.themadeira.net`. The
rollback value recorded in step 11 was therefore the *published* form and could
not have been re-created as written — measured after the deletion, the `_dc-mx`
name stops resolving entirely once its source record is gone. **The rollback is
`MX 10 → mail.themadeira.net`**, and the `mail.` A record was left in place so it
stays one record away.

*Original steps below, kept because their reasoning about verification and MX
being independent is what made the wait free.*

7. Enable Email Routing on the zone, MX still unpublished.
8. Add `ipongrac@…` as a destination and send Ivan the verification request with
   a short note explaining what the click is for. **Ivan and Todd are the only
   two people this task still waits on, and neither of them blocks
   `surfguitar101.com`.**
9. **CORRECTED 2026-08-23 — rules to an unverified destination cannot be
   created.** This step used to read *"Rules to an unverified destination can
   exist; they simply do not deliver yet."* **The dashboard refuses**: attempted
   on this zone, only the three rules targeting the already-verified
   `bgneal@gmail.com` could be created. `madeira@` `themadeira@` `ivan@` `todd@`
   were all blocked.

   **So verification gates rule creation, not merely delivery, and the
   "fully staged and parked" state this plan describes is not reachable.** The
   zone can hold Email Routing enabled plus Brian's three rules; the other four
   wait on Ivan's and Todd's clicks.

   *Consequence for flip day: it is no longer a single MX change. It is create
   four rules, verify them, then change MX — more steps, on the day when the
   temptation to hurry is highest.*

   *Consequence for requirement 3a: its central hazard — "flipping MX with a
   destination unverified, which makes Cloudflare accept the rule and then
   silently discard" — appears unreachable through the dashboard, since the rule
   cannot exist in the first place. Not proven for the API, and a destination
   that becomes unverified after its rule exists is untested. Treat the warning
   as still standing, but not as the live risk it was written to be.*
10. **Stop here until Ivan and Todd have verified** — then create the remaining
    four rules. Neither click obliges a flip, and staged-but-unflipped costs
    nothing: Postfix keeps receiving exactly as it does today.
11. ~~When Ivan has verified **and** `todd@` is resolved, **write down this
    zone's own rollback value — `10 _dc-mx.658032ac2d3a.themadeira.net`, not
    Phase 1's (requirement 6)** — then publish MX on this zone and test all
    seven addresses.~~ **DONE 2026-08-25**, with the rollback value corrected to
    its panel form `MX 10 → mail.themadeira.net` — see the Phase 2 header above.
    Six of seven addresses confirmed; `todd@` outstanding.

### Phase 3 — teardown, after both

12. Leave Postfix receiving for at least a week past each flip. MX has a TTL and
    senders cache, so mail keeps arriving at the old box regardless.
13. Decommission Postfix's inbound role; drop `deathofagremmie.com` from the
    config.

## Acceptance Criteria
- **Given** the Cloudflare account destination list
  **Then** every destination a zone's rules point at shows as verified before
  that zone's MX record is changed. *(Reworded 2026-08-22: this said "all six
  addresses ... before any MX record is changed". The prune left two
  destinations, and verification gates each zone separately —
  `surfguitar101.com` needs only Brian's, which is why it can go first.)*
- **Given** each of the 13 migrated aliases — 12 kept from the Postfix table
  plus the new `no_reply@`
  **When** a message is sent to it from an external mailbox after cutover
  **Then** it arrives at the destination the Postfix table specified — tested
  per address, not sampled. `todd@themadeira.net` is whatever requirement 3a
  settled it to be, and **`themadeira.net`'s MX is not flipped until it is
  settled.**
  *(Was "each of the 20 migrated aliases"; eight were dropped 2026-08-22.)*
- **Given** each of the eight dropped aliases
  **Then** a message to it is refused rather than silently accepted — the
  senders who still use them should find out
- **Given** `dig +short MX surfguitar101.com` and the same for `themadeira.net`
  **Then** both return Cloudflare's Email Routing MX hosts, and neither still
  points at the Linode box — for `surfguitar101.com` that means the pre-cutover
  answer `10 mail.surfguitar101.com` is gone. *(Reworded 2026-08-17: this
  criterion named the `_dc-mx.<hash>` record, which stopped being the MX target
  when `mail.` was unproxied — see requirement 6.)*
- **Given** a reply sent to `no_reply@surfguitar101.com`
  **Then** it is delivered rather than bounced
- **Given** a cron job on the new VM **made to fail**, rather than one merely
  configured to send
  **Then** its output reaches `bgneal@gmail.com` via the null client, with no MX
  record and no listening SMTP port on the VM — *a null client that discards
  silently is indistinguishable from a quiet server, which is how the old host
  lost every root message for years*
- **Given** that same message
  **Then** Postmark accepted it, i.e. its From address was rewritten onto a
  verified domain rather than left as `root@<hostname>`, which Postmark refuses
- **Given** `deathofagremmie.com`
  **Then** it has no Email Routing configuration and no aliases, and its absence
  breaks nothing. **Confirmed 2026-08-18: Brian no longer owns this domain.**
  The old box still lists it in `virtual_alias_domains` and carries four
  forwards for it in `virtual_alias_maps` (`postmaster@`, `abuse@`, `gremmie@`,
  `brian@`). None of that may be migrated — it would forward mail for a domain
  someone else controls.
- **Given** a plus-addressed form of any alias in real use
  **Then** its behaviour has been tested and either works or has a documented
  fallback

## Metadata
- **Complexity**: Low technically; Medium in coordination — the critical path
  runs through five other people's inboxes
- **Labels**: Email, Inbound, Cloudflare Email Routing, Postfix, DNS, Migration, Step 16
- **Required Skills**: Cloudflare Email Routing, Postfix virtual alias semantics,
  MX cutover sequencing, distinguishing virtual aliases from local `/etc/aliases`
- **Source data**: `/etc/postfix/virtual_alias_maps` and `postconf -n`, dumped
  from production 2026-08-16
