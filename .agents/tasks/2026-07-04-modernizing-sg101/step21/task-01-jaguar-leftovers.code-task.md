# Task: Settle Jaguar's Leftovers — Archive sg101's Apache Logs, Decide IRC and the Wiki Vhost

## Description
Three things on jaguar belong to sg101 and are not yet provided for: its Apache
logs, which have never been backed up; a public IRC server and bot; and the
still-enabled `wiki.surfguitar101.com` vhost. **The logs are time-sensitive and
go first** — they delete themselves on a rolling window, so every week this task
waits loses a week of them. The other two are decisions for Brian, recorded so
that shutting jaguar down (task 11) does not switch off a live service by
accident.

## Background
These came out of the jaguar decommission project's research pass
(`~/workspaces/bgn/jaguar-decommission/`, closed 2026-09-23) and were filed
under Step 21 in `plan.md` because they are sg101's by content. The project that
found them is closed; nothing else will pick them up.

**1. The logs.** bobcat's nightly rsync excludes every `access.log*` and
`error.log*` via `bobcat:/svr/scripts/jaguar_exclude.txt`, and runs `--delete`,
so `bobcat:/svr/backups/jaguar/www/*/log/` is empty. jaguar's logrotate keeps
about eight weeks (`rotate 8`, weekly). The decommission project archived *its*
three sites' logs on 2026-08-24; **sg101's and the wiki's were never archived.**
They are the evidence base for much of this plan — the Cloudflare IP window,
the autocomplete request count, the `/hosted` and `/photos` request count — and
questions of that kind will keep coming after cutover. `auth.log` and
`sg101.log` live under the Django project (`/svr/django-sites/sg101/...`) with
their own retention (see `AGENTS.md`), and are in scope too.

**2. The IRC server.** `ngircd` listens on `0.0.0.0:6667` and `0.0.0.0:6697`,
and `/svr/irc/sg101bot/sg101Bot.py` runs **as root** beside it, both live since
Apr 23. Step 4 pruned the Django app *named* `irc` — a status page — which never
touched the daemon. `/svr/irc` is inside bobcat's mirror, so the code survives
either way; only the running service dies with the box. An unattributed listener
on `127.0.0.1:23352` was never identified (attributing it needs root).

**3. The wiki vhost.** `/etc/apache2/sites-enabled/wiki.surfguitar101.com.conf`
still serves MoinMoin via `mod_wsgi`. Step 19 retired the wiki *in this repo*
and archived its content under `archive/wiki/`. Whether the vhost was left up
deliberately was never recorded. Its fail2ban jail, `wiki-abuse`, was
jaguar's busiest in the last four weeks (225 bans, measured 2026-09-24 from
`/var/log/fail2ban.log*`), so it is still drawing traffic.

**The evidence grade matters.** Several facts above come from the
`jaguar_linode_cfg` repo, which Brian flagged as incomplete and out of date.
Re-measure on the box before acting on any of them.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§6 Error Handling, Safety & Rollback)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` —
  Step 21, the decommission inventory
- `~/workspaces/bgn/jaguar-decommission/research/backups-and-logs.md` — how the
  other project archived its logs, and the exclude file
- `~/workspaces/bgn/jaguar-decommission/research/live-inventory.md` — the
  IRC and vhost findings

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Copy every surviving sg101 and wiki Apache log from jaguar — current and
   rotated, compressed or not — plus `auth.log*` and `sg101.log*`, to Brian's
   machine, preserving file names and modification times.
2. Record, per log family, the date range the archive actually covers, measured
   from the first and last lines rather than from file dates.
3. Checksum the archive and record where it lives. It is not committed to the
   repo — it holds client IP addresses.
4. Stop the loss going forward for as long as jaguar runs: either keep
   archiving, or remove the log lines from `jaguar_exclude.txt`. This is Brian's
   box and Brian's call; present both.
5. Record Brian's decision on the IRC server: retire it, or move it (and if
   moved, where, and under a non-root user).
6. Record Brian's decision on the wiki vhost: retire now, leave until jaguar
   goes, or replace with a static page or redirect. Include what happens to
   the `wiki.surfguitar101.com` DNS record in each case.
7. Anything these decisions add to cutover day or to shutdown goes into
   `cutover-runbook.md`, not here.

## Dependencies
- SSH to jaguar as `brian@jaguar` (the log files are readable by the `adm`
  group; confirm Brian is still in it)
- Enough local disk: a single week of sg101's `access.log` was 164 MB on jaguar
  (runbook B11), so expect gigabytes uncompressed
- Brian, for requirements 4–6

## Implementation Approach
1. List what exists first: `ls -la` over the log directories, so the archive can
   be checked against the source for completeness.
2. `rsync -a` the files down; do not decompress or rotate anything on jaguar.
3. Measure coverage per family from content (`head -1`, `tail -1`, `zcat` for
   the `.gz` files).
4. Write the record into `STATUS.md` under a Step 21 task 01 section, naming
   the archive path and checksums.
5. Put the IRC and wiki questions to Brian with the facts above and a
   recommendation for each; record the answers.

## Acceptance Criteria

1. **Archive is complete against the source**
   - Given the file listing taken on jaguar before copying
   - When it is compared with the local archive
   - Then every file is present with the same size, and the comparison is recorded

2. **Coverage is measured, not assumed**
   - Given the archived logs
   - When the first and last timestamps are read from each family
   - Then the recorded range comes from those lines, not from file dates

3. **The archive is not in git**
   - Given the archive holds client IP addresses
   - When `git status` is run in the repo
   - Then no log file appears, and the archive path is outside the working tree
     or git-ignored

4. **Both services have a recorded fate**
   - Given the IRC server and the wiki vhost
   - When this task closes
   - Then `STATUS.md` records Brian's decision for each, and any action they need
     at cutover or shutdown is an entry in `cutover-runbook.md`

5. **No source changes**
   - Given this task is archiving and decisions
   - When it closes
   - Then the application code is unchanged and the suite does not need to run

## Metadata
- **Complexity**: Low
- **Labels**: Operations, Logs, Decommission, Jaguar, Time-Sensitive
- **Required Skills**: rsync, shell, log formats
