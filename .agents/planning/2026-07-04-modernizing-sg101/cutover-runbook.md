# Cutover runbook — Step 21

**Started 2026-09-06.** Owned by Step 21; **not yet complete**, and it should not
be read as if it were. It exists because items that only matter on cutover day
have been accumulating in four different files since July — `STATUS.md`,
`implementation/plan.md`, `research/schema-drift-audit.md` and
`research/dmarc-readings.md` — and one of them,
`schema-drift-audit.md`, has carried a section headed *"Gotcha for the cutover
runbook"* since Step 11, pointing at a document that did not exist.

**This file holds the action and the pointer, never the reasoning.** Each item
says what to do, what it costs to skip, and where the decision behind it lives.
A claim restated here is a claim that will drift; if an entry starts explaining
itself at length, the explanation belongs in its home document and a link
belongs here.

**Every entry needs a source.** An item nobody can trace to a measurement or a
decision is a guess, and guesses are what a runbook is least able to survive.
Entries below are sourced; anything added later should be too.

---

## A. Before the maintenance window

### A1. Check for networks members picked after the seed list was frozen
`elsewhere`'s seeding keeps any network a profile row points at, so the data is
safe either way — but the retired networks' **icon files were deleted**, and
production serves static through `ManifestStaticFilesStorage`, where a missing
file raises rather than degrading to a broken image. A rescued network therefore
renders its owner's profile as a 500.

Run against production close to the flip. **An empty result means nothing to
do**, which is the expected outcome:

```sql
SELECT network_id, COUNT(*) FROM elsewhere_socialnetworkprofile
 WHERE network_id NOT IN ('facebook','twitter','youtube','myspace','tumblr',
   'linkedin','reddit','lastfm','flickr','foursquare','pandora','goodreads',
   'multiply','github','redbubble') GROUP BY network_id;
SELECT network_id, COUNT(*) FROM elsewhere_instantmessengerprofile
 WHERE network_id NOT IN ('aim','gtalk','msn','skype','y') GROUP BY network_id;
```

If a row comes back, restore that icon from git history before the flip. The
migration also reports it in its own output — see C3 — so this is the early
warning, not the only one.
*Source: `STATUS.md` § Step 19 Phase C task 03.*

### A2. Re-run the production working-copy audit
`fab update` is `hg pull --update`, which preserves uncommitted working-copy
edits across deploys **silently** — production ran one for ~20 months without
anyone knowing. Audited clean 2026-08-16, but production stays live on the old
code until the flip, so the audit is only true as of the day it was run.

**Extended 2026-09-12: audit the Apache configuration on the new host too.** Step
20 puts the proxy config in this repository and delivers it to the container by
**bind mount**, which means the running configuration is whatever is on disk at
that path — the same silent-divergence shape as the working-copy edit above, in a
file that is the site's security boundary. Check it with the same eye, and on the
new host as well as the old one.

**Concretely, since task 03 (2026-09-19):** the proxy reads `apache/` from the
checkout, and a graceful reload picks up whatever is there. `git status apache/
docker-compose.prod.yml` on the VM must be clean. The Apache image carries only
the program and its modules, so nothing about the site's configuration hides in
it.

