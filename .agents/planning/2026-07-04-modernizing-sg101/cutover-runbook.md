# Cutover runbook — Step 21

**Started 2026-09-06; sequenced and completed by task 08, 2026-10-05.** Owned by
Step 21. Follow *Run it in this order* on the day; the A–D entries after it say
how and why. It exists because items that only matter on cutover day
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

## Run it in this order

Written in task 08 (2026-10-05). Each step points at the entry that says how;
the entries below say why. **⏱** is machine time measured in task 07's
rehearsal (`STATUS.md` § Step 21 task 07, "the window, timed"); **~** is an
estimate, not measured. The pauses between steps, while someone reads output
and types the next command, are not in any ⏱ and will dominate.

T0 is the moment of C0. **Stop point: T0 + 60 minutes.** If the go/no-go has not
passed by then, take rollback **R0** and pick a new date.

**Already done, nothing to do on the day:** A3, B1, B2, B5, B7, B10, B11, B12,
B13 and B14 (each heading says when). B3's live recheck is S3 step 27. **B6** is
done, and its *Emergency open* and *Re-close* are S2 steps 21–22. **D9** is for
every deploy after the cutover; **D7** moved to C6.

### S0. As soon as the date is set
1. Announce the date and time to members (task 09, requirement 1). Two or
   three days' notice is enough for a window this short. ~
2. **A6**: Postmark onto a paid plan. ~
3. **A4**: DMARC readings go daily, through T+14.
4. **A5**: copy jaguar's mail logs. The baseline is read from them, so this is
   a copy, not a week of collection. ~5 min

### S1. The day before (T−1)
5. **A2**: the working-copy audit on jaguar and leopard, plus `make
   cloudflare-ranges-check` and `make firewall-check` from the Mac. ~5 min
6. **A1**: the retired-network query against jaguar. ~1 min
7. **B4** media pass (⏱ 36.9 s for the whole 4.93 G in task 07; a delta is
   less), then **B4a**'s chown; **B8** (⏱ 1.5 s).
8. On leopard: `git pull`; `git status apache/ docker-compose.prod.yml` is
   clean; `.env` has no `EMAIL_BACKEND` or `EMAIL_ALLOWLIST` and does have
   `GCAL_CREDENTIALS_PATH` (key names only, as in B14). Then `make prod-build`,
   so the window never waits on an image. ~ build time unmeasured. **Leave the
   stack down**: its database is still task 07a's beta copy, and it would
   send mail for real.
9. Walk this runbook with Claude (task 09, approach 1).

### S2. The window (T0)
10. Post the notice that the site is going down now. ~1 min
11. **C0**: freeze jaguar. **This is T0.** ~1 min
12. **C1** step 1, the dump on jaguar: ⏱ 1 m 11.9 s, then `md5sum` and
    `bzip2 -t`. ~30 s
13. **C1** step 2 on the Mac: ⏱ 1 m 35 s in all (copy 5.3 s, load 35.0 s,
    `convert.sh` 19.7 s, verify 13.8 s, `post_convert.py` 2.6 s,
    `compare_schema.py` 2.4 s, `pg_snapshot.sh dump` 8.3 s, copy to leopard
    8.1 s). **A1's query against the converted database** goes here (C3).
14. **C1** step 3 on leopard: `postgres` up ⏱ ~11 s, restore ⏱ 29.8 s; read
    `/tmp/restore-errors.txt`.
15. **C2**: the `oembed` row. ~seconds
16. **C3**: `migrate` says "No migrations to apply". ⏱ 14.6 s
17. `make prod-up`, which starts `web`, `worker` and `beat` fresh (**C4a**). ⏱
    healthy within 43 s in task 07. **No maintenance flag on leopard**: until
    the flip nobody but you can reach it (see *Maintenance notices*).
18. **C4**: `reindex_search` ⏱ 5 m 12.8 s, then `reconcile_search` ⏱ 12.6 s,
    clean. Inside the window (decided 2026-10-05).
19. **B4a**'s `image_smoke.py`, then `--s3`. ~seconds. The snapshot it asks
    for is C1's restore file.
