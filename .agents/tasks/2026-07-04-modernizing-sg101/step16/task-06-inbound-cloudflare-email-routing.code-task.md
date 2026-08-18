# Task: Move Inbound Mail from Postfix Virtual Aliases to Cloudflare Email Routing

## Description
Retire the Postfix instance's inbound role by reproducing its 20 live virtual
aliases as Cloudflare Email Routing rules across two domains, and drop the third
domain entirely. This is what allows the Step 21 VM to ship with no MX record, no
inbound port 25, and no mail server to maintain.

**The alias table converts mechanically — there is no hard part in the mapping.**
The schedule risk is entirely in Cloudflare's destination-verification
requirement, which depends on five other people clicking links in their own
inboxes. Plan around that, not around the rules.

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

| Destination | Owner | Aliases served |
|---|---|---|
| `bgneal@gmail.com` | Brian — self-verify | 10 |
| `ipongrac@…` | Ivan | 4 (both domains) |
| `creepyrick@…` | Rick | 3 |
| `dane.carter@…` | Dane | 1 |
| `todd4ta@…` | Todd | 1 |
| `malfunctioncentral@…` | Patrick | 1 |

**Five of the six require someone else to act.** This is the entire critical
path. A migration that is twenty minutes of dashboard work becomes a week or
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

0. **Prune before migrating — Brian's call, 2026-08-16.** He believes several
   aliases are no longer used and will confirm with their owners. **Do this
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

1. **Verify all remaining destinations before touching any MX record.** This
   is the ordering that makes the cutover safe: while Postfix still holds MX,
   mail keeps flowing normally and verification failures cost nothing. Send the
   third-party requests early and treat them as the long pole.

2. **Create these rules on `surfguitar101.com`:**

   | Address | Destination |
   |---|---|
   | `postmaster@` | `bgneal@gmail.com` |
   | `abuse@` | `bgneal@gmail.com` |
   | `admin@` | `bgneal@gmail.com` |
   | `brian@` | `bgneal@gmail.com` |
   | `podcast@` | `bgneal@gmail.com` |
   | `store@` | `bgneal@gmail.com` |
   | `hellbenders@` | `creepyrick@…` |
   | `meltdowns@` | `creepyrick@…` |
   | `volcanos@` | `creepyrick@…` |
   | `madeira@` | `ipongrac@…` |
   | `no_reply@` | `bgneal@gmail.com` — **new**, see background |

3. **Create these rules on `themadeira.net`:**

   | Address | Destination |
   |---|---|
   | `postmaster@` | `bgneal@gmail.com` |
   | `abuse@` | `bgneal@gmail.com` |
   | `admin@` | `bgneal@gmail.com` |
   | `brian@` | `bgneal@gmail.com` |
   | `madeira@` | `ipongrac@…` |
   | `themadeira@` | `ipongrac@…` |
   | `ivan@` | `ipongrac@…` |
   | `dane@` | `dane.carter@…` |
   | `todd@` | `todd4ta@…` |
   | `patrick@` | `malfunctioncentral@…` |

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

   **Do not let a wizard bundle this.** Cloudflare's email tooling offers to
   update MX as part of other flows — the DMARC Management setup on 2026-08-17
   was checked specifically for this. Publishing Email Routing's MX before the
   six destinations are verified would drop mail to unverified destinations,
   which is the one change in this step that breaks something real.

7. **Reproduce `/etc/aliases` on the new VM as null-client configuration**, not
   as Email Routing rules.

8. **Keep Postfix running and able to receive until the new path is verified
   end-to-end.** MX has a TTL and senders cache; mail will arrive at the old box
   for a while after the flip regardless.

## Dependencies
- Both live domains already use Cloudflare DNS — confirmed 2026-08-16 — so no
  nameserver migration is needed. Email Routing is a dashboard toggle.
- Third-party destination verification (requirement 1) gates everything else.
- Independent of the outbound Postmark tasks; sequence them separately.

## Implementation Approach
1. Enable Email Routing on `surfguitar101.com`, but do not let it publish MX yet.
2. Add all six destinations; verify `bgneal@gmail.com` immediately, and send the
   five third-party requests with a short note explaining what the click is for.
3. While waiting, create every routing rule. Rules to unverified destinations can
   exist; they simply do not deliver yet.
4. When all six are verified, publish Cloudflare's MX on `surfguitar101.com`.
5. Test each address end-to-end from an external mailbox before moving on.
6. Repeat for `themadeira.net`.
7. Leave Postfix receiving for at least a week past the flip.
8. Decommission Postfix's inbound role; drop `deathofagremmie.com` from the
   config.

## Acceptance Criteria
- **Given** the Cloudflare account destination list
  **Then** all six addresses show as verified before any MX record is changed
- **Given** each of the 20 migrated aliases plus the new `no_reply@`
  **When** a message is sent to it from an external mailbox after cutover
  **Then** it arrives at the destination the Postfix table specified — tested
  per address, not sampled
- **Given** `dig +short MX surfguitar101.com` and the same for `themadeira.net`
  **Then** both return Cloudflare's Email Routing MX hosts, and neither still
  points at the Linode box — for `surfguitar101.com` that means the pre-cutover
  answer `10 mail.surfguitar101.com` is gone. *(Reworded 2026-08-17: this
  criterion named the `_dc-mx.<hash>` record, which stopped being the MX target
  when `mail.` was unproxied — see requirement 6.)*
- **Given** a reply sent to `no_reply@surfguitar101.com`
  **Then** it is delivered rather than bounced
- **Given** the new VM's cron emitting output to `root`
  **Then** it reaches `bgneal@gmail.com` via the null client, with no MX record
  and no listening SMTP port on the VM
- **Given** `deathofagremmie.com`
  **Then** it has no Email Routing configuration and no aliases, and its absence
  breaks nothing
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