**Three files in there are the security boundary (task 04, 2026-09-19; task
07, 2026-09-23):** `cloudflare-ranges.txt` is the list of Cloudflare ranges, read
by both Apache and the origin firewall; `conf-enabled/remoteip.conf` makes Apache
believe `CF-Connecting-IP` only from those ranges; and the vhost's `RequestHeader
set X-Real-IP` carries that answer to gunicorn. An edit to any of them silently
changes who the site thinks its visitors are. Run `make cloudflare-ranges-check`
at the same time: it diffs the file against Cloudflare's published lists and
fails on any difference — 15 IPv4 and 7 IPv6 when last verified.
*Source: `STATUS.md`; the original audit is in the Step 15 record; Step 20 tasks
03, 04 and 07.*

### A3. Delete the 32 pending `gcalendar` rows in production, not just locally — DONE
Step 21 converts a **fresh** production snapshot, so rows deleted only in the dev
database come back with it and land in the pending queue on the new host.
**Done by Brian in production**, reported 2026-09-26; the date of the deletion is
not recorded. **Not yet confirmed from data:** task 07's fresh snapshot is the
first place to see it, as a count of pending events in the restored database
(task 07a, requirement 4a). If the count is not zero, this entry reopens.
*Source: `STATUS.md` § the `NEW`/`NEW_APRV` decision, settled 2026-08-31.*

### A4. Move DMARC readings to daily
From ~1 week before the flip to ~2 weeks after. Three open items resolve in that
interval and each needs both halves at the same resolution; a before/after
comparison across a change of cadence is not a comparison.
*Source: `research/dmarc-readings.md`, cadence table.*

### A5. Collect the jaguar-side email baseline
The pre-cutover window is the **only** chance to take it. Postmark's dashboard
gives a total with no category breakdown, and the baseline is what makes a later
discrepancy explainable rather than merely visible.
*Source: `STATUS.md` § Step 16 task 09, "What is still owed".*

## B. Host preparation

### B1. `secrets/gcal/gcal-service-account.json`
Git-ignored as a whole directory and **backed up nowhere**. Without it the
calendar does not come up on the new host, and it cannot be recovered — only
reissued from the Google console.

**In `secrets/gcal/`, not `secrets/`** — that directory alone is mounted into
`web`, and nothing in `secrets/` reaches the image. **Owned by uid 1000, mode
600** (on leopard that is `brian`), because the container runs as uid 1000 and a
file it cannot read fails only when someone presses Synchronize.
`GCAL_CREDENTIALS_PATH=/app/secrets/gcal/gcal-service-account.json` in `.env`.
*Source: `STATUS.md` § Step 18, § Step 21 task 03; memory `modernizing-sg101-planning`.*

### B2. `.env`
The only other un-backed-up artifact. Regenerate from `secrets.json` in the hg
backup if it is ever lost. **It also needs `GUNICORN_WORKERS=5` and
`CELERY_WORKER_CONCURRENCY=2`**, which `secrets.json` never held: the production
compose refuses to start without them. `.env.example` gives the reasoning.

**It is not a copy of the development `.env`.** That file runs on Cloudflare's
public Turnstile test keys, which pass every bot, and has no Postmark token.
Production needs real `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` from a
widget created in the Cloudflare dashboard — **none has been created yet**
(checked 2026-09-26). The widget's hostname list must include
`beta.surfguitar101.com` for task 07a as well as `surfguitar101.com`. It also
needs `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (the Postmark server token, in
both) and the `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USE_TLS` lines `.env.example`
shows commented out.
*Source: memory `modernizing-sg101-planning`; `AGENTS.md`; Step 21 task 03.*

### B3. Real client IP at the new front door
**The rewrite that makes every `REMOTE_ADDR` reader correct exists only as Apache
config on the box being retired.** Without it, on cutover day every IP the site
records silently becomes a proxy address.

**Built and verified locally 2026-09-19 (task 04).** Apache `mod_remoteip`,
`RemoteIPHeader CF-Connecting-IP`, trusted only from Cloudflare's **15 IPv4 and
7 IPv6** ranges, in `apache/conf-enabled/remoteip.conf` reading
`apache/cloudflare-ranges.txt` (the list moved there in task 07 so the firewall
shares it), bind-mounted into the proxy so it travels with the code rather than
living on a host.

