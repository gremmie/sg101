# Task: Dress Rehearsal on the VM — Fresh Snapshot to Serving Site, Timed

## Description
Run the maintenance window's data path end to end on the VM, with jaguar still
live and nothing pointed at the new host: take a fresh production snapshot,
convert it, restore it on the VM, run the first media rsync, migrate, reindex,
and smoke-test the site through Cloudflare on a test hostname. **Time every
step and measure memory at the heavy points**, because the runbook has no
timings and the 4 GB sizing is an estimate. The outputs are numbers and a
corrected runbook, not a site anyone uses.

## Background
The runbook's C section (C1–C5) has never been run as a sequence, and it lists
"ordering and timings are absent" among its own gaps. Every piece has been run
separately: the conversion chain on every data migration in Step 19,
`reindex_search` at 1m35s locally (Step 13 task 06), the backup drill in Step 20
task 06. Never together, never on this host, never against a snapshot taken
this month.

**Where conversion runs is a real question.** `tools/pgloader/convert.sh` reads
MySQL through the dev compose's `db` service (`mysql` profile), and the
production compose has no MySQL. The likely shape is: convert on Brian's machine
in the dev stack, then `tools/pg_snapshot.sh dump`, copy, and restore on the VM.
The alternative is to run the conversion on the VM. Measure the one chosen; the
choice sets part of the window's length.

**The rehearsal host holds real member data and live credentials, which makes
it dangerous in a specific way.** Mail is event-driven through `core.tasks.send_mail`:
a smoke-test forum post notifies real subscribers, a test private message
notifies a real member. The calendar service account writes to the **real**
Google Calendar. User photo uploads go to the real S3 bucket. For the rehearsal:
mail must not reach anyone (Postmark's test token, or the console backend), the
calendar key must be absent or point at a scratch calendar, and anything
uploaded must be cleaned up — `tools/image_smoke.py` already cleans up after
itself. Beat is harmless here (`pick_potd`, `cleanup`, `purge_messages`,
`max_users`, `reconcile_index` only touch this database), but check that
statement against `CELERY_BEAT_SCHEDULE` on the day.

**Collation check.** Restoring a dump rebuilds every index under the VM's
Postgres, so text indexes match its glibc. Confirm the image is the same
`postgres:16` the data was verified on, and read the database's recorded
collation version.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C5 — database migration; §6 — rollback)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — A1, A3,
  B4, B4a, B8, C1–C5
- `DOCKER.md` §7 (conversion) and §8 (snapshots)
- `.agents/planning/2026-07-04-modernizing-sg101/research/database-migration.md`
- `.agents/planning/2026-07-04-modernizing-sg101/research/schema-drift-audit.md`
  — the `oembed` history gotcha (C2)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. A fresh MySQL dump from jaguar, checksummed. It is not committed and is kept
   with the archived pristine dump in `sg101-hg-backup/snapshots/`.
2. Conversion and verification as DOCKER.md §7, including `verify.py`,
   `verify_data.py` and `compare_schema.py`. Anything that differs from the July
   snapshot's results is explained before continuing.
3. Restore on the VM; C2's `oembed` unlock if needed; `migrate`, **reading its
   output** for `elsewhere`'s retired-network warning (A1 firing late);
   `reindex_search`, then `reconcile_search` clean.
4. First media rsync by named upload directory (B4, not `media/` wholesale),
   `/hosted` and `/photos` (B8), then B4a ownership. Record transfer size and
   time; `git status media/` clean afterwards. Commit the three missing badge
   images B4 names.
5. Photo rows checked against files on disk: a count, and spot checks.
6. Mail blocked, the calendar key removed or pointed at a scratch calendar,
   before the stack starts against this data. Show that mail is blocked by
   sending one and seeing where it goes.
7. A proxied test hostname in Cloudflare pointing at the VM, accepted by
   `ALLOWED_HOSTS` and the vhost, and covered by the Origin CA certificate. Run
   `tools/prod_smoke.sh`, B3's real-client-IP check, and `tools/image_smoke.py`
   (after a snapshot, as B4a says).
8. **Timings:** each step's wall-clock time, including the dump from jaguar,
   the copy, the conversion, the restore, `migrate`, `reindex_search`, and both
   rsync passes (run the second one too, to time a delta).
9. **Memory:** peak host memory and swap during `reindex_search`, and during a
   backup run (task 05) happening at the same time as a light load on the site.
   Compare with task 03's idle figure.
10. Everything the rehearsal changed outside the VM is undone: the test hostname
    removed or left deliberately, the scratch calendar, anything in S3.

## Dependencies
- Tasks 03 (VM), 04 (host mail) and 05 (backups)
- Task 06 need not be finished; fail2ban is not part of the data path
- jaguar access for the dump; the dev stack with the `mysql` profile

## Implementation Approach
1. Write down the planned sequence first, as a draft of the window.
2. Take a local pg snapshot before anything writes to the local database.
3. Run each step with `time`, recording results in `STATUS.md` as they come.
4. Where a step differs from the runbook, fix the runbook entry, not only the
   record.

## Acceptance Criteria

1. **The site serves the fresh data**
   - Given the restored database, the synced media and the test hostname
   - When `tools/prod_smoke.sh` and `tools/image_smoke.py` run
   - Then both pass, and a recent forum post and a recent photo from production
     render

2. **Conversion is verified, not assumed**
   - Given the fresh snapshot
   - When the verification tools run
   - Then their results are recorded, and any difference from the July run is
     explained

3. **No member was contacted**
   - Given the rehearsal ran against real member data
   - When Postmark's activity log and the calendar are checked afterwards
   - Then no message reached a real address and no calendar event changed

4. **Every step has a time**
   - Given the rehearsal
   - When it finishes
   - Then each step's duration is recorded, and their total estimates the
     window's length

5. **Memory is measured under load**
   - Given `reindex_search` and a backup run
   - When peak memory and swap are read
   - Then the figures are recorded against the 4 GB plan, with a
     recommendation: stay on shared 4 GB, or resize

6. **Search is complete**
   - Given the restored and reindexed database
   - When `reconcile_search` runs
   - Then it reports no drift

## Metadata
- **Complexity**: High
- **Labels**: Cutover, Data Migration, PostgreSQL, Rehearsal, Performance
- **Required Skills**: pgloader, PostgreSQL, rsync, Docker Compose, Cloudflare DNS
