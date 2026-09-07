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
*Source: `STATUS.md`; the original audit is in the Step 15 record.*

### A3. Delete the 32 pending `gcalendar` rows in production, not just locally
Step 21 converts a **fresh** production snapshot, so rows deleted only in the dev
database come back with it and land in the pending queue on the new host.
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

### B1. `secrets/gcal-service-account.json`
Git-ignored as a whole directory and **backed up nowhere**. Without it the
calendar does not come up on the new host, and it cannot be recovered — only
reissued from the Google console.
*Source: `STATUS.md` § Step 18; memory `modernizing-sg101-planning`.*

### B2. `.env`
The only other un-backed-up artifact. Regenerate from `secrets.json` in the hg
backup if it is ever lost.
*Source: memory `modernizing-sg101-planning`; `AGENTS.md`.*

### B3. Real client IP at the new front door
**Nothing in the repo sets it.** The rewrite that makes every `REMOTE_ADDR`
reader correct exists only as Apache config on the box being retired. Whatever
fronts the new VM needs the analogue — nginx `ngx_http_realip_module` with the
Cloudflare ranges — or on cutover day every IP the site records silently becomes
a proxy address. Step 20 builds it; cutover verifies it against a real request.
*Source: `research/dmarc-readings.md` § "A cutover requirement this exposed".*

### B4. The media tree
**Nothing has been migrated.** The 4,577 local-disk user photos ride this step's
rsync; the S3 work in Step 15 changed where *new* uploads go, not where the old
ones are.
*Source: `STATUS.md` § Step 15; `implementation/plan.md` Step 21.*

## C. The maintenance window

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
Low-TTL cutover in Cloudflare.

## D. After

### D1. One real message with headers
`dkim=pass d=surfguitar101.com` and `spf=pass`. Task 02's delivery-side criteria
were left unmet **by design** — they cannot be satisfied before there is a
production environment to satisfy them in.
*Source: `STATUS.md` § Step 16 task 02, "What task 02 does not close".*

### D2. Keep jaguar warm
As an sg101 fallback the window ends in 1–2 weeks. **"Then decommission" does not
gate on that** — it gates on the separate jaguar project completing, which has
its own plan at `~/workspaces/bgn/jaguar-decommission/`.
*Source: `implementation/plan.md` Step 21, corrected 2026-08-23.*

---

## Known gaps in this list

Stated so the file is not mistaken for complete:

- **The smoke checklist is not here.** A Step 13 version exists in
  `STATUS-archive-steps-01-15.md`; whether it is still current is unchecked.
- **No rollback procedure is written down** beyond "keep jaguar warm and flip
  DNS back". What that means for data written to the new host during the window
  has not been decided.
- **Steps 19 and 20 are unfinished**, and both will add entries. Step 19 Phase C
  alone has two tasks left.
- **Ordering and timings are absent.** The sections are grouped by phase, not
  sequenced, and nothing here estimates how long the window needs to be.