**It is two halves, and the second one is easy to forget.** `mod_remoteip` fixes
what *Apache* thinks the client is; the vhost's `RequestHeader set X-Real-IP
"expr=%{REMOTE_ADDR}"` and `core.middleware.RealClientIP` are what carry that to
gunicorn, which is a separate process here and was not on jaguar. Either half
alone leaves the applications recording a constant address.

**Verify against a real request on the VM, and do not skip it.**
`tools/prod_smoke.sh` cannot cover this: every check it makes is from outside,
and what the application recorded is only visible on the host. So:

1. From a browser, through Cloudflare, fail a login on purpose.
2. On the VM, `tail var/log/django/auth.log` — the `Login failure from [...]`
   line must hold **your** address, not a Cloudflare edge address and not the
   proxy container's `172.*`.
3. `tail var/log/apache/access.log` — the same address must lead that line, since
   this is what fail2ban parses.
4. Repeat over IPv6 if the origin publishes an AAAA record.

**Then, and only then, enable fail2ban** (Step 21). In the wrong order it bans
Cloudflare.
*Source: `research/dmarc-readings.md` § "A cutover requirement this exposed";
Step 20 tasks 03 and 04.*

### B4. The media tree
**Nothing has been migrated.** The 4,577 local-disk user photos ride this step's
rsync; the S3 work in Step 15 changed where *new* uploads go, not where the old
ones are.
*Source: `STATUS.md` § Step 15; `implementation/plan.md` Step 21.*

**`media/` is half committed assets and half user uploads, so neither "sync it
all" nor "exclude it" is right.** Measured 2026-09-17 on the `modernize` branch:

| under `media/` | tracked in git | user uploads |
|---|---|---|
| `badges` | **10** | — |
| `smiley` | **87** | — |
| `podcast` | **1** | — |
| `avatars/users`, `banners`, `potd`, `downloads`, `user_photos` | 0 | **all of it** |

`.gitignore` lists `media/badges`, `media/smiley` and the rest, which reads as
though none of it is tracked — but an ignore entry does not apply to files
already tracked, and those 98 are. So:

- **`--exclude=media` loses the uploads.** They exist nowhere else.
- **An unconditional `rsync` of `media/` writes production's copies over tracked
  files.** Almost certainly identical, but it is a working-tree change nobody
  asked for, and on a `--delete` run anything tracked-but-absent on production
  would be deleted locally.

**Sync the upload directories by name rather than syncing `media/` wholesale**,
and check `git status media/` after the transfer — it should be clean.

**One known gap to fix while there:** three `bio.Badge` rows reference files that
were never committed — `badges/map.png` (Map Pin), `badges/bns_badge.png` (Brave
New Surf Pin) and `badges/script.png` (Wiki Pin). They exist on production and
arrive with this rsync, which is the moment to commit them alongside the other
ten so the set stops being partial. They render broken in local development
until then, which is how this was found.
*Source: Step 20 task 02, tracing broken images on a forum topic page.*

### B4a. Own `media/` and `var/` as the container's UID — after the rsync, not before
The application containers run as **uid 1000** (`sg101` in the image). A
container user and a host user are matched by number, not by name, so the host
directories the containers write have to be owned by 1000 or the writes fail.

**This goes after B4**, because B4's rsync sets ownership from what it copies
and would undo it. Same for any later re-sync: re-run this afterwards.

```bash
sudo chown -R 1000:1000 media var
sudo find media var -type d -exec chmod 755 {} +
```

On Debian and Ubuntu, 1000 is the first ordinary account — very likely your own
login — so these stay editable without `sudo` afterwards. Check it before
relying on it: `id -u`. **If the VM's admin account is not 1000**, either use a
UID that is free and build with `--build-arg APP_UID=<n>`, or keep 1000 and
accept that `media/` belongs to whichever account holds it.

**Verify after `docker compose -f docker-compose.prod.yml up -d`:**

```bash
docker compose -f docker-compose.prod.yml exec web id          # uid=1000(sg101)
docker compose -f docker-compose.prod.yml exec web touch /app/media/.probe \
  && docker compose -f docker-compose.prod.yml exec web rm /app/media/.probe