20. **C5**: the final media delta ⏱ 0.7 s (re-run B4a's chown after it), then
    `tools/prod_smoke.sh` on leopard ⏱ 1.8 s, 21/21.
21. **The pre-flip browser check**, part 1 of the *Smoke checklist*. ~15 min
22. Re-close the firewall: `make firewall-apply`, then `make firewall-check`
    (B6). ~1 min
23. **Go/no-go**, the list below. ~2 min. Any "no" is **R0**.
24. **C5**: the DNS flip. ~1 min. **The rollback window opens here** and closes
    at flip + 24 h.
25. Part 2 of the *Smoke checklist*, through Cloudflare. ~10 min
26. **C6**: the wiki's redirect, as its own change. ~2 min

**Expected length:** ⏱ ~9 m 50 s of measured machine time from C1 through C5
(task 07's ~9 m 10 s plus `make prod-up`), and **~45 minutes** to the flip with
the pauses, the browser check and the go/no-go. The 60-minute stop point leaves
~15 minutes of slack.

### S3. After
27. The first hour: `docker stats` and `make prod-ps` open in a terminal. No
    test before the flip ran at the live rate (`STATUS.md` § Step 21 task 08),
    so this is the first look at it, against R1's "the site cannot serve".
    Same day: **D1** (one real message with headers), **B9** (the `/media`
    cache rule), and **B3** on live traffic (your address in `auth.log` and
    `access.log`).
28. **D3**, every mail path live, once.
29. **D4**: Postmark's bounce dashboard, daily for two weeks; A4's daily DMARC
    readings run alongside.
30. The day after: **D6**, jaguar's logs.
31. Flip + 24 h: the rollback window closes. From here, fix forward.
32. Task 10's two-week watch. jaguar stays frozen and warm (**D2**) until task
    11, which also carries **D5** and **D8**.

## Go/no-go — before the DNS flip

Every line must be true. Each is one command or one look. **Any "no" is R0**,
not a fix made in a hurry.

- [ ] `/tmp/restore-errors.txt` is empty: `wc -c /tmp/restore-errors.txt` → 0.
- [ ] C2: `oembed` `0001_initial` is in `django_migrations`.
- [ ] C3: `migrate` said "No migrations to apply".
- [ ] `make prod-ps`: every service up, `web` healthy.
- [ ] C4: `reconcile_search` reported clean.
- [ ] B4a: `image_smoke.py` 7/7, and `--s3` 12/12.
- [ ] C5: `tools/prod_smoke.sh` all PASS.
- [ ] **Nothing written before the freeze is missing** (task 09, criterion 2):
      the newest IDs match on both hosts, read on jaguar with
      `SELECT MAX(id) FROM forums_post; SELECT MAX(id) FROM messages_message;
      SELECT MAX(id) FROM auth_user; SELECT MAX(id) FROM user_photos_photo;`
      and on leopard in `make prod-shell` with the same four tables'
      `.objects.latest('id').id`, before part 1 of the smoke checklist adds
      rows of its own.
- [ ] Part 1 of the *Smoke checklist* passed.
- [ ] `make firewall-check` passes: step 22 removed the temporary rule.
- [ ] A6: Postmark shows the paid plan's limit.
- [ ] The clock reads before T0 + 60 minutes.

## Smoke checklist

Current as of 2026-10-05 (task 08). **`tools/prod_smoke.sh` already covers** the
home page over TLS, one HSTS header, the redirects, the root files, `/media`,
the old SG101 1.0 URLs and the closed ports, and **`image_smoke.py`** covers
avatar, member-photo (`--s3`: the real bucket) and photo-of-the-day uploads
through the real views. Nothing below repeats them. `tools/pgloader/smoke.py`,
the Step 11 script the Step 13 list was built on, writes as a scratch user and
is **rehearsal-only**: it is not run against the real database.

### Part 1 — before the flip, straight at leopard
Open the temporary rule from B6's *Emergency open* (443 from your address
only), then a throwaway Chrome profile that sends the site's name to leopard.
It has no remembered HSTS (the live site sends `max-age=604800`), so you can
click past the Origin CA certificate:

```bash
open -na "Google Chrome" --args --user-data-dir="$(mktemp -d)" \
    --host-resolver-rules="MAP surfguitar101.com <VM IPv4>" https://surfguitar101.com/
```

Everything written here is real and stays: these are the first rows on the new
host, and the mail goes out for real.

**Reads**, each a page that renders:
- [ ] The forum index, a topic, `/forums/unread/`.
- [ ] A news story with a YouTube embed, which plays (the referrer fix, 07a).
- [ ] A podcast episode page, which plays (the jPlayer fix, 07a).
- [ ] `/bandmap/`: the map draws (the key allows `surfguitar101.com`).
- [ ] `/calendar/`, `/potd/`, `/downloads/`, `/links/`, `/polls/`,
      `/donations/` (look; do not donate), a member's profile.
- [ ] Search: a phrase, and the forum quick search.
- [ ] Feeds: `/feeds/news/`, `/feeds/forums/`, `/podcast/feed.xml/`, each XML.
- [ ] The admin: the news story form shows TinyMCE (#19).

**Writes**, as a member would:
- [ ] Log in as `brian` in lower case (the case-insensitive login, 07a).
- [ ] Register a new account with a Gmail plus-address: Turnstile passes on
      the real hostname, and the confirmation mail arrives.
- [ ] Reply in a topic, then `make prod-logs svc=worker` shows
      `reindex_document ... succeeded` (**C4a**), and the reply is found by
      search.
- [ ] A private message to the new account; its notification mail arrives.
- [ ] A photo uploaded through the post editor, and shown in the post.
- [ ] A calendar event submitted, approved in the admin, Synchronized, and
      seen on the real Google Calendar; then delete it there and in the admin.

### Part 2 — after the flip, through Cloudflare
- [ ] `curl -sI https://surfguitar101.com/` → 200 with a `cf-ray` header, and
      the request in leopard's `var/log/apache/access.log` with your real
      address (task 09, criterion 1).
- [ ] In a normal browser: the home page, a topic, a reply posted.
- [ ] A failed login on purpose: your address in `var/log/django/auth.log`
      (B3).

## Rollback

Decided 2026-10-05 (Brian); the reasoning is in `STATUS.md` § Step 21 task 08.
**The default is to fix forward.** A rollback is for a fault that cannot be:

- the site cannot serve: `web` keeps failing, or pages broadly answer 500;
- the data is wrong: rows or files missing or damaged against jaguar;
- a fault every member meets that cannot be fixed within an hour or two, such
  as login or posting broken for everyone.

One broken page, one feature with a workaround, or one category of mail is a
fix-forward.

### R0. Before the flip — abort, nothing lost
jaguar holds every write; leopard has had none but yours.
1. On jaguar: `OFFLINE = False` in `sg101/apache/sg101.wsgi`, and `touch` it.
2. If the temporary firewall rule is still open: `make firewall-apply`, then
   `make firewall-check`.
3. On leopard: `make prod-down`.
4. If part 1 of the smoke checklist put an event on Google, delete it there.
5. Post: the move is postponed and the site is back as it was.

### R1. After the flip, within 24 hours — flip back, lose the window's writes
1. On leopard: `make prod-maint-on`. Writes stop at once.
2. **List what is about to be lost**, in `make prod-shell`: the posts, PMs,
   accounts and photos with IDs above the go/no-go line's, and every event
   approved since the flip. Save the list with the rollback's record.
3. Delete from the real Google Calendar each event step 2 listed.
4. **Donations:** PayPal sends IPNs to the hostname, so a donation made in the
   window is recorded only on leopard. Take each from PayPal's activity list and
   add it on jaguar by hand.
5. In Cloudflare, point the site's records back at the values C5 wrote down.
6. On jaguar: `OFFLINE = False`, and `touch` the `.wsgi`.
7. Check: `curl -sI https://surfguitar101.com/` → 200, and a post from step
   2's list is **not** there (it is jaguar answering).
8. Post the notice below, on jaguar.
9. On leopard: `make prod-down`. Record what happened in `STATUS.md`.

**The notice** (fill in the brackets):

> We moved SurfGuitar101 to its new server on [date] and had to move back to the
> old one at [time] because [one line]. Anything posted, sent or uploaded
> between [flip time] and [rollback time] did not come back with us: forum
> posts, private messages, new accounts and photos from that window are lost.
> Sorry — please re-post what you can. We'll try the move again once it's fixed.

### After 24 hours
No rollback. Fix forward, with `make prod-maint-on` around any repair that
needs the site closed. jaguar stays frozen and warm (D2) only for a disaster
that leaves nothing on leopard to fix.

## Maintenance notices — which host, and in what order

| when | who sees what | mechanism |
|---|---|---|
| T−7 to T0 | the announcement | a forum post or news story (S0) |
| T0 (C0) to the flip | jaguar's `offline.html`: 503 for reads, 405 for writes | jaguar's `OFFLINE` flag (C0) |
| the flip onward | the new site, live | leopard, **no flag** |
| repairs, R1 step 1 | leopard's `offline.html`, 503 for everything | `make prod-maint-on` / `prod-maint-off` (Apache, `var/maintenance/on`) |

**Leopard needs no notice before the flip.** Cloudflare sends the name to jaguar
and B6 admits only Cloudflare, so no member can reach leopard until C5. Leopard's
flag would also fail `prod_smoke.sh` and the browser check, since it has no
address bypass: while it is on, it answers 503 to you as well.

**The Cloudflare Snippet** Step 20 chose as the primary mechanism was never built
and is not needed (decided 2026-10-05). jaguar stays frozen after the flip, so a
request that still reaches it is refused rather than written.

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

### A3. Delete the 32 pending `gcalendar` rows in production, not just locally — DONE, confirmed 2026-10-02
Step 21 converts a **fresh** production snapshot, so rows deleted only in the dev
database come back with it and land in the pending queue on the new host.
**Done by Brian in production**, reported 2026-09-26; the date of the deletion is
not recorded. **Confirmed from data 2026-10-02:** task 07a's requirement 4a
counted zero `Event.pending_events` in the rehearsal snapshot, before the
calendar key went in.
*Source: `STATUS.md` § the `NEW`/`NEW_APRV` decision, settled 2026-08-31.*

### A4. Move DMARC readings to daily
From when the date is set to ~2 weeks after the flip. Reports arrive one per
day per receiver whatever the reading cadence, so the "before" half is already
in `~/dmarc`; reading daily is what keeps the comparison at one resolution. Three open items resolve in that
interval and each needs both halves at the same resolution; a before/after
comparison across a change of cadence is not a comparison.
*Source: `research/dmarc-readings.md`, cadence table.*

### A5. Collect the jaguar-side email baseline
The pre-cutover window is the **only** chance to take it. **It is already on
disk:** jaguar's `/var/log/mail.log*` held four weeks on 2026-10-05, back to
09-06, rotating weekly. Copy all of them into
`~/workspaces/bgn/sg101-evidence/` with a `MANIFEST.sha256`, as D6 does, before
another week rotates out. The baseline is then read from the copy.
**Copied 2026-10-06 ~01:50 UTC** to `sg101-evidence/jaguar-mail-2026-10-06/`:
`mail.log*` and `mail.err*`, 10 files, sizes matching the listing taken first,
manifest 10/10 OK. `mail.log` runs from 09-06 07:22 to 10-05 20:48 CDT. **The
last two days before the freeze are not in it**, so D6's day-after pull takes
`mail.log` and `mail.log.1` too. Postmark's dashboard
gives a total with no category breakdown, and the baseline is what makes a later
discrepancy explainable rather than merely visible.
*Source: `STATUS.md` § Step 16 task 09, "What is still owed".*

### A6. Move Postmark off the trial plan — DONE 2026-10-06 (Brian); healthchecks.io moved to its paid plan the same day
The account is on Postmark's trial, **100 emails per period**; 18 were used by
2026-10-02, during task 07a's beta (Brian). The live site's whole outbound mail
will not fit in it. Change to a paid plan before C5's DNS flip, and confirm in
the dashboard that the new limit is in force. The mail volume the plan has to
cover is A5's baseline, not a guess.
*Source: `STATUS.md` § Step 21 task 07a.*

## B. Host preparation

### B1. `secrets/gcal/gcal-service-account.json` — DONE on leopard 2026-09-27
Git-ignored as a whole directory and **backed up nowhere**. Without it the
calendar does not come up on the new host, and it cannot be recovered — only
reissued from the Google console.

**In `secrets/gcal/`, not `secrets/`** — that directory alone is mounted into
`web`, and nothing in `secrets/` reaches the image. **Owned by uid 1000, mode
600** (on leopard that is `brian`), because the container runs as uid 1000 and a
file it cannot read fails only when someone presses Synchronize.
`GCAL_CREDENTIALS_PATH=/app/secrets/gcal/gcal-service-account.json` in `.env`.
*Source: `STATUS.md` § Step 18, § Step 21 task 03; memory `modernizing-sg101-planning`.*

### B2. `.env` — DONE
The only other un-backed-up artifact. Regenerate from `secrets.json` in the hg
backup if it is ever lost. **It also needs `GUNICORN_WORKERS=5` and
`CELERY_WORKER_CONCURRENCY=2`**, which `secrets.json` never held: the production
compose refuses to start without them. `.env.example` gives the reasoning.

**It is not a copy of the development `.env`.** That file runs on Cloudflare's
public Turnstile test keys, which pass every bot, and has no Postmark token.
Production needs real `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` from a
widget created in the Cloudflare dashboard. **Brian created one and wrote
leopard's `.env`**, reported 2026-09-27; the variable names were checked there
(`STATUS.md` § B2). The widget's hostname list is `surfguitar101.com`; task
07a's `beta` entry was removed at its teardown (2026-10-05). It also
needs `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (the Postmark server token, in
both) and the `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USE_TLS` lines `.env.example`
shows commented out.

**`SECRET_KEY`: `python3 -c 'import secrets; print(secrets.token_urlsafe(50))'`**,
not Django's `get_random_secret_key()`. Measured 2026-09-28: in an `env_file`
value, Compose replaced `$HOMEcd` with nothing and cut `ab #cd` at the space,
both silently, and django-environ resolved a leading `$` to another variable.
Django's alphabet has `$` and `#`. leopard's key is 67 characters of
`[A-Za-z0-9_-]`, the `token_urlsafe(50)` shape; the command that made it was not
recorded. Changing it later logs everyone out and voids outstanding reset and
signup links; Django's `SECRET_KEY_FALLBACKS` eases that.
*Source: memory `modernizing-sg101-planning`; `AGENTS.md`; Step 21 task 03.*

### B3. Real client IP at the new front door — PASSED on `beta` 2026-09-30; recheck on live traffic after the flip
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
Cloudflare. **Both done:** the check passed over both address families on
`beta` on 2026-09-30, and fail2ban was installed on leopard the same day (`STATUS.md`
§ Step 21 task 06). Steps 1–3 run once more on live traffic after the flip
(S3 step 27).
*Source: `research/dmarc-readings.md` § "A cutover requirement this exposed";
Step 20 tasks 03 and 04.*

### B4. The media tree — first full pass done 2026-10-01 (task 07); re-run at T−1, delta at C5
**The first full pass ran in task 07: ⏱ 36.9 s for 4.93 G.** The pass the day
before (S1) and C5's delta only copy what changed since. The 4,577 local-disk
user photos ride this step's rsync; the S3 work in Step 15 changed where *new* uploads go, not where the old
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

**Corrected 2026-09-30: sync `media/` whole, excluding exactly the files git
tracks, rather than by directory name.** The named list missed `podcast/`'s
1.4 GB of episodes (every feed enclosure points there; the table below counts
only the one tracked logo) and `slideshow/` (the home page's), which the table
never listed. *Source: `STATUS.md` § Step 21 task 07, "Found while drafting".*

```bash
git ls-files media | sed 's#^media/#/#' > /tmp/media-tracked
rsync -a --exclude-from=/tmp/media-tracked jaguar:/svr/django-sites/sg101/sg101/media/ media/
```

No `--delete`. Afterwards `git diff --name-only media` is empty (no tracked file
touched), and `git status --short --ignored media/badges media/smiley` lists only
assets that should be committed (below). **Plain `git status` shows nothing**:
`.gitignore` covers both directories, so the missing assets are ignored, not
untracked, and committing them needs `git add -f`.

**One known gap to fix while there:** three `bio.Badge` rows reference files that
were never committed — `badges/map.png` (Map Pin), `badges/bns_badge.png` (Brave
New Surf Pin) and `badges/script.png` (Wiki Pin) — and two smileys,
`smiley/images/icon_popcorn.gif` (`:popcorn:`) and
`smiley/images/icon_dead_frv1.gif` (`:frv1:`), found 2026-09-30. They exist on production and
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
cleans up after itself — 7/7 when the ownership is right. **Run it with `--s3`
as well:** without it, member photos take the local-disk branch, while
production stores them in S3 (`USER_PHOTOS_LOCAL_UPLOAD = False`). `--s3` adds
a real upload to `sg101.user.photos`, a public fetch and a delete — 12/12 in
task 07's rehearsal, the only check of that path the project has. **Take a database
snapshot first**; it creates and deletes a scratch user.

*Source: Step 20 task 12. The UID contract is checked on every CI run, which is
the only Linux this project has until the VM exists — Docker Desktop translates
bind-mount ownership and will accept a configuration the VM rejects.*

### B5. Install the Cloudflare Origin CA certificate — DONE 2026-09-27, valid to 2041-09-23
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

### B6. Apply the origin firewall — DONE on leopard 2026-09-27, refusal measured
**The web ports admit only Cloudflare, enforced by the hosting provider's
firewall** (decided 2026-09-23, Step 20 task 07). A firewall on the VM itself
was rejected: Docker forwards a published port to the container before the VM's
own input rules see it, so those rules would look right and filter nothing.

**Applied to leopard 2026-09-27**, refusal measured (`STATUS.md` § Step 21 task
03). The ranges file, the plan and the checks were built in Step 20 task 07; the
Linode adapter in Step 21 task 02. What remains on the day is *Emergency open*
and *Re-close* below, for part 1 of the smoke checklist (S2 steps 21–22).

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

### B7. Choose the backup buckets — and the constraint they must satisfy — DONE: chosen 2026-09-22, provisioned in B12
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
together. **The warm same-provider copy is Linode's Backup service on the VM**
(turned on by Brian, 2026-09-28): whole-disk snapshots, so it also holds the logs,
`secrets/` and host configuration the S3 job does not. **bobcat is not repointed**
(Brian, 2026-09-28; this said it was until then). **The object storage copy is
the one that has to be somewhere else.**

Against a Linode VM, **an AWS S3 bucket satisfies this**, and `boto3` plus the
credentials are already in the project from Step 15. Use a **new bucket**, not
`sg101.user.photos` or `sg101.forum.photos`, and a **write-scoped credential** —
the job puts objects, the lifecycle policy deletes them. **If the VM lands on
Lightsail instead, S3 shares its provider and fails the constraint** — the
bucket then goes elsewhere.
*Source: Step 20 task 06.*

### B12. Provision the backups, and prove the alarm reaches you — DONE on leopard 2026-09-28; step 7 done in task 07, 2026-10-01
The job, the buckets' rules and the restore are built and drilled locally
(`tools/backup_drill.sh`, DOCKER.md *Backups, and restoring from them*). What
cannot be drilled locally is everything with a real account behind it.
`dcp` is DOCKER.md §10's shorthand, `docker compose -f docker-compose.prod.yml`.

1. **Create the buckets** with an administrative credential — creates both,
   turns on versioning, applies `lifecycle-db.json`, and leaves the media bucket
   with no rules at all. Re-running it corrects drift. **Run it from your own
   machine, not the VM**, so the admin key never reaches the VM or its shell
   history. With an AWS CLI profile holding a temporary admin key, the key goes
   in by variable name only:
   ```bash
   docker build -t sg101-backup:prod backup/
   ( eval "$(aws configure export-credentials --profile sg101-admin --format env)"
     docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
         -e AWS_DEFAULT_REGION=us-west-1 -e BACKUP_DB_BUCKET=sg101-backup-db \
         -e BACKUP_MEDIA_BUCKET=sg101-backup-media sg101-backup:prod provision )
   ```
   **Confirm Block Public Access is on for both** (the AWS default for new
   buckets since 2023; `provision` does not set it because the local stand-in
   does not support it).
2. **Create the job's IAM user** with `backup/policy-writer.json` as its only
   policy, `@DB_BUCKET@`/`@MEDIA_BUCKET@` replaced. Nothing else — no read, no
   delete. `aws iam create-user --user-name sg101-backup`, `put-user-policy` with
   the filled-in file, `create-access-key` redirected to a mode-600 file, never
   printed. **List is allowed on purpose**: `aws s3 sync` lists to find what
   changed. Prove the rest with the key itself: put and overwrite succeed; get,
   head, delete, delete-version, list-versions, suspend-versioning,
   delete-lifecycle, list-buckets and any other bucket are refused; and the
   overwrite leaves the first copy as a non-current version.
3. **Create the healthchecks.io check**: period 1 day, grace 2 hours, alerting to
   Gmail. Put its ping URL, the buckets and the job's key in
   `secrets/backup.env` (template: `backup/backup.env.example`).
4. **Run the first backup by hand** — `dcp run --rm backup`. The first media sync
   uploads all ~4.7 GB and will take a while; later ones copy ~10 MB a month.
5. **Prove the alarm, at the receiving end.** Run it once with a wrong database
   password, `dcp run --rm -e PGPASSWORD=wrong backup`, and **see the alert arrive
   in Gmail** — not just the check turning red on the dashboard. This is the
   acceptance test task 06 could not run.
6. **Install the timer.** The `.service` already defaults to `/svr/sg101`:
   ```bash
   sudo cp backup/sg101-backup.service backup/sg101-backup.timer /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now sg101-backup.timer
   systemctl list-timers sg101-backup.timer
   sudo systemctl start sg101-backup.service     # the path the timer takes
   systemctl show sg101-backup.service -p Result  # success
   ```
   **Run the service once by hand.** Every earlier run is `dcp run` from your
   shell; the timer runs the unit as root from `WorkingDirectory`, and that path
   is otherwise first exercised unattended at 04:30.
7. **Restore once from the real bucket** into a scratch database (DOCKER.md),
   so the first proof that the real backups restore is not a disaster.

**Also worth a calendar reminder around day 91:** confirm the oldest dumps are
actually gone. Expiry is the one behaviour no local drill can show, because
lifecycle rules count in whole days.

*Source: Step 20 task 06.*

### B10. Install the `logrotate` configuration — DONE on leopard 2026-09-27
Production's log handlers are `WatchedFileHandler`: they never rotate, because a
dozen processes share `var/log/django` and a handler that renames the file it
writes leaves every other process appending to a name that no longer exists.
**Until this is installed, nothing rotates those files at all.**

```bash
sudo cp logrotate/sg101 /etc/logrotate.d/sg101
# The paths assume the checkout is at /svr/sg101; edit them if it is elsewhere.
chmod 755 var var/log var/log/django var/log/apache      # keeps a hand-run clean
sudo logrotate --debug --force /etc/logrotate.conf 2>&1 | grep 'creating new /svr'
sudo logrotate --force /etc/logrotate.d/sg101             # once, to prove it
```

**Dry-run through `/etc/logrotate.conf`, not the file alone**: that is how the
nightly service runs it, and Ubuntu's sets `su root adm` globally, which changes
what logrotate does. Every `creating new` line for `var/log/django` must say
`uid = 1000`, or the containers cannot write their log after the first real
rotation. Run on the file alone, a 775 directory prints `insecure permissions`
and is skipped; under the global `su` it is not checked at all (`STATUS.md` §
Step 21 task 03, 2026-09-27).

**Then prove the processes followed it**, which is the whole point and is not
visible from `ls`: after the forced rotation, make the site serve a page and
queue a task, then confirm the new lines are in `sg101.log` and not in
`sg101.log.1`.

```bash
tail -3 var/log/django/sg101.log
```

**Then the heartbeat, so a failed rotation reaches you.** The host has no mailer;
without this, a failure is only in `sudo journalctl -u logrotate`.

1. On healthchecks.io, create a check: **period 1 day, grace 2 hours**, alerting
   to Gmail, as B12's backup check.
2. On the VM, its ping URL into `secrets/logrotate.env`, mode 600:
   `HEARTBEAT_URL=https://hc-ping.com/<uuid>`.
3. Install the drop-in and run once:
   ```bash
   sudo install -D -m 644 logrotate/heartbeat.conf \
       /etc/systemd/system/logrotate.service.d/sg101-heartbeat.conf
   sudo systemctl daemon-reload
   systemctl cat logrotate.service | tail -3     # the drop-in is listed
   sudo systemctl start logrotate.service        # the check turns green
   ```
4. **Prove the alarm at the receiving end**, as B12 does: a throwaway config
   whose `postrotate` fails, as a failed Apache reload would.
   ```bash
   sudo install -d -m 755 -o brian -g brian /srv/lrfail && echo x > /srv/lrfail/t.log
   printf '/srv/lrfail/t.log {\n    size 1\n    postrotate\n        false\n    endscript\n}\n' \
       | sudo tee /etc/logrotate.d/zz-lrfail
   sudo systemctl start logrotate.service        # fails; the alert must arrive in Gmail
   sudo rm -r /etc/logrotate.d/zz-lrfail /srv/lrfail
   sudo systemctl start logrotate.service        # green again
   ```
   Remove the throwaway config straight away: while it is there, every nightly
   run fails. `size 1` makes the two-byte file due, so the `postrotate` runs.
   `/srv`, not `/tmp` or `/var/tmp`: the service has `PrivateTmp`. **Not a 775
   directory**: under the global `su` the service never checks, and exits 0.

*Source: Step 20 task 11, where this was exercised against the local stack; the
heartbeat, Step 21 task 03.*

### B11. Apache's own logs rotate with B10's file — PROVED on leopard 2026-09-27
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

### B8. `/hosted` and `/photos` — content from jaguar's document root — done 2026-10-01 (task 07, ⏱ 1.5 s); re-run at T−1
Two directories that were **not in the repo and recorded nowhere** until Step 20
task 03 read jaguar's vhost: `Alias /hosted/` and `Alias /photos/` point into
`/svr/www/surfguitar101.com/public/`. Measured 2026-09-19: **`hosted/` 16 MB,
`photos/` 69 MB, 1,509 files together**, and **40 requests** for either in the
access log current that day (window not measured; not split by path or by bot).

The new proxy serves both from `var/public/{hosted,photos}` in the checkout.
**`rsync` both there from jaguar**, then spot-check one file from each through
the site. `var/` is git-ignored, so nothing but this step puts them there.
*Source: `STATUS.md` § Step 20 task 03.*

### B13. Confirm `make` is on the VM — DONE: `make prod-up` in use on leopard since 2026-09-29
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

### B14. Send-only mail from the host — DONE on leopard 2026-09-28
`msmtp` as `/usr/sbin/sendmail`, relaying to Postmark on 587 with the
application's own token. It carries cron's mail and unattended-upgrades' failure
reports. **It does not carry logrotate's or the backup's failures**: systemd
does not mail a unit's output, so those have heartbeats (B10, B12).

```bash
sudo apt-get install -y msmtp msmtp-mta        # AppArmor support: the default, No
sudo sh -c 'umask 077; t=$(sed -n "s/^EMAIL_HOST_PASSWORD=//p" /svr/sg101/.env); sed "s/@POSTMARK_TOKEN@/$t/g" /svr/sg101/msmtp/msmtprc > /etc/msmtprc'
sudo install -m 644 msmtp/aliases /etc/aliases
sudo awk '$1=="user"{print "token length", length($2)}' /etc/msmtprc    # 36
ss -ltn | grep -E ':25\b' || echo "nothing on 25"
printf 'Subject: test\n\nfrom the host\n' | sudo sendmail root; echo "exit $?"
```

Then `/etc/apt/apt.conf.d/53leopard-mail`:
```
Unattended-Upgrade::Mail "root";
Unattended-Upgrade::MailReport "only-on-error";
```

**msmtp logs the token.** Its journal line carries `user=`, and Postmark's user
is the token. Filter before pasting anywhere:
`sudo journalctl -t msmtp -n 3 | sed 's/user=[^ ]*/user=REDACTED/'`.

**Rotating the Postmark token:** the new token into **both** `EMAIL_HOST_USER`
and `EMAIL_HOST_PASSWORD` in `.env` — Postmark takes it as both, and updating
only the password leaves the application failing `535` while host mail works,
because `/etc/msmtprc` is built from the password alone. Then reinstall
`/etc/msmtprc` (the second command above), then **`make prod-up`**, which
recreates `web`, `worker` and `beat` with the new value. **Not `docker compose
restart`**: it restarts the same containers with the environment they were
created with. Measured on Compose v5.2: after `restart` the old value, after
`up -d` the new one. msmtp reads its file on every send, so it needs nothing.
Check both paths: `sudo sendmail root` for the host, and
`dcp exec -T web python manage.py sendtestemail --admins` for the application.

**`unattended-upgrade --dry-run` never mails**, whatever `MailReport` says, and
a real run mails only when there is a result. Test the path it uses instead:
`printf 'To: root\nSubject: t\n\nx\n' | sudo sendmail -oi -t`.
*Source: Step 21 task 04.*

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

**The new host needs nothing here.** Until C5 no member can reach it; after,
its flag is `make prod-maint-on`. See *Maintenance notices*. **jaguar stays
frozen after the flip**, through D2's warm window, so it can never quietly
accept a write that leopard does not have.

### C1. Final snapshot → convert → restore
Run in this order in task 07's rehearsal (2026-10-01); each step's time is in
`STATUS.md` § Step 21 task 07, "the window, timed".

1. **On jaguar, after C0:** `time python /svr/scripts/mysqlbackup.py`. It writes
   `/svr/backups/sg101<date>.sql.bz2`, replacing that night's 02:00 file;
   `md5sum` and `bzip2 -t` it. Not the nightly file: that predates the freeze.
2. **On the Mac:** copy it beside the pristine dump in
   `sg101-hg-backup/snapshots/`, then DOCKER.md §7 as written: load into the
   dev `db`, `convert.sh`, `verify.py`, `verify_data.py values`,
   `post_convert.py`, `verify_data.py keys`, `compare_schema.py`. **Stop the dev
   `web`, `worker` and `beat` while converting** and skip `smoke.py`, so nothing
   writes to the database before it is dumped. Then
   `tools/pg_snapshot.sh dump <label>`, and copy the snapshot to the VM's
   `snapshots/`; `md5sum` both ends.
3. **On the VM:** `make prod-down`, then the database alone, replaced, and
   restored over stdin. `pg_snapshot.sh` cannot do this here: it drives the dev
   compose and reads a `/snapshots` mount the production `postgres` does not
   have.
   ```bash
   docker compose -f docker-compose.prod.yml up -d --wait postgres
   docker compose -f docker-compose.prod.yml exec -T postgres psql -U sg101 -d postgres \
       -c "DROP DATABASE sg101 WITH (FORCE)" -c "CREATE DATABASE sg101"
   docker compose -f docker-compose.prod.yml exec -T postgres pg_restore -U sg101 -d sg101 \
       --no-owner --no-privileges < snapshots/<file> 2> /tmp/restore-errors.txt
   ```
   **Read `/tmp/restore-errors.txt`:** empty in the rehearsal. The plain
   `CREATE DATABASE` matches the original (owner `sg101`, UTF8, `en_US.utf8`,
   as `template1` is). `postgres` alone first, so no health check meets an
   empty schema and mails ADMINS (2026-09-27).

### C2. The `oembed` migration-history unlock — a check, not a step
`forums/0001_initial` has declared `('oembed', '__first__')` since 2015, and
`check_consistent_history` refuses every `migrate` on a database without
`oembed.0001_initial` recorded. **`post_convert.py` records it on the Mac
(C1 step 2)**, so the snapshot carries it. Confirm on the VM:
`SELECT name FROM django_migrations WHERE app = 'oembed'` → `0001_initial`.
*Source: `research/schema-drift-audit.md` § "Gotcha for the cutover runbook";
`tools/pgloader/post_convert.py:52-58`.*

### C3. `migrate` on the VM, and A1 on the converted data
On the VM, `docker compose -f docker-compose.prod.yml run --rm web python
manage.py migrate` should say **"No migrations to apply"**: the migrations
ran inside `post_convert.py` on the Mac. Anything applied here means the VM's
code is ahead of the Mac's checkout, which is itself a finding. **The
retired-network check is A1's query, run against the converted database on
the Mac**, not this output: `elsewhere`'s `0004_seed_networks` reports through
`logger.warning`, which neither `post_convert.py`'s output nor this one shows.
An empty result is the expected one (2026-10-01).

### C4. `reindex_search`, then `reconcile_search`
The search index is **schema-only in every dump**, so it does not come across
with a restore. `run --rm web python manage.py reindex_search`, then
`reconcile_search`, which should say **clean**.
**It took 5 m 13 s on the VM** (1 m 35 s on the Mac): one CPU core saturated,
not memory or disk, so a larger plan of the same shared cores would not shorten
it. It is over half the window's measured time. **Decided 2026-10-05 (Brian):
inside the window**, so `reconcile_search` is clean before the go/no-go.
*Source: `tools/pg_snapshot.sh` restore output; Step 12 record; `STATUS.md`
§ Step 21 task 07, P4.*

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
**Before the flip, run `tools/prod_smoke.sh` on the VM, in its checkout, with no
argument.** It makes every request to `127.0.0.1` under the site's name, so it
tests the new origin while DNS still points at jaguar: the home page over TLS,
one HSTS header, the redirects, the root files, `/media`, the old SG101 1.0
URLs, and that 8000/5432/6379 are closed. **Not from a laptop with the VM's
address:** B6's firewall admits only Cloudflare to 443, so that needs a
temporary rule (as on 2026-09-27); on the VM the firewall is not in the path,
and B6 proved it separately. Run this way in task 07's rehearsal: 21/21,
1.8 s.

**The flip.** In Cloudflare, list the records that point at jaguar's
addresses and **write each one's current value down** first; R1 restores
them. Change only the site's records to leopard's addresses. The wiki is C6,
`irc` is D8, and MX, SPF and DMARC stay untouched (task 09, requirement 5).
The site's records are proxied, so the change takes effect at Cloudflare's
edge, with no client DNS cache to wait out. Confirm they still show proxied
afterwards.

### C6. Once the flip holds: the wiki becomes a redirect, not a dead name
A separate change from C5's, made after the new site is seen serving, so the
flip stays the only thing a rollback has to undo. Keep `wiki.surfguitar101.com`
**proxied** in Cloudflare and add a redirect rule sending it to
`https://surfguitar101.com/`. A redirect rule fires only on a proxied record, so
the record has to stay (pointed anywhere, since the rule answers before the
origin is contacted). Deleting the record instead would break the forum's old
links to the wiki. The content is already in `archive/wiki/`.

**This is also what stops jaguar adding to `block_list`.** Its `wiki-abuse`
jail made every ban on the list; with no wiki traffic reaching jaguar it has
nothing left to ban. The entries it already made still expire into a paged
unban that misses most of them, so they are cleared fourteen days later, at the
end of task 10's watch.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25; moved from shutdown
to the flip 2026-09-30 (Brian).*

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
directories and the Django `logs/` directory, and, on the day after only,
`/var/log/mail.log` and `mail.log.1` to finish A5's baseline up to the freeze, `rsync -a`, then a size check
against a listing taken first and a `MANIFEST.sha256`. **Deadline: before about
2026-11-20**, when the eight-week rotation passes the end of the previous pull
and the record gets a hole. If shutdown is later than that, pull in between.
Un-excluding the logs on bobcat does not substitute for this: its rsync runs
`--delete`, so it mirrors the same eight weeks.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25.*

### D7. Moved to C6 — the wiki goes at the flip, not at shutdown (Brian, 2026-09-30)

### D8. At shutdown: IRC goes with jaguar — delete `irc.surfguitar101.com`
`ngircd` and `sg101Bot.py` are **not** moved to the new host. They stop when
jaguar does. Then delete the `irc.surfguitar101.com` record, which is proxied
and so has never reached ports 6667/6697 by name anyway. The bot's code and
ngircd's config are copied to `~/workspaces/bgn/sg101-evidence/irc-2026-09-25/`.
*Source: `STATUS.md` § Step 21 task 01, decided 2026-09-25.*

### D9. Routine deploys, from the cutover on
jaguar's `hg up` and a touch of the `.wsgi` file has no equivalent here: the
code and the hashed static files are built into the `sg101-app:prod` image, so
a pull changes nothing until the containers are replaced. **Nothing runs
`migrate` but you.**

```bash
git pull
git diff --stat ORIG_HEAD.. -- '*/migrations/*'   # empty: no migrations
make prod-up        # no migrations
make prod-deploy    # migrations
```

- **`make prod-up`** builds while the old containers serve, then replaces
  `web`, `worker` and `beat`. `proxy` is replaced with them. Visitors meet
  a gap: refused connections while the proxy restarts, then a 503 with
  `offline.html` (the vhost's `ErrorDocument`) until gunicorn listens, and a
  request caught mid-shutdown gets Apache's bare 502. Measured 2026-10-01 on
  leopard at 20–30 s. Fine at this site's ~1 request a second.
- **`make prod-deploy`** builds first, turns maintenance mode on, runs
  `migrate` from the new image, replaces the containers, waits for `web` to
  pass its health check, then turns maintenance mode off. Measured on the Mac
  2026-10-03: 14 s in all, 503 `offline.html` for about 7 s with one real
  migration applied, and about 2.5 s of refused connections as `proxy` was
  replaced. **If any step fails it stops with maintenance mode still on**:
  read the output, fix, then rerun it or `make prod-maint-off`.
- Either way, check `make prod-ps` afterwards, and that a deferred task still
  runs (C4a): save a story, watch `make prod-logs svc=worker` for
  `reindex_document ... succeeded`.
- A change under `apache/` alone needs neither: `make prod-proxy-reload`.

*Source: `STATUS.md` § Step 21 task 07a, the podcast detail fix
(2026-10-03); the gap from leopard's Apache `error.log`, 2026-10-01; the
`Makefile`'s `prod-deploy` comment.*

---

## Known gaps in this list

As of task 08 (2026-10-05):

- **Steps marked ~ are estimates.** Only C1–C5 and B4/B8 were timed (task 07).
  `make prod-build`, the browser check and every pause between steps were not.
- **The dry read with Brian is still to come** (task 08, approach 4). Whatever
  does not make sense out of order is fixed then.
