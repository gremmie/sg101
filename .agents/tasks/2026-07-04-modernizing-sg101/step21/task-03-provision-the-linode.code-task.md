# Task: Provision the Linode and Stand Up the Production Stack on It

## Description
Create the Linode, prepare it as a Docker host, and bring up
`docker-compose.prod.yml` on it with real configuration: `.env`, the secrets,
the Cloudflare Origin CA certificate, log rotation for both Django and Apache,
and the origin firewall. **Also fix the number of web and worker processes in
configuration**, a repo change, so memory use follows a setting rather than the
machine's CPU count. The stack runs against an empty or scratch database here;
real data is task 07's.

## Background
**Decided 2026-09-24: Linode, 4 GB shared CPU, in a core compute region** —
Brian's choice, on familiarity. Linode lets a core-region instance change plan
type later (shared ↔ dedicated) keeping its data, configuration and IP
addresses, with a warm or cold resize. So starting on shared is cheap to undo.
Going *down* a size is the awkward direction, because the disk must shrink first.

**Sizing, measured 2026-09-24:**
- **jaguar** (8 GB, 4 CPUs, up 154 days): 2.4 GB used by programs, 4.3 GB file
  cache, load average 0.04. Apache with every Django site inside it 1.1 GB,
  MySQL 780 MB. That box also runs the wiki, three other sites, IRC and Postfix.
- **The local production stack**, per process: gunicorn workers ~110 MB RSS
  each, celery children ~97 MB, beat ~98 MB, Postgres ~490 MB container
  (`shared_buffers` 128 MB, `work_mem` 4 MB, `max_connections` 100), Redis
  39 MB, proxy 15 MB. Database 1.3 GB.
- **Estimated on 2 vCPU / 4 GB:** ~1.7–2.0 GB in use, leaving ~2 GB of cache —
  more than the whole database.

**The worker counts are the catch.** The Dockerfile starts gunicorn with
`${GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))}`, and the prod compose runs
`celery -A sg101 worker -l info` with no `--concurrency`, so prefork defaults to
the CPU count. Locally (10 CPUs) that is **21 gunicorn workers and 10 celery
children, ~2.5 GB before any traffic.** A resize would silently change memory
use the same way. `plan.md` has carried "pin the celery worker's concurrency"
since Step 12 task 03 for a second reason too: it decides whether tasks for the
same object can run out of order, which the search index's `indexed_at` guard
exists to survive. Name both numbers in configuration.

**Runbook items this task performs:** B1 (calendar key), B2 (`.env`), B4a
(ownership, re-run after any rsync), B5 (Origin CA cert), B6 (firewall — after
smoke, per its ordering), B10 (Django logrotate), B11 (Apache log rotation —
**undecided, and the runbook says DNS must not flip without it**), B13 (`make`).
B3's real-client-IP check needs traffic through Cloudflare, so it runs once a
test hostname points at the VM.