docker compose -f docker-compose.prod.yml exec web python /app/tools/image_smoke.py
```

The last one drives real uploads through the real views on this deployment and
cleans up after itself — 7/7 when the ownership is right. **Take a database
snapshot first**; it creates and deletes a scratch user.

*Source: Step 20 task 12. The UID contract is checked on every CI run, which is
the only Linux this project has until the VM exists — Docker Desktop translates
bind-mount ownership and will accept a configuration the VM rejects.*

### B5. Install the Cloudflare Origin CA certificate
Step 20 terminates TLS at the Apache proxy on a **self-signed certificate**,
which is all the local stack needs. The real origin certificate is a Cloudflare
Origin CA cert — long-lived, no renewal job, and trusted only for proxied traffic,
which is why it pairs with B6. **Issuing and installing it needs the provisioned
VM**, so it happens here and not in Step 20.

**Where it goes:** `secrets/tls/origin.pem` and `secrets/tls/origin.key` in the
checkout, mounted read-only into the proxy. The local self-signed pair uses the
same names, so the vhost does not change between the two. `secrets/` is
git-ignored and **backed up nowhere**, like `.env` and the calendar key.
*Source: Step 20 task 04, the TLS decision; task 03 fixed the paths.*

### B6. Apply the origin firewall — tested against a stand-in, never run on the VM
**The web ports admit only Cloudflare, enforced by the hosting provider's
firewall** (decided 2026-09-23, Step 20 task 07). A firewall on the VM itself
was rejected: Docker forwards a published port to the container before the VM's
own input rules see it, so those rules would look right and filter nothing.

**Treat this as unexercised on the VM.** The ranges file, the plan and the
checks were built in Step 20 task 07. The Linode adapter was built in Step 21
task 02 and tested against a local stand-in for Linode's API
(`make firewall-test`). No rule has been applied to the VM yet.

**Decide these with the provider, before the window** — `firewall-apply`
refuses to run until the first two are set:

| | setting | decide |
|---|---|---|
| SSH source | `FIREWALL_SSH_FROM` | `anywhere`, or your addresses — tighter, but a changed home IP locks you out until the provider's console gets you back in (Linode Lish, Lightsail browser SSH) |
| port 80 | `FIREWALL_HTTP` | `allow` from Cloudflare only, or `drop` — depends on whether the zone's HTTPS redirect means the origin never answers plain HTTP |
| provider | `FIREWALL_PROVIDER` | `linode` |
| firewall | `FIREWALL_LINODE_ID` | the numeric ID in the firewall's dashboard URL |
| token | `LINODE_TOKEN` | a personal access token with **Firewalls read/write and nothing else** |

`apply` replaces the whole rule set (Linode's `PUT …/rules`); re-closing below
depends on that. The token is firewall-scoped and stays on your machine. **Never put it on the
VM**: a token that can edit the VM's firewall, on the VM, lets whoever compromises
it open the firewall.

**The firewall exists from the moment the Linode does** (decided 2026-09-24).
Create it in Linode's create flow: inbound policy drop, one rule allowing TCP 22
(from your address, or anywhere), outbound accept. The VM is then never on the
internet unfiltered, even during first boot. **This is the firewall the script
manages** — its ID is `FIREWALL_LINODE_ID`; don't create a second one.

**Smoke-test through a temporary rule.** `tools/prod_smoke.sh <VM address>`
connects to the origin directly, bypassing Cloudflare, so the drop policy refuses
it. In the dashboard, allow 443 and 80 **from your address only**, run the smoke
(B-section checks, before DNS moves), then apply — `apply` replaces the whole
rule set, so it removes the temporary rule.

**Apply** — from your machine:

1. `make cloudflare-ranges-check` — the file still matches Cloudflare.
2. `make firewall-plan` — read it: 443 from 15 IPv4 and 7 IPv6 ranges, port 80
   and SSH as decided, nothing else inbound.
3. `make firewall-apply`, then `make firewall-check` — the live rules match.

**Verify** — the refusal is the measurement, so check the refusal first:

1. From your machine (outside Cloudflare), directly at the origin, over each
   family and each web port:
   `curl -sk --max-time 10 --resolve surfguitar101.com:443:<VM IPv4> https://surfguitar101.com/robots.txt; echo "exit $?"`
   and again with `[<VM IPv6>]`. **A correct refusal is no HTTP response at
   all** — curl exits 28 (timed out; providers usually drop) or 7 (refused).
   **Any HTTP status, even an error page, means the firewall is not filtering.**
   Repeat on port 80 with `http://` if it was set to `drop` or `allow`.
2. SSH still connects, from where `FIREWALL_SSH_FROM` says it should.
3. After the DNS flip (C5): `curl -sI https://surfguitar101.com/` returns 200
   with a `cf-ray` header — through the edge, the site serves.

**Emergency open** — when cutover-day debugging needs direct access to the
origin: open the provider's dashboard and allow 443 (and 80) from your own
address only, not from anywhere. The dashboard is the fallback because it works
even when your machine's script or token does not. Write down what you changed.

**Re-close:** `make firewall-apply`, then `make firewall-check`. Because `apply`
replaces the whole rule set, it removes the emergency rule along with anything
else not in the plan — and `firewall-check` passing is what proves it did.
Then repeat **Verify** step 1.
*Source: Step 20 task 07 (task file § Decided 2026-09-23); `STATUS.md` § Step 16
task 03 Open register.*

