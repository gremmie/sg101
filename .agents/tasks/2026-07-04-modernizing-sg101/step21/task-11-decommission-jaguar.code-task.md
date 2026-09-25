# Task: Decommission Jaguar, and Retire the MySQL Conversion Chain With It

## Description
End the fallback window and switch jaguar off: confirm its Postfix has gone
quiet, carry out task 01's decisions about the IRC server and the wiki vhost,
retire the Cloudflare Global API Key it held, and clean the block list of what
jaguar left behind. **In the same change, remove the MySQL conversion chain from
the repo** — it exists only to convert a snapshot from a MySQL server that no
longer exists once jaguar is gone.

## Background
**The gate is the decommission, not "the site looks fine."** While jaguar is
warm, a DNS flip back makes its MySQL authoritative again, and any second
roll-forward is another convert-and-verify. Removing the chain during the
fallback window removes the tools for the retry. So it waits for this moment,
and goes with it.

**D5 — Postfix quiet.** Senders cache MX records beyond their TTL, so mail for
`surfguitar101.com` and `themadeira.net` kept arriving at jaguar after the
2026-08-25 MX flip, and jaguar's Postfix was left receiving. Before shutdown:
**no inbound delivery to either domain for a week** in jaguar's mail log.

**Preconditions, both from task 09:** the cutover commit is tagged
(`verify_data.py`'s canonicalization — naive datetimes, booleans, decimal scale,
NULL vs empty string — stays findable through the tag), and the final snapshot
is archived. Git restores the tooling; nothing restores the data.

**What comes out of the repo** (from `plan.md` Step 21, *Tail item*; re-check
each against the tree first, since `requirements-docker.txt` has already gone):
- `mysqlclient` from `requirements.txt`; `default-libmysqlclient-dev`,
  `default-mysql-client` and `pkg-config` from the Dockerfile — present only for
  `tools/pgloader/verify.py` and `verify_data.py`, the two files that
  `import MySQLdb`.
- The `db` service and the `mysql` profile from `docker-compose.yml`.
- `verify.py`, `verify_data.py`, `convert.sh`, `sg101.load`,
  `crosscheck_dumpdata.sh`.
- `DOCKER.md` §6 and §7 — the largest piece, and the one most likely to be left
  behind.
- **The keep-this comments added 2026-08-02** to the requirements file,
  Dockerfile and compose. They are correct until this moment and wrong after it,
  and they read persuasively either way.

**What stays:** `compare_schema.py` (psycopg2 only; compares a database with
what the migrations would build). `post_convert.py` and `smoke.py` are
Django-only; judge each on its own merit.

**The Global API Key** was stored in jaguar's fail2ban action
(`X-Auth-Key`), with account-wide power. Task 06 moved the new host to a scoped
token. Once jaguar is off, roll the Global key so the copy on its disk (and on
bobcat's mirror of it, if `/etc` is mirrored) is dead.

**`AGENTS.md` lists two leftovers this makes removable:** `fabfile.py` (runs
`hg pull --update` against jaguar) and `tools/xapian_installer.sh`. Whether they
go in this change is Brian's call; the fabfile at least has nothing left to
deploy to.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C5 — database migration; §6 — rollback)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  21, *Tail item — retire the MySQL conversion chain*
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — D2, D5
- `DOCKER.md` §6, §7
- `STATUS.md` — task 01 (IRC, wiki vhost), task 05 (bobcat), task 06 (block list)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. D2's window has ended, by Brian's judgment and task 08's definition.
2. D5: jaguar's mail log shows no inbound delivery to either domain for seven
   days; the command and its output are recorded.
3. The IRC server and wiki vhost handled as task 01 recorded. Any DNS records
   that still point at jaguar's address (`173.255.245.115`) are listed from the
   live zones and removed or repointed — including the unproxied `_dc-mx`
   records.
4. jaguar shut down by Brian, and not deleted at once: a final Linode backup or
   image kept for a period Brian chooses.
5. The Global API Key rolled; the scoped fail2ban token keeps working.
6. A last pass over `block_list` now that jaguar's fail2ban has stopped writing:
   stranded `fail2ban` entries older than 14 days removed, before and after
   counts recorded.
7. The MySQL chain removed as listed, after checking each item against the tree.
   `grep -ri mysql` over the repo afterwards shows only history and
   `.agents/` records.
8. The suite and the deprecation gate pass; the image builds without the MySQL
   packages; `docker compose config` is valid with no `mysql` profile.
9. `plan.md`'s Step 21 box ticked and `STATUS.md` updated together.

## Dependencies
- Tasks 09 and 10; the tag and snapshot from task 09
- Brian, for the shutdown itself and the Linode and Cloudflare account actions

## Implementation Approach
1. Check the preconditions exist: `git tag -l`, the snapshot's checksum.
2. D5 first; if mail is still arriving, stop and wait.
3. Carry out the jaguar-side actions with Brian.
4. Then the repo change, on its own commit: remove, grep, build, run the suite
   and the gate.

## Acceptance Criteria

1. **Nothing is lost at shutdown**
   - Given D5's week of silence, the tag and the archived snapshot
   - When jaguar is shut down
   - Then no mail is refused, and the data and tooling remain recoverable

2. **No DNS points at jaguar**
   - Given the live zones
   - When records are listed
   - Then none resolves to jaguar's addresses

3. **The old key is dead**
   - Given the rolled Global API Key
   - When the old key is used against the Cloudflare API
   - Then it is refused, and fail2ban's scoped token still works

4. **The MySQL chain is gone and nothing broke**
   - Given the removal
   - When the image is built and the suite and the deprecation gate run
   - Then all pass, and no application or tool file references MySQL

5. **The step is closed in both places**
   - Given the finished task
   - When `plan.md` and `STATUS.md` are read
   - Then both show Step 21 complete, with the same date

## Metadata
- **Complexity**: Medium
- **Labels**: Decommission, Cleanup, MySQL, DNS, Security, Jaguar
- **Required Skills**: Docker, Python packaging, DNS, Cloudflare API, Postfix logs