**Collation.** The database is collated `en_US.utf8`, glibc's collation, and
glibc comes with the pinned `postgres:16` image, not the host. Running our own
container keeps that pinned. What must not happen is a different Postgres base
image on the VM than the one the data was verified on.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (C10 — production hardening & deployment)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md` — B1, B2,
  B4a, B5, B6, B10, B11, B13
- `DOCKER.md` §10 — running the production stack
- `.agents/planning/2026-07-04-modernizing-sg101/research/hosting.md`
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  21, *Collation is part of the host decision*; the celery concurrency item

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. **Repo:** the prod compose passes celery an explicit `--concurrency` from an
   environment variable, and `.env.example` documents both it and
   `GUNICORN_WORKERS` with the values chosen for a 2-vCPU host and the memory
   figures above. The `nproc` fallback in the Dockerfile may stay for local use,
   but production sets both.
2. Decisions for Brian, recorded before provisioning: region; distribution and
   version (the runbook assumes Debian or Ubuntu); whether the origin publishes
   IPv6 (it decides B3 step 4 and the firewall's IPv6 half); SSH source for the
   firewall; port 80 `allow` or `drop`; how Apache's logs rotate (B11:
   `postrotate` graceful vs `rotatelogs`).
3. The admin account is uid 1000, or the image is built with a matching
   `APP_UID` (B4a).
4. Host baseline: SSH keys only, no password login; automatic security updates;
   Docker Engine and the compose plugin from Docker's repository; `make`; a swap
   file, since Linode's default is small and the memory estimate is an estimate.
5. The checkout lives where `logrotate/sg101` expects (`/srv/sg101`) or the
   installed copy is edited to match (B10).
6. `.env`, `secrets/gcal/gcal-service-account.json` and `secrets/tls/origin.{pem,key}`
   are in place, readable only by the admin account and the container. Record
   where each came from; none of them is backed up anywhere else (B1, B2, B5).
7. **The firewall is created with the Linode**, in the create flow, so the VM
   is never exposed without one: inbound policy drop, one rule allowing TCP 22
   (from Brian's address if stable, otherwise anywhere), outbound accept. Its ID
   is `FIREWALL_LINODE_ID`; no second firewall is created (Linode attaches one
   per instance). Once the stack is healthy, add a **temporary** rule allowing
   443 and 80 from Brian's address only, run `tools/prod_smoke.sh <VM address>`
   from Brian's machine, then `make firewall-apply` — which replaces the rule
   set and so removes the temporary rule — then `make firewall-check` and B6's
   refusal checks.
8. Memory is measured on the VM with the stack idle, and compared with the
   estimate above.

## Dependencies
- Task 02 (the firewall adapter), for requirement 7
- A Linode account; a Cloudflare Origin CA certificate for the zone
- Brian, for the decisions in requirement 2

## Implementation Approach
1. Make the repo change first, locally: set both values, restart the local
   prod stack, count processes, and measure memory with `docker stats`.
2. Put the decisions to Brian with a recommendation for each; record them.
3. Provision; lay down the host baseline; clone; place secrets; build; start.
4. Work through the runbook's B items in order, recording each result in
   `STATUS.md` and correcting any runbook entry that turned out wrong.

## Acceptance Criteria

1. **Worker counts come from configuration**
   - Given the prod stack started with the chosen values on any machine
   - When gunicorn workers and celery children are counted
   - Then the counts equal the configured values, not a function of `nproc`

2. **The stack runs on the VM**
   - Given the provisioned Linode with secrets in place
   - When `docker compose -f docker-compose.prod.yml up -d` runs
   - Then every service reports healthy and `tools/prod_smoke.sh <VM address>`
     passes

3. **The origin refuses outsiders**
   - Given the firewall applied after the smoke run
   - When Brian's machine connects directly to the VM on 443 and 80, over each
     published address family
   - Then no HTTP response comes back — the temporary rule for Brian's address
     is gone — SSH still works from where it should, and `make firewall-check`
     reports OK

4. **Never exposed without a firewall**
   - Given the Linode's creation
   - When its network settings are read before first boot completes
   - Then a firewall is attached, dropping everything inbound except SSH

5. **Logs rotate and the processes follow**
   - Given the Django logrotate config and the chosen Apache mechanism
   - When a forced rotation runs and the site then serves a page and queues a task
   - Then new lines land in the new files, for Django and for Apache both

6. **Memory matches the estimate, or the difference is explained**
   - Given the idle stack on the VM
   - When memory is read per container and for the host
   - Then the figures are recorded next to the 1.7–2.0 GB estimate

7. **Suite and gate still pass**
   - Given the repo change
   - When the suite and the deprecation gate run as `AGENTS.md` describes
   - Then both pass

## Metadata
- **Complexity**: Medium
- **Labels**: Provisioning, Linode, Docker, TLS, Logrotate, Firewall, Deployment
- **Required Skills**: Linux administration, Docker Compose, Apache, logrotate,
  Cloudflare