### B7. Choose the backup buckets — and the constraint they must satisfy
**Two buckets, decided 2026-09-22** — dumps and media, because their retention
is opposite (dumps expire at 90 days; media never does). Everything below
applies to both. Provisioning them is B12.

Step 20 task 06 builds the whole backup path against a local S3-compatible
endpoint and **deliberately does not choose a provider**, because nothing in the
path needs one: endpoint, bucket and credentials are configuration.

**The constraint is what this entry exists to carry forward:**

> **The backup target must not share a provider or account with the VM.**

A Linode VM backed up to Linode Object Storage shares a failure domain — one
billing lapse, suspension or account event takes the site and its backups
together. `bobcat` is already a second Linode and its rsync is repointed at the
new VM (see the media and backup entries), so that copy is the warm same-provider
one. **The object storage copy is the one that has to be somewhere else.**

Against a Linode VM, **an AWS S3 bucket satisfies this**, and `boto3` plus the
credentials are already in the project from Step 15. Use a **new bucket**, not
`sg101.user.photos` or `sg101.forum.photos`, and a **write-scoped credential** —
the job puts objects, the lifecycle policy deletes them. **If the VM lands on
Lightsail instead, S3 shares its provider and fails the constraint** — the
bucket then goes elsewhere.
*Source: Step 20 task 06.*

### B12. Provision the backups, and prove the alarm reaches you
The job, the buckets' rules and the restore are built and drilled locally
(`tools/backup_drill.sh`, DOCKER.md *Backups, and restoring from them*). What
cannot be drilled locally is everything with a real account behind it.
`dcp` is DOCKER.md §10's shorthand, `docker compose -f docker-compose.prod.yml`.

1. **Create the buckets** with an administrative credential — creates both,
   turns on versioning, applies `lifecycle-db.json`, and leaves the media bucket
   with no rules at all. Re-running it corrects drift.
   ```bash
   dcp --profile backup build backup
   dcp run --rm -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... \
       -e BACKUP_DB_BUCKET=... -e BACKUP_MEDIA_BUCKET=... backup provision
   ```
   **Confirm Block Public Access is on for both** (the AWS default for new
   buckets since 2023; `provision` does not set it because the local stand-in
   does not support it).
2. **Create the job's IAM user** with `backup/policy-writer.json` as its only
   policy, `@DB_BUCKET@`/`@MEDIA_BUCKET@` replaced. Nothing else — no read, no
   delete.
3. **Create the healthchecks.io check**: period 1 day, grace 2 hours, alerting to
   Gmail. Put its ping URL, the buckets and the job's key in
   `secrets/backup.env` (template: `backup/backup.env.example`).
4. **Run the first backup by hand** — `dcp run --rm backup`. The first media sync
   uploads all ~4.7 GB and will take a while; later ones copy ~10 MB a month.
5. **Prove the alarm, at the receiving end.** Run it once with a wrong database
   password, `dcp run --rm -e PGPASSWORD=wrong backup`, and **see the alert arrive
   in Gmail** — not just the check turning red on the dashboard. This is the
   acceptance test task 06 could not run.
6. **Install the timer**, editing the path in the `.service` as for logrotate:
   ```bash
   sudo cp backup/sg101-backup.service backup/sg101-backup.timer /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now sg101-backup.timer
   systemctl list-timers sg101-backup.timer
   ```
7. **Restore once from the real bucket** into a scratch database (DOCKER.md),
   so the first proof that the real backups restore is not a disaster.

**Also worth a calendar reminder around day 91:** confirm the oldest dumps are
actually gone. Expiry is the one behaviour no local drill can show, because
lifecycle rules count in whole days.

*Source: Step 20 task 06.*

### B10. Install the `logrotate` configuration
Production's log handlers are `WatchedFileHandler`: they never rotate, because a
dozen processes share `var/log/django` and a handler that renames the file it
writes leaves every other process appending to a name that no longer exists.
**Until this is installed, nothing rotates those files at all.**

```bash
sudo cp logrotate/sg101 /etc/logrotate.d/sg101
# The paths assume the checkout is at /svr/sg101; edit them if it is elsewhere.
sudo logrotate --debug /etc/logrotate.d/sg101             # parses, changes nothing
sudo logrotate --force /etc/logrotate.d/sg101             # once, to prove it
```

**Then prove the processes followed it**, which is the whole point and is not
visible from `ls`: after the forced rotation, make the site serve a page and
queue a task, then confirm the new lines are in `sg101.log` and not in
`sg101.log.1`.

```bash
tail -3 var/log/django/sg101.log
```

*Source: Step 20 task 11, where this was exercised against the local stack.*

### B11. Apache's own logs rotate with B10's file — prove it before the flip
**Found during task 11 and deliberately not fixed there.** `var/log/apache/`
is written by the proxy container and nothing rotates it. On jaguar a single
week of `access.log` was **164 MB**, and that host had `logrotate` for it; the
new VM does not.

It is a different problem from the Django files and that is why it was left:
Apache holds its log open and does **not** follow a rename, so rotation needs a
`postrotate` that signals the container —
`docker compose -f docker-compose.prod.yml exec proxy apache2ctl -k graceful` —
or `CustomLog` piped to `rotatelogs` instead of a file, which changes
`apache/sites-enabled/`.

**Decided 2026-09-25 (Brian): logrotate with the graceful `postrotate`**, weekly,
26 kept, compressed. It is a block in the same `logrotate/sg101` that B10
installs, so installing B10 installs this too. Prove it the way B10 proves the
Django half: `sudo logrotate --force /etc/logrotate.d/sg101`, request a page, and
the request's line must be in `var/log/apache/access.log`, not
`access.log.1`. **DNS still must not flip until that has been seen on the VM.**

*Source: Step 20 task 11; Step 21 task 03.*

### B9. Re-verify the `/media` cache rule against the new origin
The Cloudflare cache rule was applied to the zone on 2026-09-20 and verified
serving `HIT` on jaguar, so it arrives at cutover already exercised — the
opposite of B6. What changes at cutover is the *origin*: jaguar sends no cache
headers for `/media` at all, so the rule's fallback branch is what is live today;
the new Apache sends `max-age=31536000` for everything under `/media` and
`max-age=2592000` for `/media/podcast/`, at which point the fallback stops being
reached and the TTLs jump from hours to a year.

The rule's Edge TTL is set to **use the origin's `Cache-Control` when present**,
so the per-category policy lives in `apache/sites-enabled/surfguitar101.com.conf`
and not in the dashboard. That means the TTLs *change* at cutover, from the
rule's fallback to the origin's own values, without the rule being touched.

**Verify after the DNS flip**, twice for the same asset, since the first request
populates the edge:

```bash
curl -sI https://surfguitar101.com/media/podcast/sg101_episode15.m4a | grep -i 'cf-cache-status\|cache-control'
curl -sI https://surfguitar101.com/media/podcast/sg101_episode15.m4a | grep -i 'cf-cache-status\|cache-control'
```

Wanted: `cf-cache-status: HIT` on the second, and `max-age=2592000` from the new
origin. `tools/prod_smoke.sh` checks the origin half of this already; the edge
half needs the real DNS.
*Source: Step 20 task 08.*

### B8. `/hosted` and `/photos` — content from jaguar's document root
Two directories that were **not in the repo and recorded nowhere** until Step 20
task 03 read jaguar's vhost: `Alias /hosted/` and `Alias /photos/` point into
`/svr/www/surfguitar101.com/public/`. Measured 2026-09-19: **`hosted/` 16 MB,
`photos/` 69 MB, 1,509 files together**, and **40 requests** for either in the
access log current that day (window not measured; not split by path or by bot).

The new proxy serves both from `var/public/{hosted,photos}` in the checkout.
**`rsync` both there from jaguar**, then spot-check one file from each through
the site. `var/` is git-ignored, so nothing but this step puts them there.
*Source: `STATUS.md` § Step 20 task 03.*

### B13. Confirm `make` is on the VM
The repo's `Makefile` holds shortcuts for the everyday production commands,
among them `make prod-maint-on`. Minimal server images often leave `make` out,
and nobody has checked this VM's. **If it is missing, the shortcut fails with
"command not found" at exactly the moment it is needed in a hurry.**

```bash
command -v make || sudo apt install make   # or the distribution's equivalent
make                                        # from the checkout: lists the targets
make prod-maint-status                      # reads var/maintenance/, changes nothing
```

If `make` cannot be installed, every target is a command written out in
DOCKER.md, which the `Makefile` only abbreviates.
*Source: the `Makefile` at the repo root.*

## C. The maintenance window

### C0. Freeze writes on jaguar, before the snapshot

**On jaguar**, edit `sg101/apache/sg101.wsgi`, set `OFFLINE = True`, and `touch`
it — mod_wsgi reloads on mtime, which is what `fab touch` already does. The site
then answers **503 for GET and 405 for everything else**, serving
`sg101/templates/offline.html`.

**The 405 is the point, not the notice.** Everything between the final snapshot
(C1) and the final media delta (C5) is a window where a member posting produces
a row that will not be in the restored database, or a file with no row. This
refuses the write rather than losing it.

**It runs on jaguar's own copy**, which is on the `main` branch, under hg, at
`/svr/django-sites/sg101/sg101/`. The `modernize` branch deleted that script as
Python 2.7 host configuration, so the copy in the git tree is gone and the one
that matters is untouched by that deletion.

**The new host is not covered by this.** Its maintenance mechanism is
Cloudflare-side — see the Step 20 record; it needs to be in place before D2's
warm window, not before the flip, because until the DNS flip nothing is pointed
at the new VM anyway.

### C1. Final snapshot → convert → restore
`tools/pgloader/convert.sh` then `tools/pgloader/post_convert.py`, the same chain
verified on every data migration in Step 19.

### C2. The `oembed` migration-history unlock
`forums/0001_initial` has declared `('oembed', '__first__')` since 2015. Now that
oembed has a migration, `check_consistent_history` **refuses every `migrate`
command** on a database carrying the old history. `--fake` cannot get past it —
the check runs first. Record the row directly. Needed unless the converted
database already carries it.
*Source: `research/schema-drift-audit.md` § "Gotcha for the cutover runbook" —
the section this file was named after.*

### C3. `migrate`, and **read the output**
Not merely check the exit code. `elsewhere`'s `0004_seed_networks` logs a warning
naming any retired network it had to keep, and the icon file to restore. That
warning is the A1 check firing late.

### C4. `reindex_search`
The search index is **schema-only in every dump**, so it does not come across
with a restore. `manage.py reindex_search`, then `manage.py reconcile_search` to
confirm.
*Source: `tools/pg_snapshot.sh` restore output; Step 12 record.*

### C4a. Restart the worker and beat, not just the web process
**Celery does not autoreload, and a stale worker fails silently.** Demonstrated
on 2026-09-07 while removing the vendored `tagging` app: the web container picked
the new code up (runserver autoreloads), the worker had been up 18 hours and was
still holding the deleted `tagging/fields.py` in memory, so every
`search.tasks.reindex_document` for a news story raised
`AttributeError: 'list' object has no attribute 'lower'` from a file that no
longer existed on disk. Nothing in the site's own output said so; the trace was
only in `docker compose logs worker`.

The consequence at cutover is worse than a traceback: **a story or post saved
after the flip would not reach the search index**, and `reconcile_search` would
report it as drift days later rather than as a deploy fault.

`docker compose up -d --force-recreate web worker beat`, then save one story and
watch the worker log for `reindex_document ... succeeded`. This applies to any
deploy, not only this one.
*Source: task 06's browser session, Brian spotted it in the worker log.*

### C5. Final media delta, then the DNS flip
**Before the flip, run `tools/prod_smoke.sh <vm-address>` from a checkout.** It
makes every request to the VM's own address under the site's name, so it tests
the new origin while DNS still points at jaguar: the home page over TLS, one
HSTS header, the redirects, the root files, `/media`, the old SG101 1.0 URLs,
and that 8000/5432/6379 are closed. It was written against the local stack;
this is its first run against a real host.

Low-TTL cutover in Cloudflare.

## D. After

### D1. One real message with headers
`dkim=pass d=surfguitar101.com` and `spf=pass`. Task 02's delivery-side criteria
were left unmet **by design** — they cannot be satisfied before there is a
production environment to satisfy them in.
*Source: `STATUS.md` § Step 16 task 02, "What task 02 does not close".*

### D2. Keep jaguar warm
As an sg101 fallback the window ends in 1–2 weeks. Decommissioning used to gate
on the separate jaguar project (`~/workspaces/bgn/jaguar-decommission/`) as
well; **Brian closed that project 2026-09-23**, so it now gates on this window
and on **D5**.
*Source: `implementation/plan.md` Step 21, corrected 2026-08-23 and 2026-09-23.*

### D3. Every mail path, live, once
`tools/email_smoke.py --live` in the production `web` container, to addresses you
own — **including an Outlook or Hotmail inbox**, since Gmail accepted this site's
mail before any of the migration and so cannot tell success from failure. Read
`Authentication-Results` in the inbox, not the provider's `250`: the tool's own
docstring says what a green run does not prove. So far one path has been sent to
one receiver; this is all ten, from the real host. The tool never takes a
recipient from the database, and `--live` cannot be undone — a dead address is a
permanent bounce against the domain.
*Source: `STATUS.md` § Step 16 task 07, "Still open"; carried 2026-09-23.*

### D4. Watch Postmark's bounce dashboard for two weeks
Starting at cutover. This replaced the graduated warm-up, dropped 2026-08-20 on
measurement: 11.9% of a year's notification mail reaches accounts dormant 3+
years, and Postmark suppresses each after one hard bounce — so early bounces
from dormant addresses are expected, and are why this is a watch rather than a
staged send.
*Source: `STATUS.md` § Step 16, the warm-up measured and dropped; carried
2026-09-23.*

### D5. Before jaguar is shut down: its Postfix has gone quiet
Senders cache MX records beyond their TTL, so mail for `surfguitar101.com` and
`themadeira.net` kept arriving at jaguar after the 2026-08-25 flip, and jaguar's
Postfix was left receiving so none of it would be refused. Before shutdown, read
jaguar's mail log for recent inbound deliveries to either domain. **None for a
week** is the condition; anything still arriving means a sender is still using
the old MX, and shutting down turns their mail into bounces.
*Source: Step 16 task 06 Phase 3; carried here 2026-09-23 when the jaguar
decommission project closed.*

### D6. Pull jaguar's logs again — the day after the flip, and last thing before shutdown
Same pull as the 2026-09-25 archive, into a new dated directory beside it under
`~/workspaces/bgn/sg101-evidence/`: sg101's and the wiki's Apache log
directories and the Django `logs/` directory, `rsync -a`, then a size check
against a listing taken first and a `MANIFEST.sha256`. **Deadline: before about
2026-11-20**, when the eight-week rotation passes the end of the previous pull
and the record gets a hole. If shutdown is later than that, pull in between.
Un-excluding the logs on bobcat does not substitute for this: its rsync runs
`--delete`, so it mirrors the same eight weeks.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25.*

### D7. At shutdown: the wiki becomes a redirect, not a dead name
The MoinMoin vhost stays up on jaguar until shutdown. At shutdown, keep
`wiki.surfguitar101.com` **proxied** in Cloudflare and add a redirect rule
sending it to `https://surfguitar101.com/`. A redirect rule fires only on a
proxied record, so the record has to stay (pointed anywhere, since the rule
answers before the origin is contacted). Deleting the record instead would break
the forum's old links to the wiki. The content is already in `archive/wiki/`.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25.*

### D8. At shutdown: IRC goes with jaguar — delete `irc.surfguitar101.com`
`ngircd` and `sg101Bot.py` are **not** moved to the new host. They stop when
jaguar does. Then delete the `irc.surfguitar101.com` record, which is proxied
and so has never reached ports 6667/6697 by name anyway. The bot's code and
ngircd's config are copied to `~/workspaces/bgn/sg101-evidence/irc-2026-09-25/`.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25.*

---

## Known gaps in this list

Stated so the file is not mistaken for complete:

- **The smoke checklist is not here.** A Step 13 version exists in
  `STATUS-archive-steps-01-15.md`; whether it is still current is unchecked.
- **No rollback procedure is written down** beyond "keep jaguar warm and flip
  DNS back". What that means for data written to the new host during the window
  has not been decided.
- **Step 20 is unfinished** and will add entries; its nine task files were
  generated 2026-09-12; B5, B6 and B8 above came from it, and C5's smoke run.
  *(Step 19 closed 2026-09-09 and no longer belongs on this list.)*
- **Ordering and timings are absent.** The sections are grouped by phase, not
  sequenced, and nothing here estimates how long the window needs to be.
