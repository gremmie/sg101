# Project Status — Modernizing SG101

**Last updated:** 2026-09-26
**Methodology:** Prompt-Driven Development (`/agent-sops:pdd`)

## Where things live — split 2026-08-26

This file had reached **685 KB / 11,828 lines**, past what can be read in one
pass, and it had started to contradict itself: on 2026-08-25 a paragraph here
restated the warm-up as still pending, 2,100 lines from the 2026-08-20
measurement that dropped it. Nobody had the whole document in view, which is the
only way that goes unnoticed.

| File | Holds |
|---|---|
| **`STATUS.md`** (this file) | the **active** step and everything still pending |
| **`STATUS-archive-steps-01-15.md`** | Steps 1–15, closed, plus the original PDD planning record |
| **`research/dmarc-readings.md`** | the twenty-three DMARC aggregate readings — a periodic instrument log |
| **`cutover-runbook.md`** | what to do on cutover day, and only that — started 2026-09-06, owned by Step 21 |

**The split is by kind, not by size.** A reading log has its own natural home and
its own growth rate; so does a record of finished steps. Splitting on size alone
is what produced the file that had to be split.

**Heading sweep 2026-09-04.** Eight section headings still read `UNCOMMITTED,
awaiting review` for work that was committed and pushed days earlier — Step 17
task 04, `question2`, the agreement labels; Step 18 tasks 02, 04, 05 and the
follow-up; Step 19 Phase A. Nothing was pending: the tree was clean and the branch
level with `origin`. Corrected to name each commit.

**The rule that prevents the next one: a heading claiming a state is a claim, and
it goes stale the moment the state changes.** This is rule 1 below failing in the
one place nobody re-reads — the heading they scrolled past to reach the content.
When work is committed, the heading is part of the commit.

**Two rules this document is kept under, both of them earned:**

1. **One claim, one home.** A decision lives in exactly one place and everything
   else points at it. The warm-up error happened because a decision lived in a
   task journal while a status paragraph restated it from memory.
2. **A section is about one task, and it gets closed.** Task 03's section reached
   3,539 lines — 30% of the file — because it was opened on 08-17, never closed,
   and absorbed task 10's work, eleven readings and a decision belonging to task
   07. A running journal wants a log file, not a status heading.

## Step 21 task 07a — a member beta before the cutover — PLANNED 2026-09-26

**A twelfth task file, `step21/task-07a-member-beta.code-task.md`, added at
Brian's request.** None of the eleven put the new stack in front of anyone but
Brian before the DNS flip. Task 07a keeps task 07's rehearsed site up for a few
days at `beta.surfguitar101.com` for a handful of invited members, who log in as
themselves; everything they write is discarded when C1 restores a fresh
snapshot. It sits between 07 and 08. The task file holds the decisions and the
reasoning; this section only points at them.

**Decided 2026-09-26 (Brian), recorded in the task:** access through Cloudflare
Access (Zero Trust organization `sg101-beta` created, Free plan, no application
yet); mail through a new allowlisting email backend, the only code the task
adds; the real Google Calendar workflow runs end to end, with beta events
deleted by hand afterwards; testers told not to donate; findings compiled at the
end, possibly as GitHub issues, and Brian decides which delay task 09.

**Runbook A3 marked done:** Brian deleted the 32 pending `gcalendar` rows in
production (reported 2026-09-26, date not recorded). **Not yet confirmed from
data** — task 07a's requirement 4a counts pending events in the rehearsal
snapshot, and task 09 falls back to the final snapshot if that did not happen.

## Step 21 task 03 — leopard provisioned and hardened; worker counts required — DONE 2026-09-27: stack running on leopard, smoked, firewalled, rotation proved; memory re-read owed at task 07

**Where it stands (2026-09-27):** secrets B1 B2 B5 in place, the stack built and
healthy on leopard, the smoke run passed through a temporary rule, B6 applied and
the refusal measured, B10 and B11 proved on the VM for every writing process, and
memory read (provisional; PostgreSQL is empty). Details in § 2026-09-27 below.
The repo half of the 775 finding is in (its rationale corrected the same day, below), and criterion 7 passed. **Carried
forward:** criterion 6's figure is re-read after task 07 restores a snapshot.

**The checkout is `/svr/sg101`, not `/srv/sg101`** (Brian, 2026-09-25), matching
jaguar's `/svr/django-sites/`. `logrotate/sg101` and `backup/sg101-backup.service`
now default to it, so nothing is edited at install and B10's `sed` line is gone.
Both files say the spelling is deliberate. The `/srv/...` paths in `apache/` and
on the right-hand side of the prod compose mounts are **inside the proxy
container** and are unchanged. Requirement 5 is met by the new defaults.

### Worker counts come from configuration (acceptance criterion 1 — met locally)

`docker-compose.prod.yml` now **requires** `GUNICORN_WORKERS` (in the shared
`x-app` environment) and `CELERY_WORKER_CONCURRENCY` (the worker's
`--concurrency`), both through `${VAR:?…}`. Without either, every prod compose
command stops and names it. They are **5 and 2**, Brian's choice on the 2-vCPU
estimate. `.env.example` explains both, the Dockerfile's `nproc` fallback stays
for any other use of the image, and DOCKER.md §10 and runbook B2 say production's
`.env` needs them. `secrets.json` never held them.

The service-level `environment:` could not carry `GUNICORN_WORKERS`: YAML merge
is shallow, so a map there would *replace* `x-app`'s and drop
`DJANGO_SETTINGS_MODULE`.

| local prod stack (10-core Mac) | gunicorn workers | celery children |
|---|---|---|
| before | **21** | **10** |
| either variable unset | compose refuses, naming it | |
| `.env` 5 / 2 | **5** | **2** |
| shell override 3 / 1 | 3 | 1 |
| back to `.env` | 5 | 2 |

All services were healthy throughout. Idle memory on the Mac: web 412, worker 163,
beat 94, proxy 15, postgres 487, redis 39 MiB, about 1.2 GB. That is not the
VM figure criterion 6 asks for. **Suite 1311 OK, gate 1311 OK.** Brian's local
`.env` has had the two lines appended.

### Decided 2026-09-25 (Brian, each on the recommendation)

| | decision |
|---|---|
| region | jaguar's |
| distribution | **Ubuntu 26.04 LTS** (support to 2031); jaguar is still on 14.04 |
| origin IPv6 | **IPv4 only**, no AAAA; Cloudflare still serves visitors IPv6. B3 step 4 and the IPv6 refusal checks drop out |
| SSH source | **anywhere, keys only** |
| port 80 | **drop**: the zone's SSL mode is **Full**, so Cloudflare reaches the origin on 443 only |
| Apache logs (B11) | **host logrotate + graceful**, weekly, 26 kept; a block in `logrotate/sg101` |
| security reboots | automatic, **10:00 UTC**, only when an update needs one |
| `brian`'s password | set (for `sudo` and the Lish console) rather than password-free `sudo` |

**Full (strict) is safe to switch on now, and that is Brian's click.** jaguar's
origin certificate is Let's Encrypt for `surfguitar101.com` and `www`, issued
2026-08-18 and expiring 11-16. Its renewals work, and leopard will carry the
Origin CA certificate.

**Apache follows a rename, measured locally.** With `access.log` renamed and no
reload, the next request landed in the renamed file. After a new file was
created and `apache2ctl -k graceful` sent, requests landed in the new one. The
new block parses under Ubuntu 26.04's logrotate. The forced rotation on the VM
is still owed.

### leopard — host setup, done 2026-09-25

**`leopard`, 192.0.2.13**, Linode 4 GB shared: 2 CPUs, 3.9 GB, 79 GB disk,
unpartitioned `/dev/sda`. **Host key ED25519
`SHA256:qkv+mWaLpvHaVJg6I3E0OXWlRChXtaBdeUo/bCz0nUk`**, recorded on first contact.

**Firewall 175729041 (`leopard`)** is attached to Linode interface 916020, and it
is the only entity attached. **It was created with no inbound rules**: the SSH
rule was not saved in the create flow, so leopard was unreachable on every port,
which is what criterion 4 asks for, if not quite as intended. With Brian's OK the
task 02 tool applied the final plan (`FIREWALL_SSH_FROM=anywhere`,
`FIREWALL_HTTP=drop`): 22 from anywhere, 443 from the 22 Cloudflare ranges.
`firewall-check` OK. Port 22 then took about a minute to answer.

- **Updates:** full upgrade to kernel 7.0.0-34, rebooted, running it.
  **Linode's Ubuntu image ships a broken debconf value**:
  `grub-pc/install_devices` holds the literal `multiselect`, so the upgrade
  failed on `grub-install` to a device of that name. Linode boots the disk with
  its own GRUB reading `/boot/grub/grub.cfg`, so the fix is an empty device list
  (`install_devices_empty true`). The regenerated `grub.cfg` then booted the new
  kernel, which proves it.
- **`brian`, uid 1000**, in `sudo` and `docker`, with root's authorized key.
  Ubuntu 26.04's `sudo` is **sudo-rs**. A successful `sudo -v` leaves no log
  line, so the check rests on Brian's report. The first try failed because both
  `passwd` prompts were for brian's *new* password.
- **SSH:** `/etc/ssh/sshd_config.d/01-leopard.conf`, sorted first because sshd
  keeps the first value it reads. It sets no password and no keyboard-interactive
  login, and **`PermitRootLogin no`**. `sshd -T` confirms it; root gets
  `Permission denied (publickey)`.
- **Security updates:** Ubuntu's default origins (the release, `-security`, and
  the two ESM security channels) plus `/etc/apt/apt.conf.d/52leopard-reboot`. The
  dry run was clean. Docker's repository is not an origin, so Docker upgrades
  stay manual.
- **Docker** 29.8.1 and Compose v5.5.1 from `download.docker.com`, a `resolute`
  build. The key fingerprint `9DC8…CD88` matches Docker's published one.
  `hello-world` runs as brian.
- **`make` 4.4.1, `git` 2.53, and a 2 GB `/swapfile`** on top of Linode's 496 MB
  partition, with `vm.swappiness = 10`.
- **Deploy key:** `~brian/.ssh/sg101_deploy`, ed25519, with no passphrase
  because nobody is there to type one. It is registered on `gremmie/sg101` as
  **"leopard (read-only)", deploy key ID 164483639**. It has no write access and
  is scoped to this one repo. `~brian/.ssh/config` makes `github.com` use it and
  nothing else. GitHub's ED25519 host key was pinned in `known_hosts` after its
  fingerprint `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU` matched the
  published one. `ssh -T` greets `gremmie/sg101`, the repo and not the account,
  which is how a deploy key shows itself. To revoke it:
  `gh repo deploy-key delete 164483639 -R gremmie/sg101`, or the repo's
  Settings → Deploy keys.
- **Checkout at `/svr/sg101`**, created with
  `sudo install -d -o brian -g brian /svr/sg101` and cloned as brian, not root,
  so `git pull` needs no `sudo`. `/svr` is `root:root 755`. Every file is
  brian's (uid 1000). It was cloned on `modernize` at `c95002ae`, clean,
  tracking `origin`, and was at `f99ba4f9` by 2026-09-27.
- **Then:** B1, B5, build and start — § 2026-09-27 below.

### `secrets/` was baked into the image, and the calendar key was unreadable there — fixed 2026-09-26

Found while preparing B1, before any secret went to leopard. **`.dockerignore`
listed `.env` but not `secrets/`**, so the Dockerfile's `COPY . /app` put the
whole directory in `sg101-app:prod`. The local image held
`/app/secrets/gcal-service-account.json` and `/app/secrets/tls/origin.key`; on
leopard it would also have held `secrets/backup.env`, the credential the compose
file keeps out of the application containers on purpose.

**And the calendar reached its key only through that copy, which it could not
read.** Nothing in the production compose mounted `secrets/` into `web`, so
`GCAL_CREDENTIALS_PATH` resolved only to the baked file: `root`, mode 600, in a
container running as `sg101` (uid 1000). Read as that user: **`Permission
denied`**. Synchronize would have failed on the new host. The suite cannot see
this, and the dev stack hides it because it bind-mounts the whole checkout.

**Fix:** `secrets` added to `.dockerignore`; the key moves to
`secrets/gcal/`, and that directory alone is mounted read-only into `web`, the
only process that uses it (the admin's Synchronize view; no Celery task does).
Not the whole of `secrets/`, which would hand the application the TLS key and
the backup credential. `.env.example`, DOCKER.md's setup table and runbook B1
give the new path; Brian's local key and `.env` line were moved to match.

| after, local prod stack rebuilt | |
|---|---|
| `/app/secrets` in the image | **absent** |
| `web`, as uid 1000 | sees only `secrets/gcal/`; key readable |
| `worker` | no `/app/secrets` |
| `Calendar(...)` in `web` | loads `sg101-calendar@api-project-786263548002.iam.gserviceaccount.com` (constructed only; nothing synced) |
| services | all healthy |

**Suite 1311 OK, gate 1311 OK.**

**No real Turnstile key existed on 2026-09-26** (Brian; nothing in these docs
recorded one). The development `.env` runs on Cloudflare's always-pass test keys,
so leopard's `.env` cannot be a copy of it. Runbook B2 now says so, and that the
widget's hostnames need `beta.surfguitar101.com` for task 07a.

### B2 — the real Turnstile widget, and leopard's `.env` — done 2026-09-27

**Brian created a production Turnstile widget and wrote leopard's `.env`**
(reported 2026-09-27; the file is dated 03:29 that morning). The widget's
hostname list, including `beta.surfguitar101.com`, is **on Brian's report and
not checked from here**.

Checked on leopard by variable *name*, never value: `/svr/sg101/.env` is
`brian:brian 600`, and it sets every variable `.env.example` leaves
uncommented. `DB_ENGINE=postgresql`, `GUNICORN_WORKERS=5`,
`CELERY_WORKER_CONCURRENCY=2`, and `GCAL_CREDENTIALS_PATH` gives the
`secrets/gcal/` path from the fix above. Neither of Cloudflare's always-pass test
keys appears in it. The checkout is at `f99ba4f9`, level with `origin`, so it
already has the `.dockerignore` fix and the `gcal` mount.

### 2026-09-27 — secrets, the stack, the smoke run, the firewall, rotation, memory

**B1.** The calendar key copied to `secrets/gcal/` (uid 1000, 600); SHA-256
matches the local copy. `secrets/` and both subdirectories are 700, and git on
leopard reports `secrets/` ignored.

**B5 — the key never left leopard.** Key and CSR generated on the host, SANs
`surfguitar101.com` and `*.surfguitar101.com` (the wildcard covers `www` and task
07a's `beta`). Brian issued the Origin CA certificate from the CSR in the
dashboard. Cert and key public keys hash identically; valid 2026-09-27 to
**2041-09-23**. CSR deleted; `origin.key` 600, `origin.pem` 644. Issuing it
changes nothing for jaguar: Cloudflare installs an origin certificate nowhere.

**Build and start.** `docker compose -f docker-compose.prod.yml build`, 2m16s on
2 vCPUs, **without** the backup profile: that profile needs
`secrets/backup.env`, which is B12. `var/` created per DOCKER.md §10.
`migrate` against the empty database, then all six services healthy.
`check --deploy`: W005 and W021 only, both deliberate (§ HSTS, 2026-09-20).

**The start sent ten error mails, and they were useful.** Between up and
`migrate`, the `web` and `proxy` health checks rendered the home page against no
tables: ten `relation "django_site" does not exist` 500s, 20:03:48–20:04:35 UTC,
each mailed to ADMINS as `ERROR (internal IP)` (the checks come from
`127.0.0.1`). Brian's copy's headers: Postmark accepted it at **20:03:49**, one
second after leopard logged the first error, the headers themselves cannot name
the submitting host, so the timing is the attribution. It then went Postmark
`sc-ord-mta114` → Cloudflare Email Routing (`admin@`) → Gmail, with **SPF, DKIM
`d=surfguitar101.com` (selector `20260817033844pm`) and DMARC passing at both
Cloudflare and Gmail** under `p=quarantine`. Runbook D1's check, seen from
leopard before the flip; D1 itself still runs after it. **Any fresh start does
this** — task 07's rehearsal and the cutover included — unless `postgres` is
brought up alone, restored and migrated before the rest.

**Smoke, through a temporary rule.** Brian added 443 and 80 from
`192.0.2.12/32`; `tools/prod_smoke.sh 192.0.2.13` passed all 21 checks.

**B6.** `ranges-check` OK (15 + 7). `check` beforehand differed by exactly the two
temporary rules. `apply`, then `check` **OK**. From the same Mac, 20 s later,
443 and 80 at the origin: **no HTTP response, curl exit 28**. Minutes earlier
the same address was served, so the refusal is the firewall's. SSH still
connects.

**B10/B11 — the 775 directories. CORRECTED the same day: the nightly run was
never affected.** A root `--debug` of `/etc/logrotate.d/sg101` skipped every
file: `parent directory has insecure permissions`. DOCKER.md's `mkdir -p
var/log/...` takes the umask; the Mac's 022 gave 755, Ubuntu's 002 for users
gives **775**. An unprivileged `--debug` does not run the check. `chmod 755 var
var/log var/log/django var/log/apache` on leopard; `var/maintenance` and
`var/public/*` stay 775.

**What was first recorded here, "as installed, logrotate would have rotated
nothing", was wrong.** Every run above named `/etc/logrotate.d/sg101` directly.
The nightly `logrotate.service` reads `/etc/logrotate.conf` first, and Ubuntu's
sets **`su root adm` globally**. With an `su` directive, logrotate skips the
permission check altogether, which is what its own error message says. Found
when the heartbeat's alarm proof, a 775 directory under the real service,
**exited 0 and rotated**. So the test ran logrotate in a way the host never
does. The `chmod`, DOCKER.md's `umask 022` and the runbook line stay: they cost
nothing and keep a hand-run of the file clean. The reasons given for them are
corrected below and in the files. `16131aad`'s commit message repeats the wrong
claim; this paragraph supersedes it.

**The global `su` was then checked for the thing it could break**: the owner of
the new file. `sudo logrotate --debug --force /etc/logrotate.conf`, as the
service runs it: it keeps euid 0, switches egid to `adm` (4) for the rotation,
and reports `creating new /svr/sg101/var/log/django/sg101.log mode = 0644 uid =
1000 gid = 1000`. The containers can still write it.

**A failure would have been silent.** `logrotate/sg101` said cron mails the
report. On leopard logrotate runs from `logrotate.timer`, and there is no
`sendmail`, so a failure reaches only the journal. That part stands, and is why
the heartbeat (below) exists.

**Then forced, and every writer followed** — the new line in the new file, none
in `.1`:

| writer | how made to write | landed in |
|---|---|---|
| Apache | graceful from `postrotate`, then 6 requests from the host | `error.log` (the reload notice), `access.log`; `access.log.1` has none |
| Celery worker | `user_stats_task.delay(999999)` | `sg101.log` |
| gunicorn workers | 8 POSTs to `/contact/` without CSRF → 403 warnings | `sg101.log`, all 8 |
| beat | its 20:30 UTC `max_users` send | `sg101.log`; no scheduler line in `.1` after the rotation |

The 404s wrote nothing to Django's log, which is why the CSRF POSTs were needed.
The Django log's timestamps are Central time, the rest UTC.

**Memory (criterion 6), idle, 20:19 UTC — provisional:**

| | MiB |
|---|---|
| web (5 workers) | 454 |
| worker (2 children) | 170 |
| beat | 93 |
| postgres | 39 |
| proxy | 13 |
| redis | 9 |
| containers | ~778 |
| host `used` | 1,384 of 3,910; swap 0 used; 2,526 available |

Under the 1.7–2.0 GB estimate, but **PostgreSQL is empty** (487 MiB on the Mac
with data), so this does not yet answer the criterion. Re-read after task 07
restores a snapshot.

**The repo half of the 775 finding (Brian approved both).** DOCKER.md §10 now
creates `var/` under `(umask 022 && mkdir -p ...)`. Under umask 002 on the Mac:
plain `mkdir -p` gave 775 throughout; `mkdir -p -m 755` gave 755 on the last
directory only, `var` and `var/log` still 775; the umask form gave 755 on all
three. The `logrotate/sg101` comment no longer says cron mails the report; it
names `sudo journalctl -u logrotate`, and the `sudo` is measured: `brian` is in
neither `adm` nor `systemd-journal`, and without it the journal shows no
entries. The unit has no `OnFailure=`. **Nothing alerts on a failed rotation**;
Brian chose option 1, a heartbeat (below). leopard's
installed copy matches its checkout; the change is a comment, so re-copying it
after the next pull is tidiness, not a fix.

**Criterion 7:** suite 1311 OK; gate 1311 OK, with `tools/deprecation_gate.sh`
printing its non-empty filter.

### The logrotate heartbeat — option 1 chosen (Brian, 2026-09-27); built, not yet installed

**Measured first: logrotate's exit status carries both failures.** As root on
leopard, three scratch configs: a 755 directory exits **0**; a 775 directory
exits **1** (`insecure permissions`); a `postrotate` of `false` exits **1**. Those
runs named each config directly. **Under the service the 775 case does not
fail at all** (the global `su`, above); the failed `postrotate` does, and it is
the failure that matters: the Apache reload.

**`logrotate/heartbeat.conf`**, a drop-in for the host's own
`logrotate.service`: `/start` before, then the URL on success or `/fail`
otherwise, from `$SERVICE_RESULT` in `ExecStopPost`. The URL comes from
`secrets/logrotate.env`; the pattern is the backup job's (healthchecks.io,
period 1 day, grace 2 hours). Every line is `-`-prefixed and the env file is
optional, so the heartbeat cannot stop the rotation it watches. It covers every
`/etc/logrotate.d` file, deliberately.

**Exercised without sudo, as a user unit on leopard** with the drop-in attached
and a local listener for the pings:

| `ExecStart` | result | pings |
|---|---|---|
| `true` | success | `/start`, `` |
| `false` | exit-code | `/start`, `/fail` |
| `true`, no env file | success | none |
| `true`, unreachable URL | success | none |

This proves the `$$` escaping and both branches. It does not prove the real
unit, whose sandbox differs.

**Installed and proved on leopard, 2026-09-27** (Brian ran the `sudo` steps).
The check went green on the first run. **The first alarm proof proved
nothing**: a throwaway 775 directory, run as the service, exited 0; the check
never saw a `/fail` and the event log showed none. That is how the global `su`
was found. The proof was redone with a `postrotate` of `false` on a two-byte
file with `size 1`: the unit failed, **the check went red, and the alert email
arrived in Gmail**. Cleaned up, run again, green. Runbook B10 step 4 now uses
the `postrotate` failure.

**Open for Brian: host mail at all.** leopard has no mailer, where jaguar had
Postfix. Measured 2026-09-27, it loses almost nothing today: no user crontab;
the `cron.daily`/`weekly` scripts (`dpkg`, `logrotate`, `man-db`, `apt-compat`,
`e2scrub_all`) exit on a systemd host, `apport` aside; timers log to the
journal. **The one gap is unattended-upgrades**: `Unattended-Upgrade::Mail` is
commented out, so a failed security update is only in
`/var/log/unattended-upgrades/`. Either a relay through Postmark (once, for
everything) or a heartbeat on `apt-daily-upgrade.service`. Not needed before
task 07.

## Step 21 task 02 — the Linode firewall adapter, rewritten in Python, exercised on a real firewall — DONE 2026-09-25, `ab7c1efd`

**`tools/origin_firewall.sh` is now `tools/origin_firewall.py`**, and its tests
are `tools/origin_firewall_test.py`, both at Brian's request. The tool keeps the
same commands, output and exit codes. The `make firewall-*` targets are unchanged,
and `make firewall-test` is new. Only the standard library is used, so the
Mac's `/usr/bin/python3` (3.9) runs it as well as the repo's 3.12. It still runs
only from Brian's machine. The VM needs neither Python nor the token for it.
Runbook **B6** names the three Linode variables. No Django code was touched, so
the suite was not run.

### Why Python — Brian's call, 2026-09-25

The adapter was first written in bash to extend Step 20 task 07's script, and it
passed its tests and mutations. Brian found the bash hard to read, and it will
be read cold, during an incident, if at all. The bugs this script has had were
bash's own: task 07's `pipefail` OK-on-a-broken-file, and while writing the
adapter a jq syntax error inside a bash string, curl's `000` status on a failed
connection, and bash 3.2's unbound empty arrays. The tests drive the command
line, not the code, so the same harness verified the port unchanged.

### How it works

- `apply` builds one body — `cloudflare-https` (443), `cloudflare-http` (80,
  only when `FIREWALL_HTTP=allow`) and `ssh` (22); inbound DROP, outbound ACCEPT
  with no rules — and sends it with `PUT …/networking/firewalls/{id}/rules`,
  which **replaces** both rule sets.
- `check` reduces the live rules and the plan to one line per
  *direction action protocol port address*, plus the two policies, and names each
  line found on only one side. Rule order, address order and labels are ignored.
  Addresses are compared through `ipaddress`, so a respelling of the same range
  is not a difference.
- Any status other than 2xx exits 2 with Linode's `field: reason` lines. The
  token goes only in the request header. It never reaches a command line or the
  output.
- An SSH entry has to be a CIDR range. A bare address is refused rather than
  read as a /32.

### Tests: `tools/origin_firewall_test.py`, 25 tests (40 checks), against a local stand-in

`unittest`, standard library only, and it runs under 3.12 and 3.9. The tool runs
as a subprocess, as it does from the Makefile. The stand-in is an in-process
server for GET and PUT on the rules endpoint. It checks the token, returns 404
for a wrong ID, validates labels and limits, records every request, and returns
rules and addresses in reverse order. Tests edit its rules dict to play the
dashboard. The tool and ranges file are copied into a scratch tree, so a
malformed-range case never touches the real file.

**The tests were written first, in bash** (`origin_firewall_test.sh`, RED
against the unchanged script, then GREEN), and ported to Python after the tool
was. Both harnesses ran the same battery.

**Mutation battery against the Python tool and the Python tests: 18 of 18
caught**, each by the test written for it, and the file restored byte-identical. It covered respelling
normalization, any-status-OK, unreachable-swallowed, apply-merges-instead-of-replacing,
port/outbound/policies dropped from the comparison, 80 always sent,
SSH unvalidated, bare address accepted, check without the plan guard, token/ID
guards removed, Linode's reasons dropped, inbound ACCEPT, `anywhere` IPv4-only,
a bad ranges line skipped, and an unknown provider accepted. **One survived the
first pass:** removing the "`FIREWALL_LINODE_ID` is unset" guard still refused,
because the digits check after it rejects an empty string. The guard's only
contribution is the message, so a test now asserts that the message names the
missing variable. The bash version's battery was 16 of 16 before the rewrite.

**Checked by hand, outside the harness.** For valid settings, `plan`'s output is
identical to the bash version's from `HEAD`. Task 07's `ranges-check` cases
still hold: dropped IPv4, dropped IPv6, stray range, malformed line, and no
trailing newline.

### Found by comparing against the real endpoints, which the stand-in cannot

- **Cloudflare answers urllib's default User-Agent with HTTP 403.**
  `ranges-check` in Python failed against `www.cloudflare.com/ips-v4` until it
  sent its own (`sg101-origin-firewall`). The Linode calls send the same one.
- An invalid `FIREWALL_HTTP` now refuses before printing anything. Bash printed
  the 443 ranges and then died. This is the one deliberate change in output.

### Exercised against the real API — 2026-09-25

The subject was scratch firewall `sg101-test`, **ID 175544886**, attached to
nothing, created by Brian in the dashboard (inbound DROP, no rules). The token
was read from `~/.config/sg101-linode-token` (mode 600), so it never entered
the transcript. It is scoped to Firewalls read/write: `linode/instances` and
`account` answered 401, and `/profile` answers any token. Settings were
`FIREWALL_HTTP=allow` and `FIREWALL_SSH_FROM=anywhere`, the fullest plan.

| step | result |
|---|---|
| `check` before any write | DIFFERS, every planned line named |
| `apply` | exit 0; version 2 |
| raw GET | **one 443 rule holding all 22 ranges (15 + 7)**; the same for 80; addresses stored verbatim and in file order; labels echoed, `description: null` |
| `check` | OK, exit 0 |
| bad token, `check` and `apply` | exit 2, `HTTP 401 / Invalid Token`, token not printed |
| wrong ID, `check` / `apply` | exit 2, `404 Not found` / `The provided ID did not match any existing Firewalls` |
| after the refused calls | `check` OK — untouched |
| hand rule in the dashboard: 443 from `203.0.113.7/32`, label `emergency` | version 3, four rules |
| `check` | **DIFFERS, `only live: inbound ACCEPT TCP 443 203.0.113.7/32`, exit 1** |
| `apply` | exit 0 |
| `check`, raw GET | OK; version 4; three rules; `203.0.113.7` absent |

**B6's open question is answered on the real API: one rule holds all 22
ranges.** An `apply` that changed nothing left the version at 2. Only real
changes bump it.

**Afterwards (Brian, 2026-09-25):** `sg101-test` is deleted, not kept for task
03. The VM's firewall is created in Linode's create flow, as B6 says. The token
is kept for now in `~/.config/sg101-linode-token` (mode 600, laptop only), since
B6 needs the same scope. It is a live credential to revoke once the cutover no
longer needs it.

**The dashboard holds an added rule as a draft until *Save Changes* is
clicked.** The first attempt at the hand edit was never saved. The raw GET,
read before anything ran, showed version 2 and three rules, so that round was
not counted.

## Step 21 task 01 — jaguar's leftovers: logs archived, IRC and the wiki decided — DONE 2026-09-25, `44431f1e`

No application code touched, so the suite was not run (acceptance criterion 5).
Actions for cutover and shutdown are runbook **D6**, **D7**, **D8**.

### The archive

**`~/workspaces/bgn/sg101-evidence/jaguar-logs-2026-09-25/`**, 555 MB, 82 files,
pulled 2026-09-25 ~13:28 CDT with `rsync -a`. It sits outside the repo because it
holds client IP addresses. The layout mirrors jaguar's paths under `svr/`:
`www/surfguitar101.com/log/`, `www/wiki.surfguitar101.com/log/`, and the whole
Django `django-sites/sg101/sg101/sg101/logs/`. The Django directory went whole,
not just `auth.log*`/`sg101.log*`, because `celery-w1.log*` rotates away too.

- **Complete against the source:** a `find -printf` listing was taken on jaguar
  *before* the copy (`source-listing/before.txt`). All 82 files are present
  locally with identical sizes, mtimes are preserved, and every `.gz` passes
  `gzip -t`. The first comparison run reported every file SHRANK, because this
  shell has no `stat` on its PATH and the sizes came back empty. The re-run uses
  `/usr/bin/stat` and treats an empty size as an error.
- **Checksums:** `MANIFEST.sha256` (82 lines, `shasum -a 256 -c` clean). The
  manifest's own SHA-256 is
  `2c77ddc4478631ae924dda242d8c1454f9f88c58d481f7617c8fcd977d5caa1e`.
- **The copy is on the laptop only.** Like `.env`, it is backed up nowhere else.

### Coverage, from first and last lines, not file dates

| family | files | from | to |
|---|---|---|---|
| sg101 `access.log*` | 9 | 27/Jul/2026 06:48 | 25/Sep/2026 13:27 |
| sg101 `error.log*` | 9 | Jul 28 11:05 | Sep 24 12:49 |
| wiki `access.log*` | 9 | 27/Jul/2026 06:49 | 25/Sep/2026 13:27 |
| wiki `error.log*` | 9 | Jul 29 17:46 | Sep 25 11:50 |
| `auth.log*` | 6 | 2025-01-09 20:32 | 2026-09-25 13:01 |
| `sg101.log*` | 11 | 2026-05-19 06:47 | 2026-09-25 13:01 |
| `celery-w1.log*` | 11 | 2026-07-12 06:45 | 2026-09-25 13:20 |

File dates would have understated this. `auth.log.5`'s mtime is 2025-04-10, but
its first line is 2025-01-09. `sg101.log.1` ends on a traceback line with no
timestamp; its last timestamped line is 2026-09-25 11:19:02. Also carried, and
stale: `celery-beat.log*`, `oembed_refresh*.log` and `ssl_images.log` (all
2015), `report.html` (2015) and `moin.log.1` (2013).

**The access logs were one rotation from losing a week.** `access.log.8.gz`
(27 Jul – 2 Aug) would have been deleted at the next weekly rotation, around
Sunday 2026-09-27 06:30.

**Two gaps in the source, not in the archive:**

- **2026-08-09, 06:53 → 09:33: no requests on either vhost.** The Apache
  error-log thread-id prefix changes across it (`125005…` → `140707…`), so this
  was very likely a jaguar or Apache restart. Nothing in `.agents/` recorded it.
- **2026-09-25 11:18–11:19: jaguar rebooted.** `uptime -s` gives 11:19:50, and
  `last -x` shows the kernel going from 6.14.3 to 7.1.9. The site served ~49
  500s (`Can't connect to local MySQL server`) over those two minutes. **Brian
  rebooted it at Linode's request for host maintenance** — expected, not a fault.

### Decided 2026-09-25 (Brian, all three on the recommendation)

**Stopping the loss: re-pull on schedule (runbook D6).** Pull again the day after
the flip, then a final pull at shutdown, each into a new dated directory beside
this one. Deadline ~2026-11-20. Taking the log lines out of bobcat's
`jaguar_exclude.txt` was **not** chosen, because it does not do what it seems to.
That rsync runs `--delete`, so bobcat would mirror the same eight-week window and
drop the oldest week in step with jaguar. That guards against jaguar dying, not
against rotation. Raising `rotate 8` on jaguar was the other option, and it is a
root edit on the production box.

**IRC: retire with jaguar, not moved (runbook D8).** Re-measured on the box:
`ngircd` on `*:6667`/`*:6697` (IPv4 and IPv6), and `sg101Bot.py` running **as
root**. Both restarted at the 11:19 reboot, so the "live since Apr 23" in the
task file is out of date. Across all of `/var/log/syslog*` (Sep 18–25), exactly
one user registered, and it was the bot (`bot!~bot@localhost.localdomain`). The
other inbound connections are scanners that never register.
`irc.surfguitar101.com` is an explicit **proxied** record (no wildcard exists),
so the name has never reached the IRC ports. The one established connection is
the bot's, over loopback. The `127.0.0.1:23352` listener is still unattributed.
Copied to `~/workspaces/bgn/sg101-evidence/irc-2026-09-25/`: the bot's tree
(8.2 MB; a Mercurial checkout at `9:a977b29a77f7`, plus its virtualenv) and
`/etc/ngircd/`, **except `server.key`**, which is root-only and not needed to
retire the service.

**Wiki: leave it until shutdown, then a Cloudflare redirect (runbook D7).**
Measured over the archive's 8.5 weeks: 176,001 requests. 68,220 of those were
403s, overwhelmingly `?action=newaccount` spam. Just 35 were referred from
`surfguitar101.com`. The redirect keeps the forum's old wiki links from
dead-ending, and the 30 pages remain in `archive/wiki/`, whose README already
says the wiki stays up until the host goes. `wiki-abuse` stood at 229 bans across
`fail2ban.log*` on 09-25 (225 on 09-24).

## Step 21 — planning pass: eleven task files, the provider chosen, and why the block list grows — 2026-09-24, `16a3533b`

**Step 21 is the active step.** Its `plan.md` line (~11k characters gathered
since August) is sorted into eleven task files in
`.agents/tasks/2026-07-04-modernizing-sg101/step21/`:

| | task | code in the repo? |
|---|---|---|
| 01 | jaguar leftovers — archive sg101's Apache logs **now**, decide IRC and the wiki vhost | no |
| 02 | Linode Cloud Firewall adapter for `tools/origin_firewall.sh` | yes |
| 03 | provision the Linode; fix worker counts in configuration | yes (compose, `.env.example`) |
| 04 | send-only host mail, proven by a failing cron job | no |
| 05 | backups on real accounts; bobcat repointed or retired | no |
| 06 | fail2ban and the Cloudflare block list, with a working unban | yes (action, jails, filters) |
| 07 | dress rehearsal on the VM, timed and memory-measured | no (badge images) |
| 08 | finish the runbook: sequence, smoke checklist, rollback | no |
| 09 | the cutover | no |
| 10 | after cutover: mail live, two weeks watched, summary regenerated | no |
| 11 | decommission jaguar; retire the MySQL chain | yes |

**Dropped as already done by Step 20:** Redis's memory policy (task 05) and the
dev/prod settings split with the stale MySQL engines (task 01).

**01 is time-sensitive:** sg101's Apache logs are on an eight-week rolling
delete on jaguar and bobcat excludes them, so each week of delay loses a week.

### Decided 2026-09-24: Linode, 4 GB shared CPU, core compute region

Brian's choice, on familiarity — jaguar and bobcat already run there. It settles
three open items: the firewall adapter targets Linode (task 02); the backup
buckets go to AWS S3, which meets B7's no-shared-provider rule (task 05); and
outbound port 25 is irrelevant because everything submits to Postmark (task 04).

**Shared can become dedicated later.** Akamai's resize docs (read 2026-09-24):
a core-region Linode can change plan type, keeping data, configuration and IP
addresses, by warm or cold resize. Shrinking is the awkward direction.

**Sizing measured, not assumed** — the figures and the estimate live in task
03's Background. In short: jaguar uses 2.4 GB of 7.9 GB for programs while
running far more than sg101; the new stack is estimated at 1.7–2.0 GB on 2
vCPUs. **The catch found:** gunicorn and celery both size themselves from
`nproc` — 21 workers and 10 children locally, ~2.5 GB idle — so task 03 pins
both in configuration.

### Why jaguar's block list only grows — found 2026-09-24, not yet confirmed live

From `/etc/fail2ban/action.d/cloudflare.conf` (Brian pasted it, credentials
redacted): the unban looks up the item ID with **one unpaginated `GET`**, and
Cloudflare paginates list items. Past one page, an IP isn't found, the action
exits 0, and the entry is stranded — which lengthens the list and strands more.
Also: no `curl --fail`, no ban persistence across restarts in 0.8.11, and the
**Global API Key** on the box. Detail and the fix are in task 06's Background;
confirming it (list size vs active bans) is task 06's first requirement.

## Step 20 task 07 — the provider's firewall, one range file, and a check that said OK on a broken file — DONE 2026-09-23, `f1014b3d` + this planning commit

**The firewall itself is UNEXERCISED: no rule has been applied to any host.** What
Step 20 could build is built and tested; the provider adapter needs the provider,
which is Step 21's, and runbook **B6** carries it. `tools/prod_smoke.sh` 21/21
unchanged; no Python touched, so the suite was not re-run.

**Decision and the three-way comparison live in the task file**, § *Decided
2026-09-23* — the provider's firewall, pushed by a script from one range file,
run from Brian's machine. Not restated here.

### Built

| | |
|---|---|
| `apache/cloudflare-ranges.txt` | the 22 ranges, their sources, "last verified", and both consumers named |
| `apache/conf-enabled/remoteip.conf` | inline lists replaced by `RemoteIPTrustedProxyList sg101/cloudflare-ranges.txt` |
| `tools/origin_firewall.sh` | `ranges-check`, `plan`, `apply`, `check`; the provider seam fails with a message |
| `Makefile` | `cloudflare-ranges-check`, `firewall-plan`, `firewall-apply`, `firewall-check` |
| `cutover-runbook.md` | B6 rewritten (decide, apply, verify, emergency-open, re-close); A2 and B3 point at the file |

**Ranges re-verified 2026-09-23 from two sources:** `ips-v4`/`ips-v6` and
`api.cloudflare.com/client/v4/ips`, etag `38f79d050aa027e3be3865e495dcc9bc` —
**the same etag task 04 recorded on 09-19**, so nothing has moved.

### Apache reads the file — measured, not inferred

Probe peers on throwaway Docker networks inside Cloudflare ranges
(`103.21.244.0/24`, `2606:4700:10::/64`) and outside (`198.18.0.0/24`), each
sending `CF-Connecting-IP`, reading `%h` from the access log:

| | trusted IPv4 | trusted IPv6 | untrusted |
|---|---|---|---|
| baseline, inline lists | claimed | claimed | own peer |
| from the file | claimed | claimed | own peer |
| file: IPv4 range dropped | **own peer** | claimed | own peer |
| file: IPv6 range dropped | claimed | **own peer** | own peer |
| file: untrusted net added | claimed | claimed | **claimed — the spoof believed** |
| directive names a missing file | Apache refuses the config | | |

**Identical before and after is what a reload that never happened also looks
like** — task 04's trap — so the three file mutations are what show the file is
live and is the boundary. Each ran behind a `configtest` guard; both files
restored byte-identical. A missing file refuses to load, loudly, rather than
trusting no one quietly.

### The check reported OK on a file with a bad line

**The first version of `ranges-check` printed the parse error three times and
then `OK … matches Cloudflare`, exit 0.** `ranges()` dies on a malformed line,
but it is read through pipes, and without `pipefail` a pipe reports its last
command. The bad line was appended after the good ones, so every real range had
already gone through and the sets matched. Caught by the mutation written for
it, not by reading; `set -o pipefail` fixed it.

| mutation | result |
|---|---|
| malformed line (`ranges-check`, `plan`) | exit 2, names the line |
| IPv4 range dropped / IPv6 range dropped | `DIFFERS`, "only at Cloudflare", exit 1 |
| stray range added | `DIFFERS`, "only in the file", exit 1 |
| file with no trailing newline | last range still read, OK |
| **guard** removed: `\|\| [ -n "$line" ]` | the no-newline file loses `2c0f:f248::/32` — caught |
| **guard** removed: `pipefail` | the bad-line file reports OK again — caught |

`apply` refuses while `FIREWALL_SSH_FROM` or `FIREWALL_HTTP` is unset — a plan
with no SSH rule is one that locks you out — and `apply`/`check` exit 2 with no
provider configured.

### Found while writing B6

- **Smoke before firewall.** `prod_smoke.sh <VM>` connects to the origin
  directly, so after the firewall it is refused like any outsider. B6 orders it.
- **The adapter's `apply` must replace the rule set, not add to it.** Re-closing
  after an emergency open is `firewall-apply`, and only a replace removes the
  emergency rule. Recorded in B6 as a requirement on the adapter.
- **Port 80 was never in the task file**, which named 443 only; the proxy
  publishes both. Now a required decision in the plan.

**Stale, pre-existing, not changed here:** `AGENTS.md` ("Nothing in this repo
does that" — task 04 made the repo do it) and `.agents/summary/architecture.md`
(Apache + `mod_wsgi`, gone since task 02).

## Step 20 task 09 — no autocomplete index, and the spelling split closed at query time — DONE 2026-09-23, `0f58f6ae` + this planning commit, PUSHED

**Suite 1311 OK and gate 1311 OK** (1303 + 8 new tests in
`search/tests/test_query.py`), **6 of 6 mutations caught**, each by the test
written for it, file restored byte-identical. Code: `search/query.py` only. No
migration.

### The autocomplete index is not added — 67 requests in 58 days

**The task's instrument did not exist.** Requirement 1 said to count usage *"from
the query logging that already exists"*; that is the `search` logger, and
`core.views.ajax_users` never writes to it. The only record is jaguar's vhost
access log, `/svr/www/surfguitar101.com/log/access.log*` (not
`/var/log/apache2/`, per Step 17 task 05). `/core/ajax/users/` is the same path
on `main`. Brian ran the count (the ssh was refused to me as a production read).

| 27 Jul – 23 Sep 2026, 58 days, the full retained window | |
|---|---|
| requests | **67** |
| days with any | 15 |
| distinct IPs | 17 |
| single-character `q` (≈ times someone started typing) | 9 |

At Step 12's **2.7 → 0.48 ms**, that is **~150 ms saved in two months** — not
worth a third index on `username` to maintain. Requirement 3 applies. The
Step 12 measurement stands if post-cutover traffic changes the answer.

**One figure the script produced is invalid and is not recorded as a finding:**
it counted "empty `[]` responses" as response size 2, but this log's size field
is `%O` (bytes sent, headers included — task 08), so it reads 0 whatever
happened.

### The spelling split — `ts_rewrite`, not either option the task offered

**Step 12's numbers reproduce** on the dev snapshot (516,861 documents):
`misirlou` 1,416, `miserlou` 2,131, both 148, either 3,399. The tail is small —
`miserlu` 20, `misserlou` 8, `miserilou` 8, `missirlou` 7, `misirlu` 7.

**`pg_trgm` fails on the measurements, twice.** As a low-result fallback it never
fires: each spelling alone returns over 1,000 rows. As a similarity match it
cannot separate the right word from a wrong one — `similarity('miserlou',
'misirlou')` is **0.50**, and so is `similarity('miserlou', 'miser')`, an
unrelated word in 199 documents. No threshold admits one and not the other.

**A synonym dictionary works and costs more than the problem.** PostgreSQL reads
synonyms only from a file in `$SHAREDIR/tsearch_data/` on the database server:
a mount on `postgres` in dev, prod and CI, a file every restore depends on, a
custom text search configuration, and a full vector recompute over 516,861 rows
— again on every added spelling, since it acts at index time.

**`ts_rewrite` does it at query time**, on the parsed tsquery: no file, no
extension, no reindex. Prototyped before choosing — a bare word becomes
`miserlou | misirlou`; the phrase `"miserlou dick dale"` becomes
`(miserlou | misirlou) <-> dick <-> dale` (67 → 101 rows); `dale -miserlou`
excludes both. Chosen by Brian 2026-09-23.

**Groups, chosen by Brian from measured candidates:**

| group | A / B / both | |
|---|---|---|
| misirlou · miserlou · miserlu | 1,416 / 2,131 / 148 | in |
| straitjackets · straightjackets | 4,455 / 274 / 62 | in |
| bel-airs · belairs · bel airs | 1,058 / 495 / 38 | in |
| astroman · "astro man" | 1,355 / 1,793 / 73 | held back — "astro man" may match unrelated text |
| wipeout · "wipe out" | — | **unbridgeable**: `out` is a stop word, so "wipe out" indexes as `wipe` alone; the 2,105 was counting "wipe" |
| ghostriders · "ghost riders" | 57 / 589 / 3 | out — likely different things |

Plurals are already one word to the stemmer (`pyramids`/`pyramid` identical),
which served as the control for the method.

**Two shapes that decided the design:**
- **A two-word form parses two ways**: typed, `bel airs` is `bel & air`; quoted,
  it is `bel <-> air`. So each form is a target twice, via `plainto_tsquery` and
  `phraseto_tsquery`. `ts_rewrite` matches an AND subset wherever its operands
  sit (`bel surf airs` rewrites too).
- **The substitute is the target OR the group, never the group alone**, so a
  rewrite only adds matches. Replacing `bel & air` with the group would have
  narrowed an unquoted search to the phrase.

**Cost, measured on the dev corpus, `count()` medians of 7:** queries without a
grouped name are unchanged (`reverb` 35.1 → 34.6 ms, `surf` 81.8 → 72.1 ms,
noise); `miserlou` 0.6 → 1.7 ms for 2,131 → 3,419 rows, `"bel airs"` 0.6 → 2.1 ms
for 495 → 1,515. The rewrite constant-folds and the GIN index serves it.
**A known wart, left:** each nested call re-expands what earlier calls
substituted, so `miserlou` becomes a 37-term OR of three words, and the
planner's estimate for such queries inflates ~17x (59,864 vs 3,419). ~1 ms
does not justify the machinery to deduplicate.

**Rendered-page check** on the dev corpus: `/search/?q=miserlou` per-type counts
sum to 3,419 and highlight both `Miserlou` and `Misirlou`; `belairs` sums to
1,515.

### Mutation battery

| mutation | caught by |
|---|---|
| filter uses plain `SearchQuery` | all 7 spelling tests (12 failures, 1 error) |
| ranking/headline uses plain `SearchQuery` | rank + snippet tests |
| substitute is the group alone | `test_a_rewritten_query_still_finds_what_it_found_before` |
| no `plainto_tsquery` target | `bel airs` subtest |
| no `phraseto_tsquery` target | `bel-airs`, `"bel airs"` subtests |
| `miserlu` dropped from its group | all three Misirlou subtests |

**The group-only mutation was first written wrong** — it removed the
placeholders and left their parameters, so every query raised and 36 tests
errored. That proved nothing about the behaviour; redone with the parameters
removed, it fails exactly the one test written for it.

## Cloudflare's HSTS is off — verified 2026-09-20, closing the vhost read's open item

**The open question from the vhost read was whether the edge adds its own HSTS
header**, since one header at the edge is consistent with Cloudflare passing
jaguar's through *or* sending its own. Matching values cannot separate those:

| | `Strict-Transport-Security` |
|---|---|
| origin, direct (`127.0.0.1` on jaguar, Host header set) | `max-age=604800` |
| through the edge | `max-age=604800` |
| **`/cdn-cgi/trace`** — Cloudflare's own response, never reaching the origin | **absent** |

**The third row is the measurement.** Cloudflare's HSTS setting is a zone-wide
response header and would apply to its own responses too; it is not there. So
the header on the live site is jaguar's, passed through unchanged, and the goal
stated when HSTS moved out of Apache and into `SECURE_HSTS_SECONDS` holds at
cutover: **one header, one source, one value** — the new Apache sends none,
Django sends `max-age=604800`, Cloudflare adds nothing.

**Which also makes `check --deploy`'s two remaining warnings deliberate rather
than accidental.** `security.W005` (`SECURE_HSTS_INCLUDE_SUBDOMAINS`) and
`security.W021` (`SECURE_HSTS_PRELOAD`) are both off because a browser caches
either for the full `max-age` and there is no way to withdraw it early —
`wiki.surfguitar101.com` still answers on the old host, and preload is baked
into browser binaries. W005 becomes answerable once nothing else lives under the
domain; W021 only after W005 has run long enough to trust.

**A side finding worth knowing, not acting on:** the same directive is in
**five** of jaguar's vhosts — `surfguitar101.com`, `bravenewsurf.com`,
`edtaxidermy.com`, `briananddebra.com`, `deathofagremmie.com`. HSTS is per-host,
so each was advertising its own, and three of those domains have since moved to
Cloudflare Pages and are no longer served by jaguar at all. A domain that
advertised `max-age=604800` and then stops sending it is only a problem if it
also stops serving HTTPS, which Pages does not — so nothing to do, but it is the
kind of thing that looks alarming when noticed later without this note.

## Step 20 task 06 — backups to two buckets, and the stream that would have uploaded a truncated dump — DONE 2026-09-22, `a61528ac` + this planning commit, PUSHED

**`tools/backup_drill.sh` 26/26 against a local MinIO, 11 of 11 mutations caught
each by the check written for it, every restored file byte-identical; the
restore commands in DOCKER.md run as written, full replacement included.
Suite 1303 OK and gate 1303 OK, unchanged (no Python touched); `tools/prod_smoke.sh` 21/21 unchanged.** What
needs a real account — buckets, the job's IAM user, the heartbeat check, and
seeing an alarm arrive in Gmail — is runbook **B12**.

### What was built

| | |
|---|---|
| `backup/Dockerfile` | `FROM postgres:16` + `awscli` 2.23.6 + `curl`, runs as `postgres` (uid 999) |
| `backup/backup.sh` | heartbeat start → `pg_dump -Fc` to a temp file in the container → upload → `aws s3 sync /media`, never `--delete` → heartbeat ok; any failure → `/fail` |
| `backup/provision.sh` | both buckets versioned; `lifecycle-db.json` on dumps; media's lifecycle *deleted*; re-runnable |
| `backup/policy-writer.json` | `s3:PutObject`, `s3:AbortMultipartUpload`, `s3:ListBucket` — no read, no delete |
| `backup/sg101-backup.{service,timer}` | 04:30 host time, `Persistent=true`, `TimeoutStartSec=6h`, a fixed container name removed by `ExecStopPost`; parse-checked with `systemd-analyze verify` |
| `docker-compose.prod.yml` `backup` | profile `backup`; `secrets/backup.env`, not `.env`; `./media` read-only |
| `docker-compose.backup-drill.yml` | MinIO, `mc`, a separate AWS CLI, a heartbeat stand-in; `env_file: !reset []` so a real credential can never reach the drill |

### Decisions, all Brian's, 2026-09-22

- **The host schedules it, not beat** — the app image has no `pg_dump`, `./media`
  is mounted only into `web`, and a beat task stops silently with the broker.
- **Two buckets.** Dumps expire at **90 days**; **media keeps everything,
  prior versions included, forever.** One bucket would have made the media's
  survival depend on a prefix filter nobody drops.
- **The dump goes to a temp file inside the container, not a stream.** The
  recorded decision had been to stream under `pipefail`. Working out drill check
  10 showed `aws s3 cp -` completes a truncated upload and exits 0 when its input
  ends early, and the job's credential cannot delete the result. **Mutation M1
  puts the stream back and the drill catches it** — "a database failure uploads
  no dump" fails, which is the truncated object appearing.
- MinIO `RELEASE.2025-09-07T16-13-09Z` from quay.io, pinned by digest — its
  images left Docker Hub 2026-09-11; frozen is acceptable for a local fixture.
- healthchecks.io for the dead-man's switch.

### Made during coding, reported for review

- **No incomplete-upload rules anywhere.** MinIO accepts
  `AbortIncompleteMultipartUpload` inside a rule and silently drops it, and
  rejects a rule containing only that — which is what media's would have been.
  Keeping them would make the drill test a configuration production does not
  run. Cost: an interrupted upload's parts, at most one dump (~120 MB,
  ~$0.003/month), until removed by hand.
- **No `pg_restore --list` before upload.** Planned, then dropped: nothing
  could make it fail where `pg_dump` had succeeded, so it could never be seen to.
- **The job cannot read its own backups**, so a restore needs an admin
  credential. Deliberate: a compromised host can neither destroy nor download
  them. DOCKER.md says so first.
- **A timeout alone would have left the hung job running.** A `oneshot` has no
  limit by default, and a hung run blocks every later night, so Brian asked for
  `TimeoutStartSec=6h`. Measured before relying on it: SIGTERM to
  `docker compose run` exits the client (143) and **the container keeps
  running** — it is Docker's, not the unit's. So the timer's run gets a fixed
  name (`sg101-backup`), which also makes Docker refuse an overlapping second
  run (measured: `Conflict ... already in use`), and `ExecStopPost=-docker rm -f`
  removes it however the run ended. Verified by hand, not under systemd:
  `systemd-analyze verify` checks only that the units parse.
- **A put-only credential is not safe without versioning** — it can overwrite.
  M8 turns versioning off and the overwrite check catches it.

### Measured

- **Production `/media` on jaguar: 4.7 GB, 14,906 files**; `downloads` 2.7 GB,
  `podcast` 1.4 GB, `user_photos` 589 MB. **Churn 9.9 MB / 192 files in 30 days,
  150 MB / 1,999 in a year** — so the first sync is the whole cost and nightly
  runs are near nothing. Recorded because task 08 measured egress, not size.
- **Dump 119,603,065 bytes**, 83 tables, restored with every row count equal;
  `reindex_search` 516,861 documents in 1 m 43 s; `reconcile_search` clean.
- **Empty directories do not survive**: object storage has only files.
  Production has 125, mostly `avatars/users/<name>` from deleted avatars.
  Harmless — Django creates directories on save — and noted in DOCKER.md so the
  gap is not mistaken for loss.

### The drill had three defects of its own, all found before trusting it

1. **MinIO's image declares `/data` a volume, and `--force-recreate` keeps
   anonymous volumes** — the second run saw the first's 152 objects, so
   "a dump reached the bucket" could pass on yesterday's dump. Fixed with
   `--renew-anon-volumes` and a new check that the buckets start empty.
2. `docker compose run` writes its status lines to stderr; fetching a version via
   a stderr swap mixed them into the body, and the overwrite check failed for a
   reason that was not the code's.
3. An empty bucket's `length(Versions)` is `""`, not `None`.

**Three mutations had no detector at first**, found by asking of each "which
check fails?" before running it: `--delete` on the sync (nothing in the bucket
was absent on disk), `provision` not removing a hand-added media rule (a fresh
bucket has none), and running as root. Each got a check; all three are now in
the 11.

**Two slips caught before shipping**: `docker compose run --no-build` does not
exist (`run` has only `--build`), which would have failed every night; and the
task file's own first decision text said `pg_dump` would run over `exec -T`,
impossible from a one-shot container without the Docker socket.

### Not verifiable here, and where it went

- **Lifecycle expiry itself** — rules count in whole days. The rules are read
  back and checked; that they fire is runbook B12's day-91 reminder.
- **The alarm reaching Gmail** — B12 step 5, a deliberate wrong-password run.
- **Block Public Access** — MinIO has no equivalent; B12 step 1 says to confirm.

## Step 20 task 10 — the stylesheet can be rebuilt, and the hand-patching stops — DONE 2026-09-21, `7f7bd3fa` + this planning commit, PUSHED

**`main.min.css` 94,386 → 79,166 bytes, every difference accounted for, both
hand-appended rules regenerated from source, CI gate added and mutation-verified
in both directions, and Brian confirmed dev and the prod stack render the same.**
No Python changed, so the suite is untouched.

**The debt this clears was visible in the tree.** A one-rule CSS fix in August
(`39aceca4`) and a second in Step 17 had both been appended *to the minified
build artifact* by hand, because no rebuild was possible. Both rules were correct
in `_sg101.scss` the whole time — only the built file was being patched.

**Three independent blockers, and `npm install` reproduced the first exactly.**
`gulp-sass` 2.x wraps `node-sass`, which needs native bindings per Node version;
on v26 the install dies in `node-gyp`. The gulpfile is gulp 3 syntax that gulp 4
removed, and `gulp` was never in `package.json` at all — only five of its
plugins. The libraries came from bower, sunset since 2017.

**Both bower pins exist on npm at the same versions, and that is what made the
change verifiable rather than merely plausible.** `foundation-sites@6.3.1` and
`motion-ui@1.2.3` are exactly what `bower.json` pinned. Installing those *and
holding the 2016 browser targets* isolated the single variable worth isolating —
LibSass vs dart-sass — before the targets were touched at all.

**The Foundation-under-dart-sass risk did not bite.** 6.3.1 predates dart-sass
and its own devDependencies still name `gulp-sass`, so it might not have compiled
at all; that was the one thing that could have turned this into an upgrade rather
than a reconstruction. It compiles, exit 0. The only noise is 16 `@import`
deprecation warnings in our own `main.scss`, plus `color.scale`/`color.adjust`
warnings from `_sg101_settings.scss`. `@import` is not removed until Dart Sass
3.0, which does not exist yet.

#### Every difference from the committed artifact, and what causes each

| Cause | Shape |
|---|---|
| Numeric precision | LibSass emitted 5 decimals, dart-sass emits 10 — `8.33333%` → `8.3333333333%`, the same twelfth of a grid |
| Quote style | `content: '+'` → `content: "+"` |
| cssnano | declarations alphabetized, some shorthands split (`border` → `border-width` + `border-style`), some rules merged |
| Prefix strategy | `-webkit-flex` (77) → `-webkit-box-flex` (77), and **61 `-ms-transform` appear that the 2016 build never emitted** |

**That last row is worth keeping.** The old artifact was missing a vendor prefix
its own stated `ie >= 9` target required. The reconstruction is *more* correct for
2016's targets than 2016's build was.

#### Dropping IE 9 removed 753 declarations and added one, and the one is the tell

The removals are vendor-prefix material in four shapes, which a count of prefixed
*properties* alone would have undercounted: 664 prefixed properties, plus
prefixed values (`display: -ms-flexbox`), prefixed selectors
(`::-ms-input-placeholder`) and prefixed at-rules (`@-webkit-keyframes`).

**The single addition is `abbr[title] { -webkit-text-decoration: underline
dotted }`, and it exists because the query was replaced rather than edited.**
`["last 2 versions", "ie >= 9"]` became `["> 0.5%", "last 2 versions", "Firefox
ESR", "not dead"]`, and `> 0.5%` reaches a Safari that `last 2 versions` never
did. Recorded because the step was described in advance as "purely prefix
removal" and it was not quite.

#### The CI gate, and why a weaker one would have proved nothing

CI rebuilds and runs `git diff --exit-code` on the artifact. **Verified by
breaking it both ways before it went in**: a hand-edit to `main.min.css` is
caught, and a Sass change committed without its rebuild is caught.
[[mutation-verify-or-it-is-not-coverage]]

`npm ci`, not `npm install` — the committed lockfile pins `caniuse-lite`, which
browserslist consults. Unpinned, the emitted prefixes would change on caniuse's
schedule and fail the check on a day nobody touched the CSS. And the build is
deterministic: two consecutive runs hash identically.

#### A trap for anyone re-running the comparison

**browserslist resolves its config from the *input file's* directory, not the
working directory.** The first comparison here built to a scratch path outside the
package, where there is no `package.json`; autoprefixer silently fell back to its
defaults, dropped IE, and emitted a different stylesheet. It looks exactly like a
toolchain difference and is not — the first cut of this task's analysis reported
806 lost declarations that were an artifact of where the output was written.
[[probes-must-not-perturb-what-they-measure]]

#### Task 02's decision honored, not re-opened

Built CSS stays committed. The application image has no `node`, `npm` or `yarn`;
`.dockerignore` already excluded `sg101/node_modules`; and `node_modules` sits
beside `sg101/static` rather than inside it, so `collectstatic` cannot sweep 129
packages into the static tree. The command is documented in `README.md` and the
silent failure mode — a forgotten rebuild ships stale styling with no error
anywhere — is in `AGENTS.md`.

## Step 20 task 12 — unprivileged containers, and the tool that could never check them — DONE 2026-09-20, `e503b69b` + this planning commit, PUSHED

**Suite 1303 OK, gate 1303 OK (unchanged — no Python behaviour changed),
`tools/prod_smoke.sh` 21/21, `check --deploy` unchanged,
`tools/image_smoke.py` 2/7 → 7/7 against the production stack.** `web`, `worker`
and `beat` run as `uid=1000(sg101)`; Celery's superuser warning is gone.

### Two write paths the task file did not have

Its list was *"web writes ./media and ./var/log/django; worker and beat write
./var/log/django"*, and it says itself that the list was read rather than
measured. Measured in the running containers:

| process | writes |
|---|---|
| `web` | `/app/media`, `/app/sg101/logs`, **`/root/.gunicorn/gunicorn.ctl`** |
| `worker` | `/app/sg101/logs` |
| `beat` | `/app/sg101/logs`, **`/app/celerybeat-schedule`** |

Both extras are inside the image, not on a mount, and both belong to root there.
gunicorn's control socket needed a real home directory — `useradd --create-home`
— and beat's schedule file moved to `/home/sg101/celerybeat-schedule` via
`--schedule`. **Brian's call: home, not a volume.** That keeps its lifetime
exactly as it was, the container's writable layer, so a restart preserves it and
a recreate does not; today's behaviour, minus the permission problem.

`PYTHONDONTWRITEBYTECODE=1` was already set, so there is no `__pycache__` to
own, and `static_root` is built as root and only read.

### UID 1000 is a contract with the VM, and macOS cannot test it

**Brian's call: 1000, overridable with `--build-arg APP_UID`.** It is the first
ordinary account on Debian and Ubuntu, so on the VM it is almost certainly the
administrator's own — which keeps `media/` manageable without `sudo` on a
single-admin box.

**Docker Desktop translates bind-mount ownership and hides the whole question.**
Measured: inside the container `/app/sg101/logs/sg101.log` is `sg101:sg101`,
while the Mac sees the same file as `brianneal:staff`. Everything passes locally
whatever UID the image uses, which is precisely the configuration the VM would
reject.

So the check went into **CI, which is `ubuntu-latest` — the only real Linux this
project has until the VM exists.** It builds the `prod` target, asserts the
processes are uid 1000, and then asserts both directions: a directory owned by
1000 is writable **and one owned by another UID is refused.** The second half is
what makes the first mean anything — without it the check would pass against a
world-writable directory.

Exercised locally before it was written, against Docker named volumes, which
live inside the VM and so carry real Linux ownership: matching UID writable,
non-matching refused. **The first attempt at that local check reported the wrong
answer** — `if docker run ... | tail -1` tests `tail`'s exit status, not the
container's, so a denial read as a success. The CI step has no pipe and was
unaffected, but the harness proving it did.

### `tools/image_smoke.py` had never run against production, for two reasons

The tool exists because *"the unit suite mocks storage and runs against a
throwaway database, so it cannot tell you that an upload works on this
deployment"*. **It could not run on the deployment that matters.** Against the
production stack it scored **2/7**, and only the two direct-model checks passed.

| | cause | symptom |
|---|---|---|
| 1 | `Client()` sends `Host: testserver`; production's `ALLOWED_HOSTS` is `['.surfguitar101.com']` (development allows `'*'`) | every view-driven check 400 |
| 2 | production sets `SECURE_SSL_REDIRECT`, so a plain-HTTP POST is answered **301 to https** — which drops the body, and `follow=True` re-issues it as a GET | 200, and nothing stored |

Both fixed in the tool: it claims the first allowed host, and sets
`X-Forwarded-Proto: https`, which is how Apache tells Django a request arrived
over TLS. **7/7 against the production stack**, as the unprivileged user —
avatars, user photos and photo-of-the-day, all through the real views.

**Neither failure was the new user, and that was established rather than
assumed**: the same image, same settings, run with `--user root` scored the same
2/7. One variable, changed alone.

**The second cause was found by reading `sg101.log`** — which only works because
task 11 landed first. Before it, a `DisallowedHost` raised in the worker or
behind gunicorn reached no file at all.

### Development stays root, and says why

**Brian's call.** Development bind-mounts the whole checkout over `/app`, so
anything the container creates lands in the working tree owned by whoever the
container runs as — and on Linux a developer whose UID is not the one baked in
gets files they cannot edit. The reason for dropping root is also absent here:
the stack publishes to localhost, carries the debug toolbar and runs the suite.
`dev` builds `FROM prod`, so it sets `USER root` back explicitly, with that
reasoning beside it.

### The dependency on task 11, closed with evidence

Task 12's file says `logrotate`'s `create` must keep `var/log/django` writable
by the new user. Task 11 chose bare `create` — no mode, no owner — specifically
so it reuses the rotated file's own. Verified rather than reasoned: rotated with
real `logrotate` while the containers ran as `sg101`, the new `sg101.log` came
back **`sg101:sg101`**, and both a web request and a queued task wrote into it.

## Step 20 task 11 — the worker was logging to nothing, and three trees were silenced — DONE 2026-09-20, `870f375d` + this planning commit, PUSHED

**Suite 1303 OK, gate 1303 OK (1296 → 1303), `tools/prod_smoke.sh` 21/21
unchanged, `check --deploy` unchanged, 10 of 10 mutations caught.** Production's
file handlers are `WatchedFileHandler`, rotation moves to `logrotate/sg101`, and
the worker's records reach the files for the first time.

### The task named one defect; there were two, and the second is worse

The task file asks why *a task's completion* is not logged. Measured on the
running production stack 2026-09-20, **nothing the worker or beat logs reaches
any file at all** — not Celery's lines, not the application's.

| | cause | effect |
|---|---|---|
| 1 | `disable_existing_loggers: True` silences `celery.app.trace` | no `succeeded` line, anywhere |
| 2 | Celery's default `worker_hijack_root_logger` replaces root's handlers in the worker | every worker record that *relies on root* — the 13 module-named loggers, celery's own — went to the container's stdout and nowhere else. Loggers with their own handler were unaffected |

**Corrected 2026-09-20, after Brian questioned the development half.** This
section first claimed `email.log` was empty *by construction* and that the mail
audit trail had no answer in production. **That was wrong, and the mistake was
mine: I reasoned from a 0-byte file instead of sending a message.**

Celery's hijack replaces the **root** logger's handlers. It does not touch a
logger that has its own, and `email`, `auth`, `search` and `antispam.turnstile`
each have one. Tested by setting the hijack back on and sending a failing
message: **`email.log` filled anyway, 504 bytes.** The file was 0 bytes because
no mail had ever been sent through a local production stack built the day
before, which is a fact about the test rig and not about the site.

**What the hijack actually costs is everything that depends on root's
handlers** — the 13 module-named loggers and celery's own. Measured: an
application warning inside a task reached the container's output and not
`sg101.log`, and `sg101.log` had not been written since 2026-09-19 despite days
of task activity. The `email` logger's `propagate: True` half was lost with
them, so the audit line was in `email.log` and missing from `sg101.log` — half
of what that comment promises, not none of it.

[[suspect-the-measurer-before-the-record]] read the wrong way round: I had the
measurement (0 bytes) and invented a mechanism for it rather than testing the
mechanism. The hedge I attached at the time — *"reasoning from the demonstrated
mechanism plus a 0-byte file, I did not send real mail"* — named the exact gap
and I wrote the conclusion down anyway.

### The asymmetry is the finding, not the absence

`received` appeared and `succeeded` did not, from the same task, which looks
arbitrary until you ask *when each logger was created*:

| logger | existed when Django applied `LOGGING` | disabled | emits |
|---|---|---|---|
| `celery.app.trace` | **yes** | **yes** | `succeeded` |
| `celery.worker.strategy` | no | no | `received` |

**So which Celery lines survive is decided by which modules happened to be
imported first.** That is not a thing to work around one logger at a time. The
fix is one `celery` entry in `LOGGING`: dictConfig disables existing loggers it
was not told about, but *resets* the descendants of one it was told about, so
naming the parent keeps the whole tree.

**The first probe of this read the opposite and was wrong.** Run as
`python -c "import django; django.setup(); ..."`, `celery.app.trace` reported
`disabled=False` — because that process created the logger *after* dictConfig
had run. Re-probed in the worker's own order (`import celery.app.trace` first,
then `django.setup()`) it reports `disabled=True`. **The probe had the property
it was measuring.** [[probes-must-not-perturb-what-they-measure]]

A detail worth keeping: `celery.app` reports `disabled=False` in both orders,
because it is a `PlaceHolder` in `loggerDict` rather than a real `Logger`, and
dictConfig's disable pass skips those. Reading it as evidence the tree was fine
would have been wrong twice over.

### The hijack, proved from the format rather than asserted

An application `logger.warning()` inside a task printed as:

```
[2026-09-20 17:37:40,634: WARNING/ForkPoolWorker-6] update_user_stats: user id 999999 doesn't exist
```

That is **Celery's** format. The project's `simple` formatter is
`%(asctime)s %(levelname)s %(message)s`, with no brackets and no worker name. A
Celery handler had handled the record, which is what hijacking root means. After
`CELERY_WORKER_HIJACK_ROOT_LOGGER = False` the same line reads
`2026-09-20 17:45:49,985 WARNING update_user_stats: ...` and lands in
`sg101.log`. **`sg101.log` had last been written on 2026-09-19**, days of task
activity ago.

`email.log` and `sg101.log` now both carry the audit line — 489 and 1,772 bytes
on an exercised send — which is what the `email` logger's `propagate: True` has
always promised. Only the `sg101.log` half was ever missing.

### Rotation, and what was actually measured about retention

Retention on jaguar, read 2026-09-20 rather than taken from the task file's
figures:

| file | backups | oldest line | span |
|---|---|---|---|
| `sg101.log` | 10 | 2026-04-19 | **5.0 months** |
| `auth.log` | 5 | 2025-01-09 | **20.4 months** |
| `email.log`, `search.log`, `turnstile.log` | — | **absent** | — |

**Three of the five do not exist on the old host at all** — they arrived with
Steps 12, 16 and 17 — so for those there is no retention to preserve and nothing
to compare against. They take `auth.log`'s shape because they are the same kind
of file. **Brian's call: match that shape and add compression.**

`auth.log` gets **12 backups where the handler kept 5**. Its history is the
stated reason this approach beat one stream per container, and 12 compressed
backups cost less disk than 5 uncompressed ones do today — which also absorbs
the higher volume the new stack will produce, since the worker now writes here
too and every gunicorn process writes where one mod_wsgi daemon used to.

**`create`, never `copytruncate`**, and `create` with no mode or owner so it
reuses the rotated file's own — which keeps working when task 12 stops the
containers running as root.

**Exercised, not asserted.** Real `logrotate` was run against the running
stack's `var/log/django` (in a Debian container, since macOS has none). After
`sg101.log` → `sg101.log.1` left a 0-byte file, a web request and a queued task
both wrote to the **new** file:

```
2026-09-20 17:48:27,043 WARNING WEB-AFTER-ROTATE
2026-09-20 17:48:27,075 WARNING update_user_stats: user id 999999 doesn't exist
2026-09-20 17:48:27,076 INFO Task accounts.tasks.user_stats_task[...] succeeded
```

### The search tasks were logging into the worker's log, not `search.log`

**Found by Brian asking how Celery uses the new `celery` entry**, which is a
better question than it sounds: the answer is that Celery never looks it up.
The entry is structural — dictConfig disables existing loggers it was not told
about, but *resets* the descendants of one it was, so naming the parent spares
`celery.app.trace` and the rest. Routing is then plain propagation up to root.

Following that through turned up a second consumer of the same tree.
`celery.utils.log.get_task_logger()` **reparents** what it returns onto
`celery.task`, and `search/tasks.py` used it. Measured in the worker:

```
search.tasks[NullHandler] -> celery.task -> celery -> root[WatchedFileHandler, StreamHandler]
```

Its parent was `celery.task`, **not `search`** — so four `logger.warning` and
`logger.info` call sites never reached `search.log`, which has its own handler
and exists precisely so a sweep's findings sit beside the queries members ran.

**`search/reconcile.py:48` already documents the trap in a comment** and
deliberately uses a plain `getLogger('search')` to avoid it. `tasks.py` did not.
One line, now matching, with the same reasoning in a comment beside it.

Verified in the running stack: `search.log` went 0 → 76 bytes with the warning,
and the line is **absent** from `sg101.log`, which is the `search` logger's
`propagate: False` doing what it has always claimed.

**A discriminating mutation kept the two new tests honest.** Reverting to
`get_task_logger` fails both. Changing the logger to `getLogger('search.tasks')`
fails only the identity test — because a name-child of `search` still routes
correctly, so `assertLogs('search')` cannot tell the two apart. Without the
second test the fix could regress to something that routes by accident.

**A defect of my own, caught by the test count.** The new case first subclassed
`TaskTestCase` and so inherited and re-ran nine of its test methods — the suite
read 1311 where it should have read 1302. It needs no fixture at all, only a
database for the content-type lookup to miss in.

### "Do we have tests that records go to the right logs?" — we did not

**Brian's question, and the honest answer was no.** The `search/tasks.py` defect
is the proof: it logged into the worker's log for its entire life and nothing
failed, because nothing looked. What existed tested the *shape* of the two
LOGGING dicts and a couple of individual `assertLogs` cases; nothing tested
where a given module's records actually end up.

**The routing, measured under production settings 2026-09-20:**

| logger | records reach |
|---|---|
| `email` | email.log, sg101.log, console |
| `auth` | auth.log |
| `search` | search.log |
| `antispam.turnstile` | turnstile.log |
| the 13 module-named loggers | sg101.log, console |
| `django` | sg101.log (WARNING) |
| `django.request` | AdminEmailHandler, sg101.log |
| `MARKDOWN` | sg101.log (WARNING) |

All correct — but a measurement does not stop the next `get_task_logger`, so it
is now `test_every_logger_reaches_the_file_it_is_meant_for`, which pins 14
module-level loggers to their destination sets.

**It asserts on the logger *object*, not its name**, which is the whole point:
`get_task_logger` leaves the name `search.tasks` intact and moves the parent, so
a name check passes while the records go elsewhere. The test imports each module
first, so anything done to the logger at import time has already happened, then
walks the propagation chain to the handlers' filenames.

**Mutation-verified against the original defect.** Reintroducing
`get_task_logger` in `search/tasks.py` now fails the suite, and says why:

```
AssertionError: Lists differ: ['NullHandler', 'StreamHandler', 'sg101.log'] != ['search.log']
```

Flipping `auth`'s `propagate` to True fails five subtests, since four loggers
feed that file and their volume would start landing in `sg101.log`.

**One consequence of putting `console` on root rather than per logger:** the
four loggers with `propagate: False` — `auth`, `search`, `antispam.turnstile`
and `django` — do not reach the container's output at all. Their files are the
record. That is visible in the table above rather than left to be discovered.

### The same defect a third time: gunicorn was logging nothing either

**Found while sizing the container-log ceiling.** `Dockerfile` ran gunicorn with
`--access-logfile -`, so `web`'s stream should carry a line per request. It
carried none: **30 requests moved the stream 0 bytes.**

Same cause as `celery.app.trace`, one layer down. gunicorn builds
`gunicorn.access` and `gunicorn.error` before a worker loads the Django app, so
`disable_existing_loggers: True` disabled both:

| logger | existed when `LOGGING` applied | disabled |
|---|---|---|
| `gunicorn.access` | yes | **yes** |
| `gunicorn.error` | yes | **yes** |
| `gunicorn` | placeholder only | no |

**`gunicorn.error` is the real loss, not the access log.** It carries "Error
handling request" and a worker's own failures, and it had been going nowhere.
A `gunicorn` entry in `LOGGING` restores the tree exactly as the `celery` one
does; both now route to `sg101.log` and the container's output.

**`--access-logfile -` is removed rather than repaired.** Apache in front
already logs every request in the `combined` format fail2ban's filters are
written against, and it logs the ones Apache serves from disk too, so it is a
superset. Restoring gunicorn's copy would have put a second line per request —
about 114,000 a day at the rate measured on the old host — into the container
stream, to say what a bounded, retained file already says. The Dockerfile now
claims only what it does.

**Three places, one mechanism.** `celery.app.trace`, `search.tasks` (through
`get_task_logger`'s reparenting) and now `gunicorn.*` all lost records to
`disable_existing_loggers: True` and import order, and none of the three failed
anything. That is what the routing test above exists to stop.

### Every container stream was unbounded

Docker's `json-file` driver has no `max-size` or `max-file` by default, and
`docker-compose.prod.yml` set none: verified with
`docker inspect` — `driver=json-file opts=map[]` on every service. A container's
stream grew until the disk did.

Now `10m` x `3` per service through a `x-logging` anchor, verified against the
resolved configuration rather than the file:

| beat | postgres | proxy | redis | web | worker |
|---|---|---|---|---|---|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

30 MB a service, six services, and months of output at the volumes measured. It
needs no host cron, which is what makes it the cheapest of the three sinks to
close.

**Which makes the count worth stating plainly: this stack had four log sinks
and three were unbounded.** The Django files (fixed here), the container streams
(fixed here), Apache's files (**still open**, runbook B11) and Docker's own
daemon log. A task called "Production Logging That Survives Many Processes"
found that the logging mostly was not surviving at all.

### Should the four `propagate: False` loggers also reach the container output?

**Asked and answered no.** `auth`, `search`, `antispam.turnstile` and `django`
keep their records to their own files. The volume argument is weak — `auth.log`
measures ~0.6 MB a month on the old host — and the real reason is what each sink
is for: the files are rotated, retained for 20 months, and read by fail2ban,
while the container stream is a live view. Root already carries `file` and
`console`, so everything that propagates is in `docker compose logs` already;
these four are exactly the ones with somewhere better to be. If one of them ever
needs to be live, the change is `console` on that handler, not propagation.

### Found and deliberately not fixed: Apache rotates nothing either

`var/log/apache/` is written by the proxy container and **nothing rotates it**.
jaguar's `access.log` was **164 MB for a single week**, and that host had
`logrotate` for it. The new VM does not.

It is left because it is a *different* problem, not a smaller one: Apache holds
its log open and does not follow a rename, so it needs either a `postrotate`
that signals the container or `CustomLog` piped to `rotatelogs`, which changes
`apache/sites-enabled/`. Recorded as runbook **B11**, undecided, and flagged
there as something Step 21 must not flip DNS without.

### Development keeps its rotation and loses the hijack — corrected 2026-09-20

Dev keeps `RotatingFileHandler`: the task file scopes rotation out and gives a
reason that holds — nobody reads development logs for history, and there is no
host `logrotate` to hand rotation to.

**The hijack was a different matter and was excluded by mistake.** It first went
into `production.py` alone, on the strength of that same "development is out of
scope" line — but that line's reasoning is about *rotation*, and says nothing
about which handlers a worker writes through. **Brian pushed back and was
right.** The setting is now in `base.py`, so a worker logs the same way in both
deployments, and dev's root gains the `console` its container output would
otherwise have lost. `root.handlers` is no longer a difference between the two
targets at all.

**What it fixes in development:** worker records reach dev's `sg101.log`, which
they never did. Measured after the change — 1,078 bytes and three worker lines
in a file that had been getting none.

**The noise it was expected to cost: none, measured.** Dev's root runs at DEBUG,
so the worry was that every propagating DEBUG record would start printing. The
same two operations produced **336 bytes of worker console against 391 before**
— slightly *less*, because Celery's `[...: INFO/ForkPoolWorker-6]` prefix is
longer than this project's `... INFO`. Five page loads added **0 bytes** to the
web console. **The whole codebase contains six `logger.debug()` calls**, all in
`core/images/upload.py` on the photo-upload path, so there is almost no DEBUG to
emit.

**The format is the tell, and it caught a false result mid-measurement.** The
first run after the change reported byte-identical output — because
`docker compose up -d` had not recreated the already-running worker, which was
still on the old settings. Celery's bracketed prefix in the output said so
before the numbers did.

## Step 20 task 08 — the egress is the podcast, and one file extension explains it — DONE 2026-09-20, `66d87c77` + this planning commit, PUSHED

**`tools/prod_smoke.sh` 19/19 → 21/21, both new checks mutation-verified.** The
origin half is done and in the repo; the Cloudflare rule is specified below for
Brian to apply, and re-verification at cutover is runbook **B9**.

### The task named the wrong category, by 24x

**Measured from jaguar's Apache access logs, 27 Jul – 20 Sep 2026, 56 days**
(`access.log` plus 8 rotations — the full retained window). `%O` from the
`combined` format, which is bytes Apache sent, i.e. **origin egress**: behind
Cloudflare that is exactly what the VM's allowance bills.

| | requests | origin bytes | share |
|---|---|---|---|
| everything | 6,384,159 | **70.98 GB** | — |
| `/media` | 297,539 | 25.36 GB | 35.7% |
| **`podcast`** | 1,349 | **19.95 GB** | **28.1%** |
| `user_photos` | 61,489 | 3.30 GB | 4.6% |
| `avatars` | 173,885 | 0.94 GB | 1.3% |
| **`downloads`** | 362 | **0.83 GB** | **1.2%** |

`plan.md` says *"`downloads` (716 MP3 rows) is the one category worth measuring
egress on"*. It is not: it is 1.2%, and the podcast is 24x larger at 15.1 MB per
request against downloads' 2.4 MB. **The reasoning behind the plan's sentence was
sound — MP3s are the biggest files — and it picked the wrong set of them.**

Peak day 2.71 GB (05 Aug); peak podcast day 1.70 GB (22 Aug), so no single day
is an outlier that carries the total.

### One file extension explains all of it

| | Cloudflare, two requests |
|---|---|
| `sg101_episode11.mp3` | MISS → **HIT** |
| `sg101_episode11.m4a` | **DYNAMIC, DYNAMIC** |

Same directory, same `content-type: audio/mpeg`, 62.9 MB either way. **`.m4a` is
not in Cloudflare's default cacheable-extension list and `.mp3` is**, and
**11 of the 15 podcast episodes point listeners at `.m4a`** (`enclosure_url`;
only 4 use `.mp3`).

**The origin sends no `Cache-Control` or `Expires` for `/media` at all** —
verified against Apache on jaguar directly, bypassing Cloudflare, where both
files return byte-identical headers. jaguar sets `ExpiresDefault` on
`static_serve` and **never on `media`**. So the `max-age=14400` visible on the
`.mp3` through Cloudflare is **Cloudflare's own** default Browser Cache TTL, not
jaguar's. Reading it as the origin's would have made the `.mp3`/`.m4a` difference
look like an origin config difference, which is the wrong place to fix it.

**The new stack reproduced the gap exactly**: `<Directory /srv>` set no
`Expires`, and `mod_expires` was not among the modules `apache/Dockerfile`
enabled.

### Bandwidth was never the constraint, and that is the real answer

**~38 GB per 30 days against the 4,000 GB included with `g6-standard-2`** (4 GB,
$24.00/mo — the plan's named VM, read from Linode's public API at
`api.linode.com/v4/linode/types`, since **no allowance was recorded anywhere in
the planning documents**).

**0.95% of the allowance. ~105x headroom — with the podcast entirely uncached.**

The task exists to decide *"whether edge caching is sufficient to make disk
storage viable"*. It is not close: **disk storage is viable with no edge caching
at all.** Caching the podcast is worth doing because 28% of origin traffic for no
reason is waste, not because anything is at risk. **Recorded this way deliberately
— the number that matters is the one that says the question was not binding.**

### The origin half, and why the TTLs live in the repo

`apache/` now enables `mod_expires` and sets, under `/media`, a year — with a
month for `/media/podcast/`. **The split is justified by mutability, not by
guesswork about traffic:**

| category | how the path is built | reusable URL? |
|---|---|---|
| `avatars/users/` | username + microsecond stamp (`bio/models.py`, whose comment says it is for cache-busting) | no |
| `downloads/` | `downloads/Y/M/D/<random>/` | no |
| `potd/` | `potd/%Y/%m/%d` | no |
| `badges`, `smiley/`, `news/`, `banners/` | plain directories, but written through Django storage, which suffixes a colliding name | no |
| **`podcast/`** | **not Django-managed at all** — `podcast.Item.enclosure_url` is a `URLField` and the audio is placed on disk by hand | **yes** |

So everything except the podcast is immutable by construction and a year is not
optimism, it is the lifetime of the bytes. **Brian's call on the podcast: one
month, and purge on republish.**

**The Cloudflare rule carries no TTLs**, deliberately: its Edge TTL is set to use
the origin's `Cache-Control` when present, so the policy above is the only copy
and it travels with the code — the jaguar complaint, not repeated.

### The rule — applied by Brian 2026-09-20, Cloudflare → Caching → Cache Rules

```
Name:  Cache /media
If:    (starts_with(http.request.uri.path, "/media/"))
Then:  Cache eligibility ....... Eligible for cache
       Edge TTL ................ Use cache-control header if present, cache
                                 request with Cloudflare's default TTL for the
                                 response status if not
       Browser TTL ............. Respect origin TTL
```

**The Edge TTL as first specified here named a control that does not exist.** It
said *"use cache-control if present, otherwise use default: 1 month"*, and
Cloudflare's form offers no custom fallback on that option — the TTL input is
greyed out. A TTL can only be named on *"Ignore cache-control header and use this
TTL"*, which would override the origin's per-category headers after cutover and
discard the reason for putting the policy in the repo at all. The option above is
the right one; **Brian caught this from the form rather than from the spec.**

**The consequence, which is the whole of the difference:** jaguar sends no
`Cache-Control` for `/media`, so today the fallback branch is live — Cloudflare's
status-code default, measured in hours. After cutover the new origin's
`max-age=31536000` (a month for the podcast) is present and the fallback is never
reached. **So the TTLs change at cutover without the rule being touched**, which
is what runbook **B9** exists to re-verify.

**Acceptance criterion 3 met 2026-09-20.** The `.m4a` that returned `DYNAMIC` on
every request went `DYNAMIC → MISS → HIT`, and `HIT` with `age: 18` thereafter:

| path | req 1 | req 2 |
|---|---|---|
| `/media/podcast/sg101_episode12.m4a` | MISS | **HIT** |
| `/media/downloads/.../walk-dont-run-drums-track.m4a` | MISS | **HIT** |
| `/media/avatars/users/...jpg` | HIT | HIT |

**A first probe read `DYNAMIC` three times for `/media/downloads/` while the
podcast was already `HIT`**, which looked like the rule matching one subtree and
not another. It was propagation across PoPs, and retesting a minute later showed
every path caching. Recorded because a single reading of `cf-cache-status`
immediately after a rule change is not evidence of anything.

**The full 28% saving lands at cutover, not today**, since the short fallback TTL
will not hold ~24 podcast requests a day spread across ~20 files and many PoPs.
That is acceptable on the measurement above — egress is 0.95% of the allowance —
and the reason to apply now was to reach cutover with the rule exercised.

### Two things left alone

**`?source=iheart` appears on 48 podcast requests.** Cloudflare's cache key
includes the query string, so those are separate cache entries from the bare
URL. Not worth an ignore-query-string rule: it is 3.5% of podcast requests, and
the rule would apply to all of `/media`, where a query string could one day mean
something.

**18 requests for `/media/downloads/` returned 404**, and a long tail of
`/media/.env`, `/media/.git`, `/media/terraform.tfstate` and similar probes
appears throughout — attack noise, a few bytes each, listed here only so the next
reader of these figures does not mistake them for a finding.

## Step 20 task 05 — Redis bounded, and the socket that outlived its machine — DONE 2026-09-20, `0b6a96b0` + this planning commit, PUSHED

**Suite 1296 OK, gate 1296 OK (1292 → 1296), `tools/prod_smoke.sh` 19/19
unchanged, `check --deploy` unchanged, 8 of 8 mutations caught.** Production
Redis is `redis:8.10` with a 256 MB ceiling and `maxmemory-policy volatile-lru`;
`REDIS_UNIX_SOCKET` and the branch that consumed it are gone.

### What the old host actually holds, measured 2026-09-20

Taken before anything was decided, because "what should the ceiling be" deserved
a number. jaguar, Redis 2.6.13 and memcached, both 150 days up:

| | Redis (db 0 + db 1) | memcached (the cache db 2 replaces) |
|---|---|---|
| in use | **1.88 MB** (peak 2.31 MB) | **1.05 MB** |
| ceiling | none | 64 MB |
| keys | db0 831, db1 3 | 369 |
| evictions | — | **0 in 150 days** |
| hit rate | — | 53,076,509 / 53,779,782 = **98.7%** |

**The whole post-cutover working set is ~3 MB.** So the ceiling is a blast
radius, not a capacity estimate: 256 MB is ~85x the measurement and 4x a limit
that was never once touched. It is `REDIS_MAXMEMORY` in `.env`, defaulting in
the compose file, because the VM does not exist yet — the constraint is recorded
and the number stays revisable, the same split Step 20's planning names.

**jaguar's `maxmemory-policy volatile-lru` is not evidence of a decision.** It is
Redis 2.6's *default*; the default became `noeviction` in 3.0, which is what both
candidate images start with. Measured on both rather than recalled.

### Requirement 3's premise was false, and the three exceptions are named

The task says to confirm kept state and broker keys carry no TTL. **The broker
does not. db 0 does** — `expires=3` of 831, enumerated rather than inferred:

| key | TTL when read | what it is | safe to evict? |
|---|---|---|---|
| `core:stats` | 10,373 s | 4 h copy of `core_statistic` pk=1 | **yes** — `get_stats()` falls back to the database and repopulates |
| `user_photos:counts:Jerome` | 59,557 s | upload rate limiter, 50 per 86,400 s | **no** — nothing rebuilds it |
| `user_photos:counts:Colorado_Instrumental` | 6,208 s | same | **no** |

**Brian's call: accept and document.** Eviction begins only at the ceiling, and
the blast radius is one member regaining part of a 50-photo day. What makes that
a decision rather than an oversight is that it is now *pinned*:
`core/tests/test_redis_ttls.py` asserts the inventory, so a fourth expiring key
in db 0 fails the suite and has to be argued for.

### The eviction was exercised, not asserted

Filled db 2 past the real 256 MB ceiling (3,500 × 100 KB) with broker messages
and kept state present:

| | before | after |
|---|---|---|
| `used_memory` | 1.57 MB | 255.97 MB against a 256.00 MB ceiling |
| db 1 `celery` | llen 3, ttl −1 | **llen 3, ttl −1** |
| db 0, the three keys with no TTL | present | **all present** |
| db 0 `user_photos:counts:brian` | present, ttl 86,400 | **evicted** |
| db 2 | 0 | 2,322 of 3,500 survived; `evicted_keys` 1,178 |

So the documented caveat is demonstrated rather than predicted — the one db-0
key the policy can take is exactly the one the table above says it can.

**The first run of this was invalid and said the opposite.** It reported the
broker's `celery` list gone, which would have made `volatile-lru` unusable. The
cause was not eviction: the local production stack had been up 19 hours since
task 03, so **a live Celery worker consumed the messages** the probe had just
queued. `RestartCount=0` ruled out a crash, and the `_kombu.binding.*` sets in
db 1 were the tell — a connected client's, not a seeded one's. Re-run with
`worker` and `beat` stopped, the broker is untouched.
[[probes-must-not-perturb-what-they-measure]], in the form where the perturbing
thing is not the probe but something else already running beside it.

### Redis 8, and the lifecycle table that would have answered wrongly

`redis.io`'s "product lifecycle" page gives 6.2 an EOL of **2025-02-28** and is
the first hit for the question. **It is Redis *Enterprise*'s schedule.** Redis
Open Source's own `SECURITY.md` lists **6.2.x as supported, "support extended"**,
and 6.2.23 / 6.2.24 shipped 2026-07-23 and 2026-08-17 beside the 7.x and 8.x
patches. Taking the wrong table at face value would have retired a version that
is still receiving fixes — and it also lists **8.0.x as unsupported** while 6.2
is not, so "newer is safer" fails here too.

The move was measured rather than argued, since 6.2 → 8.10 looks like four major
versions:

| | redis:6.2.24 | redis:8.10.1 |
|---|---|---|
| full suite | 1292 OK | **1292 OK** |
| Celery worker + beat, real broker | — | **5 tasks published and consumed** |
| the 24 commands this app issues | ok | **identical** |
| an RDB written by 6.2.24 | — | **loads; values and TTLs intact** |
| `maxmemory-policy` default | `noeviction` | `noeviction` |
| baseline `used_memory` / RSS | 885 KB / 7.97 MB | 1.38 MB / 22.96 MB |

**The worker run is the one that counts.** `CELERY_TASK_ALWAYS_EAGER` means 1292
green tests say nothing about kombu against a real broker, so the suite could not
have caught a broker-level incompatibility. The command surface this site uses is
1.x-era — `zadd`, `hgetall`, `lpop`, `incr`, `expire` — which is why the version
gap overstates the risk. Nothing migrates either: the development `redis` service
has no volume at all, and production's is empty on a VM that does not exist.

**The measured cost of 8.10 is five bundled modules** — `search`, `ReJSON`,
`timeseries`, `bf`, `vectorset` — that the site never calls, worth ~15 MB of RSS.
They can be switched off by mounting an empty tmpfs over
`/usr/local/lib/redis/modules` (verified: 22.62 → 12.40 MB RSS, suite still
green), since the entrypoint loads whatever `.so` files it globs there.
**Brian's call: leave them.** The saving is cosmetic on an 8 GB VM and the tmpfs
line is not self-explanatory. Recorded here so the option does not have to be
rediscovered.

### The socket default was the dead architecture, and the live configs were the exceptions

`base.py` defaulted `REDIS_UNIX_SOCKET` to `/var/run/redis/redis.sock` and
pointed `CELERY_BROKER_URL` at the same path, so `dev.py`, `docker_test.py` and
`production.py` each had to switch it back off by hand. **Deleted rather than
inverted**: with nothing able to supply a socket, `core/services.py`'s
`if unix_socket_path:` was unreachable and the setting dead with it. Gone from
six files, plus the commented-out `CELERY_RESULT_BACKEND` that named the same
socket and a `new_join=1` option Celery dropped years ago.

`base.py` now reads `REDIS_HOST`/`REDIS_PORT` from the environment and builds the
broker URL from them, so the three container modules stop repeating it;
`docker_test.py` keeps only its own broker database (15) and `production.py` only
its cache.

**The new settings test covers `base` and `test` as well**, which
`DEPLOYMENT_SETTINGS` does not — they are where the socket default actually
lived, so the inversion would have gone uncovered exactly where it was made.
Neither names a database, so it needed a Redis-only snippet rather than
`DEPLOYED_BACKENDS_SNIPPET`.

### Two mutations that proved nothing until they were fixed

8 of 8 caught, but two had to be rewritten first, both instances of the same
rule — [[mutation-verify-or-it-is-not-coverage]]:

1. **Adding `expire` to `accounts:user_count` was self-neutralizing.** The next
   line is `redis.set(USER_COUNT_KEY, count)` on the `count == 1` branch, and
   `SET` clears a TTL. The test passed because the mutation undid itself, not
   because the test was blind. Re-aimed at `accounts:new_users`, which is
   `lpush`/`ltrim` only — caught.
2. **Deleting `conn.expire(key, seconds)` from the rate limiter left an empty
   `if` block**, so what failed was an `IndentationError` at import. A syntax
   error is not the fault under test. Replaced with `pass` — caught.

### Not done here

The `banners:url:*` lists and `forums:*` caches in db 0 are written without a
TTL and are also derived — they rebuild from the database on a miss. They are
*not* in the exception table because nothing evicts them, and giving them TTLs to
make them evictable would be a change to how the site behaves under memory
pressure it has never been under.

## Step 20 task 04 — the real client IP, and the half jaguar never needed — DONE 2026-09-19, `472b1e03` + `559c64e1`, PUSHED

**Suite 1292 OK, gate 1292 OK (1271 → 1292), `tools/prod_smoke.sh` 19/19
unchanged, 17 of 17 mutations caught.** `mod_remoteip` trusts Cloudflare's 15
IPv4 and 7 IPv6 ranges and believes `CF-Connecting-IP` only from them; the vhost
restates the result as `X-Real-IP`; `core.middleware.RealClientIP` puts it back
into `REMOTE_ADDR` before anything reads it.

### The finding: porting jaguar's file is necessary and not sufficient

The task file's premise was *"jaguar already solves it… task 03 chooses a
Debian-based image precisely so this ports as a file."* **It ports as a file and
then does not work**, because jaguar ran Django *inside* Apache under `mod_wsgi`.
There, `mod_remoteip`'s rewrite **was** the application's `REMOTE_ADDR` — one
process, no hop. Task 02 replaced `mod_wsgi` with gunicorn behind
`mod_proxy_http`, putting a network hop between the server that knows the client
and the process that records it.

Measured before it was diagnosed: with `remoteip.conf` in place and correct,
Apache logged `198.51.100.7` while the application logged `172.19.0.7` — **the
proxy container's own compose address**, for every request, from every visitor.

| | trusted peer, `CF-Connecting-IP: 198.51.100.7` | untrusted peer, same header |
|---|---|---|
| `%a` (client) | `198.51.100.7` | `192.168.65.1` |
| `%{c}a` (peer) | `103.21.244.3` | `192.168.65.1` |
| `%h` (what `combined` logs) | **`198.51.100.7`** | `192.168.65.1` |

**`%h` follows the substitution**, so `combined` is untouched and fail2ban's
format-specific filters keep working — the reason Apache was chosen over nginx.

**The consequence worth keeping separate:** Step 21's fail2ban reads the *Apache*
log and was therefore already satisfied by the Apache half alone. The six
applications were not. A half-done version of this task would have looked
finished from the direction anyone was watching.

### Requirement 2 — the range re-check, 2026-09-19

`www.cloudflare.com/ips-v4` and `ips-v6`, cross-checked against
`api.cloudflare.com/client/v4/ips` (etag `38f79d050aa027e3be3865e495dcc9bc`).
**15 IPv4 and 7 IPv6, identical to jaguar's list as sets and in published
order. No drift since 2026-08-21.** Two sources, not one read twice. The file is
generated from the fetched lists rather than retyped.

### `IP_PAT` was IPv4-only, and had been for as long as it existed

`get_ip()` matched `(\d{1,3}\.){3}\d{1,3}` and returned `None` otherwise —
**which is also what "no address" looks like**, so it failed silently. Every
visitor arriving over IPv6 got `None`, **on jaguar today**, since `mod_remoteip`
is live there and Cloudflare serves IPv6.

Blast radius is the three `get_ip` callers, not the six direct `REMOTE_ADDR`
readers: who's-online never counted an IPv6 visitor, `turnstile.verify` lost the
`remoteip` hint (degraded, not broken — it already omits a `None` deliberately),
and the search log recorded no address. **The three address columns are
`GenericIPAddressField`**, so nothing ever truncated or raised; the address was
dropped in one function, quietly. Now validated with `ipaddress.ip_address`,
which also stops a value that merely *begins* with an address being accepted as
one.

Proved end to end through the stack: `whos_online:visitors` in Redis db 0 held
`198.51.100.7` and `2606:4700:4700::1111` after one anonymous visit from each
family. Before, the second would not have been there.

**`get_ip` also unwraps IPv4-mapped IPv6** (`::ffff:192.0.2.3` →
`192.0.2.3`), so one visitor cannot become two identities. Nothing observed
sends the mapped form — Apache gives the plain one for IPv4 peers — so this is a
guard, not a fix for something measured. Nothing else is rewritten: an address in
an equivalent-but-different spelling is returned as the proxy sent it, and a
mutation canonicalizing everything is caught.

**It is `get_ip` only, and that is not all the readers.** Six applications read
`request.META['REMOTE_ADDR']` directly and never call `get_ip` — `forums`,
`comments`, `downloads`, `donations`, `antispam`, `accounts` — so a mapped
address would still reach `Post.user_ip`, `Comment.ip_address` and
`Download.ip_address` as written. Covering those would mean normalizing in
`RealClientIP` instead, where `REMOTE_ADDR` is set. Deliberately not done;
recorded here so the gap is not rediscovered as a bug.

### `CSRF_TRUSTED_ORIGINS` is not needed — measured, with a control

The task file asserted it was. It is not: `ProxyPreserveHost On` means
`request.get_host()` is the browser's own host, so Django's Origin check matches
without it.

| POST through the proxy | result |
|---|---|
| Origin and Host both `surfguitar101.com` | 200 |
| Origin and Host both `www.surfguitar101.com` | 200 |
| Host `surfguitar101.com`, Origin `www.surfguitar101.com` | **403** |

**The third row is what makes the first two mean anything** — without it, two
200s are equally consistent with the CSRF check being absent. Not added:
unused configuration in the security boundary has a cost, and the setting earns
its place only if a www→apex redirect or a posting subdomain is ever introduced.

### Mutation batteries — 17 of 17, after the first run measured nothing

**Django, 11/11**, every file restored byte-identical (sha256): `RealClientIP`
dropped from production `MIDDLEWARE`; moved from first to third; made a no-op;
its address validation skipped; pointed at `X-Forwarded-For`; made to overwrite
`REMOTE_ADDR` with no header present; `get_ip` reverted to the IPv4 pattern; and
`get_ip` made to accept a leading address out of a longer string. Three more on
the mapped-form unwrap: reverted to the old behaviour, widened to canonicalize
every address, and with the mapped check inverted.

**Apache, 6/6**, each through a graceful reload and re-probed, both files
restored byte-identical: IPv6 ranges swapped for an unrelated one, the IPv4 range
holding the peer swapped out, `RemoteIPHeader` pointed at `X-Forwarded-For`, the
trust list widened to include the spoofing peer (**the spoof was then believed**,
which is what proves the list is the boundary), `X-Real-IP` not set, and
`expr=%{REMOTE_ADDR}` → `expr=%{CONN_REMOTE_ADDR}`.

**The first Apache run reported 3 of 7 survived, and all three were wrong.** The
mutations renamed `RemoteIPTrustedProxy` to an invalid directive — so
`apache2ctl -k graceful` **refused the configuration and Apache kept serving the
one it already had.** The probe then measured the unmutated system and read as a
survival. **An invalid configuration is not a mutation**; the battery now runs
`configtest` after each one and reports `INVALID` rather than a result. Same
class as the `mysql -B` escaping in the collation audit — a difference in the
measurement presented as a difference in the thing.

Two more of my own errors in the same run, both of which produced a confident
wrong answer first:

- **`0.0.0.0/0` is not accepted by `mod_remoteip`**, so the trust-widening
  mutation was invalid rather than survived. Redone with `192.168.0.0/16`, which
  contains the spoofing peer, and it was caught.
- **`$DC` holding `docker compose -f …` does not word-split in zsh**, so a reload
  silently never ran and the mutation read as survived. The same trap the
  collation audit recorded, in a different shape.

### Two things found while probing, neither a defect

- **Apache binds its listeners at startup.** The proxy container was started
  before the IPv6 probe network was attached, so it bound IPv4 only and the IPv6
  probe could not connect at all — which looked exactly like a missing IPv6
  trust entry. After a restart it binds `[::]:443` dual-stack. A probe artifact,
  but worth knowing on the VM: attach the interface, then start.
- **Without `mod_remoteip` loaded, Apache refuses to start**, because
  `remoteip.conf`'s directives become invalid. That is the good failure: loudly,
  at start, rather than silently recording the edge. Disabling the module as a
  mutation therefore also needs the container recreated from the image
  afterwards.

### Testing

`core/tests/test_real_client_ip.py` is new and holds criterion 6 in one place:
comments, forum topics, forum posts over IPv6, and downloads read back from the
database, plus failed login and failed registration read back from `auth.log`.
**Every request arrives with `REMOTE_ADDR` set to the proxy's address and asserts
a different one**, so a test that passes because the middleware did nothing is
not possible. The logging pair copies the enable-and-restore dance from
`contact/tests/test_views.py`.

**What the suite cannot cover, and what to do instead:** `tools/prod_smoke.sh`
makes every check from outside, and what the application recorded is visible only
on the host, so the smoke script is **not** extended here. Cutover runbook **B3**
now carries the manual verification and the ordering constraint into Step 21.

### Not done here

The proxy's own `X-Forwarded-For` handling is untouched. `mod_proxy_http`
appends the corrected client to it on the way to gunicorn, and nothing reads it —
`get_ip`'s docstring and `AGENTS.md` both say not to, and that stands.

### Deferred — routing the other readers through `get_ip` (asked 2026-09-19)

**Question: should the applications that read `REMOTE_ADDR` directly call
`get_ip` instead, and should the normalization live in the middleware rather
than in `get_ip`? Answer: partially, and no. Neither is urgent and nothing is
blocked.** Recorded here with the measurements, because they are what set the
priority and they are not obvious from the code.

**The normalization stays in `get_ip`.** The two pieces answer different
questions and the split is the point: `RealClientIP` answers *whose address is
this*, which is deployment-specific and only correct behind the proxy;
`get_ip` answers *is this a usable address, canonically spelled*, which is true
in dev, in the suite and on the VM alike. Moving it into the middleware would
make canonical spelling a property of running in production — the same input
returning different strings in dev and prod — and would still not reach
`get_ip`'s own callers outside production.

**Switching the direct readers is worth less than it looks, because the database
already refuses bad values.** All three address columns are PostgreSQL `inet`,
and two of them are `NOT NULL`:

| column | type | null |
|---|---|---|
| `comments_comment.ip_address` | `inet` | NO |
| `downloads_download.ip_address` | `inet` | NO |
| `forums_post.user_ip` | `inet` | YES |

So a value that is not an address cannot be stored today. Switching those three
writers to `get_ip` turns a `DataError` into an `IntegrityError`; it changes
which exception is raised, not whether bad data lands. **This corrects an
assumption made earlier the same day** — that the direct readers could persist
junk. They cannot.

**The six log-only sites would get worse, not better.** `donations`,
`antispam` (x2) and `accounts` (x3) interpolate the address into a string and
default it to `'?'` or `'unknown'`. `get_ip` returns `None`, so a straight swap
makes `auth.log` read `Login failure from [None]` — in the file fail2ban parses
and the registration-spam analysis ran on. They would need
`get_ip(request) or '?'`, which is more code for identical behaviour.

**The one real argument for doing it**: `get_ip`'s docstring is the single place
this project states the rule about never preferring a client-supplied header,
and seven of the ten call sites do not go through it. That is consistency and
discoverability, not correctness.

**Priority low; the mapped form has no producer in this stack.** Gunicorn binds
`0.0.0.0:8000`, so it only ever sees IPv4 peers, and Apache reports plain forms
already — measured during the mutation battery, a plain `192.168.65.1` from an
IPv4 client against a `[::]:443` listener. The unwrap added to `get_ip` guards a
case nothing currently generates.

**Where it belongs: after Step 21.** Not Step 20, which is production hardening;
this is application tidying of the kind Step 19 Phase D collects, and nothing
before cutover needs it.

## Step 20 task 03 — the production stack, Apache in front — DONE 2026-09-19, `60c54324` + `127c22c6`, PUSHED

**Suite 1271 OK, gate 1271 OK, `tools/prod_smoke.sh` 19/19, `check --deploy`
down to W005 and W021, both deliberate.** `docker-compose.prod.yml` runs `proxy`
(Apache), `web` (gunicorn), `worker`, `beat`, `postgres` and `redis` with
production settings; only the proxy publishes a port. Brian browser-tested it
2026-09-19 through a throwaway Chrome mapped to the local stack: good.

### jaguar's vhost, read for the first time — and what it said

`sites-enabled/surfguitar101.com.conf` had been recorded nowhere in `.agents/`.
Brian ran the read (the ssh was refused to me as a production read). It settled
one question and turned up three gaps:

- **HSTS came from jaguar's Apache**, `Header add Strict-Transport-Security
  "max-age=604800"`. **Now Django's**: `SECURE_HSTS_SECONDS = 604800`, no
  subdomains, no preload, and the new Apache sends none, so there is one header
  with one value. ~~Whether Cloudflare's own HSTS setting is off is **not
  verified**; one header at the edge is consistent with either.~~ **Verified off,
  2026-09-20 — see below.**
- **`/robots.txt`, `/favicon.ico` and the Google verification file were served
  only by Apache aliases.** WhiteNoise serves them under `/static/`, so without
  aliases all three would have 404'd at cutover. The live `/robots.txt` is
  byte-identical to `static/robots.txt`, `last-modified` one minute after
  `ab46ab25` — jaguar's file, cached by Cloudflare. Brian relies on Cloudflare for
  bot control; the alias is kept anyway, since dropping it later is one line.
- **Five SG101 1.0 URL rewrites**, ported verbatim.
- **`/hosted/` and `/photos/` alias into jaguar's document root** — 16 MB + 69 MB,
  1,509 files, 40 requests in that day's access log (window not measured, not
  split by bot). Carried: served from `var/public/`, rsync'd at cutover as
  runbook **B8**.

Not ported, deliberately: jaguar's 2016 cipher list (it allows TLS 1.0/1.1; only
Cloudflare connects to the new origin, so Debian's defaults stand), `mod_wsgi`,
Let's Encrypt's `.well-known/`, and static `Expires` headers (WhiteNoise sets
its own).

### Decisions taken (Brian, 2026-09-19)

| Decision | Choice |
|---|---|
| 03/04 boundary | 03 builds the whole vhost; 04 keeps `mod_remoteip`, the range re-check, `CSRF_TRUSTED_ORIGINS` |
| Compose | a standalone `docker-compose.prod.yml`, project `sg101-prod` |
| Apache config | top-level `apache/`, Debian layout, the **directory** bind-mounted |
| `sg101/apache/` | removed (it was empty and untracked since task 02) |
| Health checks | the home page, not a `/health/` view |
| Django logs | bind-mounted to `var/log/django` |
| Smoke test | `tools/prod_smoke.sh`, taking an origin address |

**Why the project name matters:** both compose files use the same service names,
so without `name: sg101-prod` they are one project and `up` on either replaces
the other's containers. **Why a directory mount:** vim saves by writing a new
file, and a single-file bind mount keeps the old inode — an edit that never
reaches Apache and no error saying so.

**Why the home page:** it is uncached apart from a 600s slideshow fragment, so
every render queries PostgreSQL and loads forum tags that read Redis. A health
view would have been ~15 lines and four tests to prove less. Two checks every
30s is ~5,800 renders a day against ~90k real requests.

### Requirement 10: both halves of the socket

`production.py` now sets `REDIS_UNIX_SOCKET = None` and
`CELERY_BROKER_URL = redis://{REDIS_HOST}:{REDIS_PORT}/1`, the `dev.py` shape.
`base.py`'s default is untouched; inverting it is task 05's requirement 5.

### Measured against the running stack

The development database was piped into the production stack's own volume
(`pg_dump` from dev, search data excluded): **463,223 posts, 15,227 users** on
both sides. All six services came up healthy on the first start.

| Criterion | Result |
|---|---|
| 1 serves through Apache, DEBUG off | 200; the 404 page is not the debug page |
| 2 no MySQL | `db` absent; the prod image cannot import `debug_toolbar` |
| 3 proxy only | 8000, 5432, 6379 refused — **with the dev stack stopped**, which publishes all three |
| 4 access log on the host | `combined` lines in `var/log/apache/access.log`; the proxy's own health requests excluded |
| 5 health | PostgreSQL stopped → `web` and `proxy` unhealthy at **71s**, healthy **20s** after it restarted |
| 6 graceful reload | **240/240** requests 200 across two reloads |
| 7 Redis consumers | Celery's own `inspect stats`: the worker ran `core.tasks.max_users`; a logged-in first request wrote `whos_online:users` in db 0 |
| 8 docs | `DOCKER.md` §10 |

Two readings of criterion 5 worth keeping: a **stopped** container shows
`exited`, not `unhealthy` — the dependents are what report it — and the
**worker stays healthy** with the database down, because its check is a broker
round trip.

**Maintenance mode** returns `offline.html` with 503 whether gunicorn is up or
down, POSTs and `/robots.txt` included. With no flag and gunicorn down, visitors
get the same page, since the 503 error document covers a dead backend too.

### Mutation batteries — 14 of 14, one only after a check was added

**Settings, 7/7**, `production.py` restored byte-identical: socket left
inherited, broker back on the socket, broker on db 0, redirect off, HSTS on
subdomains, preload on, HSTS at a year.

**Apache, 7/7**, each run through a graceful reload and the smoke script, vhost
restored byte-identical: a legacy rewrite dropped, `X-Forwarded-Proto` dropped
(home page 301s to itself), the robots alias dropped, HSTS added in Apache (two
headers), the `/media/` proxy exclusion dropped, the health-check log exclusion
dropped (caught by reading the log, not the script), and **`set` →
`setifempty` on `X-Forwarded-Proto`, which survived the first run.** The script
never sent the header, so it could not tell the two apart. A check now sends
`X-Forwarded-Proto: http` and expects 200; it fails on `setifempty` with a 301.

### Three errors of my own in the probes

1. **zsh does not word-split `$P`**, so the first restore ran nothing on the
   production side. The dev dump was read and cut off; nothing was written.
2. **The who's-online probe sent `sessionid`**; this site's cookie is
   `sg101_sessionid`. The first "no write" was an anonymous request, not a
   broken stack.
3. **`core:stats` in db 0 nearly counted as proof the worker ran.** `get_stats()`
   copies the row from the database into Redis on any read, so it proved only
   that *something* wrote db 0. Celery's own count is what shows the worker.

### Open, and not this task's — each now has an owner (2026-09-19)

| Item | Owner |
|---|---|
| Task completion lines logged nowhere | **task 11**, new |
| Log rotation races | **task 11** — `WatchedFileHandler` + host `logrotate`, Brian's call |
| Client address in the access log | **task 04**, already its purpose |
| Containers run as root | **task 12**, new |
| `redis:6` | **task 05**, requirement 8 added |

The detail as found:

- **Task completion lines appear nowhere** — not in the worker's output, not in
  `var/log/django`. "Received" is logged; "succeeded" is not.
- **Log rotation races.** N gunicorn workers, the Celery worker and beat all
  write the same files through `RotatingFileHandler`, and each process rotates
  on its own. Lines can be lost or land in the rotated file. True since task 02
  brought gunicorn; jaguar's single mod_wsgi process never had it. **Decided
  2026-09-19:** keep the separate files — `auth.log`'s long retention is what the
  registration-spam analysis ran on — with `WatchedFileHandler` in production
  and rotation on the host. Stdout and the Docker log driver was considered and
  rejected because it merges the files.
- **Client address in the access log** is the Docker gateway locally, and will be
  Cloudflare's edge on the VM until task 04.
- **The application containers run as root**, and Redis stays at 6 to match dev.
  Measured: `web` is `uid=0`, and the worker prints Celery's superuser
  `SecurityWarning` at every start. Apache's root parent with `www-data`
  children is the standard arrangement and not part of this.

**Step 20 is twelve tasks, not ten**, as of 2026-09-19: tasks 11 and 12 were
generated from the rows above.

## Step 20 task 02 — gunicorn, WhiteNoise, and a static pipeline that had never run — DONE 2026-09-17, `7d51fe34`, PUSHED

**Suite 1269 OK, gate 1269 OK, `check --deploy` down to the two warnings this
task deliberately leaves.** The production image no longer runs `runserver`, and
`sg101/wsgi.py` exists for the first time.

### The finding: `collectstatic` had never worked on this stack

`collectstatic` exited 1 under `ManifestStaticFilesStorage` with a
`UnicodeDecodeError` — **two files in TinyMCE's `spellchecker` plugin are
latin-1**, and they have been since 2011.

**It never surfaced on jaguar, and the reason is exact.** `fabfile.py:15` has run
`collectstatic` with production settings on that host for years. Hashing reads
bytes; only files matching `HashedFilesMixin.patterns` are decoded as UTF-8 to
rewrite references. Read out of the installed 5.2 rather than recalled:

```
*.css -> 3 reference pattern(s)
*.js  -> 1 reference pattern(s)
```

**The `*.js` entry is recent** — it exists to rewrite `sourceMappingURL`. On
Django 1.8 only CSS was post-processed, so those two files were hashed as bytes
and never decoded. **The blast radius grew underneath files nobody had touched.**

**Nothing else on this stack runs `collectstatic`, so the first deploy to the new
host would have failed** — at cutover, on the day with the least room for it.

**Fixed by deleting the plugin** (Brian's call): it is not in the enabled list —
`table,advhr,emotions,insertdatetime,preview,searchreplace,print,contextmenu,fullscreen,media,paste`,
**11 of 36 shipped plugins** — so re-encoding would have fixed a plugin nothing
loads. With it gone, **1122 files copied and all 1122 post-processed**, no
missing-reference failures. That answers the task's open question: the existing
`ManifestStaticFilesStorage` configuration does survive Django 5.2's `STORAGES`,
and the encoding was the only blocker.

### Decisions taken

**`sg101/wsgi.py` has no default settings module.** `manage.py` and `celery.py`
default to development, which is right for a person at a terminal. The same
default in a WSGI entry point means a server whose environment lost the variable
serves tracebacks with `ALLOWED_HOSTS = ['*']`. **Failing to start is the better
outcome**, and every launch path sets the variable.

**`collectstatic` at image build, not container start.** ~2s for 1122 files. The
image is self-contained and the manifest cannot drift from the code it was built
from. **CI gets it free**: `docker compose build web` builds the `dev` target,
`dev` is `FROM prod`, so the layer runs — verified by finding
`staticfiles.json` in the dev image. **The dev *container* shows none of it**,
because the `.:/app` bind mount shadows the directory; harmless, since
`runserver` serves from source.

**Built CSS stays committed, and CI will verify it is reproducible.** Brian's
call, and it is recorded as task 10's obligation: after the rebuild works, CI
runs the build and fails on a diff. Ordering trap noted there — added before the
toolchain works, it turns every run red.

**`SecurityMiddleware` added, redirect and HSTS deferred.** It has existed since
**Django 1.8** — jaguar's own version — and was never added; `check --deploy`,
which shipped in the same release, is what reports it. Adding it alone supplies
`X-Content-Type-Options`, `Referrer-Policy` and `Cross-Origin-Opener-Policy`
from their defaults. **`W001` is gone; `W004` (HSTS) and `W008` (SSL redirect)
are the two that remain and are task 03's acceptance criteria.** A test asserts
both settings are still off, so turning them on is a deliberate edit.

**Maintenance mode is not rebuilt in `wsgi.py`.** The `OFFLINE` flag worked
because mod_wsgi reloaded on mtime; gunicorn imports once per worker. It also
only answers while the application is up, which is not the case it is wanted
for. **Cloudflare is primary** (a Snippet returns 503 without contacting the
origin, and allows an IP bypass — watch the Workers free tier, 100k/day against
a measured ~90.8k/day, so bind the route only while it is on), **Apache in task
03's stack is the backstop**, and jaguar's own copy of the script is the cutover
write-freeze, now runbook **C0**.

### `STATIC_ROOT`, and a stray directory it explains

Moved out of `base.py` to `test.py`, where the name `/tmp/test_static_root`
always said it belonged. **`base.py` now defines no `STATIC_ROOT`**, as it
defines no `DATABASES` and no `LOGGING`. Consequence, and the point of doing it:
`collectstatic` under dev settings now raises `ImproperlyConfigured` instead of
writing to `/tmp` — **and can no longer create a stray `static_root/` on the Mac
through the bind mount**, which is how it appeared twice while this task ran.
`.gitignore`'s `static_serve` was jaguar's name for that directory and is
repointed.

### Two corrections earned while tracing broken images

Brian asked why some images 404 on a forum topic page. **Every one of the 35
`/static/` URLs on that page returns 200**; every 404 is `/media/`.

**1. Badges are media, not static, and the broken ones are not the ones they
looked like.** `bio/models.py:43` is `ImageField(upload_to='badges')`. Of 13
`Badge` rows, 10 files are present and serve 200 — **including News
(`newspaper.png`) and Calendar (`date.png`)**. The three that 404 are **Map,
Brave New Surf and Wiki** (`map.png`, `bns_badge.png`, `script.png`), which were
never committed. `script.png` is a document icon, which is probably why it read
as "news".

**2. `media/` is half committed assets and half user uploads**, and
`.gitignore` hides that: it lists `media/badges` and `media/smiley`, but **an
ignore entry does not apply to already-tracked files** and 98 of them are
tracked — 10 badges, 87 smileys, 1 podcast file. So neither `--exclude=media`
nor a wholesale `rsync` of `media/` is correct at cutover. Recorded as runbook
**B4**, with the three missing badge files as a gap to close there.

**A measurement error of my own, corrected in the same breath.** I first reported
`media/smiley` as 87 tracked against 1 on disk and called it a broken checkout.
It is 87 against 87, `git status` clean. I had counted on-disk with `ls` — which
saw one entry, the `images/` subdirectory — and tracked with `git ls-files`,
which is recursive, then compared the two as though they measured the same thing.
The same flaw produced a bogus `potd` row. **Comparing two counts requires that
both counted the same thing** — see [[probes-must-not-perturb-what-they-measure]]
for the neighbouring failure.

### Verified by running the image, not by reading it

- prod image: `gunicorn 26.2.0`, `2*CPU+1` workers (21 booted on a 10-CPU host),
  sized at start so the VM's count governs rather than the build machine's
- hashed asset → `Cache-Control: max-age=315360000, public, immutable`
- unhashed name → `max-age=60, public`
- rendered page references `css/v3/main.min.04783fc9afb1.css`, from the manifest
- missing asset → 404; home page → 200 with all three security headers
- **pins checked against PyPI rather than recalled**: my first draft wrote
  `gunicorn==23.0.0` and `whitenoise==6.11.0`; current are **26.2.0** and
  **6.12.0**, and this project aligns to the current line

Five tests cover the production wiring, each watched to fail — WhiteNoise moved
last, `SecurityMiddleware` removed, `STATIC_ROOT` reverted, the proxy header
dropped, HSTS switched on — with both settings modules byte-identical after each.

## Step 20 task 01 — one settings module per deployment — DONE 2026-09-17, `0764b87a` + `3d82ab26` + `20188f2a` + `9dfda6dc` + `f5657698`, PUSHED, CI GREEN

Four staged commits plus one fix. **Suite 1254 → 1264, the deprecation gate
matching at every stage, checks clean.** The settings package is now one module
per deployment, and the image has a production target that carries no
development tooling.

**The images.** `Dockerfile` splits into `prod` and `dev`, `dev` built `FROM
prod` so the runtime layers are shared. Verified by listing the built images
rather than reading the file: `prod` carries none of `django-debug-toolbar`,
`coverage` or `testfixtures`, and does carry Django 5.2.17, psycopg2 2.9.12 and
celery 5.6.3; `dev` carries the toolbar at 7.1.1. Sizes 2.17 GB and 2.18 GB —
the difference is the three tools, nothing installed twice.

**`requirements-docker.txt` is deleted.** Measured equal to `requirements.txt`
plus `coverage`, `django-debug-toolbar` and `testfixtures`, with **no differing
pins** — exactly `requirements_dev.txt` flattened — so the targets now express
the boundary its contents used to. This retires the hand-mirroring hazard where
a pin added to `requirements.txt` alone rebuilt cleanly and changed nothing.
**Three files, three consumers, and the third is why the duplication existed**:
`main`'s `requirements.txt` is what live production installs from, and `main`
carries no `requirements-docker.txt` at all. **The duplication ends with jaguar,
not here.**

**One thing to carry to task 03: a bare `docker build .` builds the *last*
stage, which is `dev`.** Checked, and it produced an image with the toolbar in
it. `prod` exists only if something names it, so the production compose must set
`target: prod` explicitly or it ships the toolbar and the split buys nothing.

**`local.py` + `docker.py` → `dev.py`.** The shim inherited `local.py` whole and
overrode the database and Redis onto TCP, to keep the bare-metal reproduction
faithful — a reason that expired several steps ago. `manage.py` and
`sg101/celery.py` had defaulted to `local.py`, **whose MySQL DSN named a unix
socket on a box nobody runs**, so the default settings module was one nothing
could use; both now default to `sg101.settings.dev`, verified with
`DJANGO_SETTINGS_MODULE` unset rather than assumed. The toolbar's
`find_spec` guard is gone, the module being dev-only, and `docker.py`'s
`SHOW_TOOLBAR_CALLBACK` folded into the same config.

**`LOGGING` comes from `sg101/settings/logging_config.py`**, shaped like
`databases.py`. `dev.py` 238 → 88 lines, `production.py` 247 → 93, one 186-line
helper replacing ~290 duplicated ones. **The eight differences are four
parameters**, because five of the eight — four handler levels and the `auth`
logger — are the single decision *dev is verbose*, written out five times.
**Gate: each module's `LOGGING` dumped before and after and compared, both
byte-identical.** One apparent difference dissolved on reading: the `file`
handler stays at DEBUG in both targets, since what `sg101.log` collects is
decided by the root logger's level, so its own level is inert in production.

**`production.py` no longer describes jaguar.** `from_env('postgresql')` for the
database, the cache `LOCATION` on `redis://host:port/2`, and `STATIC_ROOT` off
the `static_serve` path. None of `/var/run/mysqld`, `unix://`,
`REDIS_UNIX_SOCKET` or `static_serve` appears in the module. `STATIC_ROOT` is a
container path and **deliberately provisional** — where `collectstatic` writes,
and whether anything serves it from disk, belongs to task 02.

### What this cost in wrong claims, which is the part worth keeping

**Three, and only one was caught by reading.**

**1. The toolbar's middleware position, inherited from `plan.md`.** Covered in
its own section above: the task file said "after `CommonMiddleware`", which is
the position Step 14 task 04 measured and abandoned, and acceptance criterion 7
would have certified the regression.

**2. "No view — and no database — is reached."** Asserted in a test docstring
*and* in `3d82ab26`'s commit message, about the `/forums` → 301 check. **CI
failed on it** — `relation "django_site" does not exist`, three failures. It
passed locally because this dev database has the production snapshot loaded and
CI's is empty. Both halves were wrong: Django issues the `APPEND_SLASH` redirect
from `process_response` once the response is already a 404, so the request
traverses the whole chain, and `FlatpageFallbackMiddleware` — last in
`MIDDLEWARE`, therefore first to see the response — queries `django_site`
looking for a flatpage. **The probe that "confirmed" it could not distinguish
the two cases, and the conclusion was recorded anyway.**

The observable was replaced rather than repaired. The test now builds a
`DebugToolbar` against a bare `HttpRequest` and reads which panels come out
**enabled**, which is the state that governs the behaviour: `DISABLE_PANELS`
does not remove a panel from the list, it decides which are consulted, and only
an enabled panel intercepts. Proved hermetic by pointing the subprocess at an
unresolvable `DB_HOST` — the old check dies, the replacement answers.

**A subprocess test inherits the developer's database.** That is the general
lesson: several tests here load a deployment module in a subprocess, and they
are safe only because they read configuration. Anything that issues a *request*
from one is testing against whatever happens to be in the local `sg101`.

**3. What the mutation battery covers.** Written into a docstring from
reasoning, then contradicted by running it. Moving the toolbar to index 1 fails
the middleware assertion **alone** — the redirect still answers 301 from index 1
— so the observable never covered the position. And a **misspelled
`DISABLE_PANELS` key does not re-enable `RedirectsPanel`**, because the toolbar's
own defaults already disable it; what the typo loses is `ProfilingPanel`. The
typo is invisible from `RedirectsPanel`'s side, and only the `ProfilingPanel`
assertion catches it — the *"an empty `DISABLE_PANELS` means turn both on"*
finding running in reverse.

### Found by running `check --deploy`, and left as a decision

**`SecurityMiddleware` is not in this project at all**, and **no `SECURE_*`
setting is defined anywhere** — `security.W001`, against `base.py:112` starting
`MIDDLEWARE` with `CommonMiddleware`. **Task 02's requirement 4 says to place
WhiteNoise "immediately after `SecurityMiddleware`, which is where it must
sit"**, so that instruction cannot be followed as written — the same class of
defect as the `sg101.wsgi` that did not exist, and the second in that file that
reading alone did not catch.

**Not fixed here, on purpose.** Adding it is what makes `SECURE_SSL_REDIRECT`
and `SECURE_HSTS_SECONDS` do anything, and **HSTS is hard to walk back once
browsers have cached it**; it also interacts with Cloudflare already terminating
TLS. Recorded in task 02 as its own decision with its own values, with the note
that a new first middleware changes the `MIDDLEWARE[0]` assertion the toolbar
tests now make.

### Still open, and task 03 owns it — reassigned 2026-09-18

**Closed by task 03, 2026-09-19** — see its section above.

**`production.py` is not deployable yet.** It never overrides
`CELERY_BROKER_URL`, so it inherits `base.py:283`'s
`redis+socket:///var/run/redis/redis.sock` — jaguar's path. **It also never nulls
`REDIS_UNIX_SOCKET` (`base.py:274`)**, and `core/services.py` takes the socket
branch whenever that setting is truthy, so db 0 — who's-online, written by the
`WhosOnline` middleware on any request that lacks its online cookie, and the forums' latest-post lists — is
on jaguar's socket too. The 2026-09-17 reading caught the broker and missed this
half; found 2026-09-18 while untangling the task order.

**Tasks 03 and 05 each listed the other as a dependency.** Brian's call, 2026-09-18:
**03 first.** Both socket overrides move into task 03 as requirement 10, since its
criterion 1 cannot pass without them; task 05 keeps the memory policy, the
`base.py` default inversion and the dead branch in `core/services.py`. Both task
files carry an amendment record.

**Ten new tests**, every one mutation-verified with the mutated file restored
byte-identical after each: four on the toolbar's wiring, four on what the two
deployments' logging may disagree about, two on which database and cache the
deployed modules name. The logging cases read each module's **own** `LOGGING`,
so a deployment module that quietly stopped using the shared helper fails seven
of them — verified by making it stop.

## PLANNING — Step 20: nine task files, and the proxy decision that was wrong twice (2026-09-12)

Step 19 closed 2026-09-09, making Step 20 the active step. Nine task files
generated in `.agents/tasks/2026-07-04-modernizing-sg101/step20/`, covering the
plan's own scope plus the items other steps hung on it: the real-client-IP
rewrite, origin exposure, the two indexes deferred out of Step 12, and two carried
items filed under Step 21 in `plan.md` that are hardening rather than cutover —
the dev/prod settings split (carried 2026-08-07) and Redis's memory policy
(carried 2026-08-05).

### The proxy choice was never made, and then it was made wrong

**`research/docker-strategy.md` still lists it as open:** *"Decide gunicorn+nginx/
Caddy vs. WhiteNoise-only."* The design says `Caddy/nginx or platform router`, and
`plan.md` states the real-IP requirement proxy-agnostically, naming
`ngx_http_realip_module` only as an example of satisfying it. **nginx propagated
into `STATUS.md` and `plan.md`'s Step 21 ordering note as though it were the
decision.** It was not.

**Decided 2026-09-12: Apache.** The deciding argument is that a verified working
configuration already exists for exactly the load-bearing item — jaguar's
`conf-enabled/remoteip.conf`, checked against Cloudflare's published list
2026-08-21 with no drift — and that fail2ban's jail filters are log-format
specific. Operator familiarity is the tiebreaker and is a legitimate one for a
single-admin site.

**Then decided wrong, and corrected the same day.** The first draft put Apache on
the host. That breaks the project's own sequencing — *"do everything locally,
deploy once at the end"* — because **no VM is provisioned**, so the step would not
have been exercisable at all. It also repeats the jaguar complaint: config that
does not travel with the code. **Apache is a service in the production compose
stack.** The argument for a host daemon — several sites sharing a box — does not
apply, because the decommission project is capturing the other sites as static
mirrors bound for Cloudflare Pages, leaving this VM single-purpose.

**The fail2ban justification for a host daemon was also weak.** It bans by pushing
addresses into a Cloudflare IP list that a WAF rule drops at the edge — an API
call, not local packet filtering. It needs to read an access log, which a bind
mount provides.

### The request rate, measured — 2026-09-12

Taken because "are there performance concerns with Apache in Docker" deserved a
number rather than an opinion. From `/svr/www/surfguitar101.com/log/access.log` on
jaguar, **572,177 requests over 6.3 days**, 2026-09-06 06:48 → 2026-09-12 14:09
local:

| | Rate |
|---|---|
| Average | **~1.05 req/s** |
| Busiest hour (09-10 17:00) | 5,062 req/hr — **~1.4 req/s** |
| Busiest minute (09-08 13:18) | 506 req/min — **~8.4 req/s** |

Bridge-network NAT costs tens of microseconds per packet, so at these rates
containerization is immaterial. **Apache will also do less work than it does
today**, since it currently runs `mod_wsgi` with Python embedded in its workers
and becomes a pure reverse proxy.

**Three consequences worth acting on, none about CPU:** bind-mount I/O is slow
under Docker Desktop on macOS and native on the Linux VM, so a sluggish local
`/media` test is not a production signal; the access log should be bind-mounted
rather than sent to the json-file driver, which also gives fail2ban the path it
needs; and `EnableSendfile` should be set explicitly rather than inherited, given
the overlay filesystem underneath.

**This measurement has a shelf life.** It comes from jaguar's Apache log, which
rotates, and the send-side baseline dies with the host. Anything to be compared
against it must be captured before the decommission.

### Three things that need the VM, and therefore are not in Step 20

Task 07 authors the origin firewall ruleset but cannot apply it, and task 04's
Cloudflare Origin CA certificate cannot be installed. Both are now entries **B6
and B5** in `cutover-runbook.md`. Task 07's rules will reach cutover day
**unexercised**, and its task file says so in as many words.

**The backup storage provider is the third, and it is deferred on purpose rather
than for lack of a VM.** Nothing in task 06's path needs it: endpoint, bucket and
credentials are configuration, in the pattern `base.py:350-352` already uses, and
the task builds and drills the whole path against a local S3-compatible endpoint.
**What is decided now is the constraint, because that is the part that gets lost:**

> The backup target must not share a provider or account with the VM.

A Linode VM backed up to Linode Object Storage shares a failure domain. `bobcat` is
already a second Linode and its rsync is repointed at the new VM, so that is the
warm same-provider copy; the object storage copy has to be elsewhere. Against a
Linode VM, an AWS S3 bucket satisfies it, and `boto3` and credentials are already
here from Step 15 — **a new bucket, not the media buckets, on a write-scoped
credential with deletion left to a lifecycle policy.** Recorded as
`cutover-runbook.md` **B7**.

**The general shape is worth naming, since it recurs across these nine tasks:**
separate the constraint from the choice. Write down the property that must hold,
defer the selection to where the information is, and the selection cannot quietly
violate the property.

## Step 20 — the task files audited against the plan before task 01 ran (2026-09-17)

The nine task files were generated 2026-09-12 from the step's scope. Read back
against `plan.md`'s own Step 20 section before starting task 01, **four of them
were wrong or incomplete, and the count of tasks was wrong.** Corrected in place,
each amended file carrying its own amendment record.

**Five defects and one missing task, and the two worst were inherited from
`plan.md` rather than invented.** A task generator is only as good as the section
it reads, and nothing had been diffing that section against the files it produced.

**What the generation pass missed, and it is one pattern:** `plan.md`'s Step 20
section is long and carries items added to it over five weeks —
`plan.md`'s "four things to settle together" (2026-09-08), the Sass toolchain
(2026-08-13), the real-client-IP rewrite (2026-08-21). **The nine files covered
the step's headline scope and dropped the items appended to it later.** A task
generator reads the section; nobody diffed the section against the files it
produced.

| Defect | File | Correction |
|---|---|---|
| `prod` target told to install `requirements.txt` | task 01 | `Dockerfile:65-66` installs `requirements-docker.txt`; the three files and their three consumers are now a table in the task |
| The settings consolidation was absent | task 01 | The `local.py`/`docker.py` merge, the `manage.py:5` / `celery.py:11` defaults, the `LOGGING` extraction and the `production.py` rewrite are now requirements 3-7 |
| gunicorn told to serve `sg101.wsgi` | task 02 | **That module does not exist.** Creating it is now requirement 1 |
| Maintenance mode was about to be deleted in silence | task 02 | The `OFFLINE` flag and `offline.html` live only in the mod_wsgi script; a replacement is now an explicit decision |
| The two socket consequences had no home | task 05 | `base.py:264`'s default inversion and `core/services.py:26`'s dead branch are now requirements 5-6 |
| The Sass toolchain had no task file at all | **task 10, new** | `plan.md` has carried it here since 2026-08-13 |
| The toolbar's middleware position was **backwards** | task 01 | It is **index 0**; the file named the position Step 14 task 04 replaced |

### The one that would have done real damage: the toolbar's position, recorded backwards

Task 01's background said *"It sits after `CommonMiddleware`, that placement was
measured"*, and requirement 7 and acceptance criterion 7 both said to preserve it
there. **That is the position Step 14 task 04 measured and abandoned on
2026-08-15.** `local.py:55` prepends the middleware, so the toolbar is at **index
0**; `DISABLE_PANELS` is `{RedirectsPanel}`, not the empty set the old reasoning
depended on.

Implementing the requirement as written would have moved the toolbar back to
index 1, reintroducing the `APPEND_SLASH` interstitial Brian's call removed — and
**acceptance criterion 7 would have certified it as correct.** A task file that
encodes a stale claim as an acceptance criterion converts documentation drift into
a verified regression, which is the failure mode worth naming out of this audit.

**Where it came from, and both sources are now fixed.** `plan.md`'s Step 20
detail still carried the pre-move paragraph (including *"`RedirectsPanel`, which
is live because `DISABLE_PANELS` is empty"*), and its Step 21 carried-item line
repeated the claim in one clause. The task generator read `plan.md` faithfully;
the plan was wrong. **The measurement had been recorded correctly all along** — in
`STATUS-archive-steps-01-15.md`, with the three-row table and its control — which
is the argument for the 2026-08-26 split doing its job: the closed-step record
kept the evidence while the forward-looking plan drifted.

**The criterion now asserts the observable**, `/forums` answering 301 rather than
a 200 interstitial, instead of a list index alone. An index is a spelling; the
redirect is the reason.

### The one that would have cost the most time: `sg101/wsgi.py` does not exist

Task 02 said gunicorn would serve `sg101.wsgi`. There is no such module —
`runserver` builds its own handler, so nothing has ever needed one. The only WSGI
file in the tree is **`sg101/apache/sg101.wsgi`**, jaguar's mod_wsgi script, which
`site.addsitedir`s a **Python 2.7** site-packages path and hardcodes
`DJANGO_SETTINGS_MODULE = 'sg101.settings.production'`.

**And that script is the only home of a feature nothing else provides.** An
`OFFLINE = False` flag at its top switches the site to an `offline_handler`
serving `sg101/templates/offline.html` with `503` (and `405` on non-GET) —
maintenance mode, toggled by editing the file, which is what `fabfile.py:33`'s
touch reloads. The template is still in the tree. Deleting the script as a
Python 2 artifact takes maintenance mode with it, and **the day it is most likely
to be wanted is cutover day.**

### `requirements.txt` is not a vestigial twin — Brian, 2026-09-17

Worth recording because the first correction I drafted implied it was. **`main`'s
`requirements.txt` is what live production installs from today** — Django 1.8.15,
MySQL-python, the Xapian eggs — and `main` has no `requirements-docker.txt` at
all. So on this branch there are three files with three consumers: the image and
CI read `requirements-docker.txt`, `requirements_dev.txt` reaches
`requirements.txt` through `-r`, and jaguar reads `main`'s copy. **The duplication
ends with jaguar, not with this step** — collapsing the two is not Step 20's.

### The static-assets decision now has exactly one owner

`plan.md` says the committed-CSS-vs-deploy-build question is *"one decision about
static assets, not two"*, interacting with WhiteNoise, `collectstatic` and
`ManifestStaticFilesStorage`. **Task 02 decides it; task 10 implements it.** Task
10 says so in as many words, so the decision cannot be made twice and differently
— which is the failure this project has already had once, with the proxy choice
that "was never made, and then was made wrong."

**Step 20 is ten tasks, not nine.** Every prose reference to "these nine tasks"
above this line predates 2026-09-17 and is left as written rather than
back-edited; this section is the correction.

## PLANNING — Step 12 (PostgreSQL full-text search) — DESIGNED 2026-07-26

Requirements clarification only; nothing built. Q&A in `step12-idea-honing.md`
(Q1–Q11), design in `research/search-design.md`, and the Step 12 section of
`implementation/plan.md` rewritten to match — its earlier sketch said a
`SearchVectorField` per model, which the design supersedes.

**Process note: this ran as idea-honing only, not a full `/pdd`.** A complete PDD
pass would have produced a second `detailed-design.md` and a second `plan.md`
restating what the parent project already holds — the exact duplication that
caused the `db22869` drift. So the Q&A ran, and its output folded into the
existing `research/` and `plan.md`. Roughly 60% of PDD's value at 20% of its
artifact weight.

**The Q&A earned its keep by finding things nobody remembered.** Step 4 deleted
the Xapian stack but left its templates, and `pre-step-4-prune` still has the
code, so prior behavior was *recovered* rather than guessed:

- **The old search sorted newest-first, not by relevance** — the tips block says
  so and `SearchQuerySet().order_by('-pub_date')` confirms it — despite the
  template rendering a score. Relevance ranking is therefore a change, not a
  restoration, and had to be chosen deliberately.
- **The three-box form was always a UI over websearch syntax.** `forms.py`
  synthesized `terms "exact phrase" -excluded` and handed Xapian one string.
  Collapsing to a single `websearch` box changes the interface, not the query
  language.
- **Search was login-gated**, and the reason is in the source: bots were hammering
  it, with a contemporaneous comment about someone probing for SQL injection. An
  earlier draft of the Q&A recorded search as public — **Brian corrected it**.
- **Query logging already exists** and Brian wants it kept — one `INFO` line per
  search with terms, models, username and IP. Recorded first as a deferred *new
  feature*, which was wrong twice over: it exists, and it makes Q6's deferred
  "did you mean" decidable on evidence later.
- **`Kahunas`** — one private category, 487 topics and 19,088 posts — turned an
  abstract permissions question into a concrete one.
- **10,987 comments, 72% of them Photo-of-the-Day chatter**, settled the
  comments-in-search question on data.
- **`bigtikidude`'s 25,768 posts** set the upper bound on the author-rename
  fan-out, which is what made the indexing strategy a real question.

**Brian changed two of my recommendations, both correctly.** He asked whether
Celery should own *all* index updates rather than the sync/async split I had
proposed; it should — the deciding argument is failure isolation, not
performance, since inline indexing couples a vector-building bug to posting
itself. And he supplied the login-gate and query-logging facts above. A third
suggestion of mine — adding a masthead search box — turned out to be proposing
something `v3/base.html:49` has had all along.

**Decisions:** relevance-ranked with newest tiebreak; single websearch box with
the type checkboxes kept; all 8 documents including profiles at full parity;
private categories never indexed; every write via Celery on
`transaction.on_commit`; no typo tolerance yet; quick search restored;
`normalization=1` plus `setweight` A/B/C; comments out; login gate only; query
logging kept in a dedicated `search.log`.

**Architecture:** one denormalized search table, one weighted `tsvector`, one GIN
index, `ORDER BY rank, -date`, ~490k rows. Forced by relevance ordering plus
pagination across eight document types.

**Eight code-task files generated 2026-07-27** at
`.agents/tasks/2026-07-04-modernizing-sg101/step12/`: 01 search app +
`SearchDocument` + document registry, 02 reindex command + ~490k backfill, 03
Celery incremental indexing + private-category exclusion, 04 view/form/templates
+ ranking + `search.log`, 05 forums quick search, 06 the `ajax_users` ordering
fold-in, 07 verification against production data, 08 weekly reconcile sweep. Task
02 runs before 03 deliberately — a populated index exercises all eight registry
entries against real data and gives tasks 04/07 something to develop against.

**Second design revision (2026-07-27): the weekly reconcile sweep is taken after
all** — the design had offered and declined it. Brian asked what one would cost,
noting that manual reindexing was what Haystack/Xapian required anyway. The
decisive question was **whether a reconcile has to reindex everything: it does
not.** Comparing sets and timestamps in SQL computes no vectors, so **cost tracks
the drift found, not the corpus** — measured, scanning `id, update_date` across
all 463,222 forum posts (94% of the corpus, 417 MB table) takes **170 ms**, and
the full eight-type sweep should be low single-digit seconds. Two enabling facts
that weren't in view when it was first declined: **seven of eight documents carry
a `db_index=True` `update_date`** (so *stale* is detectable, not just *missing*;
the eighth, `ygroup.Post`, is a frozen archive needing none), and **nothing in
the codebase bulk-updates an indexed model** (no `.update()`/`bulk_create`/
`bulk_update` across the seven apps — the one `.update()` hit is `ForumLastVisit`,
unindexed), so signals really do see every application write. **Built as
reporting only, repairing nothing** — task 03's indexing is supposed to make
drift impossible and the sweep tests that claim rather than masking it; it also
reports private-category rows separately, those being a privacy defect rather
than staleness. **Consequence: `indexed_at` lands on `SearchDocument` in task 01**
(adding it later = migration + 490k-row backfill). Also noted for task 03:
registering a `post_delete` receiver on `forums.Post` disables Django's
fast-delete path, so bulk deletes get slower but correct.

**Design revised during task generation (2026-07-27): the author-rename fan-out
is gone.** Brian had second thoughts on it, which prompted checking what can
actually trigger a rename — and the answer reframed the problem. **`username` is
immutable**: written once at activation (`accounts/utils.py:20`), no form edits
it, only an admin can change one. **`first_name`/`last_name` are the only
user-editable author text**, via `bio.EditUserForm`. So the entire 25,768-row
cascade traced to one pair of form fields — and it was reachable by an ordinary
user editing their own profile, which meant "notice the rename, run the reindex
command" had nothing to notice with. Measured: **2,937 of 15,227 members (19%)
have a full name at all**; `bigtikidude` has both a full name and those 25,768
posts. **Decision: full names are indexed only on the `bio.UserProfile`
document**, where a rename rebuilds one row; content documents keep `username` at
weight C. No fan-out task, no batching trigger, no test surface for it. This is a
*narrower* cut than the all-or-nothing alternative Q5 rejected — find-a-member-
by-real-name still works through profiles; find-posts-by-real-name does not.
Recorded in the Q5 addendum, `search-design.md` §3, and `plan.md`.

## EXECUTION — Step 12 (PostgreSQL full-text search) — **COMPLETE 2026-08-02**

All nine tasks done. `/search/` is restored on native PostgreSQL full-text
search, with no Haystack, no Xapian and no third-party search package: an eight
type index of 516,858 documents, incremental maintenance from signals through
Celery, a weekly sweep that reports drift, the forums' duplicate-topic quick
search, and per-type result counts. 798 tests green.

**Deferred out of Step 12, each with its measurement attached:** the
Misirlou/Miserlou spelling split, needing a synonym dictionary or `pg_trgm`
(Step 20); and a `UPPER(username)` functional index for the member autocomplete,
2.7 ms → 0.48 ms (Step 20).

### The end-of-Step-12 prune — DONE (2026-08-02)

798 tests green (unchanged — nothing in the suite referenced any of it), `check`
and `makemigrations --check` clean.

**The 14 dead `search_title` / `search_summary` methods**, across `forums.Topic`,
`forums.Post`, `news.Story`, `ygroup.Post`, `downloads.Download`,
`weblinks.Link`, `podcast.Item` and `bio.UserProfile`. Two survive, for reasons
that are not symmetrical: `bio.UserProfile.search_title()` is genuinely search
code, called by `search/documents.py` because on a profile the author *is* the
document, so username and full name both belong at weight A. `podcast.Item.
search_title()` is not — `podcast/detail.html` hands it to social sharing, and
it now carries a comment saying so, because after this prune the name is the
only thing suggesting otherwise.

**`bio`'s `profile_content_update` signal and its two senders**
(`UserProfile.save()` and the link-delete branch of `edit_elsewhere`), dead since
Step 4 removed `custom_search`. `bio/signals.py` held nothing else and is
deleted. The profile document does not depend on it: `search/receivers.py`
already connects `post_save` on `User` and `UserProfile`, and both `post_save`
and `post_delete` on `elsewhere.WebsiteProfile` — which is exactly the path the
removed call sat beside in that view. Removing the sender from
`edit_elsewhere` also stranded its `update_occurred` flag, whose `else` branch
was unreachable anyway (the guard tests the same three POST keys the body does),
so both went with it.

Two follow-on edits the prune forced, each a comment that had come to name
something no longer in the tree: `search/receivers.py`'s docstring listed
`profile_content_update` among the signals the old stack listened to, and two
`search/documents.py` comments cited `search_summary()` as the thing that *left
a field out* — provenance for indexing `tags` on news and `url` on weblinks. The
distinction those comments draw is still real, so they now name the old stack's
template and the model method beside it rather than a method by name.

**Not pruned:** `forums`' `topic_content_update` / `post_content_update`.
`forums/latest.py` still receives both for the RSS latest-posts datastore.

**Also pruned, on Brian's call:** `sg101/templates/search/indexes/`, the eight
Haystack-era `*_text.txt` templates. The last Python reference to any of them
went with `bio.UserProfile.search_summary()`. The reason to hesitate was that
`search/documents.py` cited the directory as the recorded provenance of the
field choices, and two field-level comments lean on it — but **the tag holds
them**: `pre-step-4-prune` has all eight templates *and* the seven
`search_indexes.py` classes that rendered them, so the pointer now names the tag
and a reader following it gets strictly more than the orphaned directory offered.
Worth noting that this tag is a full-repo snapshot, not the templates-only tree
it can appear to be — `git ls-tree` scopes to the shell's current directory, so
running it from inside a subdirectory silently answers a narrower question.

**Next: Step 13 task 04** — the Django 4.1 rung.

## PLANNING — Step 18: the sync died in 2021, and the Step 8 stub is not why (2026-08-31)

**`plan.md`'s framing was wrong, and the correction came from Brian.** The step
reads "resolve the Step 8 `gcalendar` stub", which implies the Python 3 flip is
what took the calendar out. It is not. **Google deprecated the client library
gcalendar used; upgrading was impossible because the site was pinned to Python
2.7 behind a wall of dependencies** (Brian, 2026-08-31). The stub, added
2026-07-19, disabled a code path that had already been dead for five years.

That reverses the relationship between this step and the ladder below it.
Step 18 is not repairing damage Step 8 did — **Steps 8 and 13 removed the thing
that made this unfixable**, and that is why the step is reachable at all.

### The sync has been dead since 2020 — measured against the database, 2026-08-31

`gcalendar_event`, 1,510 rows:

| | |
|---|---|
| Events on the Google calendar (`status=ON_CAL`) | **1,478** |
| Last one to reach Google | submitted **2020-03-03** |
| Stranded (`NEW` or `NEW_APRV`) | **32** |
| Last submission of any kind | **2023-01-12** |

Stranded by year of submission: **2021 → 16, 2022 → 12, 2023 → 4.** Nothing
submitted after 2020-03-03 ever reached the calendar.

**Three of the 32 sit in `NEW_APRV`, all approved on 2021-02-22.** That is the
load-bearing row in this table: someone approved them by hand and Google never
got them. It is the difference between a feature nobody used and a feature that
was tried and failed. The other 29 are in `NEW` — never approved — which reads
as the natural consequence of learning that approving does nothing.

**8 of the 29 carry `create_forum_thread`.** None of the 32 are all-day events.

### The credentials file dates the last attempt — from jaguar, 2026-08-31

```
/home/brian/google/gcal.dat      mtime 2021-10-17   1146 bytes
/home/brian/google/myrsakey.pem  Apr 2013            887 bytes
```

`gcal.dat` was last written **2021-10-17 — eight months after the three
stranded approvals.** So the credentials were successfully refreshed or
re-authorized *after* the failure, and events still did not sync. This is
independent corroboration of the library-deprecation cause and it rules out
"the token went stale", which is what an mtime this old would otherwise suggest.

`myrsakey.pem` (2013) and the single `gcalendar_accesstoken` row (`auth_date`
**2011-07-01**) are two earlier auth generations, both dead.

### Two corrections, both mine, both from guessing at a cause

1. **I proposed token expiry as the likely 2021 failure** and used it to argue
   for a service account. Brian supplied the actual cause. The service-account
   case had to be re-argued on simplification grounds alone, which is where it
   now rests — it does not get to claim it prevents what broke this.
2. **I twice wrote that the two-step approve-then-sync workflow stranded the
   three events**, and recommended moving the push onto Celery to close the gap.
   The deprecation stranded them: they were approved, sync was pressed, it
   failed. **The recommendation was withdrawn**, and the manual button stays.

Both are the same error — reading a cause off a shape in the data instead of
measuring it — and in both cases the correction came from the person who was
there. See `suspect-the-measurer-before-the-record`.

### The public calendar never used the API

`sg101/templates/gcalendar/index.html:44` is an `<iframe>` to
`google.com/calendar/embed` aggregating two calendar IDs, one of them not
SG101's. It needs no credentials and has kept working throughout. **Everything
Step 18 restores is the member submission → admin approval → push pipeline**,
which is invisible to logged-out visitors. This bounds the step: no public page
changes.

### DECIDED 2026-08-31 — service account, not OAuth user consent

Brian's call, after an explanation of the two models: *"a service account makes
the most sense now and will be less to maintain."*

The current design has the app act **as Brian's Google account**, with all the
machinery that consent requires. A service account is **its own identity**, and
the calendar is shared with its address the way it would be shared with a
person. What that deletes:

| | OAuth | Service account |
|---|---|---|
| `gcalendar/oauth.py` (147 lines) | rewritten | ~5 lines, folds into `calendar.py` |
| `EventAdmin.authorize` / `auth_return` + 2 admin URLs | stay | delete |
| Redis flow cache (`FLOW_CACHE_KEY`, 60s window) | stays | deletes |
| Authorize button + credentials-status block in `google_sync.html` | stay | delete |
| `GCAL_CLIENT_ID`, `GCAL_CLIENT_SECRET` | stay | retire |
| `check_credentials_status()` | stays, and *means* something | deletes — nothing expires, so an mtime stops being a health signal |

`calendar.py` sheds the `httplib2.Http()` + `credentials.authorize(http)` dance
under either option; the modern library takes credentials directly.

**The argument that carried it is not failure-mode, it is surface.** ~150 lines
stop existing, nobody ever re-authorizes, and there is no OAuth consent screen —
which matters because an External app in *Testing* status on the calendar scope
gets refresh tokens that expire in **7 days**, and *In production* on a sensitive
scope can require verification. None of that machinery existed in 2011 when this
was written. A service account does not touch it.

### The console checks — Brian, 2026-08-31

| Check | Result |
|---|---|
| Project `786263548002` (from the client ID in `.env`) | **alive** |
| The 2011 OAuth client | present, **warned as unused and subject to deletion** |
| Calendar API enabled | **yes** |
| Owner of `i81lu3fkh57sgqqenogefd9v78@group.calendar.google.com` | **Brian** |

The last row is the one the decision needed: sharing the calendar with a service
account requires owning it.

**A calibration recorded because I overstated it first:** I predicted the OAuth
client would likely be purged and said that would remove OAuth's "already
configured" advantage *entirely*. What Brian found is milder — the client exists
and carries a dormancy warning that using it again would clear. It is not a
strike against OAuth; it is a statement about how long nothing here has run.

### DECIDED 2026-08-31 — the manual sync button stays; no Celery

Considered and rejected: queueing the push from the admin approve action on
`transaction.on_commit`, the way Step 12 routes every search index write.

Rejected on two grounds, after the evidence for it collapsed (see corrections):

- **Volume does not justify a queue.** The busiest year on record is 302
  submissions (2011); the last three years total 32, and the last one arrived in
  January 2023.
- **The button gives synchronous errors.** `google_sync` renders `err_msg` into
  the page at the moment it is pressed. A Celery task writes to the worker log.
  For a feature that has just spent six years failing silently, the version that
  reports into the browser is the safer one.

### DECIDED 2026-08-31 — the stranded events are deleted by hand, not migrated

Brian's call: the 32 will not be published, and he will delete the `NEW` ones
**from the Django admin**. No data migration, no task file.

**This is the better shape, and a hazard was avoided by taking it.** A migration
keyed on `status=NEW` would also delete any genuinely new submission arriving
between merge and production deploy — `NEW` is exactly the state a fresh
submission occupies. That is the same class of problem as the PayPal
`payment_date` backfill's "what does it key on" question in Step 19. Selecting
rows by hand has no cutoff to get wrong.

Safe to do at any time: **nothing has a foreign key to `gcalendar_event`**
(checked against `pg_constraint`), and none of the 32 ever reached Google, so no
Google-side event is orphaned by the deletion.

**Settled 2026-08-31: all 32 go, `NEW` and `NEW_APRV` alike** — Brian's call
after the `NEW_APRV` three were raised separately. He deletes them **in
production as well as locally**, which is the part that matters beyond tidiness:
Step 21 converts a *fresh* production snapshot, so rows deleted only in the dev
database would return with it and land in the pending queue on the new host.

### The app has no tests, and Step 18 is where it gets some

There is no test module anywhere under `gcalendar/`. Reported coverage is
entirely incidental — other apps' tests importing the URLconf and the admin:

| | line rate |
|---|---|
| `calendar.py` | **22%** |
| `oauth.py` | 33% (deleted by this step) |
| `views.py` | 30% |
| `forms.py` | 34% |
| `models.py` | 71% |

`Calendar._make_time()` — the UTC conversion that decides what time an event
appears at — has no coverage at all, and it was rewritten from `pytz` to
`zoneinfo` during Step 13 task 09 without a test proving the conversion.

### Two live probes before the sync is trusted

Neither is answerable from the code, and both change what the batch can do:

1. **Does `anyoneCanAddSelf: True` still work** on an event inserted by a service
   account? `calendar.py:120` sets it on every event body. It is a guest-list
   feature, and service accounts have had limits there without domain-wide
   delegation.
2. **Can the service account edit and delete the 1,478 existing events**, which
   were created by Brian's account rather than by it? Sharing with "Make changes
   to events" should grant this, but the update and delete paths are worth
   proving against one real event before the batch is trusted with them.

**Update 2026-09-01: probe 2's *update* half is answered YES** — see *Task 03
probe 2, the update half* below, which holds the evidence. `delete` and probe 1
remain open, and the delete probe has a subject-selection hazard recorded there.

### `gcalendar_accesstoken` → Step 19

One row, `auth_date` 2011-07-01, no model behind it, already listed in
`tools/pgloader/compare_schema.py`'s `LEGACY_TABLES`. It is a pruning job, not a
revival job — recorded against Step 19 with the other verify-then-prune work
rather than widening this step's diff.

### The links were removed in 2023, and the page has been unreachable since

**Brian, 2026-08-31:** when the problem surfaced he removed the calendar links
from the sidebar in both designs. Found and dated: **`7073a406`, 2023-03-19**,
"Remove links to calendar & member map", deleting
`<li><a href="{% url 'gcalendar-index' %}">Calendar</a></li>` from
`sg101/templates/base.html` and `sg101/templates/v3/base.html`.

**The order rules out a story worth not telling.** The last event of any kind was
submitted **2023-01-12** — *two months before* the links came out. The removal
did not cause the collapse in submissions; the sync failure did, and the removal
is what has kept `/calendar/` unreachable from the site since. A write-up saying
members stopped submitting because they could not find the page would have the
sequence backwards.

**Both base templates are live**, so restoration is two edits, not one:

| Template | Templates extending it |
|---|---|
| `sg101/templates/base.html` | **26** — the forums, flatpages |
| `sg101/templates/v3/base.html` | **55** |

**The trap, recorded because it would take the whole site down:** `7073a406`
removed *two* links, the calendar's and the Member Map's. `membermap` was
**pruned in Step 4**, so `membermap-index` no longer exists. Reverting that
commit puts `{% url 'membermap-index' %}` back into both base templates, and
`NoReverseMatch` fires **at render time** — every page that extends either base,
which is every page. The link must be restored by hand, never by revert.

**This became task 04**, gated on task 03: restoring the link before the sync is
proven re-advertises a submission form feeding a queue nobody drains, which is
exactly the state that produced the 32 stranded events.

### Task files — four, generated 2026-08-31

At `.agents/tasks/2026-07-04-modernizing-sg101/step18/`:

| | |
|---|---|
| **01** | the calendar client on a service account — deps, settings, the `calendar.py` port, and the tests `calendar.py` has never had |
| **02** | delete the OAuth surface — `oauth.py`, both admin views and URLs, the template furniture, `GCAL_CLIENT_ID`/`SECRET`, plus the admin's first tests |
| **03** | verify against the real calendar — the two probes, the end-to-end run, and the console setup written down for Step 21 |
| **04** | restore the calendar links to both base templates — added after Brian recalled removing them; gated on 03 |

**01 and 02 are deliberately not merged**, though 01 must touch `admin.py`
anyway. Splitting matches how Step 17 ran — build the new path, then adopt it
and delete the old — and it keeps the deletion diff readable on its own.

**There is no task 04 for tests.** Tests are written inside 01 and 02 under
`/agent-sops:code-assist`, and mutation-verified before each task closes. Task 03
is not a test task: it exists because two questions are unanswerable by any mock,
and a mock would only assert our assumptions back at us.

**Explicit non-goal: the member-facing views.** `views.py` (30%) and `forms.py`
(34%) have no dedicated tests either, but this step does not touch the add / edit
/ delete views. Covering them is real work worth doing and is recorded here
rather than folded in silently.

### A nine-year-old no-op found while reading the template

`sg101/templates/gcalendar/google_sync.html:29` wraps each event in
`{% if not event.on_calendar %}`. **`Event` has no `on_calendar` attribute** —
the model has `status`, `is_approved()` and `google_html()`. Django resolves the
miss to `string_if_invalid` (`''` by default), so the condition is always true
and has never filtered anything.

It is also redundant by construction: the view passes
`Event.pending_events.all()`, and that manager already restricts to the three
approved-and-pending states, so an `ON_CAL` event cannot reach the loop. **Task
02 deletes the condition rather than repairing it** — a working version would
express a second time what the manager already guarantees.

### Task 01 — DONE 2026-09-01: the client runs on a service account

`gcalendar/calendar.py` authenticates as a service account through
`google-auth` and builds its batch from the service. Pins:
**`google-api-python-client==2.200.0`**, **`google-auth==2.57.0`**.
`gcalendar/tests/` exists for the first time — **23 tests**, suite **1,007 →
1,030**, gate green. `oauth.py` still stands; task 02 takes it.

**Two requirements files, and only one of them is installed.** The image and CI
build from **`requirements-docker.txt`**; `requirements.txt` mirrors it for
production. Pinning the packages in `requirements.txt` alone rebuilt cleanly and
changed nothing — `import googleapiclient` still failed. Both files carry the
pins now. The same trap applies to any later dependency in this project.

**The `apiclient` compatibility shim still ships in v2, so installing the
libraries by itself flipped `_GCAL_API_AVAILABLE` to true.** The Step 8 guard
was not inert once its dependencies came back: `from apiclient.discovery import
build` resolves under 2.200.0, and the old constructor would then have built an
**unauthenticated** service instead of raising. The guard was deleted in the
same change that added the pins, so the window never opened, but a task that had
added the dependencies first and ported later would have had one.

### What was measured against the real libraries, not mocked

| | |
|---|---|
| `google-auth` 2.57 requires | **`cryptography`** — not `rsa`/`cachetools`, which 2.x used to pull |
| A generated key loads and **signs** in the image | 256-byte signature |
| `build('calendar','v3')` with outbound sockets blocked | **succeeds** — static discovery, no network at construction |
| `new_batch_http_request()` batch URI | **`https://www.googleapis.com/batch/calendar/v3`** |

The last row is the concrete form of why v2 will not let you construct a
`BatchHttpRequest()` yourself: that bare constructor posted to the global
`/batch` endpoint Google retired in 2019. The third row matters for the admin
page — constructing a `Calendar` cannot hang on a network call.

### `_make_time()` — the baseline was measured before it was tested

Run against the pre-change implementation and encoded into the tests, so they
describe behavior this task did not alter rather than behavior it assumed:

| input | output |
|---|---|
| 2026-07-04 20:30 `US/Pacific` | `2026-07-05T03:30:00Z` (UTC-7) |
| 2026-01-10 20:30 `US/Pacific` | `2026-01-11T04:30:00Z` (UTC-8) |
| 20:30, no zone | `2026-07-04T20:30:00` |
| date only, `US/Pacific` | `2026-07-04T07:00:00Z` |
| `Not/AZone`, `US/Pacific/extra`, `../../etc/passwd` | `CalendarError` |
| **`''`** | `2026-07-04T20:30:00` — **not an error** |

**The blank case corrected a comment that had it backwards.** The `except` clause
said "ValueError covers empty and path-shaped input", but `''` never reaches
`ZoneInfo` — it short-circuits on `if not tz_name` and comes back naive. That is
the *right* behavior, since `Event.time_zone` is `blank=True` and blank is the
ordinary case; only the comment was wrong, and it now says path-shaped only.

### 21 mutations, all caught

17 against `calendar.py`, 4 against `admin.py`, each restored byte-identical
(sha256-checked) with the suite green after.

**The one worth recording is M12**, which replaces the zone lookup with a fixed
UTC-8: it fails the **July** test and leaves the **January** test green. That is
the pair earning its keep — either date alone cannot tell a real `zoneinfo`
lookup from a hardcoded offset, and the `pytz`→`zoneinfo` rewrite in Step 13
task 09 shipped with no test at all.

A4 is the other one with something to say: making a bad key escape as `OSError`
rather than `CalendarError` turns the admin sync page into a **500**. That is
what requirement 7 forbids, and it is now held down by a test that posts to the
view.

### The sync button was a 500 before this task, not a stub message

`google_sync` called `oauth.get_credentials()` **before** constructing a
`Calendar`, and that hit the oauth stub's `NotImplementedError`. So the polite
"temporarily disabled" message in `calendar.py` was unreachable from the admin —
pressing Synchronize raised. The view now constructs the `Calendar` directly and
renders `CalendarError` into the page.

### Left deliberately for task 02

`cred_status` still means "a file exists at `GCAL_CREDENTIALS_PATH`", and the
page still says *Credentials file status* with a *Request new credentials* link
next to it. With a service account nothing expires, so that block is about to
mean nothing — task 02 deletes it, along with `oauth.py`, the two auth views and
the `{% if not event.on_calendar %}` no-op. Three admin tests were written here
rather than deferred, because requirement 7's justification is a rendered page
and nothing else proved it.

**Not browser-tested, and this is the reason:** the page is admin furniture task
02 rewrites, and the render is proven through the real template
(`assertContains` on the submit button, which also proves the
`{% url 'admin:gcalendar-authorize' %}` tag still resolves) plus a live 302 to
the login page from the running dev server. Task 03 is the one that puts a
person in front of it.


### Against the live calendar, 2026-09-01 — the key is in and read access works

The service account is **`sg101-calendar@api-project-786263548002.iam.gserviceaccount.com`**,
project `api-project-786263548002` — the same project number Brian's console
checks found. Key at `secrets/gcal-service-account.json` (git-ignored as a whole
directory, `0600`), `GCAL_CREDENTIALS_PATH=/app/secrets/gcal-service-account.json`.
Reading `calendars().get` and `events().list` both succeed, which is what proves
the calendar is **shared** with the account.

**`.env` edits do not reach a running container.** Compose loads `env_file:` at
container *creation*, so the first attempt still saw the old
`/home/brian/google/gcal.dat`. `docker compose up -d --force-recreate web worker
beat` is the fix, and the symptom — `FileNotFoundError` on a path you just
changed — reads like a bad key.

### Task 03 probe 2, the update half: ANSWERED YES

**The service account can edit events created by Brian's account.** Proven on a
real, wanted change rather than a throwaway: the two endless recurring gigs below
were patched with an `UNTIL`, and both had `creator: bgneal@gmail.com` and an
`updated` of 2019-03-17, so they were unambiguously his and not the service
account's.

**Still unproven: `delete`, and `anyoneCanAddSelf` (probe 1).** Neither is
answered by an update, and neither should be assumed from it.

### Task 03 probe 1 and the delete half: BOTH ANSWERED YES, 2026-09-02

**Probe 1 — `anyoneCanAddSelf` is accepted and stored.** An event inserted
through the sync button came back from `events().get()` carrying
`"anyoneCanAddSelf": true`. Read back from what Google stored, not inferred from
the insert not erroring — and since `_make_event` sets the field on every body, a
rejection would have failed every insert rather than this one.

**The delete half, twice, because the two runs answer different questions.**

| Run | Subject | Proves |
|---|---|---|
| Event 1656 through the site | created by the **service account** minutes earlier | our `DEL_APRV` code path end to end |
| *Delete Me*, direct API call | created by **`bgneal@gmail.com`** in the Google UI | the permission production actually needs |

The second run is the one that matters. All 1,478 rows point at events a human
account created, so deleting the service account's own event proves nothing about
them. `events().delete()` returned no exception, the event went to `cancelled`,
and it is gone from a normal listing. The ACL reads `sg101-calendar@…` = **writer**
and `bgneal@gmail.com` = owner, which documents delete as included — recorded as
documentation, not as the answer.

**Trap for whoever probes this next: a deleted event answers `events().get()`
with 200, not 404.** It returns the tombstone with `status: 'cancelled'`, and it
disappears only from `list()` without `showDeleted`. A probe written to expect a
404 would read a successful delete as a failure — and the 404 you *do* get from
this API is the pre-2015 URL-form id, a different fault that looks identical if
only status codes are read.

**The insert also ran the pipeline end to end**: submitted and approved by Brian,
pushed by the Synchronize button, row to `ON_CAL` with `google_id` and
`google_url` populated, `00:41:38Z` rendering as `19:41:38-05:00` from US/Central
input. `delete_callback` then destroyed the row rather than re-statusing it, so
the table is back at 1,478 and the pending queue is empty.

### The whole cycle, through the member and admin views — Brian, 2026-09-02

Insert, **edit** and delete each ran end to end, and the public `/calendar/`
iframe was checked at every stage: created → approved → synced → visible in the
iframe; edit request → approved → synced → the change visible in the iframe;
delete request → approved → synced → gone from the iframe.

That closes criteria 4 and 5, including the edit half, which until now had only
been proven by a direct API patch on 2026-09-01. Criterion 1 is met too: the key
is `0600` at `secrets/gcal-service-account.json`, ignored by `.gitignore:22` as a
whole directory, and absent from `git status --untracked-files=all`.

### CORRECTED — the member Delete button is not broken, and the probe is why

**Task 05's file recorded the member Delete button as dead on CSRF. It is not**,
and this cycle is what caught it: Brian's delete request went through the member
UI and worked.

The recorded claim was that `gcalendar_edit.js` sends no token and that **no
`$.ajaxSetup` exists anywhere in the tree**. The first half is true; the second is
false. `sg101/static/js/v3/sg101.js:4` installs a global `beforeSend` that sets
`X-CSRFToken` from the cookie on every relative URL, and `gcalendar/edit.html`
extends `v3/base.html`, which loads jQuery (281) and then that file (284). The
header is attached before the delete handler ever runs.

**The instrument could not see the mechanism.** The 403 was measured with the
Django test client under `enforce_csrf_checks=True`, and the test client does not
execute JavaScript. Posting the shipped payload by hand measures "an untokened
POST is rejected" — true of every view behind `CsrfViewMiddleware`, and silent on
whether the button works. `git grep ajaxSetup` answers it in one second and was
not run outside `gcalendar/`.

Two rules this breaks, both already written down. `measure-before-recording-in-planning-docs`:
the grep's *absence* of a hit was recorded as an absence in the tree.
And AGENTS.md's own warning that `CELERY_TASK_ALWAYS_EAGER` hides worker faults
because the suite cannot see them generalizes — **a test-client probe cannot
answer a question whose answer is in the browser.** Task 05's file is corrected;
its tests stay, since a tokened-accepted / untokened-403 pair is real coverage of
`delete_event`, but neither is a defect.

**Task 05's other reported defect was re-checked on the strength of this one, and
it stands.** `event.repeat = 'none'` (`views.py:44` and `:89`) assigns to a field
`Event` does not have — absent from `_meta.get_fields()`, from `0001_initial`,
and from the tree apart from those two lines. So task 05 now carries one real
finding rather than two, and its scope shrinks accordingly.

### What task 03 still owes

Nothing measurable. Both probes are answered, all five verification criteria are
met, and the console setup was written down on 2026-08-31. The task can be closed
when its write-up is read back against the file.

### The endless recurring events — 11, and only 2 of them are stale

Measured across 1,516 events (`singleEvents=False`, so masters count once):
**17 recurring masters, 11 with no `UNTIL` or `COUNT`.** They are two different
things and the distinction is the whole finding:

- **9 annual commemorations** — Valentines Day, SG101 Birthday, and the birthdays
  of Link Wray, Dick Dale, Don Wilson, Paul Johnson, Leo Fender, Eddie Bertrand
  and Bob Bogle. A birthday recurring yearly forever is *working*, not stale.
  Whether to keep them is editorial. **None has a `gcalendar_event` row** — they
  were created directly in Google.
- **2 stale gigs**, both monthly since April 2019 and still generating instances
  into 2027: *Matt Heaton's Retrosonic Surf Noir Guitar - Solo* (1st Thursday)
  and *The Electric Heaters at Shore Leave - Surfin' Sundays* (1st Sunday).

**Both stale ones DO have `gcalendar_event` rows at `ON_CAL`, and that is
diagnostic.** `_make_event` never sets `recurrence` and the submission form has
no way to — so both were submitted through the site as single events, pushed,
and **made recurring by hand in the Google UI afterwards** (Brian confirms).

**DONE 2026-09-01: ended rather than deleted**, `UNTIL=20260901T235959Z`.
0 future instances remain; **89 past instances preserved on each.** Deleting
would have left two `ON_CAL` rows pointing at a 404 and would break any later
edit/delete request against them; truncating keeps the database and Google
consistent for free.

### The database and the calendar reconcile exactly — after a false alarm

**All 1,478 `ON_CAL` rows match a live Google event. Zero orphans.** 38 events on
Google have no row, which is the 9 birthdays, the other recurring masters, and
~23 others created directly in the UI.

**The first reading said 1,012 rows were orphaned — 68% — and it was the
measurement.** `google_id` is stored in two formats, split cleanly by year:

| stored form | rows | submitted |
|---|---|---|
| GData v2 feed URL, `https://…/private/full/<id>` | **1,012** | 2011–2014 |
| bare v3 event id | **466** | 2014–2020 |

2014 is the overlap — the year the site crossed from GData to Calendar v3.
Normalizing to the last path segment reconciles all 1,478. See
`suspect-the-measurer-before-the-record`: the alarming number was the instrument.

### DEFECT found by that reconciliation: edit and delete are broken for 68% of events

`sync_events` passes `event.google_id` straight into `eventId=`, so a pre-2015
row sends the whole URL as an event id. **Verified against the live API: a
`events().get()` with a URL-form id returns 404**, the URL percent-encoded into
the request path; the same call with a bare id returns the event.

So `EDIT_APRV` and `DEL_APRV` **cannot work on any event submitted before 2015**
— 1,012 of 1,478. Latent, because nobody edits a 2013 gig, and invisible until
now because the sync has been dead since 2020.

**Immediate consequence for task 03: its delete probe MUST use a post-2014
event.** Picking an old one fails with a 404 that looks exactly like a
permissions problem, and would be read as "the service account cannot delete."

**DECIDED 2026-09-01, and DONE: normalize on read.** `Event.google_event_id` is
a property returning `google_id.rsplit('/', 1)[-1]`, and `sync_events` addresses
both the update and delete calls through it. No data is rewritten and the split
is a no-op on the 466 rows already bare, so it cannot disturb the modern half.

A data migration over the 1,012 rows was the alternative and buys nothing extra:
the URL form is what Step 21's fresh production snapshot contains either way, so
a migration would have to run there too. Hiding old events from the member edit
list was considered and rejected — it fixes nothing and removes a member's
ability to correct their own event.

**Verified against the live calendar: all 1,478 `ON_CAL` rows now resolve to a
real Google event through the property**, up from 466. The extracted segment was
confirmed to be the v3 id by `events().get()` on three pre-2015 events before
the fix was written, which is the assumption the whole option rested on.

**Exposure that made it worth doing rather than documenting.** 166 members own a
pre-2015 event and **74 have logged in since 2024**, several within the last two
months. And the failure is not a single failed edit: a failed callback does not
save the row, so it stays `EDIT_APRV` / `DEL_APRV`, `pending_events` keeps
returning it, and the sync page shows an error on *every* subsequent sync until
an admin resets the row by hand. A poison pill in the queue, not a one-off.

**5 mutations, all caught.** The one worth recording is N3 — a *plausible* wrong
implementation, `split('/private/full/')[1]`, which handles the URL form
correctly and raises `IndexError` on an already-bare id. It was caught by the
bare-id and empty-id tests plus two existing sync tests, which is what those
two otherwise-trivial-looking tests are for.

### Task 04 also carries two template fixes on the public calendar page

Brian looked at `/calendar/` for the first time in years (2026-09-01) and
Google's embed UI has moved on underneath the copy:

- `index.html:29-30` tells members to use "the pull-down menu in the upper right
  corner". It is now a **calendar icon, second from the right** in the embed's
  toolbar.
- The callout's "This calendar is **now** aggregating several Google calendars"
  has read oddly for years; worth rewriting while in there.

**The timezone handling is correct and needs no change** — `views.py:22-31` sets
`tz` from `user.profile.time_zone` (falling back to `US/Pacific` when logged
out), and the template feeds it to the embed as `ctz=` *and* states it in prose.
The calendar's own zone is `America/Chicago`, which affects only Google's own UI,
not what members see. Three zones can be on screen at once — the event's, the
viewer's, and the calendar's — which is worth knowing before reading a task 03
result as a conversion bug.

## Step 18 task 02 — the OAuth surface is gone — DONE 2026-09-02, `ee1b9b7c`, PUSHED

`gcalendar/oauth.py` (142 lines), both admin auth views and their two URLs, the
credentials-status block and its Authorize link, `GCAL_CLIENT_ID`/`SECRET`, and
the nine-year-old `{% if not event.on_calendar %}` no-op all stop existing.
**227 lines deleted against 176 added, and all but 14 of the additions are
tests.** Nothing about the sync's behavior changes.

`{% load core_tags %}` went with the block: `bool_icon` was checked first and was
its only use in that template.

### The admin's first tests: 46% → 100%, and 22 mutations

`gcalendar/admin.py` is **49 statements at 100%**, from 46% incidental. Suite
**1,035 → 1,043**, green, and green again under the deprecation gate as a
separate run.

Written in two phases, which is what made the deletion safe to do at all:

- **Seven characterization tests first**, green against the *pre-deletion* code —
  the page's queryset, what it renders, an unreadable key reported in the page, a
  clean sync, a `CalendarError` out of `sync_events`, and three over
  `approve_events`. These are what the deletion had to survive.
- **Two more written to fail**, and watched failing for the right reason: the
  credentials furniture absent with the button still rendering, and
  `NoReverseMatch` for both removed route names.

The `approve_events` tests drive the action **through a changelist POST**, not a
direct call to the method. A direct call passes just as well with `actions`
empty, which would be a live defect no test could see.

**`admin:gcalendar-google_sync` is asserted to still reverse in the same test as
the two `NoReverseMatch` assertions.** Dropping every custom URL — the plausible
over-broad edit — satisfies the negative assertions perfectly, and M14 confirms
that guard fires.

**22 mutations, each seen to fail the assertion it targets.** Three of the first
round were the interesting part: they were *caught*, but by an assertion earlier
in the same test, so the assertion actually under test never ran. Splitting
`test_the_page_selects…` from `test_the_page_renders…`, and splitting the
credentials-furniture and clean-sync mutations one string at a time, is what made
each claim independently falsifiable. See
`mutation-verify-or-it-is-not-coverage`: catching the mutation is not the bar,
catching it *with the assertion that claims to* is.

**The badge assertion needed a fixture to mean anything.** `award_badge` logs and
returns when no `Badge` row carries the id, so a test that forgets to create the
`CALENDAR_PIN` row passes while proving nothing. The row is created explicitly
and M12/M13 confirm the assertion discriminates.

### DECIDED 2026-09-02 — a blank key is invisible until the button is pressed

Unwrapping the submit form changes what an unconfigured deploy sees: the button
now renders whenever events are pending, and a blank `GCAL_CREDENTIALS_PATH`
surfaces only when it is **pressed**. Brian's call, taken over gating the form on
the setting instead.

**The button gives no advance sign either way** — same label, same page. Gating
it was costed on 2026-09-02 (`os.access` plus a notice naming the setting, ~15
lines and three tests) and **declined**: Brian is the only user of this page and
will know at once whether the key is in place. Recorded because the reasoning is
what makes it revisitable — the answer changes the day anyone else syncs.

One failure path that says what is wrong beats a button-less page that explains
nothing. **The consequence is that task 01's settings comment became false** —
`base.py:349` and the `.env.example` header both said blank "disables the
integration: the sync page offers no button without it", which now describes a
gate that does not exist. Both are corrected to say that blank is invisible until
the button is pressed.

### The blank-key message said `''`, and now names the setting

Measured through the real constructor, a blank path reported
`Could not read the credentials file: [Errno 2] No such file or directory: ''` —
accurate, and it reads like a fault in the site rather than a setting nobody
filled in. A wrong *path* reported the path and was always useful; blank was the
one case that told you nothing.

`Calendar.__init__` now raises before touching the filesystem:
**`No service account key is configured: GCAL_CREDENTIALS_PATH is blank.`**
This is `calendar.py`, task 01's file, amended here because task 02's decision is
what made the message reachable from the page.

`test_a_blank_credentials_path_is_a_calendar_error` asserted only the exception
*type*, so it passed against both messages. It now asserts the setting name is in
the text and the stat wording is not, and **three mutations** say it
discriminates: no guard at all, a guard that does not name the setting, and — the
one worth keeping — a guard that names the setting *and* still says "No such
file", which the `assertNotIn` is the only thing that catches.

### The removed URLs do not 404 — they land on the admin index

Checked against the running server while logged in:
`/admin/gcalendar/event/authorize/` and `.../auth_return/` now fall into the
`ModelAdmin` `<path:object_id>/` catch-all, redirect to `authorize/change/`, find
no `Event` with that id, and bounce to `/admin/` with the admin's "doesn't exist"
message. **Two redirects and a 200, not a 404** — worth knowing before reading a
bookmarked Authorize link's behavior as the route still being live. The suite
asserts the thing that is actually true: neither name reverses.

### Rendered in the running stack, not just the suite

A `{% url %}` to a deleted route raises at *render*, not at import, so a missed
reference would not show up as a failing import. The page was fetched from the
dev server as a logged-in superuser: **200, the event listed, the Synchronize
button present, and no credentials line or Authorize link.** The button was not
pressed — that would have posted to the live calendar.

The probe needed a pending event and a superuser, and the dev database had
neither (`pending: 0`, and Brian's own account's password is his). Both were
created, used, and deleted; the database is back at **1,478 events, 0 pending**,
probe user gone.

### What task 03 inherits

Nothing from this task is owed. The sync page is now the single failure path it
was meant to be, and `cred_status` no longer exists to be confused with a health
signal. Task 03's remaining probes are unchanged: `delete`, and
`anyoneCanAddSelf`.

## Step 18 task 04 — the calendar is reachable again — DONE 2026-09-02, `1e53962e`, PUSHED

`<li><a href="{% url 'gcalendar-index' %}">Calendar</a></li>` is back in both
live base templates, in the positions `7073a406` took it from: `base.html`
between Submit News and Contact, `v3/base.html` at the top of the Surf Music
dropdown. **Restored by hand, not by reverting** — that commit also removed the
Member Map link, and `membermap-index` was pruned in Step 4, so a reverse-apply
would have put a `{% url %}` for a dead route into both bases and 500'd every
page on the site. The copyright bump in the same commit is unrelated and was left
alone.

`/calendar/` has been unreachable from anywhere on the site since 2023-03-19.
It is reachable from both designs again as of today, which is what the whole step
was for.

### The tests render pages, because that is the only thing that catches this

`gcalendar/tests/test_navigation.py` fetches `forums-index` (`base.html`, still
worn by the busiest part of the site) and `home` (`v3/base.html`), asserting the
anchor with `html=True` and building its href from `reverse()`. Suite
**1,043 → 1,045**, green, and green under the deprecation gate.

**A `{% url %}` naming a missing route raises at render, not at import.** A
string search of the template or an import-level check passes while the page
500s in a browser — which is exactly the failure a revert would have introduced.
**Mutation P3 proves the tests catch it**: pointing the link at
`membermap-index` fails the forums test. P1 and P2 delete the link from one
template each and fail exactly one test apiece.

Neither nav sits inside an auth conditional — measured, not assumed — so the
tests need no login and the link shows for anonymous visitors.

### Nothing else needed the link

Checked per requirement 6: **this project has no sitemap**, and the only other
`gcalendar-index` references are breadcrumbs inside the calendar app's own
templates. `core/tests/test_pruned.py` already asserts `membermap-index` does not
reverse, so criterion 2 needed no new test — and `git grep membermap -- '*.html'`
is empty.

### The two pieces of stale copy on the public page

Both fixed here, as this section assigned on 2026-09-01:

- *"the pull-down menu in the upper right corner"* → **"the calendar icon at the
  top of the calendar, second from the right"**, which is where Google's embed
  now keeps it. The first attempt said "in the toolbar above" and Brian caught
  it: the callout sits *above* the iframe, so "above" pointed the reader away
  from the control. The wording carries no page-relative direction now, which is
  what makes it survive the callout moving.
- The callout was **rewritten rather than patched**, on Brian's pick from three
  drafts: *"Along with our own events, this calendar carries listings from
  friends' calendars around the surf music world — so you can find more shows in
  one place."* The original said *"This calendar is now aggregating several
  Google calendars… without duplicating efforts in the community"* — the "now"
  dated from whenever the second calendar was added, "aggregates" is a machinery
  word on a page about gigs, and the payoff was written from the site's side
  ("lets **us** give **you**") about a rationale the reader has no use for.

### The page now recruits calendar owners — added 2026-09-02, outside task 04

A `secondary callout` under the Add / Change buttons:

> Keep your own Google calendar of shows? You don't have to add events here one
> at a time — contact us and we'll add your calendar alongside ours.

**Placement was the decision, not the wording.** The main callout at the top of
the page explains that the calendar carries listings from friends' calendars, so
the offer is thematically at home there — but that callout is the first thing
every visitor reads, and this offer is for the few who run a gig calendar of
their own. Under the buttons, it answers the button: the person looking at *Add
New Event* is exactly who "you don't have to do this one at a time" is for. The
button group is **not** auth-gated, so the offer is public, which suits a band
that has never registered.

A `<p class="help-text">` variant was rendered alongside it for comparison and
dropped. Worth noting for a future editor: in this codebase `help-text` is used
*only* as form-field help, always under a label, so a standalone use would have
been the first of its kind.

### Step 18's original scope is complete

Tasks 01–04 were the step as planned on 2026-08-31. Task 05 was added on
2026-09-01 to cover the member-facing half that no other task opened, and it
closed on 2026-09-03 — see the section below. **Step 18 is complete.**

## Step 18 task 05 — the member-facing views, covered — DONE 2026-09-03, `c6d56849` + `6c920b0d` + `725cb3f4`, PUSHED

`gcalendar/tests/test_forms.py` (16 tests) and `gcalendar/tests/test_views.py`
(36) give `forms.py` and `views.py` their first tests. Suite **1,045 → 1,097**,
green, and green under the deprecation gate. Line coverage, measured with
`coverage run --source=gcalendar`:

| | before | after |
|---|---|---|
| `views.py` | 30% | **100%** |
| `forms.py` | 34% | **100%** |

Both figures before were incidental — other apps' tests importing the URLconf.

### The edit page 500'd on three of Brian's own events

**Found while writing the tests, measured, and fixed on Brian's call.**
`EventEntryForm.__init__` prefills an existing event's times for the hour
selects, and formatted them unconditionally:

```python
initial['start_time'] = instance.start_time.strftime(self.TIME_FORMAT)
```

Both time columns are `null=True`. For an event with `all_day` False and no
start time, that is `AttributeError` raised while the form is being *built*, so
`edit_event` never renders — it 500s.

**Reproduced through the real view against the dev database**, not inferred from
reading: calling `edit_event` for each row as its owner raised
`AttributeError: 'NoneType' object has no attribute 'strftime'`.

| | |
|---|---|
| Rows with `start_time` NULL and `all_day` False | **3** — pks 2, 376, 377 |
| Their status | all `ON_CAL` |
| Their owner | all `Brian` |
| Where they appear | `/calendar/change/` pages **4** (rows 93, 94 of 128) and **6** (row 126) |

So they were live links on Brian's own change page, and every one of them
answered a 500. **Not reachable through the member form**: the Start Time widget
is a `Select` over `TIME_CHOICES` with no blank option, so a browser always posts
an hour. The admin can create one, and the three that exist are from 2011–2012,
predating this form. Measured on the dev database, which carries the same 1,478
events as the live calendar; production itself was not queried.

**The fix** falls back to the same hours a new event opens on (`19:00`/`20:00`),
which is what the `all_day` branch two lines above already does, rather than to
midnight — a select with no blank option cannot express "no time", so the edit
will set one either way, and the house gig hours are the less surprising value
to hand back. After it, all three render 200 with `19:00` preselected.

### `event.repeat = 'none'` is gone

The two dead assignments in `add_event` and `edit_event`, on the decision
recorded 2026-09-02. `Event` has no `repeat` field, so each set an instance
attribute that was never persisted and never read; `repeat` now appears nowhere
in the tree. The save-path tests (`test_the_submitted_values_are_stored`,
`test_the_edited_values_are_stored`) were written and seen green **before** the
lines came out, so the deletion had something to regress against.

### The delete button: still no defect, and now covered

Nothing new to report — this confirms the 2026-09-02 correction rather than
revisiting it. The mechanism is more local than that correction knew: **the
change page sets the `csrftoken` cookie itself** (measured — `gcalendar-index`,
`gcalendar-edit_events`, `home` and `accounts-login` all do), so
`sg101.js`'s global `$.ajaxSetup` has a cookie to read on the very page carrying
the button. `DeleteEventCsrfTestCase` runs a client with
`enforce_csrf_checks=True` and performs that sequence — load the list, post the
id with the cookie's value as `X-CSRFToken` — which succeeds, paired with an
untokened post that is 403.

### Two characterizations pinned as they stand, not changed

Both were **closed the same day** in the follow-up below; the tests written here
are what made them visible, and what caught the change when it came.

- **`edit_events` lists only `ON_CAL` events, `edit_event` filters on nothing.**
  A member cannot see an event they just submitted, but one who kept the URL can
  move a `NEW` event to `EDIT_REQ` directly.
- **`clean()` skips its own cross-field check without a start time.** The guard
  reads `if start_date and start_time and (...)` and `start_time` is
  `required=False`, so an all-day event ending the day before it begins
  validates cleanly. Unreachable from the page — the select always posts an
  hour.

### The mutation battery found a test with no teeth, and two mutations with none

33 behaviours, each broken deliberately with the specific test that must notice;
files restored and verified byte-identical after every run, suite green at the
end. 27 of the first 32 were caught outright. The five that were not are the
reason the battery is worth running:

- **Two were my own bad anchors.** The `edit_events` queryset line is indented
  four spaces, not eight, so the mutation was never applied and the "survival"
  was an artifact of the instrument. Both caught once anchored correctly.
- **Two mutations did not reproduce their fault**, because `delete_event` guards
  each case twice. Disabling `if request.user.is_authenticated` changes nothing:
  `AnonymousUser != event.user`, so the ownership check answers the same 403.
  And disabling the `event_id is None` half of the input guard changes nothing
  either — `Event.objects.get(pk=None)` raises `DoesNotExist` (measured; not
  `ValueError`), so a missing id reaches the same 400 by the other route. Both
  were caught once the mutation broke *both* convergent paths.
- **One test really had no teeth.** `test_the_dates_and_times_are_prefilled_...`
  used a fixture whose start time was `19:00` — the form's own
  `DEFAULT_START_TIME` — so replacing the instance's value with the default was
  invisible. Fixture changed to `18:30`/`21:30`, and the mutation is caught.

Two docstrings were also cut back to what their assertions prove: one claimed to
distinguish `add_event`'s save path from `edit_event`'s, which no assertion can
— both call `site_markup` with the same arguments and produce identical HTML.

## Step 18 follow-up — the two characterizations, closed — DONE 2026-09-03, `89b88fad` + `386bcff9`, PUSHED

Both were recorded above as behaviour to pin rather than change. Brian's call to
fix them, once the tests made the shape of each clear. Suite **1,097 → 1,101**,
green under both runs, `views.py` and `forms.py` still at 100%.

### `edit_event` now applies the rule `edit_events` lists by

One line: `get_object_or_404(Event, pk=event_id, status=Event.ON_CAL)`. The
ownership check is untouched, so another member's event is still a 403 rather
than a 404.

**The direction was a real choice and Brian picked the narrower one.** The
alternative was to list every event with a status column, so a submitter could
see what they had just sent — a wider change to the list, the template, and to
which statuses stay editable mid-sync. Enforcing the existing rule instead
changes no workflow: it makes the view agree with what `edit.html` already tells
the member, that an event with a pending change is waiting on the staff.

**Why it is worth closing at all is the sync queue, not tidiness.** The only
link into `edit_event` is the event title in `edit.html`, inside the loop over
the `ON_CAL`-filtered list — so the reachable case is a URL the member
legitimately had a moment ago, in history or behind the Back button, for an
event that has since left the list. `edit_event` sets `EDIT_REQ` *whatever the
status was*, and `PendingEventManager` selects the three `_APRV` statuses. So a
member who pressed Back after staff approved their change could put the row back
to `EDIT_REQ` and **drop it out of the sync queue with nothing said** — no
error, nothing pushed, and the calendar simply not updating. Same shape after a
delete: posting from a kept URL turned `DEL_REQ` into `EDIT_REQ` and cancelled
the member's own deletion request.

`test_an_approved_event_cannot_be_taken_out_of_the_sync_queue` is the test named
after that, and it asserts membership of `Event.pending_events` rather than the
status alone, since the queue is the thing that was at risk.

### `clean()` compares the dates when it has no times to compare

The guard required `start_time`, an optional field, before comparing anything —
so a submission missing an hour skipped the check entirely, and for an all-day
event the times were not even part of the comparison being skipped.

```python
if start_date and end_date:
    if all_day or not (start_time and end_time):
        start, end = start_date, end_date
```

**It falls back to the dates rather than inventing an hour.** With only one time,
or none, the date ordering is the whole of what can honestly be asserted; an
event on a single day with no times stays valid, which the two companion tests
pin so the stricter check cannot start rejecting what it should not.

### Mutation battery — 4 of 4 caught

`status=Event.ON_CAL` removed from the lookup; the old `clean()` guard restored
whole; the fallback narrowed to `if all_day:` alone; and `>` widened to `>=` to
give the two must-stay-valid cases teeth. Files restored byte-identical, suite
green after.

## PLANNING — Step 17: the cost rationale is dead, registration is the real target (2026-08-27)

**R23's premise is true about reCAPTCHA and false about this site.** The step was
justified on 2026-07-04 by reCAPTCHA's move to a 10k/month cap — a real vendor
change, never sized against SG101. Measured against the box, this site's busiest
month is **71 assessments**. The cost argument does not survive contact with the
number, and Step 17 proceeds on privacy and user friction instead.

**DECIDED: adopt Turnstile, on the contact form and registration both.** The
integration is written once and used twice.

### The current widget is reCAPTCHA v2, checkbox

`sg101/templates/contact/contact_form.html:55` renders `<div class="g-recaptcha"
data-sitekey="…">` with no `data-size="invisible"` and no `data-callback`, loads
`api.js`, and `contact/forms.py:44` reads `g-recaptcha-response`. That is the
"I'm not a robot" checkbox, not v2-invisible and not v3. Added 2018-04-14 in
`153b6afd`, on `main` — so the deployed code is the code read here.

**`contact/` is the only reCAPTCHA caller in the repo.** Registration has none.

### The pricing claim, verified at the source

From Google's own billing page (`docs.cloud.google.com/recaptcha/docs/billing-information`,
last updated 2026-08-11), **not** a competitor's blog — every third-party summary
of this has an interest in the framing:

| Tier | Price |
|---|---|
| Up to 10,000 assessments/month, **per organization** | free |
| 10,001–100,000/month | $8 flat |
| Over 100,000/month | $0.001/assessment |

### What this site actually consumes — measured 2026-08-27

`contact/forms.py:52` has logged one line per `siteverify` call since 2018. Read
from `/svr/django-sites/sg101/sg101/sg101/logs/sg101.log{,.1..10}` on jaguar
(rotation is 100 KB × 10, giving ~5 months):

| | |
|---|---|
| Window | **2026-04-01 → 2026-08-27**, 149 days |
| Assessments | **225** |
| Outcome | **225 `True`, 0 `False`** |
| `error-codes` | `<Missing>` on all 225 — never once populated |
| Busiest month | **71** (June 2026) |
| Per month | Apr 49 · May 51 · Jun 71 · Jul 34 · Aug 20 (27 days) |
| Recent rate | 1–3/day |

**Peak month is 0.7% of the free tier — roughly 140x headroom.** Annualised,
~550/year against 120,000/year free.

**Nothing else aggregates against the allowance.** The cap is per *organization*,
and jaguar hosts two other Django sites; `bravenewsurf` and `madeira` were
grepped and neither uses reCAPTCHA.

### The classic key is healthy, not degraded — the finding that could have forced the step

Google no longer issues classic keys and recommends migrating them. Third-party
reporting (**unconfirmed** — this is not in Google's own docs) says classic keys
were auto-migrated to Cloud projects, and that one not linked to a project with
billing runs degraded.

**225 consecutive successes with `error-codes` never populated says otherwise**,
and the chain is proven end-to-end at **2026-08-27 13:29:01**: script loaded,
user solved the checkbox, token issued, `siteverify` accepted it.

**Why the counts alone could not have shown this.** A client-side failure — script
blocked, key rejected before a token is issued — produces *absent* log lines, not
failures, because `contact/forms.py:45` raises before `siteverify` is ever
called. The monthly decline from 71 to 20 is therefore not readable as health on
its own. **Today's successful line is what settles it**, and it is the whole
reason to prefer a recent success over a clean tally.

### v3 was never the right tool, and cost is not why

v3 returns a score, not a verdict: the threshold becomes ours to choose and
re-tune forever. It spends quota **per page load** rather than per submit, and
Google's guidance is to load it site-wide for scoring accuracy — which is also
the worse privacy posture of the three. Rejected on maintenance surface.

### Turnstile's free tier is uncapped — from Cloudflare's plans page

Free plan: **"Unlimited challenges (traffic or verification requests)"**, 20
widgets per account, 10 hostnames per widget, 7-day analytics retention.

**Several third-party sites claim a 1M/month cap. That number does not appear in
Cloudflare's own documentation** and is recorded here as noise, not as a limit.

Migration shape is close to like-for-like with what `contact/forms.py` already
does — a div, a script, and a server-side verify POST. **Turnstile's siteverify
takes the same `remoteip`** the contact form passes today via
`get_ip(self.request)`; the `CF-Connecting-IP` dependency that makes that value
correct is recorded once in task 03's *Open* register and hangs on Step 20.

### Registration already has four layers, and they are being defeated

`accounts/forms.py` protects registration with a static knowledge question
(`question1`, "What number appears in the site name?" → `101`), a hidden honeypot
(`question2`, logged CRITICAL), a visible honeypot (`question3`), and a
registration code (`RegisterCodeForm`).

**CORRECTED 2026-08-27, during task generation — the code word is not emailed,
and calling it that overstated it.** The flow was read rather than assumed:
`register` puts a generated code in the **session**, `register1` renders a
placeholder, `static/js/accounts_code.js` fetches the code from the
**`/register/code/` JSON endpoint** (`accounts/views.py:82`, no auth), and
`register2` checks what the user types against the session copy. **The code is
handed to the client and echoed back**, so what it actually tests is whether the
client runs JavaScript. It is a JS-execution gate, not a possession check.

**The possession check is a separate, later stage** — `register_confirm`, the
emailed activation link, which does require control of a mailbox. It sits after
the code, not in it.

Measured from `auth.log` (**2025-01-10 → 2026-08-25, ~19.5 months** — this file
retains far longer than `sg101.log`):

| | |
|---|---|
| Successful registrations | **1,038** |
| Registration failures | **1,499** |
| Blocked by the anti-bot layers | **876** — 439 wrong answer, 276 visible honeypot, 161 hidden honeypot |
| Registration events/month | 57–137 (last 12 months), peak **137** (Oct 2025) |

**CORRECTED 2026-08-27 — the earlier "2,698 failure lines" was wrong.** 2,698 is
*every* `Accounts/registration` line: 1,038 successes, 1,499 failures, and 161
duplicate CRITICAL entries, because a filled hidden honeypot is logged twice —
once by `clean_question2()` and once by `_validation_error()`. The 161 duplicates
are a useful cross-check: they match the "Wrong answer #2" count exactly. **The
error was reading a `grep -c` of the shared prefix as if it counted only
failures**, which is the same shape as every miscount this project has recorded:
the number was real, the population under it was not the one named.

**And spam still gets through. Seven accounts registered successfully and were
later deactivated for spam** between 2026-04-03 and 2026-07-24 — inside
`sg101.log`'s ~5-month window, so **~1.4/month**. That figure counts only the
ones caught; it is a floor, not a rate.

**`question1`'s answer is a fixed constant.** That is consistent with the shape of
the evidence: it stops generic crawlers — 439 of them — and is one line of code
for anything targeting SG101 specifically.

**REVISED 2026-08-27 by the correction above, and the revision runs toward
Turnstile rather than away from it.** The original text here hedged that a
challenge would not close the gap, because clearing an *emailed* code word
implies a human or a solving service. That premise was wrong. What a bot needs
today is: answer a fixed constant, leave two fields blank, run JavaScript (or
simply GET `/register/code/`), echo the value back, and control a mailbox.
**Every one of those is scriptable except the mailbox**, and disposable mailboxes
are cheap. So 1.4/month getting through is what this design predicts rather than
a surprise, and Turnstile substitutes a real bot check for the JS-execution gate
that is currently doing that job.

**The hedge is not withdrawn entirely.** A solving service still defeats any
CAPTCHA, so this raises cost rather than shutting the door. What changed is the
expected size of the effect: against the bots this flow actually admits, it
should be larger than first stated. **The value of measuring 1.4/month now is
that it is a pre-change baseline** — it is what "did it work" gets judged
against.

### Which layer stops bots and which stops people — measured 2026-08-27

**Counting blocks cannot answer this**: a bot turned away and a human tripped up
look identical in a tally. The discriminator is **whether that IP ever completed
a registration afterwards** — a blocked bot does not come back and succeed, a
fumbling human does. **Password-mismatch is the control group**, as close to a
pure-human failure as the log offers, and it reads 68%.

| Layer | Hits | Distinct IPs | IPs that later succeeded | Reading |
|---|---|---|---|---|
| `question2` — **hidden** honeypot | 161 | 111 | **8%** | near-pure bot |
| `question3` — **visible** honeypot | 276 | 202 | 27% | mixed; ~55 real people tripped |
| `question1` — the `101` question | 439 | 281 | 35% | mixed; ~98 real people tripped |
| **registration code mismatch** | 214 | 134 | **77%** | **almost pure human** |
| *(control)* password mismatch | 116 | 99 | 68% | humans by definition |

> **CORRECTED 2026-08-30 — 35% of this corpus has no client IPs in it.** Between
> 2025-06-19 and 2025-08-10 the site logged Cloudflare's edge addresses as
> `REMOTE_ADDR`, so the "IPs that later succeeded" column — which keys on IP
> identity — is inflated for every row. Recomputed with that window excluded the
> ordering holds, but the honeypot reads **0%**, `question3` **12%**, `question1`
> **21%** and the code step **89%** against a **78%** control. The table above is
> left as it was measured; see *Cloudflare dated, and 35% of the layer
> measurement had no client IPs*. **`question1` and `question3` were roughly 3x
> more bot-catching than these numbers say**, which is the half of this table
> that argued for removing them.

**The code step performs worse than the control.** The people it stops are
overwhelmingly humans who mistyped or lost the code and retried; it turns away
about 1.6 IPs/month that never return. Its only anti-bot function is proving the
client runs JavaScript — precisely what Turnstile does as a side effect of doing
something much harder. It is close to pure friction.

**`question1` costs more than it collects.** ~9 IPs/month turned away for good
against ~5/month of real people who had to retry.

**The hidden honeypot is the one genuinely worth keeping.** 8% is the cleanest
bot signal in the system, it is free, and it costs users nothing because they
never see it. It also catches a *different* class than a challenge widget does —
naive form-fillers rather than headless browsers — so it complements Turnstile
instead of duplicating it.

**Caveat, stated because the metric is a proxy and not proof.** Shared and CGNAT
addresses inflate the overlap; rotating IPv6 deflates it. The control at 68% is
what calibrates the scale, and **the code step's 77% sits above the control** —
that ordering is the robust part, whichever way the proxy errs. Separately, the
log records only failures, so people who *abandoned* at the code page without
failing are invisible: the friction cost is a floor, not an estimate.

### DECIDED 2026-08-27 — simplify the flow rather than bolt Turnstile onto it

Brian's own read, and the reason this was measured: the flow was built before
reCAPTCHA existed, and predates the option it now duplicates.

| Layer | Decision |
|---|---|
| `question1` (the `101` question) | **remove** — Turnstile covers the class at lower cost to users |
| `question3` (visible honeypot) | **remove** — the hidden one does the job without confusing people |
| `question2` (hidden honeypot) | **keep** — best discriminator measured, free, invisible |
| The 2-step code flow (`register1`, `register2`, `RegisterCodeForm`, `accounts_code.js`, `/register/code/`) | **remove** — Turnstile subsumes the JS gate; the step is net friction |
| Emailed activation (`register_confirm`) | **untouched** — this is the possession check, and the only one |
| Turnstile | **on `register`, stage one** — cost imposed before a session, a `PendingUser` row, or an email exists |

Registration goes from four pages and four checks to **`register` → `thanks`**
plus the emailed confirmation, with Turnstile and one invisible honeypot.

### Volume if Turnstile goes on both forms

Worst case, assuming every registration event spends a verification: 137 + 71 =
**~210/month**. Against reCAPTCHA's free tier that would be 2% of the cap; under
Turnstile it is moot. **Brian's read that traffic is low enough was correct.**

### Task files — four, generated 2026-08-27; a fifth added 2026-08-28

Sequence is **01 → 02 → 03 → 04**, strictly add-before-remove. **Task 05**
(the no-token line and a dedicated log file) came out of task 02's verification
and is independent of 03 and 04 — worth running *before* 03, since registration
is the more heavily targeted form and the file should exist before its volume
arrives.

- `step17/task-01-turnstile-verification-helper.code-task.md` — the shared
  server-side helper in `antispam/`, which is what finally makes the plan's
  "update the `antispam` app" true; the app was the wrong home for reCAPTCHA and
  is the right one for a helper with two callers. Carries the settings, the
  `.env.example` entries, and **the timeout fix** — `contact/forms.py:47` calls
  `requests.post` with no `timeout=`, the same bug class as `EMAIL_TIMEOUT` in
  Step 16 task 02, and a port that preserved it would be the one bad outcome.
  Three outcomes, not two: passed, rejected, and could-not-determine, because a
  provider outage and a failed challenge are different events.
- `step17/task-02-contact-form-turnstile.code-task.md` — the swap, plus deleting
  every remaining reCAPTCHA reference. Goes before registration because this
  form's behaviour is measured, so a regression is visible.
- `step17/task-03-registration-turnstile.code-task.md` — the widget on stage one,
  **removing nothing**. Registration is deliberately over-protected at the end of
  it.
- `step17/task-04-retire-registration-code-flow.code-task.md` — the
  simplification. **DONE 2026-08-30**, see its own section. Most of its diff is
  `accounts/tests/test_views.py`, not the deletions — **half right, measured
  after the fact**: the test file is the largest single file at 142 changed
  lines, but the diff as a whole is 329 deletions against 56 insertions, so the
  removals dominate it.

**Turnstile's test keys make this developable in Docker, which reCAPTCHA never
was.** Cloudflare's dummy sitekeys and secrets work from any domain including
`localhost`, with no account and no hostname allowlisting, and task 01 ships the
always-passes pair as the committed `.env.example` defaults. Today
`.env.example:43-45` holds blank reCAPTCHA keys, so a fresh checkout cannot
exercise the contact form at all. **Both entries deleted by task 02, 2026-08-28**
— true when written, and the sentence is kept because it is the argument for the
test-key defaults, not a description of the current tree. **This matters more than convenience**: Step 16
task 05 recorded six defects found in ten minutes of browser testing that 946
green tests could not see, and reCAPTCHA has been obstructing exactly that.

**One defect class flagged for task 02, unverified deliberately.** Turnstile
tokens are single-use, so a form that fails validation for an unrelated reason
re-renders with a spent token and confuses the next submit. Whether the same
fault exists today under reCAPTCHA v2 was **not** checked — the task says to
determine it rather than assume, because "fixes a long-standing defect" and
"introduces a new one" are different claims and only measurement separates them.

### Still open

- ~~**The registration flow itself**~~ and ~~**where the widget goes**~~ —
  **both CLOSED 2026-08-27** by the measurement and decision above.
- ~~**`requests.post` has no timeout**~~ — **CLOSED 2026-08-27 by task 01.**
  `antispam/turnstile.py` posts with `timeout=settings.TURNSTILE_TIMEOUT`, and
  the old un-timed call at `contact/forms.py:47` went with reCAPTCHA in task 02.
- ~~**The 1.4/month spam baseline needs re-reading before `sg101.log` rotates**~~
  — **the deadline was wrong and is withdrawn 2026-08-30.** The read itself is
  done; see *the spam baseline, read from the database* below.

  **What this bullet got wrong, twice.** It said the baseline is registration
  lines in `sg101.log`, greppable as `grep 'Accounts/registration' sg101.log*`.
  That file contains **zero** such lines — they are all in `auth.log`, which is
  what the measurement section 160 lines above this one already said and what
  this bullet contradicted. Anyone following the grep would have got an empty
  result and concluded the evidence had rotated away.

  **The urgency was real but attributed to the wrong half.** The *numerator* —
  `User deactivated for spam:` lines — genuinely is in `sg101.log`, which
  retains ~5 months and did bound the seven events to 2026-04-03 → 2026-07-24.
  The *denominator*, registrations, is in `auth.log` at 19.7 months.

  **And the whole clock is moot, because the logs were never the only
  instrument.** `antispam.utils.deactivate_spammer()` writes the fact to the
  database — `UserProfile.status = STA_SPAMMER`, `status_date` set explicitly —
  so the history is durable, complete, and reaches back to **2011**. Nothing
  perishes. Read it whenever.

  **Still true, and unchanged:** production serves the **`main`** branch on
  Python 2.7 until the Step 21 DNS flip, so registration there runs the old flow
  with no Turnstile, the *before* period is still accruing, and no *after* data
  exists yet or can. The *after* remains `grep Turnstile turnstile.log*`.

## PLANNING — Step 17 task 05: the contact form's real traffic, measured 2026-08-28

Prompted by a question during task 02's browser checks — the always-blocks
sitekey instance produced no log line at all. That is correct behaviour, and it
is also the instrument's one blind spot. Whether closing it was affordable
turned entirely on a number nobody had, so it was measured before being argued.

**Source: `/svr/www/surfguitar101.com/log/access.log*` on jaguar — the vhost's
own log, not `/var/log/apache2/`.** That distinction cost a false start: the
system-wide log carries no sg101 traffic at all, and a first count there
returned **zero** `POST /contact/` across its full retention. A zero that agrees
with no other evidence is a wrong instrument, not a finding.
[[suspect-the-measurer-before-the-record]]

### 3,669 POSTs, 52 messages

Window **2026-06-29 → 2026-08-28**, 61 days, the vhost log's full retention.

| Status | Count | Reaches `ContactForm.clean()`? |
|---|---|---|
| 200 — form redisplayed | 2,296 | **yes** |
| 403 — CSRF rejected | 1,318 | **no** |
| 302 — message sent | **52** | yes |
| 411 | 3 | — |

**Roughly 70 POSTs for every message a human actually sent**, and about **37
token-less submissions a day that no instrument on this site has ever
counted.** The 225 reCAPTCHA verifications behind this step's rationale were
counting only the traffic that got as far as a token; the form's real load is
~25x that. The rationale is unaffected — 225 assessments against a 10,000/month
cap is still 0.7% — but the picture of what the form *does* was wrong by an
order of magnitude.

**The 403s were verified, not assumed.** A POST with no CSRF token against the
dev stack returned 403 and left the Turnstile line count unchanged: Django's
middleware rejects before the view runs, so 36% of this traffic costs nothing
and needs no line. That measurement is what took the estimate from ~60 lines a
day to ~37.6.

### The retention arithmetic, which is why this is not a one-line change

`sg101.log`'s rotation set spans **2026-04-01 → 2026-08-28** — 149 days in
~1,062 KB, so **7.1 KB/day**. That window is exactly the one the 225-verification
measurement used; it consumed the entire retention.

37.6 lines/day at ~63 bytes is **2.3 KB/day** → 9.4 KB/day → **149 days becomes
~113, a 24% cut** to the file every volume measurement in this step depends on.
Affordable, but not free, and paid by the instrument itself.

**`auth.log` and `search.log` are this project's own answer** — separate files at
2 MB x 5 with `propagate: False`, for exactly this reason. At that budget the
new volume is thousands of days.

### Split into task 05 rather than folded into task 02

Brian's call, 2026-08-28. The work is a handler, a logger entry in two settings
modules, and one line with a test — small, but it is `LOGGING` scope on a task
whose diff was otherwise finished, and Step 19 already has a settings-module
cleanup queued. `step17/task-05-turnstile-log-file-and-no-token-line.code-task.md`.

**It carried one open design decision** — whether the no-token line comes from a
second helper entry point or from a fourth `TurnstileOutcome` that `verify(None)`
returns without calling out. **DECIDED 2026-08-29: the fourth outcome.** Reasoning
and consequences in the task 05 section below.

## Step 17 task 03 — the widget on registration, and nothing removed — DONE 2026-08-29, `93e50cab` + `8d160757`, PUSHED, CI GREEN

Four files. **1001 → 1007 tests** green, suite and deprecation gate both run.
Registration now has **five** layers and is deliberately over-protected: task 04
is what takes four of them away.

### DECIDED 2026-08-29 — the token arrives as a view kwarg, not as a read of `self.data`

Brian's call, over reading `self.data.get('cf-turnstile-response')` inside
`clean()`. Both spellings work; the argument that settled it is that
`RegisterForm` already refuses to take the request. It asks for `ip` because it
needs one datum, not a request object, and the token is the same shape of thing:

```
form = RegisterForm(request.POST,
                    ip=request.META.get('REMOTE_ADDR', '?'),
                    token=request.POST.get('cf-turnstile-response'))
```

The contact form reads its token off `self.request.POST` because it *is* handed
the request. The two callers differ because the forms differ, not by accident.

**The failure mode of the kwarg is loud**, which is the other half of the case: a
view that forgets it hands over `None`, the helper returns `NO_TOKEN`, and every
submission is refused with a line in two log files. Mutation 10 is exactly that
defect, and `test_success` fails on it.

### The page had to stop saying it has no CAPTCHA

`register.html` told the user *"Hey at least we don't have one of those annoying
CAPTCHA things, right?"* directly above where the widget now sits. One sentence
deleted; the rest of the apology paragraph is left for task 04 to rewrite, since
that is the task that removes the questions it apologises for.

**This is the only copy change**, and it is not a behaviour change: requirement
6's "change nothing else" is about the anti-spam layers.

### Eleven mutations, all caught

Each defect was introduced, the named test watched to fail, the file restored and
checked byte-identical by md5.

| # | Defect | Test | What it said |
|---|---|---|---|
| 1 | `TURNSTILE_SITE_KEY` dropped from the view context | `test_widget_is_rendered` | site key absent from the page |
| 2 | api.js `<script>` removed | `test_widget_is_rendered` | script URL absent |
| 3 | widget div added to `register2.html` | `test_the_widget_is_only_on_stage_one` | the widget reached stage three |
| 4 | REJECTED branch deleted | `test_a_rejected_token_blocks_registration` | registration proceeded |
| 5 | `self.token or 'x'` | `test_a_missing_token_costs_no_request` | "Expected 'post' to not have been called. Called 1 times." |
| 6 | UNAVAILABLE fails closed | `test_an_outage_fails_open` | no redirect to `register1` |
| 7 | `raise ValidationError` in place of `_validation_error` | `test_a_rejection_is_logged_for_the_instrument` | "the rejection is not greppable in the usual shape" |
| 8 | `source='register'` | `test_success` | expected call not found |
| 9 | honeypot `logger.critical` removed | `test_question2` | no CRITICAL record |
| 10 | the view stops passing `token=` | `test_success` | NO_TOKEN, no redirect |
| 11 | `remoteip` passed as `None` | `test_success` | `verify('a-token', None, ...)` |

**Mutation 5 is the one worth keeping.** Criterion 4 asks that a missing token
cost no HTTP request, and a test that mocks `verify()` cannot show that — it can
only show what the form did with the answer. That one test stands the class-wide
mock down and stubs `antispam.turnstile.requests.post` instead, so the real
helper runs and the assertion is about the wire. The contact form's equivalent
test does not: task 02 deferred the property to `antispam`'s own tests, which is
defensible and is one assertion weaker.

### Verified against the running stack, because the suite cannot see `LOGGING`

Test settings disable logging wholesale, so no unit test can say which file a
line lands in. One POST with no token, against the dev stack on `.env`'s test
keys, produced both lines:

```
turnstile.log:  INFO  Turnstile: no token (registration)
auth.log:       ERROR Accounts/registration [192.168.65.1]: Please verify you aren't a robot (None)
```

`turnstile.log` is task 05's file and needed no settings change to carry a second
source. The `auth.log` line is the shape requirement 5 asked for — the IP in
brackets, greppable beside every other registration failure this site has logged
since 2018.

### The order of the layers, and what a rejected submission costs

`clean()` runs after every `clean_<field>`, so a submission that fails the
honeypot or `question1` **still spends its token**: the challenge is verified,
the token is consumed, and the re-rendered widget issues a new one. That is the
contact form's behaviour too, watched in a browser during task 02, and it is
kept rather than optimised away — skipping verification when the form is already
invalid would make the log a measure of *valid* submissions rather than of
traffic, which is not what the instrument is for.

### What task 04 inherits

- **`RegistrationTest` mocks the helper once, in `setUp`**, with
  `self.verify.return_value` as the per-test dial. Twenty POSTs reach
  `accounts-register`; without a class-wide mock each unmocked one would reach
  Cloudflare from the suite.
- `self.post_vals` and one inline POST body carry `'cf-turnstile-response'`.
- The five layers are all still live, each with its own test and its own log
  line. Task 04 removes `question1`, `question3` and the `register1`/`register2`
  code flow. **`question2` — the hidden honeypot — stays**, requirement 2,
  including its CRITICAL log line. Registration ends task 04 with two layers,
  not one. **Done 2026-08-30, exactly as written** — two layers, and the
  honeypot's CRITICAL line is still asserted by `test_question2`, which the
  mutation battery's M5 confirmed still discriminates.

  **Measured 2026-08-29, on jaguar, because the argument for keeping it was
  running on reasoning alone.** The honeypot's CRITICAL line goes to the `auth`
  logger, so it is in `auth.log` — 2 MB x 5, reaching back over 19 months — not
  in `sg101.log`, which is where an earlier draft of this bullet put it and where
  it would have been unanswerable.

  `grep -c Honeypot auth.log*` over **2025-01-09 → 2026-08-29 (19.7 months)**:

  | | |
  |---|---|
  | honeypot hits | **161**, about **8.2/month** |
  | months with at least one | **19 of 20** (only 2025-08 empty) |
  | distinct source IPs | **111**; the busiest contributed 14 |
  | successful registrations in the same corpus | **1,038** |

  The 1,038 matches the denominator every other measurement in this step uses,
  which is the check that this is the same corpus and not a different window.

  **The layer is doing work: 8.2 submissions a month stopped against 1.4 spam
  accounts a month that got through.** Those two rates come from different
  windows — 1.4/month was read over `sg101.log`'s ~5 months, this over 19.7 — so
  the ratio is indicative, not a computed multiple.

  **What this does not establish**, and the reason the original sentence was
  wrong to state it as fact: nothing here says these are bots that never run
  JavaScript, nor that Turnstile would fail to catch them. A hidden field filled
  in is an automated form-filler *or* an aggressive password manager, and hits
  are not distinct actors — one IP accounts for 14. What is now measured is the
  volume this layer catches, not that Turnstile would miss it.

### The browser pass — DONE 2026-08-29, by Brian, and the log carries the proof

Chrome automation was unavailable again, so this ran by hand, against the dev
stack with the keys swapped in `.env` between instances. All four instances of
the widget's own JavaScript behaviour were watched — the same table task 02 used:

| Instance | Keys | Watched |
|---|---|---|
| solve and proceed | defaults | widget renders, resolves, complete form reaches the code page |
| **re-render** | defaults | an unrelated field error redisplays the form and **the widget reappears and re-solves** |
| server-side refusal | secret `2x…AA` | widget goes green, siteverify says no, form refuses |
| client-side block | sitekey `2x…AB` | the widget itself refuses and issues no token |

**`.env` held no Turnstile lines at all** — the site runs on task 01's test-key
defaults in `base.py`, which is what made this swappable at all. Each instance
was one added line and a `docker compose up -d web`; a plain `restart` re-uses
the old environment and silently tests nothing. `.env` was restored and verified
byte-identical afterwards.

**The re-render instance is the one the logs settle, and it could not be settled
any other way:**

```
18:42:16,824  auth   Accounts/registration [192.168.65.1]: A user with that username already exists. (Brian)
18:42:17,054  turn   Turnstile: passed (registration)
18:42:54,567  auth   Accounts/registration [192.168.65.1]: Please choose a password of 6 characters or more. (None)
18:42:54,767  turn   Turnstile: passed (registration)
18:43:09,236  turn   Turnstile: passed (registration)      <- no auth failure after it: stage one succeeded
```

**Three `passed` in a row and not one `rejected`.** Tokens are single-use, so a
widget that came back green on the re-rendered page *without* re-solving would
have sent a spent token on the next submit and logged `rejected (registration)`
— a rejection the user did not cause, and the defect task 02 flagged as
unverified. It is not there.

**The same five lines confirm the ordering** that was reasoned rather than
measured above: the field errors land at `:16.824`, the Turnstile line at
`:17.054`. Field cleans run first and `clean()` verifies afterwards, so an
already-invalid submission still spends its token.

### Two findings from the browser pass, neither of them this task's

**The registration code page hung on "Please wait for the registration code to
appear…"**, and it was not a hang: `/accounts/register/code/` returned 500 with
`ValueError: Another profiling tool is already active` from
django-debug-toolbar's `ProfilingPanel`. A concurrency race, not a code path —
`register1` fires its AJAX at `$(document).ready` alongside the page's other
loads, and `cProfile.enable()` refuses while another request is being profiled.
The same error appears four more times in the rotated log, all four at
`2026-08-28 13:02:47` across four parallel `/media/…` requests. **Dev only**:
`local.py:29` installs the toolbar under `DEBUG` and an importable package;
`production.py` never does. The endpoint itself answers `200 {"code":
"FAIL-123"}` to a direct request. Not fixed — disabling `ProfilingPanel` would
contradict the deliberate decision recorded at `local.py:60-69`; a reload wins
the race.

**`accounts/static/js/accounts_code.js` is a `$.get()` with no error handler**,
so *any* failure of that endpoint renders as an eternal "Please wait…" with no
way forward — identical in a browser to what a production 500 would look like,
and the user is stranded mid-registration. Pre-existing. **Not worth fixing:
task 04 requirement 6 deletes the whole mechanism** — the `register1`/`register2`
views, their routes and templates, `get_code`, and this JS file.

### Still owed

- ~~**The 1.4/month baseline re-read**~~ — **DONE 2026-08-30 from the database**,
  which is where it should always have been read; see *the spam baseline, read
  from the database*. This bullet's own point stood: nothing shipped here reaches
  production until the Step 21 cutover.

### Files

`accounts/forms.py`, `accounts/views.py`,
`sg101/templates/accounts/register.html`, `accounts/tests/test_views.py`.

## Step 17 task 05 — Turnstile gets its own file, and the invisible submissions become visible — DONE 2026-08-29, `634d93f3` + `f9d4de7f`, PUSHED, CI GREEN

Six files. **994 → 1001 tests** green, suite and deprecation gate both run.
`logs/turnstile.log` exists and carries all four outcomes; `sg101.log` carries
none of them.

**One qualifier, measured 2026-08-29 during task 03's browser pass**: *none of
the outcomes* is the claim, and it holds — but in **dev** `sg101.log` still gets
a `DEBUG … "POST /turnstile/v0/siteverify HTTP/1.1" 200` line per verification.
That is urllib3, not this helper, and it lands there because `local.py`'s root
logger runs at DEBUG. `production.py`'s root is INFO, so it does not happen on
the host the retention arithmetic was about.

### DECIDED 2026-08-29 — the fourth outcome, not a second entry point

Brian's call, over shape A (`turnstile.no_token(source)` beside the form's own
guard).

**The deciding argument was task 03, not elegance.** Under shape A the
"never call Cloudflare without a token" property is a convention each calling
form re-implements, and forgetting it is silent — the form still works, it just
spends a request on every bot that never loaded the widget. Under shape B the
property belongs to `verify()` and is proven once for every caller that will
ever exist. Registration is the second caller and the more heavily targeted
form.

**Two costs were accepted with the decision and both are discharged here.**

1. *The no-HTTP-request guarantee moved.* It was a property of
   `ContactForm.clean()` and is now a property of `verify()`. The visible sign
   is `contact/tests/test_views.py`, where `verify.assert_not_called()` became
   `verify.assert_called_once()` plus a falsy-argument check. **That is a
   deliberate weakening at the form level**, compensated by two helper-level
   tests that no form can bypass. Recorded so it is not later read as an
   accidental loss.
2. *`TurnstileOutcome` stopped meaning "what Cloudflare said".* Its docstring
   said exactly that and is rewritten: four values, of which the first two
   describe something Cloudflare said and the other two say why it did not.

### The blind spot had a wire cost nobody had counted

Writing the failing test first exposed something the task file did not predict.
Before the change, `verify(None)` did not merely fail to log — **it posted
`{'response': None}` to Cloudflare and waited for the answer.** The form's guard
was what kept that from happening in production, so the defect was latent rather
than live, but it was one careless caller away from real traffic. The RED run
says so in the mock's own words:

```
AssertionError: Expected 'post' to not have been called. Called 1 times.
Calls: [call('https://challenges.cloudflare.com/turnstile/v0/siteverify',
             data={'secret': ..., 'response': None}, timeout=20)]
```

This is the argument for shape B arriving as evidence rather than as reasoning:
the invariant was already being relied on and was already not held by the helper.

### Eight mutations, all caught

Per the standing rule that a passing test proves nothing until watched to fail.
All seven new tests were written before the implementation and watched to fail;
the battery below re-checks that each fails for the *right* reason, since three
of the seven first failed only with `AttributeError: NO_TOKEN`, which proves the
enum member is missing and nothing else.

| # | Mutation | Test that caught it |
|---|---|---|
| M1 | no-token returns `REJECTED` | `test_none_is_no_token` |
| M2 | `if not token` narrowed to `if token is None` | `test_empty_string_is_no_token` |
| M3 | the no-token line is not logged | `test_no_token_logs_at_info_naming_the_form` |
| M4 | the `source` suffix is dropped | `test_no_token_logs_at_info_naming_the_form` |
| M5 | no-token logged at WARNING | `test_no_token_logs_at_info_naming_the_form` |
| M6 | form gives no-token the *rejected* message | `test_no_captcha_response` |
| M7 | the guard comes back into the form | `test_no_captcha_response` |
| M8 | the early return is deleted entirely | `test_no_token_makes_no_request` |

**M8 was added after the first battery of seven, which had a hole:** nothing in
it forced `test_no_token_makes_no_request` to fail, so the test carrying
criterion 1's "no HTTP request may be made" was the one test not yet shown to
discriminate. M2 is the same shape of care — `request.POST.get()` returns `''`
for a present-but-empty field, and a truthiness test narrowed to `is None` would
pass every other test in the file.

**M7 was fixed rather than accepted.** It was caught, but by
`AttributeError: 'NoneType' object has no attribute 'args'` rather than by an
assertion — a regression would have read as a broken test. Asserting the call
before reading its arguments makes it fail as a failure.

### Verified against the running stack, because the suite cannot see `LOGGING`

Four `verify()` calls through the real docker settings, then both files read:

```
2026-08-29 15:37:34,122 INFO    Turnstile: no token (stack check)
2026-08-29 15:37:34,187 INFO    Turnstile: passed (stack check)
2026-08-29 15:37:34,324 INFO    Turnstile: rejected (stack check) ['invalid-input-response']
2026-08-29 15:37:34,326 WARNING Turnstile: unavailable (stack check) -- request failed: ...
```

and one real POST through the view, which is what proves the form path rather
than the helper in isolation:

```
2026-08-29 15:37:51,370 INFO Turnstile: no token (contact form)
```

**`sg101.log` received no Turnstile line.** It did receive two `urllib3` DEBUG
lines about the POSTs to `challenges.cloudflare.com` — a different logger, not
this one, and **local/docker-only**: production's root logger is at INFO, which
drops them. Named here because a future reader greps `sg101.log` for
`turnstile`, finds two lines, and needs to know they are not these.

**The no-token case produced no `urllib3` line at all**, which corroborates
criterion 1 outside the mock: nothing reached the network.

### The WARNING moves too, and the cost is bounded by where monitoring is going

DECIDED 2026-08-29, Brian's call. `propagate: False` is per-logger, not
per-level, so the `unavailable` WARNING leaves `sg101.log` along with the INFO
volume. **That line is the only record that a check did not happen**, and
`sg101.log` is where an incident is debugged first — the exact reasoning that
made the `email` logger `propagate: True`.

**Brian's answer, and it is the one that settles it: file placement is a
human-grep concern, and monitoring is expected to become a dashboard that reads
every log.** An aggregator does not care which file a line is in, so the loss is
real only for as long as the answer to "was there an outage" is a person running
`grep`. The retention argument that motivated the split is unaffected by any of
that — it is about bytes per day in `sg101.log`, not about who reads it.

The alternative is recorded so the trade is not re-litigated blind: a second
handler on `sg101.log` filtered to WARNING would put two `RotatingFileHandler`
instances on one file, which can rotate out from under each other and lose
records, and would complicate the settings-module cleanup Step 19 has queued.
**Until an aggregator exists, `turnstile.log` is the only place a Cloudflare
outage appears** — worth knowing during the cutover window, and not worth
engineering around.

### Files

`antispam/turnstile.py`, `antispam/tests/test_turnstile.py`,
`contact/forms.py`, `contact/tests/test_views.py`,
`sg101/settings/production.py`, `sg101/settings/local.py`.

The two settings modules differ only in handler level (`INFO` / `DEBUG`), which
is how they already differ for `auth`, `search` and `email`.

## Step 17 task 04 — registration collapses to one page — DONE 2026-08-30, `f4144435`, PUSHED

Nine files. **1007 → 1006 tests** green, suite and deprecation gate both run,
`check` clean. Registration is now `register` → `thanks` plus the emailed
confirmation, with Turnstile and one invisible honeypot.

Removed: `question1` (the `101` question), `question3` (the visible honeypot),
`RegisterCodeForm`, `CODE_WORD_CHOICES`, `generate_registration_code`, views
`register1` / `register2` / `get_code`, routes `accounts-register1` /
`accounts-register2` / `accounts-code`, templates `register1.html` /
`register2.html`, and `accounts/static/js/accounts_code.js`. Kept: `question2`
and its CRITICAL line, and `register_confirm` untouched.

### Three findings that changed the task as written

**1. Requirement 8's premise was wrong, and checking cost one `git log`.** The
task file says `@log_auth_failures('Register')` "currently decorates
`register2`". It decorated **both** stages, and has decorated `register` since
`3eef6754` (2013-09-01). So the deliberate decision it asked for is *keep what
stage one already has*, and deleting `register2` removed a duplicate rather than
the only instance. **What changes in the auth log:** the ~214 code-mismatch
failures the layer measurement counted stop appearing as `Register failure`
lines, because the layer that produced them is gone. fail2ban still sees every
stage-one failure, which is the property that matters to it.

**2. `tools/email_smoke.py` was an unlisted fifth caller.** Its
`registration_confirmation()` producer fabricated a `reg_info` session and drove
`RegisterCodeForm.save()`. The task's file list named four files and did not
include it; requirement 9's grep is what surfaced it. Repointed at
`RegisterForm` and **run** — `--only registration`, 4/4 checks passed — rather
than left to a parse check.

**3. `RegisterForm.save()` lost its `request` parameter.** Everything the moved
work uses is `cleaned_data` plus `self.ip`, both already on the form. That also
made the smoke-tool producer match the shape `forgot_username()` already used
for `ForgotUsernameForm`, so the two producers now read the same way.

### The page had to stop apologising for questions it no longer asks

Requirement 7 asked only for the two field blocks. Two other things on
`register.html` became false the moment they went, both user-visible, and
**Brian chose to fix both**:

- the `warning callout` — *"We are really sorry about all the crazy questions in
  the registration form"* — had nothing left to apologise for. Turnstile is a
  checkbox and the honeypot is invisible. Deleted.
- the submit button read **Next Step →**. There is no next step. Now **Register**.

Same class as task 03's *"the page had to stop saying it has no CAPTCHA"*: copy
that a change falsifies is part of the change.

### Ten mutations, all caught

Tests followed the code here, so the battery is what makes them evidence. Each
defect was applied, the class run, the file restored, and the restored file
confirmed byte-identical by sha256.

| | Mutation | Caught by |
|---|---|---|
| M1 | an old route resolves again | `test_the_old_routes_are_gone` |
| M2 | the success log line is reworded | `test_the_success_line_keeps_its_shape` |
| M3 | the redirect goes somewhere else | `test_success` |
| M4 | the confirmation email is not sent | `test_success` |
| M5 | the honeypot stops discriminating | `test_question2` |
| M6 | a rejected token is allowed through | `test_a_rejected_token_blocks_registration` |
| M7 | a missing token is allowed through | `test_a_missing_token_costs_no_request` |
| M8 | an outage fails closed | `test_an_outage_fails_open` |
| M9 | `verify()` called with another `source` | `test_success` |
| M10 | the pending user is created under another name | `test_success` |

M10 is the one that earns its place: M3 and M4 prove the redirect and the mail,
but only M10 forces the assertion that the row created is the row the form was
asked for.

### Verified against the running stack, because the suite cannot see `LOGGING`

The suite asserts the success line through `assertLogs`; what `STATUS.md`'s
counting greps is a file written through the real `LOGGING` config, which the
test settings disable. So the whole flow was walked over HTTP against the dev
stack — real routing, real form, a real Turnstile call on the always-passes test
secret, and the real Celery worker rather than `CELERY_TASK_ALWAYS_EAGER`:

```
1. GET  register page          : widget present
2. POST registration           : 302 -> /accounts/register/thanks/
3. PendingUser created         : walkthrough_u1 <walkthrough_u1@example.com>
5. GET  activation link        : account active=True, pending rows left=0
6. POST login                  : 302 -> /profile/me/
7. old routes /1/ /2/ /code/   : 404, 404, 404
```

and the three log files then read:

```
auth.log      Accounts/registration conf. email sent to walkthrough_u1@example.com
              for user walkthrough_u1; IP = 127.0.0.1
turnstile.log Turnstile: passed (registration)
email.log     category=registration to=walkthrough_u1@example.com outcome=sent
```

**That first line is requirement 4 discharged against the instrument rather than
against a mock.** It is the success signal the 1,038-registration denominator is
built on, and it is byte-compatible. The scratch account was deleted afterwards.

### The browser pass — DONE 2026-08-30, by Brian

Chrome automation was unavailable again. **The four-instance key sweep was
deliberately not repeated:** the widget `div` and the script tag are
byte-identical after this task — the template diff is three removals and the
button text — so nothing about the widget's own JavaScript changed, and task
03's sweep still covers it.

| Checked | Result |
|---|---|
| layout after three blocks came out of the grid | fine |
| the honeypot, now the only question left | not visible |
| re-render, via a reused username | **the widget came back solved** |
| the button | reads *Register* |
| a full successful registration | no problems |

**The re-render instance was worth repeating even though the sweep was not**,
because what *triggers* a re-render changed: `question1` and `question3` errors
are gone as causes, so the path was re-entered through a duplicate username.

**The logs settle it, as they did for task 03**, and this is the pass read back
out of the instrument rather than reported from the screen:

```
15:20:06,528  auth   Accounts/registration [192.168.65.1]: A user with that username already exists. (Brian)
15:20:06,722  turn   Turnstile: passed (registration)
15:20:06,743  auth   Register failure from [192.168.65.1] for Brian
15:22:36,957  turn   Turnstile: passed (registration)
15:22:37,082  auth   Accounts/registration conf. email sent to xy@e.com for user tester; IP = 192.168.65.1
```

**Two `passed`, no `rejected`, and the first one is what makes the second mean
anything.** The field error at `:06,528` lands *before* the Turnstile line at
`:06,722` — field cleans run first and `clean()` verifies afterwards — so the
rejected submission **spent its token**. Tokens are single-use, so the `passed`
at `15:22:36` cannot be that same token: the widget issued a fresh one, which is
only possible if it re-solved on the re-rendered page. A widget that came back
green without re-solving would have logged `rejected (registration)` with
`timeout-or-duplicate`. Task 02's single-use defect stays closed for this form,
now on this task's own evidence.

The `tester` / `xy@e.com` `PendingUser` row from that registration is still on
the dev stack unactivated, and expires 24 hours after `2026-08-30 20:22`.

### A ten-year-old defect in the block Brian asked about, not this task's

Reviewing the checkbox layout surfaced that **all three agreement labels are
dead**. The template writes `for="form.agree_age.id_for_label"` — the `{{ }}`
are missing, so the attribute renders as that literal string while the inputs
carry `id_agree_age`, `id_agree_tos`, `id_agree_privacy`:

```html
<input type="checkbox" name="agree_age" required id="id_agree_age">
<label for="form.agree_age.id_for_label">I certify that I am over the age of 13</label>
```

Clicking any of the three label texts does nothing; only the box itself
responds. Introduced **2016-07-12 in `2e7e8f79`** ("Convert registration views
to V3 design") and present nowhere else in the templates — the honeypot's label
two rows below renders `for="id_question2"` correctly.

**It is on this step's theme and cannot be measured from the logs.** Three
*required* checkboxes with unclickable labels is exactly the registration
friction Step 17 exists to remove. But the `agree_*` fields raise Django's own
`BooleanField` required error rather than going through `_validation_error()`,
so no auth-log line names them and the layer measurement never counted them. How
many people this cost is **not recoverable** — recorded as a defect found, not
as a quantity.

**Not fixed here.** It is unrelated to retiring the code flow, and folding it
into a 329-deletion diff would hide it.

### Still owed

- ~~**The agreement labels**~~ — **DONE 2026-08-30**, with the stacking, in its
  own section below.
- ~~**The 1.4/month baseline re-read**~~ — **DONE 2026-08-30**, from
  `UserProfile.status` rather than from any log. Nothing here reaches production
  before Step 21.

### Files

`accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`,
`accounts/tests/test_views.py`, `sg101/templates/accounts/register.html`,
`tools/email_smoke.py`, and three deletions:
`sg101/templates/accounts/register1.html`, `register2.html`,
`accounts/static/js/accounts_code.js`.

## Step 17 — Cloudflare dated, and 35% of the layer measurement had no client IPs — 2026-08-30

**Brian's hypothesis, that the spam cliff coincided with putting Cloudflare in
front, and his recollection that `mod_remoteip` came "some time later".** Both
are confirmed, and chasing the gap between them found a defect in the
measurement that drove this entire step.

### The dates, from two instruments that share nothing

Before `mod_remoteip`, Apache recorded Cloudflare's *edge* IP as the client, so
the corpus dates the change itself. Every bracketed IP in `auth.log` classified
against Cloudflare's published ranges:

```
2025-06-18   all real client IPs
2025-06-19   Cloudflare edge IPs appear      cf=38   real=110
2025-06-20                                   cf=203  real=53
2025-06-21   100% Cloudflare edge            cf=265  real=0
   ...        (52 days)
2025-08-10   mod_remoteip enabled            cf=37   real=30
2025-08-11   all real client IPs again       cf=0    real=64
```

**2025-06-19 is the day Brian's Cloudflare account was created**, read off the
dashboard and volunteered independently of this measurement. `mod_remoteip`'s
symlinks in `mods-enabled` and `conf-enabled` are stamped **2025-08-10** 13:47
and 14:00. The logs, the account page and the filesystem agree.

### The consequence: a 52-day hole where IP identity means nothing

For 2025-06-19 → 2025-08-10 every `REMOTE_ADDR` the site recorded was one of a
small pool of Cloudflare edge addresses. Unrelated actors collapse onto the same
"IP". **954 of 2,700 registration lines — 35% of the corpus — fall inside it**,
including the largest spam wave on record.

**That corpus is what the layer decision table was computed from**, and its
discriminator is *"did this IP ever complete a registration afterwards"* —
precisely the quantity a shared address destroys. Contamination by layer:

| Layer | Hits inside the window |
|---|---|
| `question1`, removed | **221 / 439 — 50%** |
| `question3`, removed | **110 / 276 — 40%** |
| registration code | 67 / 216 — 31% |
| `question2`, kept | 38 / 161 — 24% |

### Recomputed with the window excluded

The method was first validated by reproducing the recorded numbers from the
whole corpus — 8 / 27 / 35 / 68 / 76% against the recorded 8 / 27 / 35 / 68 /
77%, so this is the same instrument and not a second one that happens to agree.

| Layer | IPs | Later succeeded | As recorded |
|---|---|---|---|
| `question2` hidden honeypot | 73 | **0%** | 8% |
| `question3` visible honeypot | 106 | **12%** | 27% |
| `question1` the 101 question | 131 | **21%** | 35% |
| *(control)* password mismatch | 68 | 78% | 68% |
| registration code mismatch | 79 | **89%** | 76% |

**The ordering is unchanged, which is exactly what the original caveat said was
the robust part.** That caveat — "the robust part is the *ordering*, not the
absolute percentages" — is vindicated rather than embarrassed.

**The magnitudes move a long way, and not all in the same direction:**

- **The honeypot is a cleaner signal than recorded** — **0 of 73** IPs that
  filled it ever registered successfully, against 8%. Keeping it was right, more
  strongly than the record claimed.
- **The code step is more purely human than recorded** — 89% against 76%, now
  well clear of the 78% control. Removing it was right, more strongly than the
  record claimed.
- **But `question1` and `question3` were more bot-catching than recorded** —
  21% and 12%, not 35% and 27%. The record read those as "~98 real people
  tripped" and "~55 real people tripped"; outside the window it is 28 of 131 and
  13 of 106. **The friction those two layers imposed was overstated by roughly
  3x, which is the half of the decision table that argued for removing them.**

**The removals still stand, on arguments that never depended on these
percentages:** `question1`'s answer is a fixed constant and one line of code for
anything targeting this site by name; `question3` was visible, so it confused
real people by construction; and Turnstile now covers the classes both were
catching. **What is corrected is the evidence base, not the decision** — and the
distinction matters, because the record presented those percentages as the
measurement that settled it.

**Why excluding the window is correct rather than convenient:** inside it, IP
identity does not exist, so those events cannot contribute to an IP-keyed
discriminator at all. They are not being discarded for being inconvenient; they
carry no signal for this question. The cost is that the excluded period contains
the July 2025 wave, so the remaining population is smaller and differently
composed.

### And it answers the spam-cliff question in the negative

**Cloudflare was fully in front for the whole of July 2025** — 100% edge IPs,
`real=0` every day — which is the month **244 spam accounts registered**, the
worst in the corpus. The proxy was live and did not stop it.

So the cliff is not "Cloudflare went in front". Whatever ended the wave in
August 2025 was not the proxy's arrival and was not a registration code change —
`accounts/` and `antispam/` have no commits between 2025-04 and 2026-01.

**IDENTIFIED 2026-08-30 from the Cloudflare audit log, and it is not a
Cloudflare feature — it is fail2ban.** Brian exported 2025-08-04 → 2025-09-30,
229 events:

```
2025-08-10 13:47 CDT   mod_remoteip enabled            (jaguar filesystem)
2025-08-10 15:34 CDT   IP list "block_list" created    "List of IP addresses
                                                        to block", num_items 0
2025-08-10 15:38 CDT   WAF rule created, phase http_request_firewall_custom
                         action: block
                         expression: (ip.src in $block_list)
2025-08-12 onward      111 further list operations, kind append/delete,
                       "bulk operation accepted" -- i.e. automated
2025-08-13, 08-14      API tokens created: "Fail2ban", "Fail2ban attempt 2"
```

**fail2ban on jaguar pushes bans into a Cloudflare IP list and a WAF rule drops
them at the edge.** Built in one afternoon, 1h45m after `mod_remoteip`.

**The ordering is the mechanism, not a coincidence.** Before 2025-08-10 fail2ban
was blind: jaguar saw only Cloudflare edge addresses, so there were no client
IPs to ban, and banning what it *could* see would have banned Cloudflare.
`mod_remoteip` restored real client IPs, which is what made IP banning
meaningful — and the block list was built the same afternoon. **The 52-day
window was not merely a logging defect: for its duration the site's IP-based
defences could not work at all.**

**This also corrects an earlier sentence in this section.** "Registration
attempts reaching Django never fell" was too strong. July's 886 fell back to
~135 and held at the pre-wave baseline of ~100/month, while spam *successes*
fell far below their own prior baseline — 14.5/month to ~1.25. That is the
signature of banning repeat offenders: the long tail of one-off attempts
continues, the persistent sources stop getting through.

**Caveat, and it is why this reads "identified" rather than "proved".** The
audit log records configuration, not blocked requests. Cloudflare Security
Events would show actual blocks, but that retention is short on this plan and
August 2025 is long gone. This is a precisely dated, mechanistically coherent
correlation, not a measured causal chain.

### The consequence for Step 21, which is the part that matters going forward

**The ~1.25/month floor is held by fail2ban plus edge blocking, not by the
registration form.** Nothing in `accounts/` is doing this work. Three
consequences:

1. **The blocking has to be rebuilt on the new VM, and it will not come along by
   itself.** fail2ban's jails and the Cloudflare API credentials are host
   configuration, not repo content — nothing in this repository would recreate
   them.
2. **It has to be rebuilt in the right order, and the 52-day window is the
   lesson.** The new VM also sits behind Cloudflare, so **the real-client-IP
   rewrite must be working before fail2ban is enabled**, or the new host repeats
   2025's mistake and bans the edge. Step 20 already carries that rewrite
   (Apache `mod_remoteip`, the same 15 IPv4 and 7 IPv6 ranges) as its own item;
   this makes it a **prerequisite of the blocking** rather than an independent
   task.
3. **Turnstile will be judged against a floor fail2ban is holding down.** If the
   blocking is not carried over, spam rises at cutover for reasons that have
   nothing to do with the registration flow — and that rise would read as
   Turnstile failing. See *the spam baseline, read from the database*.

## Step 17 — the spam baseline, read from the database — 2026-08-30

**Prompted by Brian asking why a baseline read was owed at all**, which turned
out to be the right question: the answer was recorded against the wrong file and
the deadline did not exist.

### The instrument, and why it beats both logs

`antispam.utils.deactivate_spammer()` sets `UserProfile.status = STA_SPAMMER`
(4) and assigns `status_date` explicitly — `auto_now_add` binds only on insert,
so the assignment survives the update. `User.date_joined` gives the registration
date. So every spam deactivation the site has ever made is in the database with
both dates, **1,601 profiles, `status_date` spanning 2011-02-28 → 2026-07-24.**

Against that, `sg101.log` offers 7 events over 5 months and `auth.log` offers
registrations only. The logs were never the limiting instrument; nobody had
looked at the durable one.

### The read, monthly, since 2024-09

`flagged` counts by `status_date`; `spam-regs` counts the same accounts by
`date_joined`; `all-regs` is every registration in the month.

```
month     flagged  spam-regs  all-regs        month     flagged  spam-regs  all-regs
2024-09       37        37        69          2025-09       10        10        34
2024-10       74        79       101          2025-10        4         6        31
2024-11       67        61        93          2025-11       12        11        41
2024-12        3         5        27          2025-12        5         4        28
2025-01       12        10        54          2026-01        1         1        32
2025-02       10        11        42          2026-02        2         2        26
2025-03       12        12        36          2026-03        1         1        21
2025-04       16        16        34          2026-04        3         2        27
2025-05       25        27        63          2026-05        2         2        36
2025-06       13        11        45          2026-06        1         1        27
2025-07      245       244       298          2026-07        1         1        25
2025-08       25        24        54
```

**The 1.4/month figure is corroborated by an independent instrument.** 2026-01
through 2026-07 reads 1, 2, 1, 3, 2, 1, 1 — **11 over 7 months, ~1.6/month**,
against ~1.4/month derived from an entirely different source over a different
window. Two instruments that share no code agree.

### What the 3.7-month window could not show, and it matters more than the number

**The baseline sits at the bottom of a cliff.** 2025-07 flagged **245** spam
registrations; 2026 runs 1–3 a month. Total registrations fell too — ~100/month
in late 2024 to ~25/month now — but nothing like as far: **the spam share went
from 78% of registrations in 2024-10 to about 4% now.**

**Nothing in the registration code explains it.** `accounts/` and `antispam/`
have no commits between 2025-04 and 2026-01; the repo activity in that window is
`robots.txt`, bot disallow rules, wiki links and tests. **The cause is not
identified and is not guessed at here.**

**Two consequences for Step 17, and they cut against the plan as written:**

1. **The effect may be undetectable.** At ~1.6/month, roughly 19 events a year,
   a reduction from Turnstile needs a long observation window before it is
   distinguishable from noise. "Did it work" was always going to be judged
   against this number; the number is now known to be too small to answer the
   question quickly.
2. **A rate that fell for reasons outside the flow can rise for the same
   reasons.** Whatever ended the 2025-07 wave was not a registration change, so
   the current quiet is not evidence the current layers are strong — and a
   post-cutover rise would not be evidence Turnstile failed.

**Right-censoring, stated because it is easy to miss:** recent registrations have
had less time to be caught and flagged, so the newest months understate. The last
flag in the corpus is 2026-07-24, which is why 2026-08 has no row rather than a
zero row.

### The read is done; what is still owed is smaller

The *before* number is now measured from a durable source and needs no
re-reading. What remains is the *after*, which cannot exist until the Step 21
cutover puts Turnstile in front of real traffic — and, on the evidence above,
will take a long time to say anything.

## Step 17 — `question2` becomes `question` — DONE 2026-08-30, `85edcd34`, PUSHED

Three files, **1007 tests** green, suite and deprecation gate both run. The `2`
indexed a sequence whose other members task 04 deleted.

### Why not `honeypot`, and why not `secret_question`

**`honeypot` names the trap in the HTML.** That argument is weaker than it
sounds — the field already carries `style="display: none;"` inline, so anything
inspecting the markup can spot it — but at equal clarity there is no reason to
choose the self-describing name.

**`secret_question` was the proposal and was rejected on maintainer
confusion.** "Secret question" is the established term for account-recovery
security questions, and on a *registration* form a maintainer meeting that
field would reasonably go looking for where the answer is stored. Same
objection Brian raised to `website`, and stronger: `question2` is meaningless,
`secret_question` points at a different feature that exists.

**`question` is accurate and keeps the baseline comparable.** It is now
literally the only question on the form. It also stays in the same family as
`question2`, which matters because **a rename is unmeasurable against the
8.2/month honeypot baseline** — a form-filler sees the wire name, and Turnstile
already confounds that rate. A name from the same family keeps a filler's
behaviour as close to the measured condition as a rename allows. The field name
carries no meaning on its own; the docstring and the `Honeypot filled` log line
do, which is where the meaning has always been.

### `Wrong answer #2` becomes `Wrong answer`, and the cross-check survives it

The `#2` was the same stale index. Dropping it rather than rewording the line
is what preserves continuity: **`grep 'Wrong answer' auth.log*` now matches both
the historical `Wrong answer #2` lines and every new one**, so the cross-check
spans the rename instead of being split by it. Verified unique — no other
message in the codebase begins with those words, and neither retired layer's
message did (`question1` logged "Incorrect answer to our anti-spam question",
`question3` "Oops, that should be blank").

**The `Honeypot filled` CRITICAL line is untouched**, so `grep -c Honeypot` —
the counter every honeypot measurement uses — is unaffected in either
direction.

### The test now asserts both lines, and four mutations say it discriminates

`test_question2` is now `test_the_honeypot_is_caught_and_logged` and captures at
`ERROR` rather than `CRITICAL`, so it sees the pair rather than half of it.
**Asserting both is the point:** a filled honeypot is deliberately logged twice,
and it is the pair that lets a count of hits be checked against a count of
failures. A silent drop of either line leaves both counts looking healthy while
disagreeing — which is the shape of the miscount corrected on 2026-08-27.

| | Mutation | |
|---|---|---|
| M1 | the honeypot stops discriminating | caught |
| M2 | the CRITICAL hit line is dropped | caught |
| M3 | the paired failure line is reworded | caught |
| M4 | the field name drifts from the template | caught |

**M4 is the one the rename made necessary** — form and template agreeing on a
field name is a property nothing checked before, and a rename is exactly when
it breaks.

### Verified on the running stack

One POST with the field filled, through real routing and the real logging
config:

```
15:55:39,409  CRITICAL  Accounts/registration: Honeypot filled [127.0.0.1]
15:55:39,409  ERROR     Accounts/registration [127.0.0.1]: Wrong answer (a bot filled this)
15:55:39,486  ERROR     Register failure from [127.0.0.1] for honeypot_probe
```

No `PendingUser` created, form refused, rendered field reads
`name="question"`.

**Earlier sections in this file name `question2` and `test_question2`.** They
are the record of what was true when written and are left alone; this section
is where the rename lives.

## Step 17 — the agreement labels, dead since 2016, and the form's layout with them — DONE 2026-08-30, `816a4312`, PUSHED

Five files, **1006 → 1007 tests** green, suite and deprecation gate both run. The
defect and how it was found are recorded in task 04's section above; this is
what was done about it.

```
-  {{ form.agree_age }}<label for="form.agree_age.id_for_label">...
+  <div>{{ form.agree_age }}<label for="{{ form.agree_age.id_for_label }}">...</div>
```

**The `for` fix and the stacking are the same three lines, which is why they are
one change.** Nothing else on the page shares the fault: every other field in
the template already writes `for="{{ ... }}"`.

### Why a wrapping `div` rather than CSS

The three sat inline because of one Foundation rule:

```css
[type=checkbox]+label,[type=radio]+label{display:inline-block;...;margin-right:1rem}
```

**That rule needs the label to be the input's adjacent sibling**, so wrapping
each *pair* in a block element stacks them while leaving the rule — and its
`.5rem` gap between box and text — still applying. Overriding the rule instead
would have meant new CSS at equal specificity loaded after Foundation, which is
a worse trade for three checkboxes. The label keeps its explicit `for` rather
than being wrapped around the input, for the same reason: wrapping breaks the
sibling adjacency the rule is written against.

### The test asserts the association, not the layout

`test_the_agreement_labels_name_their_own_boxes` regexes each input's `id`
against the `for` of the label beside it, tolerant of whitespace and strict on
the pairing. **Three mutations, all caught:**

| | Mutation | |
|---|---|---|
| M1 | the 2016 defect restored verbatim | caught |
| M2 | a label points at a different box | caught |
| M3 | the label separated from its input | caught |

M1 is the one that matters — the historical defect, put back exactly as it was,
now fails.

**The stacking is deliberately not tested.** It is presentation, it is visible
in a browser and nowhere else, and a test asserting a `div` wrapper would fix
the markup rather than the property. Brian eyeballs it; the suite guards the
part that has a right answer.

**This is the shape of defect the suite was never going to find on its own.** A
label whose `for` names nothing renders without error, validates as HTML, and
looks correct in a screenshot. It took someone asking about the layout.

### The submit button stops being pulled to the right

```
-  <div class="clearfix"><button class="primary button float-right">Register</button></div>
+  <div class="row"><div class="columns"><button class="primary button">Register</button></div></div>
```

Brian's call, looking at the simplified page: with the form down to one screen
the far-right button reads as detached, and directly under the widget is where
the eye already is.

**The `row`/`columns` wrapper is not decoration — it is what makes "directly
under" true.** `.columns` carries `padding-left: .625rem`, so a button left in
its `clearfix` div would sit that much left of the Turnstile widget, which is
inside `.columns`. Reusing the widget's own wrapper aligns the two left edges
exactly. The `clearfix` went with the float: it existed only to contain it, and
no float remains anywhere in the form.

Untested, for the same reason the stacking is: it is presentation, and there is
no right answer a test could hold it to.

### The widget needed a bottom margin, and that meant touching the built CSS

`.cf-turnstile` is not a form control, so it inherits none of the
`margin: 0 0 1rem` Foundation gives inputs, and sat directly on the button once
the button stopped floating away from it. The rule is one line:

```scss
.cf-turnstile { margin-bottom: 1rem; }
```

**1rem is not a taste choice** — it is the same bottom margin every text input
on the form already carries, so the widget now sits in the rhythm the rest of
the fields established.

**Written twice, deliberately, following `39aceca4`'s procedure.** The v3
stylesheet is built from `sg101/scss/` by a gulp-sass toolchain that does not
run on a current Node, and the build product is committed. So the rule goes in
`_sg101.scss`, which is the source of truth, **and** the compiled form is
appended by hand to `main.min.css` at the position a rebuild would place it —
last, since it is last in the source. Verified served by the dev stack rather
than assumed from the file.

**A rebuild should produce the same bytes; if it ever does not, the SCSS
wins.** That is `39aceca4`'s rule, restated here only because this is the second
time it has been applied and a procedure used twice is worth being findable.

## Step 17 task 02 — the contact form on Turnstile, and reCAPTCHA is gone — DONE 2026-08-28, `e8f8f47d` + `1dd06d52`, PUSHED, CI GREEN

Nine files. **989 → 994 tests** green, suite and deprecation gate both run.
`grep -ri recaptcha` now matches only `.agents/`, which is what requirement 7
asked for. **The site's CAPTCHA is Cloudflare Turnstile as of this task**;
registration still runs its own question-and-honeypot flow and gets the widget
in task 03.

### The old assertion was watched to fail, and it failed on three things at once

The task file predicted `contact/tests/test_views.py:61` would break on the
helper's timeout. Run against the swapped form, before repairing it:

```
Expected: post('https://www.google.com/recaptcha/api/siteverify',
               data={'secret': '<the live reCAPTCHA secret>', 'response': ..., 'remoteip': '127.0.0.1'})
  Actual: post('https://challenges.cloudflare.com/turnstile/v0/siteverify',
               data={'secret': '1x0000...AA', 'response': ..., 'remoteip': '127.0.0.1'}, timeout=20)
```

URL, secret **and** `timeout=20` — the assertion sees the whole call shape, not
just that a call happened. Reaching it took one adjustment worth recording: the
first run errored at `@patch('contact.forms.requests.post')` instead, because
the swap removes that attribute entirely. **A patch target that no longer
exists errors before the assertion it guards ever runs**, so the test would
have gone green-to-error rather than green-to-failure, and the demonstration
the task wanted would have been lost. Retargeting the patch at
`antispam.turnstile.requests.post` let the call actually happen and the
assertion actually fail.

### DECIDED 2026-08-28 — `verify()` takes a `source` label

Brian's call, over a second form-level log line or an anonymous one.

`contact/forms.py:52` has logged one line per verification since 2018, and it
is the *only* instrument this site has for challenge volume — the 225
assessments over 149 days that decided this step's rationale were read from it,
and the Step 17 register still owes a re-read of the 1.4/month spam baseline.
Task 01's helper logged one line per verification but named no caller, so the
moment task 03 adds registration the two callers become indistinguishable in
`sg101.log`.

`verify(token, remoteip=None, source=None)` renders the label as a suffix,
absent when unnamed. **One line per verification, and it says which form.**
The helper stays policy-neutral — a caller's name is provenance, not policy.

### Both log lines were read out of the real file, not asserted in a mock

Two live submits against Cloudflare's actual siteverify endpoint, one per test
secret, then `grep Turnstile sg101/logs/sg101.log*`:

```
2026-08-28 12:56:30,132 INFO Turnstile: passed (contact form)
2026-08-28 12:56:30,357 INFO Turnstile: rejected (contact form) ['invalid-input-response']
```

`invalid-input-response` is Cloudflare's own code for the always-fails secret —
the first `error-codes` value this project has ever seen populated, against 225
reCAPTCHA verifications that never populated one. The lines land in `sg101.log`
because `antispam.turnstile` has no logger entry and propagates to root, which
is the same file and the same route the old `contact/forms.py` line took.

### The spent-token defect exists in neither the old code nor the new — determined, not assumed

The task file required this be *checked*, because "fixes a long-standing
defect" and "introduces a new one" are different claims.

A submit that fails validation for a non-challenge reason (empty `message`) was
re-rendered and the response body searched for the token that had just been
spent: **zero occurrences.** The page comes back with an empty
`<div class="cf-turnstile" data-sitekey="...">` and nothing else — the token
lives in an input the provider's script creates at render time, and a Django
re-render is a full page load, so the script builds a new widget. `git show
HEAD:` confirms the reCAPTCHA markup had the same shape, an empty
`<div class="g-recaptcha">`. **Neither form ever echoed a spent token back**,
so requirement 6 is satisfied by the mechanism rather than by new code.

**Watched in a browser 2026-08-29, and the prediction held.** Brian submitted
with an invalid email, Django re-rendered with the field error, and the
Turnstile widget reappeared and resolved to a green checkmark on its own. The
residue that reasoning could not reach — the script failing to re-issue — is
closed by observation.

### HTML5 validation narrows the defect's reach, and it broke the first attempt to see it

The browser test could not be run as designed. Django renders `required` on the
textarea, so submitting with an empty `message` **never leaves the browser**: a
"Please fill out this field" tooltip appears and no request is made. The path
had to be reached with an email the browser accepts and Django rejects — `a@b`,
which needs only an `@` under HTML5 and fails `EmailField` — or by setting
`form.noValidate` from the console.

**That is a correction to the HTTP evidence above, not only a procedural note.**
The curl test that established "zero occurrences" produced a page no browser
could have produced, because curl skips client-side validation. Its conclusion
survives — the server never echoes a spent token — but the path it walked is
not one a user can walk, which is the same shape as the `/var/log/apache2` zero
in task 05's measurement: an instrument answering a slightly different question
than the one asked. [[probes-must-not-perturb-what-they-measure]]

**And it makes the original concern rarer than the task file assumed.** For a
real user the browser catches the common non-challenge failures before a token
is ever spent. What still reaches the server and re-renders is the honeypot
tripping, a Turnstile rejection, and server-only validation like this email
case.

### Fail open, applied at the form

`REJECTED` raises; `UNAVAILABLE` falls through to a send. That is task 01's
recorded decision, and the message the user sees differs by construction:
a rejection shows *"We couldn't verify that you aren't a robot"*, an outage
shows the thanks page. The honeypot still applies in both.

### Mutation verification — ten, each seen to fail

| # | Mutation | Caught by |
|---|---|---|
| 1 | fail **closed** on `UNAVAILABLE` | `test_captcha_unavailable_fails_open` |
| 2 | verify even when the token is absent | `test_no_captcha_response` |
| 3 | accept a rejected token | `test_captcha_failure` |
| 4 | drop `source` at the call site | `test_usage` |
| 5 | stop passing the IP | `test_usage` |
| 6 | helper ignores `source` entirely | two `LoggingTestCase` tests |
| 7 | suffix always present, even unnamed | `test_source_is_omitted_when_unnamed` |
| 8 | `UNAVAILABLE` path drops `source` | `test_source_survives_the_unavailable_path` |
| 9 | view stops passing the site key | `test_widget_is_rendered` |
| 10 | template loses the widget div | `test_widget_is_rendered` |

**Mutations 9 and 10 exist because the first battery had a hole.** Nothing
covered the view context key and the template variable agreeing; both could
have been renamed to nonsense with the suite still green, and the failure would
have been a form nobody could submit. `test_widget_is_rendered` was written to
close it, and only then were 9 and 10 run. All four mutated files restored
byte-identical, control run green.

### Verified end to end against the live API, not against mocks

A second web container on `:8001` carrying
`TURNSTILE_SECRET_KEY=2x0000000000000000000000000000000AA` (Cloudflare's
always-fails secret), the default `:8000` keeping the always-passes one. Real
HTTP submits through the real form:

| Instance | Result |
|---|---|
| `:8000`, always-passes secret | **302 → `/contact/thanks/`**, mail rendered by the console backend |
| `:8001`, always-fails secret | **200**, `<ul class="errorlist nonfield">We couldn't verify that you aren't a robot.</ul>`, no mail |

### The browser pass — DONE 2026-08-29, by Brian, and every criterion is now met

Chrome automation was unavailable, so this ran by hand. All four instances of
the widget's own JavaScript behaviour were watched, which is what no HTTP-level
test in this task could see:

| Instance | Watched |
|---|---|
| `:8000` | widget renders and resolves to a checkmark; a complete form sends |
| `:8000`, invalid email | re-render, and **the widget reappears and re-solves** — criterion 5 |
| `:8001`, always-fails secret | refused, server-side — criterion 7 |
| `:8002`, always-blocks sitekey | refused, client-side — criterion 7 |

**`:8002` is where the log question came from**, and its answer became task 05:
a widget that never issues a token produces no line at all, because the guard
raises before anything is logged.

The three throwaway instances have been removed; `:8000` is the ordinary stack.

### Still owed

- ~~**`.env` still holds `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY`**~~ —
  **DONE 2026-08-29, by Brian.** Zero references remain and the stack restarts
  on the edited file, which also confirms nothing was reading them. The key pair
  can still be deleted at Google's console; registration never used it, so
  nothing anywhere depends on it now.
- **The 1.4/month spam baseline re-read** still stands, unchanged by this task.
  The line to grep is now `Turnstile: .* (contact form)` rather than
  `Contact Form captcha response` — and **task 05 will move that file**, so read
  it there once that task lands.
- **The token-less submissions are still uncounted** — the guard raises before
  anything is logged. Measured and scoped into **task 05**; see the planning
  section above.

## Step 17 task 01 — the verification helper, and a default that is not blank — DONE 2026-08-27, `c96648dc`, PUSHED

Four files, 308 insertions, **972 → 989 tests** green under the deprecation gate.
Nothing user-visible changed and reCAPTCHA still works; task 02 does the swap.

| | |
|---|---|
| `antispam/turnstile.py` | outcome enum, result, `verify()` |
| `antispam/tests/test_turnstile.py` | 17 tests |
| `sg101/settings/base.py` | four settings, beside the reCAPTCHA block |
| `.env.example` | Turnstile entries, with Cloudflare's public test keys |

### Three outcomes, because a bool would have hidden an outage

`verify()` returns `PASSED`, `REJECTED` or `UNAVAILABLE`. A failed challenge and
an unreachable provider are different events, and **collapsing them is how a
Cloudflare incident becomes "the form rejects everyone" with nothing in the log
saying why.**

It also never raises. Transport and protocol failures become `UNAVAILABLE`, so a
form's `clean()` does not have to catch `requests` exceptions. **That is the
actual fix for `contact/forms.py:47`**, where `r.json()` on an HTML error page
surfaces today as a 500 on the contact form.

### The timeout, which is the whole reason this was not a copy-paste

The call being replaced had none. `TURNSTILE_TIMEOUT` follows `EMAIL_TIMEOUT`'s
shape exactly — `env.int`, default 20 — because it is the same bug class Step 16
task 02 found, and the one outcome this task could not produce was a port that
preserved it.

### DECIDED — fail open, and log loudly

Brian's call, 2026-08-27. A caller treats `UNAVAILABLE` as passed, so a
Cloudflare outage does not take the contact form and registration down.

**`UNAVAILABLE` logs at WARNING, not INFO, and the reason is a consequence of
failing open:** a passing check and a skipped one are indistinguishable
downstream, so that line is the only record the check did not actually happen.
At INFO it would sit unremarked beside ordinary passes.

**Neither form is naked during the window.** Contact keeps its honeypot;
registration keeps the hidden honeypot — 8%, the best discriminator measured —
and the emailed activation link. **The helper stays neutral**: it returns the
outcome and tasks 02 and 03 apply the policy.

### The key defaults are test keys, not blanks — a deliberate departure

`TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` default to Cloudflare's published
test keys. **The reCAPTCHA block directly above them defaults to `''`**, which is
why a fresh checkout cannot exercise the contact form at all today. The test keys
always pass and work from any domain including `localhost` with no Cloudflare
account, so a clone now has working forms with no configuration. Production
overrides both.

### `antispam/turnstile.py`, not `antispam/utils.py`

That module imports `bio`, `comments`, `forums` and `user_photos`. Two form
modules needing none of it would drag four app dependency graphs in behind them
and invite an import cycle. `antispam/decorators.py` is the same narrow shape and
`accounts/urls.py` already consumes it — **so the plan's "update the `antispam`
app" is finally true, of a helper rather than of reCAPTCHA.**

### The TDD order was inverted, and the mutations are why that is recoverable

**Recorded rather than hidden: the implementation was written before the tests.**
The compensation was not an assertion that the order held, but the battery below
— **8 mutations, 8 caught**, file restored byte-identical, control run green.

| Mutation | Caught by |
|---|---|
| drop the `timeout` kwarg | errors=1 |
| return `PASSED` on transport exception | failures=3 |
| log the token | failures=1 |
| skip the status-code check | failures=1 |
| stringify a `None` `remoteip` | failures=1 |
| drop error codes from the result | failures=1 |
| log `UNAVAILABLE` at INFO | failures=1 |
| treat a non-dict body as a pass | failures=1 |

Every test has therefore been watched to fail against a deliberate defect, which
is the guarantee the ordering is only a means to. See
[[mutation-verify-or-it-is-not-coverage]] — the standard is the failure observed,
not the sequence.

### The test settings disable logging, and three tests failed for that alone

First run: three logging tests failed with *no logs of level INFO or higher
triggered*, for a reason unrelated to the code. `contact/tests/test_views.py`
already had the enable-and-restore dance; it was copied rather than a second
pattern invented. **Worth knowing before writing any `assertLogs` test in this
repo** — the failure looks like a missing log line and is not one.

### What task 02 inherits

- **The fail-open policy is documented but not yet implemented.** The helper
  returns three outcomes; nothing consumes them until task 02.
- **The spent-token question is still open and deliberately unverified.**
  Turnstile tokens are single-use, so a form failing validation for an unrelated
  reason re-renders with a spent token. Whether the same fault exists today under
  reCAPTCHA v2 must be *determined*, not assumed — "fixes a long-standing defect"
  and "introduces a new one" are different claims.
- **`grep -ri recaptcha` still matches application code.** Task 02 is what makes
  it match only `.agents/`.

## Step 16 task 07 — the smoke tool, and a Microsoft inbox — TOOLING DONE 2026-08-26, `4d77b672`, PUSHED

**The acceptance criterion for Step 16 as a whole is met, repeatably.** A message
built by the site, sent through Postmark by `tools/email_smoke.py --live`,
arrived in an Outlook inbox with every verdict passing. Three files, 1,055 lines,
**951 → 972 tests** green under the deprecation gate.

| | |
|---|---|
| `tools/email_smoke.py` | renders every path; `--live` sends; `--check-headers` reads |
| `tools/live_mail.sh` | keeps the provider settings out of `.env` |
| `core/tests/test_email_smoke.py` | 21 tests, the coverage and safety rules |

### The capture, 2026-08-26

```
Authentication-Results: spf=pass smtp.mailfrom=pm-bounces.surfguitar101.com;
  dkim=pass header.d=pm.mtasv.net; dkim=pass header.d=surfguitar101.com;
  dmarc=pass action=none; compauth=pass
helo=sc-ord-mta113.mtasv.net; client-ip=50.31.156.113
X-Microsoft-Antispam-Mailbox-Delivery: ... dest:I ...
Message-Id: <02a00dc5-4fb5-4f25-854b-ba002bd242a4@mtasv.net>
```

- **`dest:I`** — Inbox, from the header rather than by eye, at the receiver that
  has been refusing this site's mail for years.
- **Return-Path alignment holds in ordinary traffic**, not just in the hand-sent
  probe of 08-25: SPF is evaluated against `pm-bounces.surfguitar101.com` and
  aligns relaxed under `aspf=r`.
- **Two DKIM signatures ride together**; only `d=surfguitar101.com` aligns, and
  it is the one DMARC passed on.
- **A third Postmark IP: `50.31.156.113`**, inside `50.31.156.96/27` like `.116`
  and `.118`. Expect it in a future reading; its absence would say the reports
  are not seeing everything this domain sends.

### `Message-ID` is closed by substitution, not by repair — and this was predicted

The dead domain appears **nowhere**, including in `Message-ID`. That is a *pass*
where task 03 Finding 7a and task 07 requirement 11 both expected a failure, and
requirement 11 said in advance what a pass would mean: *"most likely Postmark
rewriting the header -- rather than being taken as the fix."*

**That is exactly what happened.** Postmark replaces the header with its own
`@mtasv.net` value. **Django's code is unchanged and still builds a `Message-ID`
from the sending host's FQDN**, so nothing was fixed; the header that carried the
dead domain is simply no longer the one that ships. Recorded this way because a
later reader finding "dead domain absent" in this file would otherwise conclude
the code was repaired, and go looking for a commit that does not exist.

### `SCL=-1` is NOT the reputation result, and the tool said it was

The plan treats the post-cutover SCL as the measure of whether the provider move
bought anything: the 2026-08-17 baseline scored **3** — *"authentication now
perfect, reputation still neutral"* — and task 07 asks whether that improves.

This capture reads `SCL=-1`, and **that is not an improvement on 3 because it is
not a score.** Exchange stamps `-1` when a message **skipped filtering** — a
safe-sender list, a contact entry, or an allow rule at the receiver. It records
that *this mailbox* trusts the sender, which is a different claim from the sender
having earned a reputation, and it cannot be compared with a baseline that was
actually scored.

**The mailbox has been receiving these test messages since 2026-08-17**, so the
probe is measuring its own history —
[[probes-must-not-perturb-what-they-measure]] in its plainest form.

**Consequence: the SCL question is still open**, and closing it needs a Microsoft
address that has never been told to trust this sender. Nothing else in the step
depends on it; the deliverability claim rests on authentication and on `dest:I`,
both of which this capture supplies.

**The tool reported it as "the real score."** It would have gone into this file
as the best result yet. Corrected the same day and mutation-verified: it now
prints `FILTERING SKIPPED, not a score` and names what would measure the thing.

### Four defects that reading did not find and mutation did

Each is now pinned by a test that fails when the defect is reintroduced.

1. **The tool passed a template referencing a variable that no longer exists.**
   Django renders a missing variable as `''` and carries on, so asserting a
   non-empty body proved nothing — which is precisely what requirement 2 says
   this tool exists to catch. Paths are now rendered under `string_if_invalid`.
   **The first sentinel was itself inert**: it was `<<MISSING:%s>>`, autoescaping
   renders `<<` as `&lt;&lt;`, and the marker never matched the body it was
   supposed to be found in. Only a second mutation showed it.
2. **The template name in the output was an unverified label.** A producer could
   claim one file and render another. The `template_rendered` signal now checks
   it — in the suite, since that signal only fires under the test runner.
3. **Setting Celery's eager config at import** reconfigured the shared app for
   every importer and broke **11 retry tests** in `core.tests.test_tasks`, which
   depend on an eager task *not* propagating. Moved to the entry point. The first
   regression test for it was worthless — `setUp` had already imported the tool,
   so the damage preceded the reading.
4. **`--live` was a false green.** With no provider configured the container
   falls back to the console backend on `localhost:1025`, and `--live` printed
   ten messages to stdout, announced *"real messages through localhost"*, and
   reported **23/23 checks passed having sent nothing** — the one failure mode
   this tool exists to prevent, produced by the tool. `check_live_backend()`
   refuses, naming every problem at once. **Found by Brian asking whether he
   could run it at all.**

### Coverage is enumerated by category, because the hand-list had already rotted

The task file said **seven paths**; there are **ten**, across nine categories,
plus Django's error mail which carries none. Task 05 added the email-change
confirmation and notice four days after the list was written, and
`messages/views.py:416` was a second PM shape it never had.

`COVERED` maps every `EmailCategory` to a producer and a test fails until a new
category has one — the same trick task 09 used for `SUBJECT_SAFE`, and for the
same reason: a hand-maintained list is a list that is wrong later.

### No recipient ever comes from the database

`notify_topic_subscribers()` reads `topic.subscribers`, and **the dev database is
a production snapshot full of real member addresses**, so a producer built on a
real row would mail real members from a tool whose purpose is sending test
messages. The forum producer builds its post in memory and stubs the subscriber
query — which also keeps it clear of the `Forum.last_post` CASCADE. Asserted by
`test_no_recipient_comes_from_the_database`, mutation-verified: pointed at the
DB, it fails and names the category.

`email_admins` gets the same treatment via `override_settings(ADMINS=...)`,
otherwise a live run would mail the real admin address on top of the recipients
asked for.

### Sending is a deliberate act, not a property of the dev stack

`tools/live_mail.sh` passes the six mail variables to one `--rm` container rather
than leaving them in `.env`. **The hazard it answers is specific**: with the
provider configured in `.env`, the site at `localhost` can mail real people, and
nobody has to do anything unusual — a forum reply notifies real subscribers.

**The token is passed by name, not by value.** `docker compose run -e VAR` with
no `=` takes it from the shell, so it reaches neither the command line, nor `ps`,
nor shell history. The script refuses a token file stored inside the repository,
reads it rather than sourcing it (`pg_snapshot.sh`'s reasoning: sourcing a file
to get one value out runs everything else in it as shell), and warns if `.env`
carries an active `EMAIL_BACKEND`, because then the script is not what is
protecting you.

### What the tool cannot do, stated in it

`image_smoke.py --s3` closes its own loop — upload, fetch back, delete, confirm
gone. **Email has no read-back.** A `250` is accepted-for-delivery and nothing
more. `--check-headers` reads what a human fetches: the four verdicts, the real
SCL, `dest:I`/`dest:J`, and whether the dead domain appears anywhere but
`Message-ID`.

### Still open

- **The two-week bounce-dashboard watch**, which replaced the graduated warm-up
  (dropped 2026-08-20 on measurement). It starts at cutover, not now.
- **The SCL comparison**, above — needs an untrained Microsoft mailbox.
- **A live run of all ten paths.** One path to one receiver is what has been
  sent; `--only` exists so a first send against a young sending reputation is one
  message rather than ten.

## Step 16 task 02 — the Postmark backend, whose diff contains no Postmark — DONE 2026-08-17, `72e823d` + `7f316dd` + `d7fefb5`, PUSHED, CI GREEN

Three commits, 878 tests green, and **not one line of provider-specific code.**
Task 01 had already made every mail setting environmental, so "point Django at
Postmark" is `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` and a token set in the
deployment environment — the code change is zero. What the task actually
contained is the part its one-line plan description hid: **a local MTA is a
durable retry queue and an external provider is not**, and **one site email
never went through the site's mail path at all.**

### Retry and error classification — `72e823d`

`core.tasks.send_mail` was a bare `msg.send()`: no `bind`, no retry, no backoff,
no timeout. That was safe only because the far end was Postfix on `localhost`,
which accepted in about a millisecond and then owned delivery, queueing and
retrying for days. Pointing `EMAIL_HOST` at a provider deletes that queue in a
diff that only touches settings.

| Knob | Value | Reason |
|---|---|---|
| `max_retries` | 5 | transient only |
| backoff | `4 * 2**retries`, capped 600s, jittered | a provider outage fails every queued message at once; an unjittered backoff retries them all in the same instant, repeatedly |
| `acks_late` | `True` | a worker killed mid-send re-runs the task, so a message can go out twice — for a registration confirmation a duplicate is an annoyance and a loss blocks a signup |
| logger | `'email'` | so failures land in task 09's `email.log` beside the per-send lines, not only in `sg101.log` |

**The `except` ordering is the whole mechanism.** `SMTPRecipientsRefused` and
`SMTPSenderRefused` are *subclasses* of `SMTPException`, so the obvious
`autoretry_for=(SMTPException,)` would retry six times on a refused recipient,
burning quota and delaying the error. Celery 5.6 has no `dont_autoretry_for`, so
`PERMANENT_ERRORS` is caught in an explicit clause ahead of the transient one.

The give-up log happens **before** the final `retry()` call, not in a handler
after it, because `retry()` re-raises the original exception rather than
`MaxRetriesExceededError` — a handler keyed on the latter would never fire.
Recipient and subject are logged; never the body.

**Correction, recorded on review 2026-08-18: the jitter is not "full jitter",
though the docstring and the commit message both call it that.**
`_retry_countdown` returns `random.uniform(ceiling / 2, ceiling)`, which is
*equal* jitter in the AWS taxonomy; full jitter is `uniform(0, ceiling)`. The
behaviour is fine and arguably the better choice here — it keeps a floor under
the delay, so a retry storm cannot collapse toward retrying immediately — but
**the name in the code was wrong, and a name is what the next reader trusts**
rather than re-deriving the arithmetic. Renamed in `3157216`, behaviour
untouched, 878 tests green under the gate.

**Mutation-verified against two mutants rather than one.** Removing the retry
fails five of the seven new tests; swapping the `except`-clause order fails the
other two; every test fails under at least one. *An earlier attempt that reverted
the module wholesale only produced an `ImportError`, which proves the file
changed rather than that the behaviour is covered* — see
[[mutation-verify-or-it-is-not-coverage]].

### Password reset was the one email that bypassed the wrapper — `7f316dd`

`accounts/urls.py` wired Django's stock `PasswordResetView` with no
`form_class`, so `PasswordResetForm.send_mail()` built an
`EmailMultiAlternatives` and sent it itself: **no Celery, no retry from the
commit above, and no send logging when task 09 lands** — and synchronously,
inside the request. That handoff was sub-millisecond to a relay on localhost and
becomes a TLS handshake plus a network round trip to a provider, on the page a
locked-out member is already frustrated by.

`SitePasswordResetForm` overrides `send_mail()` and nothing else; finding the
matching accounts and generating the token stay with Django in `save()`. Three
details that are easy to lose in that rewrite:

- **The subject keeps `''.join(subject.splitlines())`.** The subject template
  ends in a newline, and a newline in a subject header is an injection.
- **`from_email` arrives as `None`** — the view's default — because Django leans
  on `EmailMultiAlternatives` falling back to `DEFAULT_FROM_EMAIL`. The wrapper
  takes the address as an argument, so it is resolved explicitly or the `From`
  header becomes the literal string `"None"`.
- **The swallow is kept, and the risk it covers moved rather than went away.**
  Django swallows send failures here so a broken mail path cannot 500 the reset
  page — which would also disclose whether an address has an account. Routing
  through Celery means `delay()` talks to the broker, so an unreachable Redis
  now raises inside the request where an SMTP failure no longer can.

An HTML alternative body raises `ImproperlyConfigured` rather than being dropped
silently; nothing in the project configures one.

**Mutation-verified by removing `form_class` from the URLconf: four of the five
new tests fail. The pre-existing full-flow reset test still passes under that
mutant** — because the stock view sends the mail too, which is exactly why it
could never have caught this.

### Making the enumeration test discriminate — `d7fefb5`

`test_unknown_address_sends_nothing_and_still_redirects` asserted only that an
unknown address redirected and sent nothing. Both hold under Django's stock form
as well, so **it pinned nothing about this change.** It now posts a known address
and an unknown one and asserts the two responses are indistinguishable — same
status, same redirect chain, same rendered body — mutation-verified with a
`clean_email()` that raises "No account with that address", the helpful-looking
change it exists to catch. The old version passed that mutant.

Its docstring records what it is *not*: a user-enumeration guard rather than a
routing test, and the one test in the class that does **not** discriminate the
wrapper being wired up. It also records the limit it does not cover — a known
address renders templates and queues a task while an unknown one returns
immediately, so **timing still separates them.** That difference is Django's own
and is not introduced here.

### Logger wiring, written into task 09 before anyone configures a handler — `2a05a03`

Naming the logger `'email'` has two consequences that would otherwise be decided
by pattern-matching the existing config:

- **`propagate: True`.** The `auth` and `search` loggers set `False` to keep
  their volume out of `sg101.log`; email's measured volume is ~30/day, and an
  incident is debugged from `sg101.log` first.
- **Never attach `mail_admins` to it.** It sends email, so alerting on a mail
  failure fails for the reason it is alerting about — and loops if that failure
  is itself logged.

### What task 02 does *not* close

Code-complete; **its delivery-side acceptance criteria are unmet by design.**
Still open, and belonging to the cutover rather than to this sitting: the
Postmark variables in the production environment, one real message with headers
showing `dkim=pass d=surfguitar101.com` and `spf=pass`, the rollback
demonstration (restore the old variables, no code change), and task 03's
requirements 5–7 — the SPF rewrite, then `~all`, then `-all`. Task 07 owns the
broader smoke and the stale-list warm-up.

Test count moved 866 → 873 (retry) → 878 (reset), green under `docker_test` and
under the deprecation gate at each commit.

**Next: task 04** — delete "email this story to a friend", the site's only path
that sends to an arbitrary external recipient, before Postmark ever carries
traffic from this domain. Task 03's DMARC clock started 2026-08-17, so the first
week of aggregate reports is readable from ~2026-08-24.

## Step 16 task 01 — email configuration to the environment — DONE 2026-08-17, `b5b5686`, PUSHED, CI GREEN

Finishes 12-factor work Step 3 skipped: every `EMAIL_*` setting was a hardcoded
literal and `.env.example` had no mail variables at all, so pointing the site at
a provider meant editing code. Each read now takes the current literal as its
default, which is what let task 02 contain no provider-specific code.

**Method, because "settings refactor" is exactly where an unnoticed behaviour
change hides:** every resolved mail setting was diffed across `docker`,
`docker_test` and `production`, before and after, with an empty environment. The
two changes below are therefore the only ones — measured, not asserted.

### The two deliberate changes

- **`SERVER_EMAIL` was unset**, so Django used `root@localhost`. That is not
  dead config: `production.py` installs `AdminEmailHandler`, which sends error
  mail from `SERVER_EMAIL` — **a different path from
  `core.functions.email_admins()`**, which sends from `GPP_NO_REPLY_EMAIL`. A
  local relay accepted `root@localhost`; a provider will not sign for it. Left
  alone, **error reporting would have been the first thing to break after
  cutover** — the failure that hides every other failure.
- **`EMAIL_TIMEOUT` was `None`**, meaning no timeout in `smtplib`. Harmless
  against a local socket; against a remote host a hung connection blocks the
  sending thread with no bound. Now 20s, and it satisfies task 02's criterion
  that the timeout is a bounded number in every environment.

Also: `DEFAULT_FROM_EMAIL` is decoupled from `ADMINS[0][1]`, so adding or
reordering an admin no longer silently changes every outbound `From`; and
`EMAIL_HOST` is dropped from `production.py`, where it restated base's value.

### The `.env.example` entries are commented out, not listed blank

Compose loads that file through `env_file:` and CI seeds from it, so a bare
`EMAIL_PORT=` sets the variable to the empty string rather than leaving it
absent — **and empty beats the default**: `int('')` raises at settings-load
time and nothing starts. Only the two credential variables are safe listed
blank, their default being blank. The reasoning is in the file itself so it does
not get tidied away by someone filling in the blanks.

`ADMINS` stays hardcoded: a nested structure `django-environ` does not read
cleanly, for exactly one admin.

866 tests green under `docker_test` and under the deprecation gate; `check` and
`makemigrations --check` clean; **`check --deploy` byte-identical to before.**

*CI note: this commit and `72e823d` have no run of their own — they were pushed
in the batch whose tip was `2a05a03`, which is green, so both are covered by
that run rather than by one naming them.*

## Step 16 task 04 — delete "email this story to a friend" — DONE 2026-08-18, `3b5eb64`, PUSHED, CI GREEN

165 deletions, nothing added. The view, the thanks view, `SendStoryForm`, both
URLs, both templates, the link in `story.html` and `story_summary.html`, and the
whole `NewsEmailStoryTests` class.

**Why it was a Step 16 task rather than a Step 19 prune:** it was the only path
in the site that sends to an arbitrary external recipient — any address typed
into a form, no CAPTCHA, no rate limit, and a `Reply-To` taken from the sender's
profile email, which any member can set to an address they do not control. On a
dedicated IP the blast radius was a domain we own; on a provider's shared pool it
lands on other senders, and the provider's answer to abuse is suspension, which
would take registration confirmations and password resets with it. **Deleting it
before cutover means Postmark never sees traffic from this path.**

### Two corrections to the task file

- **Four tests, not three.** The enumerated surface missed
  `test_email_thanks_renders`, so the class went whole. **The count moves
  878 → 874**, not the 866 → 863 the task predicted — 878 being where tasks 01
  and 02 left it. Recorded because this project tracks that number and an
  unexplained move costs someone an investigation.
- **A fourth import fell out unused.** The task flagged `get_full_name` and
  `render_to_string` as needing a check; `Site` from
  `django.contrib.sites.models` also existed in `news/views.py` only for this
  feature. `settings`, `HttpResponseRedirect` and `reverse` have other callers
  and stayed.

`email_thanks` rendered `send_story.html` rather than a thanks template — there
is no `email_thanks.html` in the tree — so a latent oddity goes with it.

### The render check needed a control, and nearly did not get one

First attempt rendered both pages as an anonymous client and found no
"Email to Friend". **That proved nothing**: the link lived inside
`{% if user.is_authenticated %}`, so an anonymous render never showed it, before
or after. Re-run logged in — the case that used to show the link — with
`Permalink` asserted present in the same `<ul>` as the control that the probe can
match text in that region at all. See
[[measure-before-recording-in-planning-docs]], item 7.

**Also worth recording: there is no linter to satisfy.** The task's acceptance
criteria ask for a clean linter run; this project has none configured, which is
the item Step 19 carries. Imports were verified by grepping each symbol for
surviving uses instead.

874 green under `docker_test` and under the deprecation gate; `check` clean;
`check --deploy` unchanged; no residual references outside `.agents/` for any of
the seven search terms. `contact/forms.py` untouched — its `Reply-To` is also
user-supplied, but its recipient list is `settings.MANAGERS`, so it can only ever
mail us and there is no third party to abuse.

**Next: task 10 requirement 4** (SPF at the HELO name), then Step 16 tasks 05–09.
*(Task 08 landed first, 2026-08-19.)*

*Corrected 2026-08-20: this line used to read "once tomorrow's DMARC report is
read," and requirement 4 has no such dependency — it publishes one TXT record.
The DMARC week gates policy tightening only; see the scoping note in Open.*

## Step 16 task 08 — registration tokens from `secrets` — DONE 2026-08-19, `20ad77ed`, PUSHED, CI GREEN

`PendingUserManager._make_key()` derived the registration confirmation key from
`SECRET_KEY`, a per-process counter, an eight-character `random.sample` and the
date, then took every other character of a SHA-1. Replaced with
`secrets.token_urlsafe(32)`. Also `secrets.compare_digest` for the comparison and
`secrets.choice`/`secrets.randbelow` for the registration code word.

**The point was never that it was breakable.** `SECRET_KEY` in the hashed input
means an attacker who cannot read the settings cannot reproduce a key, whatever
the Mersenne Twister does. What was wrong is that its security rested on one
ingredient while *appearing* to rest on four — which is worse than a short honest
token, because it discourages the question. The task file's own risk assessment
said so and this execution did not inflate it.

The helper is module-level in `accounts/utils.py`, not a private method on the
manager, **so task 05 imports it rather than copying a bad one.** That sequencing
is the entire reason this is its own task.

### Requirement 8 asked for a confirmation and got a refutation

It said the route "takes `username` and `key`; a longer key changes the URL's
length, not its structure. Confirm the route still matches." **It did not match,
and on two axes at once:**

```
before:  (?P<key>[a-zA-Z0-9]{20})        fixed length, no - or _
after:   (?P<key>[A-Za-z0-9_-]{20,64})
```

A 43-character URL-safe token fails the length *and* the alphabet. This was not
theoretical: the token minted in the end-to-end run was
`UdH8BK15k9q13--FE4gYjEjYkIXH7oRIw60q8rmAZ7w`, which contains `--` and would have
404'd. The comment above the pattern asserted "a fixed 20-char alphanumeric run"
and went with it.

**The lower bound of 20 is load-bearing, not laziness.** A `{43}` bound would
reject every confirmation link already sitting in an inbox, for the full day the
expiry window stays open — turning a widening migration into a silent outage for
anyone mid-registration at deploy time. Acceptance criterion 4 covers exactly
this and now has a test of its own: `test_confirm_registration_differing_case`
happened to use a 20-character key and so covered it *incidentally*, which is not
coverage — nothing in that test says the short key matters, and a later edit
would have removed it without anyone noticing.

### Three mutations, each seen to fail

Per [[mutation-verify-or-it-is-not-coverage]]. None of these tests counted until
the thing they guard was broken and they were watched to fail:

| Test | Mutation | Result |
|---|---|---|
| key shape ≥32 chars, URL-safe alphabet | the unmodified `_make_key()` | `20 not greater than or equal to 32` |
| legacy 20-character key confirms | regex narrowed to `{43}` | error — route no longer resolves |
| wrong key refused | comparison replaced with `if False:` | `a wrong key created the user anyway` |

**The alphabet assertion does not discriminate and the test says so.** The old
20-character lowercase-hex key also matches `^[A-Za-z0-9_-]+$`; only the length
separates old from new. Recorded in a comment so nobody later reads the regex as
doing work it is not doing.

`test_wrong_key_is_refused` likewise records what it is *not*: it passes equally
under a plain `!=`, because both reject a wrong key. `compare_digest`'s property
is timing, which no functional test observes. What it catches is the comparison
being dropped or inverted — which is what the mutation demonstrates.

### The acceptance criteria contradicted the background, and the criterion was wrong

One criterion asked that a tree-wide grep for `random.sample` leave
`wiki/middleware.py` as the **only** hit. It cannot: `core/templatetags/
core_tags.py:243` also has one, and the same task file's out-of-scope list says
to leave it — banner rotation, no security property. **Satisfying the criterion
would have meant changing something the task forbids.** Corrected the criterion
rather than the code, and recorded why. `wiki/middleware.py` stays untouched
deliberately; Step 19 deletes that app, so fixing it is work thrown away.

### Counts came out of the shipped code, including one that was already wrong

Brian's review caught comments like *"thirteen addresses in this database"* as
stale-prone, and he was right in a way that had already bitten: the test module
docstring said the migration "has to clear twelve of them", when it clears
thirteen — the byte-identical figure carried across, two turns after the same
confusion had been untangled. Ten count-claims removed across five files;
comments now describe shape (*"an address held by more than one account"*) and
the numbers stay in this file and `research/collation-audit.md`, which are dated
records where a figure is the point.

`0008`'s docstring gained the reason rather than just losing the count:

> The groups are computed rather than listed. The database this runs against is
> not the one it was written against: a snapshot taken later may hold a group
> this author never saw, and listing today's would silently skip it.

**`0003`'s docstring is rewritten too**, since it is where this started —
*"Thirteen addresses... Twelve of those pairs are byte-identical"* described the
state it inherited and read ever after as the state it left. It now says plainly
that folding a case variant makes its group byte-identical, so it leaves *more*
genuinely-shared addresses than it found, and names the earlier wording as the
thing that cost time. Editing an applied migration's docstring is safe; Django
does not hash migration files. [[measure-before-recording-in-planning-docs]]

### Verification

877 green under `docker_test` and under the deprecation gate; `check` and
`makemigrations --check` clean; **`check --deploy` byte-identical** before and
after, the one pre-existing `security.W001` unchanged. CI green on the pushed
commit (run `32316319294`).

**Registration was exercised end to end against the real dev database, not a
freshly built test one** — which is the only way the migration itself is under
test. Column confirmed at 64 after `migrate`, a token minted, the confirm URL
followed, the user created, the pending row consumed, artifacts cleaned up.
`secrets.randbelow(900) + 100` reproduces `random.randint(100, 999)`'s inclusive
range exactly.

Imports removed as dead once `_make_key()` went: `random`, `string`, `hashlib`,
`base64` and `settings` from `accounts/models.py`, `random` from
`accounts/forms.py`. `datetime` stays — `purge_expired()` still uses it.

Test count 874 → 877.

**Next: task 05** (verified email address changes), which is what the shared
helper exists for. *(Done 2026-08-22.)*

## Step 16 task 09 — one line per email, and a category that cannot go unclassified — DONE 2026-08-21, `1763704f`, PUSHED, CI GREEN

904 tests green (877 before), check clean, no migrations, deprecation gate green.
Every message the site sends now writes one INFO line to a dedicated
`email.log` **at send time, so it carries the outcome rather than the intent**:

```
category=registration to=member@example.com from=admin@surfguitar101.com outcome=sent subject=Confirm your registration
category=pm_notification to=other@example.com from=no_reply@surfguitar101.com outcome=sent subject=<redacted>
```

`outcome` is `sent` / `retrying` / `failed`, so a failure is distinguishable by a
value rather than by a missing line. Recipients in full, following `search.log`'s
precedent — answering *"did this member get their confirmation"* is the
operational reason the file exists, and this step has spent a week unable to
answer exactly that from Postfix logs. The body never appears, and neither does a
subject a member wrote.

**Brian's two calls at the design step**, both recorded before implementation:
full addresses rather than a count plus a hash, and subjects verbatim **except**
`pm_notification` and `contact_form`, whose subject lines are member-authored.
The third — Django's `AdminEmailHandler` — he declined, so crash reports are not
categorised or counted; **named in the settings handler comment rather than left
silent**, since a line count of `email.log` undercounts total sends by that many,
and STATUS expects a run of them until cutover.

### The enum, and the argument that actually decided it

`core/email_categories.py` holds an `enum.StrEnum`. **Measured on the container's
Python 3.12 rather than assumed**: a plain `Enum` raises `TypeError` under
`json.dumps` — which is what Celery does to task arguments — and formats as
`EmailCategory.REGISTRATION`; `StrEnum` does neither, and compares equal to the
bare string, which is also what keeps requirement 4's in-flight tasks working.

**The deciding argument was not typo safety.** Brian asked for the pros and cons
of constants, and the honest answer was that the tests pin each call site either
way. What settled it is that an enum is *enumerable*, so a test can assert
`set(EmailCategory) == SUBJECT_SAFE | SUBJECT_REDACTED`. **That makes adding a
category without classifying it impossible to commit**, where the allowlist alone
only made the omission fail safely. Both are kept: the allowlist guards runtime,
the test guards the set. `SUBJECT_REDACTED` has no runtime consumer and carries a
comment saying so, so nobody deletes it as dead code.

### Three things the task file had wrong

1. **Requirement 5's password-reset half was already built.** Task 02 (`7f316dd`)
   added `SitePasswordResetForm` and wired it through `form_class`. Reset already
   reached the wrapper and Celery; this task only had to pass a category. No
   separate commit, no behaviour change.
2. **"Fourteen call sites" is nine.** `email_admins` and `email_managers` are
   themselves wrappers with many callers, so categorising inside those two covers
   the whole `admin_notification` family in one place.
3. **The `assertLogs` idiom already existed.** `settings/test.py` disables logging
   globally, which beats `assertLogs`; `core/tests/test_tasks.py:84` already
   re-enables it in `setUp` with `addCleanup`, and task 02 even left a fixture
   body reading `'secret body text that must not be logged'`.

### `uncategorized` is redacted, and two task 02 tests said so

Two of task 02's failure tests broke: they send without a category, and
`uncategorized` is in the redacted set, so their subject vanished from the
failure line. **The fix was to give those tests a category, not to weaken the
assertion** — every real caller passes one now. Keeping `uncategorized` redacted
is the fail-safe direction: the case it protects against (a caller who forgets a
category on member-authored mail) is likelier than the case it costs (a
short-lived in-flight task logging a failure without its subject).

### The propagation claim was wrong, and a measurement fixed it

The task file said `propagate: True` puts *"the complete audit trail in
`email.log`, and delivery failures in `sg101.log`."* **It puts everything in
both.** A propagated record is offered to each handler up the chain and **the
ancestor logger's own level is never re-checked**, so `root` being `INFO` filters
nothing — only the `file` handler's level applies, and it is `DEBUG`. Found when
Brian asked why the levels differ between `production.py` and `local.py`.
Verified with one send and `grep -c` in each file: one hit in each. The behaviour
is what was wanted at ~30 messages a day; only its description was wrong.
Corrected in both settings modules and in the task file.

*(The levels themselves, since the question is a fair one to ask again:
formatters have none. Only handlers and loggers do, and a record must clear
both. The only real production/local differences are `root` and `auth`, DEBUG on
a dev box and INFO in production. For `search` and `email` the logger is INFO in
both, so local's DEBUG handler changes nothing — local handlers are uniformly
DEBUG by convention so they are never the constraint.)*

### Two test defects found on the way

1. **`core/tests/test_functions.py::test_django_case` was testing the wrong
   path.** It passed `defer=True` while claiming to cover the inline send, and
   reached `EmailMessage` through the eagerly-executed Celery task — the patch
   target resolves to the same module object either way, so it passed for a
   reason unrelated to its name. Now `defer=False`.
2. **One of this task's own tests was vacuous.** `test_no_recipients_logs_no_send_line`
   mocked the task, so no line is written whether the empty-recipient guard fires
   or not; it would have passed with the guard deleted. Rewritten against
   `defer=False`, and mutation 5 below now fails it.

### Mutation verification — five, each seen to fail

| Mutation | Result |
|---|---|
| guard removed from `log_send` | 1 failure |
| `subject_for_log` never redacts | 5 failures |
| wrapper drops `category` on `delay()` | 2 failures |
| a ninth enum member left unclassified | 1 failure — the exhaustiveness test |
| empty-recipient guard removed | 2 failures |

Per [[mutation-verify-or-it-is-not-coverage]]. The forums call-site test also
failed for a fixture reason worth keeping: `setUp` creates its member with an
empty email address, and the wrapper drops empty recipients before sending —
the guard working, discovered by walking into it.

### End-to-end, because no unit test covers the settings wiring

Two real sends under `sg101.settings.docker`, read back out of
`sg101/logs/email.log` (gitignored by `*.log`). The handler creates its own file
and the redaction fires. The suite proves the mechanism; only this proves the
configuration.

### What is still owed

The task's own step 9: **after a month in production, compare the measured
totals against the estimates in STATUS and record the delta.** That cannot start
until this is deployed, and **the pre-cutover window is the only chance to
collect a jaguar-side baseline** — which is why this task went first among the
four that were unblocked. Postmark's dashboard will give a total with no
category breakdown; this is what makes a discrepancy explainable.

## Step 16 task 05 — an email address is not yours until you answer mail at it — DONE 2026-08-22, `d3f5cd4e` + `da938045`, PUSHED

The Step 11 REVISIT, closed. `/profile/edit/` no longer writes `User.email`:
a requested address goes into a new `accounts.PendingEmailChange` row, a
confirmation link is mailed to it, and only following that link moves the
address onto the account. **951 tests green** (904 before), gate green, `check`
and `makemigrations --check` clean, `check --deploy` unchanged.

### The form change is the whole guarantee

`email` came **out** of `EditUserForm.Meta.fields` and became a declared-only
field. A `ModelForm` writes its Meta fields to the instance, so leaving it there
would have meant undoing the write in `save()` — a thing a later edit can
forget. Off the Meta list, the form *cannot* touch `User.email`, and the view
asks `requested_email()` instead. The mutation test for this is putting `email`
back: two tests fail immediately.

That also disposes of requirement 7 without touching a template. The three
surfaces that render an address — `view_profile.html:87`, `members.html:48`,
`display_post.html:25` — all read `user.email`, which is now never the pending
one. Asserted rather than assumed, across all three at once, since nothing else
in the suite would notice a regression.

### Requirement 3's premise was wrong, and the answer is both

It said sweeping expiry from "the existing cleanup task" is "more consistent
with the codebase." Measured: `PendingUser.purge_expired()` has exactly one
caller and it is **on use**, in `register_confirm` — not scheduled at all.
Brian took both, each doing a job the other cannot:

- The confirm view fetches the row and **then** checks `is_expired`, so an
  expired link says so. `register_confirm` purges first and therefore cannot
  tell an expired link from a mistyped one — its template hedges with "it may
  have expired". This one does not have to.
- `core.tasks.cleanup` calls `purge_expired()` daily. Nothing guarantees a
  member who abandons a request ever visits a view that would collect the row.

The import in `cleanup()` is local, and the comment says why: `accounts.utils`
imports `core.functions`, which imports `core.tasks`.

### The race requirement 4 could not see

Two members can request the same *free* address — neither holds it, so the form
passes for both — and both confirm, minting exactly the kind of duplicate pair
this task exists to prevent. Brian's call was to guard both ends: `clean_email`
also rejects an address pending un-expired for another account (registration
already does this for `PendingUser`), and the confirm view re-checks uniqueness
before the write, answering with a distinct "that address was claimed" page.

### The 26 accounts, verified against the real database

`clean_email` returns before doing any work when the submitted address matches
`self.instance.email` case-insensitively. That guard is the requirement, not an
optimization. Verified two ways:

- A test that fails against the naive implementation — watched to fail with
  *"a member sharing an address cannot save: {'email': ['That email address is
  already in use by another account.']}"*.
- A read-only probe over the dev database: **13 groups, 26 accounts** (unchanged
  since 2026-08-16), the real form instantiated against each real row,
  **0 that could not save**.

A case-only edit of your own address counts as unchanged for the same reason —
same mailbox, and calling it a change would make a member confirm an address
they already hold.

### Five mutations, each seen to fail

Per [[mutation-verify-or-it-is-not-coverage]].

| Test | Mutation | Result |
|---|---|---|
| duplicate-pair member saves an unrelated edit | unconditional `exclude(pk=…)` | rejected as already in use |
| requested address never reaches `User.email` | `email` back in `Meta.fields` | `'new@…' != 'paul@…'`, form and view |
| expired link says expired | drop the `is_expired` branch | "Couldn't find 'expired'" |
| wrong key refused | `compare_digest` → `if False:` | wrong key applied the change |
| three surfaces show the verified address | write `User.email` at request time | all three fail |

### End to end against the dev database, not a fresh test one

The only way the migration itself is under test. A scratch user, a change
requested, the edit page checked, the link followed **logged out** — the link is
read in the new mailbox, possibly on another device, so confirming deliberately
does not require a session. The key minted was
`m3f7Xedx_cMg9EamMrV0C1-geMcoHVK8hakIGFYlWnw` — it contains both `-` and `_`,
which is the exact token shape that broke the registration route in task 08, and
the route pattern here handles it because it was copied from the fixed one.
Scratch user and all rows removed afterward; snapshot
`sg101-20260822-141919-pre-step16-task05.dump` taken first.

### Decisions worth keeping

- **Cancel and resend live in `bio`, not `accounts`.** Only the confirmation
  view belongs beside `register_confirm`; these two are posted from the profile
  edit page and redirect back to it. Putting them in `accounts` would have made
  it import `bio` URL names, and the whole point of the model living in
  `accounts` is that the dependency points `bio -> accounts` only.
- **Resend re-requests the same address** rather than re-mailing the old link,
  so the expiry window restarts — a member who waited most of a day does not get
  a link good for the remaining hour. It does **not** re-notify the old address:
  that address was told when the change was requested, and a resend is the same
  request again.
- **The courtesy mail to the old address carries no action link**, as the task
  file decided. Asserted by test: the key appears in the message to the new
  address and not in the one to the old.
- **One category, `EmailCategory.EMAIL_CHANGE`**, in `SUBJECT_SAFE` — both
  subjects are site-authored. The log line's recipient already distinguishes the
  confirmation from the courtesy note.

### Six defects came out of ten minutes in a browser, against 946 green tests

**This is the finding worth carrying forward, not the feature.** The suite was
thorough by every measure this project uses — mutation-verified, exercised
against the real database, 41 new tests — and it was blind to the entire
rendered surface. Every one of these passed the suite and failed a human
looking at the page:

| What broke | Why nothing caught it |
|---|---|
| A multi-line `{# #}` rendered to the page as literal text | Django's tokenizer is not `DOTALL`, so it is not a comment token. Tests asserted the pending address appeared, never that the markup around it was clean |
| Cancel/Resend flashes never displayed | Only **four** templates on the site include `core/message_list.html` and `edit_profile.html` was not one; the messages surfaced two pages later. Tests asserted `assertRedirects`, and the redirect was always right |
| The two buttons stacked instead of sitting inline | Nothing asserted on layout, and nothing asserted the buttons were on the page at all — the cancel/resend tests POST straight to the URLs, so a missing button would have shipped green |
| Cancel from the profile page teleported you to the edit page | The redirect target was hard-coded and every test asserted that exact target |
| The save flash and the notice said the same thing twice | Two correct behaviours, ugly together. No test can see that |
| A stale Celery worker had been failing **every** deferred send | See below |

The shape is identical in all six: **the tests asserted state, never what a
person would see.** A view can be correct in every respect the suite checks and
still be unusable. Worth remembering when the next task's acceptance criteria
are all `assertEqual` on model fields.

### The stale worker, which is a trap and not a one-off

Every deferred `send_mail` in the dev container was dying with
`TypeError: EmailMessage.__init__() got an unexpected keyword argument
'category'` — and the code was fine. **The `worker` container had been up since
2026-08-16**, five days before task 09 added that parameter (2026-08-21), so it
was executing the old function. The tell is a traceback whose line number lands
on a comment: old code object, new file on disk.

Two consequences:

- **No deferred send had succeeded in dev since task 09 landed.** Task 09's
  STATUS entry claims two real sends read back out of `email.log`; those cannot
  have gone through this worker, so the deferred path was never exercised after
  that change.
- **`manage.py runserver` reloads on edit and Celery does not.** The suite
  cannot see this at all: `CELERY_TASK_ALWAYS_EAGER` imports fresh code every
  run. **Editing a task means `docker compose restart worker`, or you are
  testing code you did not write.**

### UI decided at the page, as the task file asked

- The notice is a **shared partial**, `bio/pending_email_change.html`, included
  by the profile page *and* the edit page. Brian's call: the edit page is not
  where a member spends time. Two copies of that markup would have drifted.
- **It cannot reach anyone else's profile, structurally.** `view_profile`
  redirects to `bio-me` when the subject is you, so `my_profile` is the only
  view that renders that page for its owner and the only one that supplies
  `pending_change`. No `{% if this_is_me %}` to forget. Mutation-verified by
  leaking it deliberately.
- **Cancel and Resend return to the page they were pressed on**, via a posted
  `next` validated with `url_has_allowed_host_and_scheme` — trusting a
  form-posted redirect target is an open redirect, and there is a test for
  three hostile values.
- **One form, two `formaction` buttons.** Two forms stack, because a form is
  block-level and no `text-align` moves a block.
- **The save flash is gone**; the notice on `bio-me` says all of it and stays.
  Cancel and Resend keep theirs, because there the callout *disappears* and a
  thing vanishing is not an explanation.

### Two tests were passing for the wrong reason, and both got sharper

Neither was wrong when written; both stopped discriminating once the notice
appeared on the profile page.

- `test_profile_page` asserted the pending address was **absent** from
  `bio-me`. The owner's own notice now names it deliberately, so the assertion
  failed for correct behaviour. The real property is "do not *publish* an
  unverified address", and publishing is the `mailto:` link — now
  `assertContains('mailto:paul@…')` and `assertNotContains('mailto:new@…')`,
  which is stricter than what it replaced (the old one passed if the address
  vanished entirely).
- `test_the_member_is_told_the_change_is_pending` asserted the address appeared
  after saving. With the flash dropped it would have kept passing — off the
  notice instead. Repointed at the notice explicitly, and verified to fail when
  the include is removed.

**Not done here, deliberately:** `unique=True` on `User.email`. Those rows would
fail the migration, and reconciling them is a data question with a human in it.
Requirement 6 says so; it stays a follow-on once the data is clean.

**OPEN, Brian to decide (raised 2026-08-22, deferred):** should
`core/message_list.html` move into `v3/base.html` for all 58 V3 templates? The
measurement that makes it decidable: all **22** `messages.*` call sites live in
exactly four modules (`messages` 13, `bio` 6, `user_photos` 2, `bandmap` 1),
and those map one-to-one onto the five templates that include the message list —
so the convention holds today, but only by hand, and the failure mode is a
message ambushing you on a later page rather than being dropped. All five
current includes sit under `v3/base.html`, so the move is clean; **they would
have to be removed, or messages render twice.**

**Next: task 06** (inbound → Cloudflare Email Routing) and task 07 (the smoke
tool), with task 03's DMARC week still the long pole.

## PLANNING — Step 16 task 06: the alias prune, which collapsed the critical path (2026-08-22)

No code and nothing touched in Cloudflare yet. Requirement 0's prune ran, and it
turned the task from one gated on five people into one that is **half executable
today by Brian alone**.

Brian asked all five destination owners; four answered.

| Owner | Answer | Effect |
|---|---|---|
| Rick | wants none | `hellbenders@` `meltdowns@` `volcanos@` dropped — **destination gone** |
| Ivan | keep all but `madeira@surfguitar101.com` | three kept — **destination stays** |
| Dane | drop | **gone** |
| Patrick | drop | **gone** |
| Todd | no answer yet | undecided, and it gates nothing yet |

Plus Brian's own, needing nobody: `store@surfguitar101.com` and
`brian@themadeira.net` dropped, `admin@themadeira.net` kept.

**21 rules → 13. Six destinations → two.**

### The consequence neither of us had stated: `surfguitar101.com` is now 100% Brian

All six of its surviving rules point at `bgneal@gmail.com`. Ivan's
`madeira@surfguitar101.com` was the only external address on that zone, and he
is the one who asked to drop it. **So the domain carrying `admin@`, `no_reply@`,
`postmaster@` and the site's entire mail identity has no third-party dependency
at all** — it can be migrated start to finish, today, waiting on nobody. Only
`themadeira.net` needs Ivan.

It is also the better rehearsal: every address on it is Brian's to test by
mailing it and watching it arrive, and any surprise is his to fix immediately
rather than discovered on someone else's mail.

### What survives, and why — recorded so a later prune cannot remove it by accident

`admin@surfguitar101.com` is `DEFAULT_FROM_EMAIL` **and** `SERVER_EMAIL`
(`settings/base.py:236,244`) — the From on every site email and on Django's
error mail — and is published as a mailto in `potd/view.html:53`.
`no_reply@` is `GPP_NO_REPLY_EMAIL`, the From on PM, contact-form and flag
notifications, and **bounces today** because no such alias exists.
`podcast@` is published as a mailto in `podcast/base.html:27`. `postmaster@` and
`abuse@` stay on both zones per RFC 2142. Each rule row in the task file now
carries its reason.

`store@` was checked rather than assumed: `/store/` is an "Editor's Choice"
recommendations page whose every item links out to Amazon, John Blair's site or
reverbjunkiesfilm.com. The site sells nothing itself, there is no order flow, and
the page publishes no address. Nothing in the repository referenced `store@`.

### Two mechanism facts that changed the plan's shape

**MX is per-zone, and the two domains are independent.** Requirement 1 said
"verify all remaining destinations before touching any MX record", which reads as
both domains gating any flip — and that misreading is exactly what would have
made `surfguitar101.com` wait on Ivan for no reason. Reworded to gate per zone.

**Verification and MX are independent actions.** Verifying a destination is a
click in the owner's inbox recording consent; it publishes no DNS, routes no
mail, touches Postfix not at all, and never expires. **So Ivan verifying does not
oblige anyone to flip `themadeira.net`** — that zone can sit fully staged, rules
created and destination verified, with MX still pointing at jaguar and mail still
arriving exactly as it does today, indefinitely. The only real deadline is Step
21's cutover.

### `todd@themadeira.net` — undecided, and the earlier recommendation was wrong

The task file had recommended routing `todd@` to Brian as a holding pen, on the
reasoning that Todd would otherwise block everything on one person. **Brian
objected, and the objection is sound: people writing to `todd@` are writing to
Todd, and he never agreed to Brian reading it.**

The recommendation was wrong on a second count too, which the objection exposed:
`themadeira.net` is gated on Ivan regardless, so the pen removed no blocker. It
traded someone else's mail privacy against a scheduling problem that does not
exist. Combined with the independence fact above, **the default is simply to
wait, at no cost.** Requirement 3a now records three options — wait (default),
drop and let it bounce (what Rick, Dane and Patrick chose), or the pen for a
genuine deadline — and the one thing that must not happen either way: flipping MX
with a destination unverified, which makes Cloudflare accept the rule and then
silently discard.

### Where it stands

**Phase 1 (`surfguitar101.com`) is unblocked and is now transcription.** Verify
Brian's own destination, create six rules, write down the rollback value
`10 mail.surfguitar101.com` (not the `_dc-mx` name — task 03 superseded that
2026-08-17), publish MX as its own deliberate step, test six addresses.
**Do not let Cloudflare's enable-Email-Routing wizard publish MX as a
convenience step** — that is the one change here that breaks something real.

**Phase 2 (`themadeira.net`) is staged but deliberately parked**, pending Ivan's
click and a decision on Todd. **Todd answered 2026-08-23 — see the execution
section below; the decision is no longer open.**

## Step 16 task 06 Phase 1 — `surfguitar101.com` inbound is Cloudflare's — DONE 2026-08-23

No code. Six routing rules, one verified destination, four DNS records written
and one deleted, all by hand in the dashboard and through the API. **Inbound mail
for `surfguitar101.com` no longer touches jaguar.** Phase 2 remains staged.

### What is live

| Change | Value |
|---|---|
| MX | `41 route1` / `46 route3` / `98 route2 .mx.cloudflare.net` |
| MX removed | `10 mail.surfguitar101.com` — **rollback value, recorded before the flip** |
| Rules | `admin@` `no_reply@` `podcast@` `postmaster@` `abuse@` `brian@` → `bgneal@gmail.com` |
| Catch-all | **left Disabled** — so dropped aliases are refused, not silently discarded |
| `cf2024-1._domainkey` TXT | Cloudflare's Email Routing DKIM key, 2048-bit |
| Apex SPF | rewritten — `a` and `mx` dropped, `include:_spf.mx.cloudflare.net` added |

All six addresses tested end-to-end from an Outlook mailbox — **per address, not
sampled**, which is what the acceptance criterion asks for. `no_reply@` delivers
instead of bouncing, the one change members will notice.

**The staged-then-flip sequence worked exactly as intended.** The three Cloudflare
MX records were added while `10 mail.surfguitar101.com` still existed; priority 10
kept winning, so every sender continued to reach jaguar and nothing changed until
the single deletion. That deletion was the entire cutover. **Additions before the
deletion is the load-bearing ordering** — reversed, there is a window with no MX
at all, where senders fall back to the apex A record, which is Cloudflare's HTTP
proxy and does not answer on port 25.

### The wizard trap was real, and worse than the task file recorded

Requirement 6 warns against letting Cloudflare's flow bundle the MX change. The
**Add missing records** button proposed five records at once with no per-record
control, and **one of them was a second apex `v=spf1` string**:
`v=spf1 include:_spf.mx.cloudflare.net ~all`. Publishing it alongside the existing
apex record is a `permerror` at every receiver — task 03's Finding 4, which notes
it *"fails harder than publishing no SPF at all."* The button was never pressed;
the three MX records went in by hand instead.

**A second reason not to press it emerged later.** After the MX records were added
manually, the Settings page still reported **all five records missing**, the three
correct MX records included. Cloudflare tracks records it created itself by ID, so
hand-made records read as absent even when the values match exactly. Pressing the
button at that point would have added three *duplicate* MX records. **The panel is
cosmetic and will keep saying missing** — the DNS is right and the mail flows.

### Two deliverability defects, both found by reading a real header

The first messages landed in Gmail's spam. Rather than accept that as
new-forwarder friction, one delivered message was read in full, and it named two
distinct faults:

```
dkim=permerror (no key for signature) header.i=@surfguitar101.com header.s=cf2024-1
spf=fail   ... does not designate 104.30.8.10 as permitted sender
```

**Defect 1 — Cloudflare signs forwarded mail as your domain, with a selector that
was not published.** Every forwarded message carried *two* signatures: one for
`cloudflare-email.net`, which passed, and one for `surfguitar101.com`, which
permerrored because `cf2024-1._domainkey` did not exist in the zone. A failing
signature scores worse than no signature. It was recorded as *optional* when the
record list was first reviewed — correct as to routing, wrong as to
deliverability.

**Defect 2 — CORRECTION: Email Routing forwards under *your* domain, and does
need your SPF authorization.** This document's earlier reasoning — that Cloudflare
forwards with its own envelope sender and therefore needs nothing from the apex
record — was wrong, and the Return-Path says so:

```
Return-Path: <SRS0=TCQU=qg=outlook.com=bgneal43@surfguitar101.com>
```

Cloudflare's SRS rewrite lands in **`@surfguitar101.com`**, so the forwarding hop
is evaluated against the apex record and hard-failed under `-all`. That is why
Cloudflare proposes an SPF record at all. **The objection to *how* it proposes it
still stands**: the fix is to merge the include into the existing record, never to
publish a second one.

### The DKIM key is shared across Cloudflare's customer zones — confirmed by test, not assumed

The dashboard truncates the key with an ellipsis, and the API endpoints that serve
it (`/email/routing` and `/email/routing/dns`) refused a token holding
`Zone → Email Routing Rules → Read`, `Zone → DNS → Edit` and an account-level
Email Routing permission. `/email/routing/rules` worked, so the token was valid and
the permission that opens those two endpoints was not discoverable by guessing.

The key was instead taken from `cf2024-1._domainkey.cloudflare-email.net` on the
hypothesis that Cloudflare uses **one shared signing key** — argued from the
selector name being identical on their domain and ours, where a per-customer key
would carry a per-customer selector the way Postmark's `20260817033844pm` does.

**The prefix match proved nothing and was explicitly not treated as evidence**:
`MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA` is the fixed DER/SPKI header of
*every* 2048-bit RSA key. It establishes key size, never identity. So the
hypothesis was published and then tested, with the two outcomes named in advance —
`pass` confirms, `fail` refutes and the record comes straight back out:

```
dkim=pass header.i=@surfguitar101.com header.s=cf2024-1
```

**Confirmed.** Cloudflare's Email Routing DKIM key is shared across customer
zones. Nothing in the planning documents knew this.

*Incidentally this is the domain's first 2048-bit key — both existing selectors,
`dkim` and `20260817033844pm`, are 1024-bit — and at 420 bytes it exceeds the
255-byte DNS string limit and is stored as two strings. That is exactly the
incidental cost task 03's Correction 1 predicted for a hypothetical Postmark
rotation; it turned up here first.*

### Finding 3's prediction came true, on the day the MX moved

Task 03's Finding 3 said `mx` *"becomes actively wrong the moment inbound mail
moves to Cloudflare Email Routing, at which point `mx` would authorize
Cloudflare's inbound MX hosts to send outbound as this domain."* Measured
immediately after the flip:

```
a  -> 172.67.218.217, 104.21.53.213     (HTTP proxy)
mx -> 162.159.205.11-.25                 (Cloudflare's inbound MX hosts)
```

Neither covers the forwarder, so neither accidentally rescued Defect 2. The apex
record was rewritten in place — **one record updated, never two coexisting**:

```
before:  v=spf1 a mx ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 -all
after:   v=spf1 ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 include:_spf.mx.cloudflare.net -all
```

This **partially executes task 03 step 5 ahead of its scheduled slot** at the
Postmark cutover, because live forwarding created the need tonight. Postmark's
`include:spf.mtasv.net` deliberately stays out until then. `-all` is kept; jaguar
stays authorized by the explicit `ip4:`; DNS lookups drop from 2 to 1.

Final state of a forwarded message, all four verdicts green:

```
dkim=pass  @cloudflare-email.net / @surfguitar101.com / @outlook.com
spf=pass   104.30.8.10 designated
dmarc=pass
```

### Requirement 3a is settled, and none of its three options is what happened

**Todd answered 2026-08-23: keep the alias, and move it to `member35@example.com`.**
Requirement 3a framed the choice as *wait (default) / drop / holding pen* — all
three of which presuppose continued silence. He broke the silence, so the question
the requirement was built to answer no longer exists.

Two consequences. **It is a new destination, not a re-point** — the Gmail address
is unverified and needs its own click, so Phase 2 now waits on two third-party
verifications, Ivan's and Todd's, rather than one. And **the privacy objection
that killed the holding pen is retired**: Todd has now said where he wants his
mail to go, which is the consent the pen would have manufactured.

**Neither verification gates anything until MX moves**, per the independence fact
already recorded above: `themadeira.net` can stage fully — Email Routing enabled,
all seven rules created, both destinations pending — with MX still pointing at
jaguar and mail arriving exactly as it does today, indefinitely.

### Loose ends

- **`admin@surfguitar101.com` was briefly added as a *destination* by mistake**,
  and Cloudflare rate-limited its deletion. It was inert throughout — no rule
  targeted it — and it was **deleted 2026-08-23**. Its verification mail was
  deliberately left unclicked: verifying an address on a zone Cloudflare routes is
  the shape that creates forwarding loops.
- **`_dmarc`'s `rua` includes `admin@surfguitar101.com`**, so the local-copy path
  that feeds `tools/dmarc_report.py` now runs through Email Routing rather than
  Postfix. Reports should keep arriving; **the eighth reading should confirm receipt
  rather than assume it**, since the `p=none` → `quarantine` decision rests on them.
  **CLOSED 2026-08-24** — six reports arrived in the Gmail copy, four organizations,
  none of them in jaguar's maildir. See the eighth reading, which also records that
  receipt is established by the absence of any other path rather than from a
  `Received` chain.
- **Jaguar still holds `surfguitar101.com` in `virtual_alias_domains`**, so mail
  the old box originates to these addresses is delivered by its local alias table
  and never consults MX. Tests must come from an external mailbox. It also means
  `no_reply@` still bounces *locally* — inert, since nothing sends to it.
- ~~Sending **from the site** has not been exercised since the apex SPF
  rewrite.~~ **CLOSED 2026-08-23 by a live contact-form submission** — the one
  loose end that was reasoning rather than measurement:

  ```
  spf=pass   173.255.245.115 designates, smtp.mailfrom=no_reply@surfguitar101.com
  dkim=pass  header.i=@surfguitar101.com header.s=dkim
  dmarc=pass header.from=surfguitar101.com
  ```

  **Dropping `a` and `mx` cost nothing** — jaguar passes on the explicit `ip4:`.
  Two incidentals: the envelope sender reads `no_reply@surfguitar101.com` rather
  than a bare local part, which is task 10's `sender_canonical` rewrite observed
  on live mail; and unlike the forwarded test messages this one is
  `header.from=surfguitar101.com`, so it is *this* domain's DMARC being
  evaluated and it will appear in the next aggregate report as an aligned pass.

**Next: Phase 2 (`themadeira.net`)** — enable Email Routing MX-less, create the
seven rules, request verification from Ivan and from Todd at his new address. Then
task 07's smoke and cutover verification, which now has the Outlook mailbox it had
been waiting for.

## Step 16 task 03 step 7 — `p=quarantine` published 2026-08-25 — the monitor phase is over

**The policy was tightened the same day the Postmark path was first measured, and
the ordering is the point.** The case for tightening on 08-24 rested on ten clean
readings of the sender being *retired*. The case acted on rests on the sender
being *adopted*: Postmark measured at two receivers, aligned on both mechanisms,
landing in a Microsoft inbox. Those are different arguments and only the second
one covers the mail this domain is about to start sending.

```
before:  v=DMARC1; p=none;       rua=mailto:00fc…@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com
after:   v=DMARC1; p=quarantine; rua=mailto:00fc…@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com
```

One word changed; `rua` byte-identical with both destinations intact. **Verified
authoritatively: exactly one `v=DMARC1` string at `_dmarc`, TTL 300**, so rollback
to `p=none` propagates in five minutes.

`p=none` ran **2026-08-17 → 2026-08-25**, nine days, eleven readings, four
reporting organizations, eight receiving domains, one sending source until today,
and **zero messages aligned on neither mechanism in any window from any
reporter.**

### The quoting warnings are cosmetic, and the hazard is obeying them

Cloudflare's DNS editor flagged several TXT records as needing quotes, while
indicating it would publish them with quotes anyway. **That warning is about the
input field, not the stored value.** DNS transports TXT as quoted
character-strings regardless, so Cloudflare supplies the quoting at publish time.

**The failure mode is typing the quotes in.** That produces *double* quoting —
literal `"` characters inside the string — turning `v=spf1` into `"v=spf1`, which
matches nothing, or a DKIM key into one that no longer verifies. Both fail
silently, which is the recurring shape of every defect in this step.

**Audited rather than assumed.** Twelve mail-related TXT records across both zones
checked for embedded literal quotes: **zero**. All five DKIM keys decoded with
`openssl rsa -pubin`:

| Selector | Decodes |
|---|---|
| `dkim._domainkey.surfguitar101.com` | 1024-bit |
| `20260817033844pm._domainkey.surfguitar101.com` | 1024-bit |
| `cf2024-1._domainkey.surfguitar101.com` | 2048-bit |
| `dkim._domainkey.themadeira.net` | 1024-bit |
| `cf2024-1._domainkey.themadeira.net` | 2048-bit |

**Left alone deliberately.** Same reasoning as the `ns1`–`ns5.linode.com` rows and
the decision not to grey-cloud `mail.themadeira.net`: cosmetic warnings on working
records, and tidying them during a mail cutover converts one change into several.

**Incidental worth recording: Postmark's selector is 1024-bit**, the same size
task 03's Finding 2 objected to in the legacy `dkim` key. The provider move did
not upgrade key size. Postmark issues 1024 by default and supports rotation to
2048. Not acted on — it passed at both Gmail and Outlook today — but the finding
that prompted the audit is not actually resolved by the migration that was
supposed to resolve it.

### DEFECT found 2026-09-04 in the DEPLOYED `main` BRANCH — over-long body lines break DKIM, and the modernize branch already fixes it

**Three messages signed by jaguar's `opendkim` failed DKIM verification at Google**
— one in the 09-02 window, two in 09-03 — and survived only because SPF was
aligned. The raw message for `44C7F5864DF` closed it the same evening; the
nineteenth reading and its addendum in `research/dmarc-readings.md` carry the
evidence, including two hypotheses fitted and falsified on the way.

**The mechanism, measured on two of the three messages.** jaguar runs `main` on
**Django 1.8.15 / Python 2.7**, which never wraps a body: `utf8_charset.body_encoding
= None` is unconditional there. `opendkim` signs the unwrapped body in `cleanup`
with `c=simple/simple`. Postfix's `smtp` client then enforces
`smtp_line_length_limit = 998` on delivery, inserting CRLF+SPACE **at a byte
offset** — both observed breaks cut a token in half — so Google hashes a body that
is not the one that was signed: `dkim=neutral (body hash did not verify)`. **The
first wrap point measured at exactly 998 bytes in both messages**, independently.

**The trigger is line length alone.** `44C7F5864DF` is 8-bit Cyrillic and
`0077E586513` is 7-bit pure ASCII, and both fail identically — charset and transfer
encoding do not enter into it. Long lines have two sources: a member (or spammer)
typing 3,000 characters into the contact form, and **Celery's failure reports, which
`repr()` the whole task kwargs onto one physical line** and can manufacture one out
of any large argument.

**No code change is needed: the modernize branch already fixes it.** Django's
`SafeMIMEText.set_payload` (ticket #22561) selects a quoted-printable charset
whenever a body line exceeds `RFC5322_EMAIL_LINE_LENGTH_LIMIT`, and 1.8.15 predates
it. Verified on the bench under this repo's venv rather than read off a changelog:

| Running | 3,440-byte body line |
|---|---|
| jaguar, Django 1.8.15 | `8bit`, Postfix wraps it, signature breaks |
| modernize, Django 5.2.17 | `quoted-printable`, **zero lines over 998 bytes on the wire** |

**Two fixes to avoid, if it is ever tempting to patch `main`.**
`Canonicalization relaxed/relaxed` does not help — an inserted line break survives
relaxed body canonicalization. Raising `smtp_line_length_limit` is worse than the
defect: RFC 5321 §4.5.3.1.6 caps a line at 1,000 octets including CRLF, so 998 is
the standard and the site is what violates it. Hard-wrapping in
`core.functions.send_mail` would also be wrong — it edits what the member wrote,
where a transfer encoding leaves the content untouched.

**Step 21 fixes this at the source rather than hiding it**, which corrects this
entry's first draft. What remains is the interval: until the deploy, every
over-long line the legacy site emits loses its DKIM signature and rides on SPF
alone.

**Bearing on step 7's successor.** `p=reject` stays unrecommended until after the
Step 21 deploy — not because the cause is unknown, but because the fix is not
deployed yet. The DSN class remains one mechanism deep by design. Nothing argues
for reversing `p=quarantine`; every disposition in all sixty-eight reports is `none`, and
the captured message itself reads `dmarc=pass ... dis=NONE`.

**Still open:** whether `B4EFD5864BF` (6,050 bytes) is the same class — the one of
the three still assigned by shape rather than observed — and the standing prediction
that this class goes to zero at the Step 21 deploy, which the reading log will
report without anyone arranging it.

**Confirmed 2026-09-05 by the twentieth reading:** the 09-04 window carried three
Google-bound messages of 5,963–6,079 bytes — all larger than any of the three that
failed — and Google reported no signed-DKIM failure at all. **The size fit is dead
from both sides**, 08-31 below the threshold and 09-04 above it, and the
line-length mechanism is the only surviving account. A clean window cannot confirm
it, only fail to contradict it; the confirming test is the next window that carries
a body line over 998 bytes.

**The class recurred 2026-09-08 in the twenty-first reading** — a fifth message, in
Google's 09-05 window, taking it to 4 rows and 5 messages. That reading identifies
nothing further: the five candidates in the window size 728 to 6,254 bytes, which
brackets `B4EFD5864BF` from both sides, and the daily `brian` cron message sits at
the head of *every* Google window because the UTC−7 day opens at `02:00` local and
that message goes out at `02:01` — so neither size nor injection path discriminates.
The aggregate report carries no message identifier and the bodies are gone from the
queue. **The confirming test is unchanged and still unrun.**

**The class did not recur 2026-09-12 in the twenty-second reading**, and the
absence is weaker than it looks. Five Google windows have been filed since the
last occurrence in 09-05 — 09-06, 09-08, 09-09, 09-10, 09-11, carrying 6, 7, 14,
10 and 9 messages — and none carries a `pass`/`fail` row. The class stands
unchanged at 4 rows and 5 messages. **But Google filed nothing for the 09-07
window, which carried 20 messages** — more than any window that was filed, and
more than twice their median. The largest untested window in the series is the one
with no report, so the "before" half of the Step 21 before/after has a hole in it
that no later reading can fill. See *The 09-07 reporting hole* below.

**⚠️ CORRECTED 2026-09-12 — this class is 3 rows and 4 messages, not 4 and 5, and
has been over-counted since the nineteenth reading.** Google's 09-07 report,
recovered from Gmail the same afternoon, made the discriminator visible: the DSN
class carries **no `<dkim>` element at all** and SPF on the HELO name
`mail.surfguitar101.com`, while this class carries a `<dkim>` element failing on
`surfguitar101.com`. **The 09-01 message is unsigned** — it is the DSN the
eighteenth reading had already identified, absorbed one reading later into a class
defined as *"not the bounce class"*. Corrected: **over-long-line = 3 rows, 4
messages (09-02, 09-03 ×2, 09-05)**; DSN in reports = 2 rows, 3 messages (09-01,
09-07 ×2). Both classes render identically in the *evaluated* fields that
`tools/dmarc_report.py` prints and every tally was built from, which is how five
readings shared one error. [[suspect-the-measurer-before-the-record]]

**The standing prediction is unaffected in direction** and now has a smaller,
cleaner "before": 4 messages across 3 windows, all signed, all at Google. The DSN
class is not expected to reach zero at the deploy — it appears whenever something
bounces — which is exactly why conflating the two would have made the before/after
unreadable.

**RESOLVED the same day by the twenty-second reading's addendum, and the class did
not recur.** Cloudflare's dashboard for 09-07 reads `SPF aligned 26 (100%)`,
`DKIM aligned 24 (92.31%)`, `IP count 1` — two `pass`/`fail` messages from jaguar
alone, which is this class's exact signature. **They are the DSN class instead.**
jaguar's log carries exactly two null-sender messages on Sep 7, `CF7C258658B` at
`03:01:01` and `C781A5865B2` at `15:59:18`, and they are the only two between
`Sep 6 06:47` and `Sep 12 13:05`; both are Google-bound and both fall in the UTC−7
09-07 day. DSNs bypass the milters and carry no signature, and SPF falls back to
the HELO name, which aligns relaxed. **The over-long-line class stands at 4 rows
and 5 messages, and the "before" half is intact** — 09-07's 20 Google-bound
messages produced no signed-DKIM failure. The discriminator was the eighteenth
reading's own prescription, `grep 'from=<>'` on the mail log, used for the first
time here.

### RESOLVED 2026-09-12 — The 09-07 reporting hole is in our collection path, and Yahoo alone did not file

Found by the twenty-second reading. Five days after the window closed, the
2026-09-07 window is missing three of the five endpoints that had mail in it:
`google.com` (20 messages in its UTC−7 day), `yahoo.com` (2, UTC) and `aol.com`
(1, UTC). `protection.outlook.com` (2) and `comcast.net` (3) both filed for the
same window and both reconcile exactly with the send log.

**CLOSED 2026-09-12: Google's 09-07 report was recovered from Gmail** at 14:39 and
is now in `~/dmarc`, holding the predicted 20 messages. The window stands at 25
across three endpoints against Cloudflare's 26, so **`aol.com`'s single-message
09-07 report is the entire remaining gap** — searched for in Gmail and not found.
The reasoning below is kept because it is what identified the file to look for.

**Two explanations, and the reading cannot separate them.** Either the three
reporters did not file, or they filed and the reports never reached `~/dmarc` —
the `rua` local copy runs `admin@surfguitar101.com` through Cloudflare Email
Routing to Gmail and is saved by hand. Three simultaneous absences across three
independent organizations favor the collection path; against that, Microsoft's own
09-07 report arrived four days late, so "absent at five days" is not "never sent".
**AOL has not filed since the 08-31 window** and the single AOL-bound send the log
covers (09-07) has no report; Yahoo's absence is two windows wide before it resumes
at 09-09 with an exact report — which is what one lost delivery batch would look
like.

**The test does not go through our mail at all and should be run before the next
reading.** `_dmarc`'s other `rua` destination is
`00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net`, verified intact
2026-09-12. If Cloudflare's dashboard shows Google, Yahoo and AOL volume for
2026-09-07, the reports were filed and our collection path lost them — and
re-downloading may still close the hole. If it shows the same gap, three reporters
skipped the window.

**Why it costs more than one window.** 09-07 is the largest Google day in the
current log, and the signed-DKIM failure class the Step 21 before/after depends on
is measured only from Google's reports. The entry above says what that costs.
[[probes-must-not-perturb-what-they-measure]]

**ANSWERED the same afternoon.** Cloudflare DMARC Management (zone → Email),
Report detail for September 7 2026: **volume 26**, DMARC pass 26 (100%), SPF
aligned 26 (100%), DKIM aligned 24 (92.31%), IP count 1. **26 against the 5 in
`~/dmarc` — the reports were filed and our collection path lost them.**

**Yahoo is the only endpoint that genuinely did not file.** 26 decomposes as
Google 20 + Comcast 3 + Microsoft 2 + AOL 1; the only way to reach 26 is to drop
one of the two 2s, and Microsoft's report is a file in `~/dmarc` so it reached
Cloudflare on the same record's other `rua` destination. **AOL filed and we lost
it** — the opposite of what the entry above suspected. The decomposition is
arithmetic over one total, not reporter identity, which this dashboard never
shows; re-downloading the 09-07 reports would settle it by observation.

**What the window costs is the row detail, not the measurement.** Volume and
alignment rates survive; source IPs, `policy_published`, `envelope_to`, Report-IDs
and reporter identity do not, so 09-07 can never be reconciled
endpoint-by-endpoint. The Step 21 before/after is unaffected — see the class entry
above, where the window's two DKIM failures resolve as bounces.

**The open item is now the collection path itself, and it is wider than one
window.** `admin@surfguitar101.com` runs through Cloudflare Email Routing to Gmail
and is saved by hand; something there dropped **two of the four reports filed for
09-07, carrying 21 of its 26 messages**, while keeping the other two. **Every
earlier window in this log was collected the same way,
so the corpus totals are a floor rather than a census.** Cloudflare's view is the
control that can measure the gap across the series, and reading it against the log
belongs before the Step 21 window, not during it.

### A second forwarder appears at web.de, and it is the first forwarding measured under the tightened policy — 2026-09-12

Four new source IPs in Google's 09-09 → 09-11 windows, all reversing to
`mout.web.de` and registered to 1&1 Mail & Media / IONOS, verified by lookup.
Seven messages, every one `dkim=pass` on `d=surfguitar101.com`, `spf=fail` because
the forwarder rewrote the envelope sender into `web.de`, every one delivered
`disposition=none`. They reconcile exactly with seven sends to one address,
`member29@example.com`, and fall in the same UTC−7 days Google reports them in.

**The mechanism is the one the fourth and fifth readings described at
`209.85.220.41`** — a member mailbox auto-forwarding site mail onward, From header
preserved, signature intact, SPF unalignable. It is member-side configuration with
nothing to fix on the box. **What is new is the conditions:** those earlier
observations were made under `p=none` or in the first days of `p=quarantine`, and
were used to argue that a tightening *would not* strand forwarded mail. These
seven ran under live `p=quarantine` and a live `-all` SPF record. The argument is
now a measurement taken after the tightening rather than a prediction about it.

**Bearing on the deferred `p=reject` decision.** These seven are precisely the
mail `p=reject` would put at risk, and they are at risk only through DKIM — one
broken signature on that path and the forward is refused rather than quarantined.
That is the quantity to set beside the decision, not an argument against it, and
it is small: one recipient, one forwarder.

### FIXED 2026-09-04 — `ContactForm.subject` refuses newlines at the form — `c2c84441`

Found by reading the production error that turned out to be `0077E586513`. A
contact-form submission arrived with a trailing CRLF in the subject — a header
injection attempt — and Django's `forbid_multi_line_headers` refused it. **The
protection worked and still works.** What follows it is the problem.

| Subject | Django 1.8.15 (jaguar) | Django 5.2.17 (modernize) |
|---|---|---|
| trailing `\r\n` — the live payload | `BadHeaderError` | stripped by `CharField(strip=True)`, sends fine |
| newline in the **middle** | `BadHeaderError` | **`BadHeaderError` still** |

`strip()` only touches the ends, and `contact/forms.py` declares
`subject = forms.CharField()` with no newline validation. Because
`core.functions.send_mail` defers to Celery, the exception lands as a task failure
and an admin error report containing the entire submission, rather than as a
validation error the submitter sees — and that report is itself a source of
over-long lines.

**A hardening, not an emergency.** The injection is blocked either way. What was
wrong is *where* the rejection surfaced.

#### The fix: `clean_subject()`, four tests, four mutations

`contact/forms.py` gains one field-level clean beside `clean_honeypot`, raising
`forms.ValidationError` on `'\n'` or `'\r'`. Both characters rather than
`splitlines()`: a lone CR terminates no header, but it has no business in a
single-line field.

**Two alternatives were considered and rejected**, and the reasoning is the part
worth keeping:

- **Flatten in `save()`**, copying `accounts/forms.py:247`
  (`''.join(subject.splitlines())`). **The precedent does not transfer.** There the
  newline comes from a template file that ends with one — known, benign, authored
  by us. Here it is adversarial input, and flattening would silently accept an
  injection attempt while rewriting what a member typed.
- **Guard in `core.functions.send_mail`.** It duplicates Django's
  `forbid_multi_line_headers`, which is already the backstop and is not going
  anywhere — and it would still raise inside the Celery task, so it does not fix
  the defect that was actually observed.

**Scope is `subject` alone, and the boundary was measured rather than assumed.**
`email` also reaches a header as `Reply-To`, but `EmailField` already rejects
`"a@b.com\r\nX-Injected: 1"`. `name` and `message` reach the body only.
`contact/views.py` reads `?subject=` into `initial`, which is re-validated on POST.

| Test | Pins |
|---|---|
| `test_embedded_crlf_is_refused` | the production shape; **asserts the message reaches the rendered page**, not just the form object |
| `test_embedded_lf_is_refused` | bare LF |
| `test_embedded_cr_is_refused` | bare CR |
| `test_trailing_newline_is_stripped_not_refused` | the payload that actually arrived, which `CharField(strip=True)` already made safe |

**The RED run reproduced the production defect in the suite.** Before the fix the
three refusal tests failed by redirecting to the thanks page — the form validated,
`save()` ran, and the send died unseen inside eager Celery. **`mail.outbox` is
empty in both the broken and the fixed case**, so that assertion does not
discriminate and the tests' teeth come from the form error and the rendered body.
A test that had asserted only "no mail was sent" would have passed against the bug.
[[mutation-verify-or-it-is-not-coverage]]

**Mutation battery — 5 of 5 caught**, each by the expected test, file restored
byte-identical each time:

| Mutation | Caught by |
|---|---|
| `if False:` — guard neutered | all three refusal tests |
| drop the `'\r'` check | `test_embedded_cr_is_refused` |
| drop the `'\n'` check | `test_embedded_lf_is_refused` |
| reword the error message | all three refusal tests |
| `CharField(strip=False)` | `test_trailing_newline_is_stripped_not_refused` |

Dropping `'\n'` does **not** fail the CRLF test, because `\r\n` still contains a
CR. That test is caught by either half of the condition and so discriminates
neither; the two single-character tests are what separate them.

**One mutation initially reported a false pass** — a shell-quoting slip meant the
pattern never matched, the file was never modified, and the run printed `OK`
against unmutated code. Caught by an assertion on the replacement count. A
mutation that does not apply is indistinguishable from a mutation that is caught,
which is why the count is asserted rather than the edit assumed.
[[suspect-the-measurer-before-the-record]]

**Verification:** 1,117 tests green under `docker_test`, and green again under the
deprecation gate as a separate run. Test count 1,113 → 1,117.

**Browser pass — 2026-09-04, by Brian.** Confirmed in the running stack, which is
the only thing that can confirm it: a plain `<input type="text">` cannot carry a
newline at all, because the HTML value-sanitization algorithm strips CR and LF —
`input.value = 'a\nb'` is silently cleaned. The field was replaced with a
`textarea` from the DevTools console to get the character in. **That is the finding
the browser trip actually produced: this defect is unreachable from a browser and
only a scripted POST can raise it**, which is consistent with the payload that
arrived, and is why the suite is the primary evidence here rather than the
exception.

### Rollback

```
v=DMARC1; p=none; rua=mailto:00fc656c22e64e73bb643fb00331d013@dmarc-reports.cloudflare.net,mailto:admin@surfguitar101.com
```

Edit the existing record. **Never add a second one** — two `v=DMARC1` strings at
`_dmarc` means the domain is treated as having no DMARC record at all, losing
policy *and* reporting silently. Same class as the double `v=spf1` string that
Finding 4 identified and that Cloudflare's **Add missing records** button still
offers to create.

### What the next reading answers

Three things land in the 2026-08-25 window's reports, and the eleventh reading
should check each:

1. **`policy_published` should read `p=quarantine`** — the receivers confirming
   they see the change, as distinct from `dig` confirming it was published.
2. **A second sending source should appear** — `50.31.156.116` and/or `.118`,
   Postmark, SPF and DKIM both aligned. That would be the first non-jaguar source
   in eleven readings. Its *absence* would be the more significant result: it
   would mean the reports are not seeing everything this domain sends.
3. **Dispositions should stay `none`.** Only failing mail earns a `quarantine`
   disposition, so an all-`none` window remains the healthy state and is not
   evidence the policy failed to take effect. Item 1 is what distinguishes those.

**ANSWERED 2026-08-26 — see the eleventh reading. 2 and 3 landed; 1 did not, and
that is a timing property rather than a fault.** Postmark's `50.31.156.116`
appears in Google's 08-25 report with both mechanisms aligned, every disposition
across all fourteen files is `none`, and all three 08-25 reports still print
`p=none`. The record resolves as `p=quarantine` from both nameservers, and Yahoo
generated a `p=none` report at 05:43:03Z on 08-26 — hours after publication —
which shows `policy_published` reports the policy *applied during the window*,
not the record as it reads at generation time. **Corroborated the same day by a
second reporter** — Comcast filed for 08-25 at 01:46:46Z, also reading `p=none`;
see the eleventh reading's addendum in `research/dmarc-readings.md`. **The twelfth reading — 2026-08-27, covering 2026-08-26 —
returned two of three.** Google and `bellsouth.net` read `p=quarantine`;
`yahoo.com` read `p=none`, from the same reporter and the *same filing run* as
`bellsouth.net`. The record was re-verified from both authoritative nameservers
and is intact, and Google is enforcing the policy — an explicit `forwarded`
override on the one failing row. So the split is a per-receiving-domain rendering
question inside Yahoo rather than a defect in the zone, and the property above is
insufficient rather than refuted: it predicts both Yahoo reports agree, and they
do not. The 08-27 window settles it.

### When the reading log stops — exit condition set 2026-09-05

**Until now this was an open-ended commitment.** Twenty readings exist and nothing
in the plan, this file or the log's own preamble said what ends them. The readings
were opened to prove the authentication records correct and to raise the policy
safely, and **that job is finished**: `p=quarantine` has been live since
2026-08-25 across 62 reports, 397 messages, five reporting organizations and
eleven reporting endpoints, with every disposition `none`.

**Three open items keep the instrument running, and all three close at the Step 21
cutover:**

1. **The over-long-line DKIM defect** — the standing prediction is that the class
   goes to zero at the deploy. It is the cleanest before/after this project has,
   and it is worthless without readings on both sides of the cutover.
2. **The `p=reject` decision**, deferred by the nineteenth reading to *after* the
   deploy: identify the cause, re-measure on the new signer, then decide.
3. **Postmark has never appeared in an aggregate report** — absent since the 08-27
   window. The only evidence for that path is the two hand-sent test messages of
   08-25. The cutover is what makes it a reporting source, and these reports are
   the instrument that confirms it.

**UPDATED 2026-09-12 by the twenty-second reading.** `p=quarantine` now stands at
**80 reports, 511 messages**, eighteen days, every disposition `none` (the
figure includes Google's 09-07 report, recovered from Gmail that afternoon). A
**fourth**
item joins the three above and it is about the instrument rather than the domain:
**the collection path drops reports.** Cloudflare holds 26 messages for the 09-07
window against the 5 in `~/dmarc`: two of the four reports filed that day, carrying
21 of its 26 messages, were lost between Cloudflare Email Routing, Gmail and the
manual save. **Every
window in this log was collected that way, so every total in it is a floor rather
than a census**, and the reading that establishes how wide the gap is has not been
done. Cloudflare's own view is the control, it retains a limited history, and
reading it against the series belongs before the Step 21 window rather than during
it — which makes it the item to run first.

**UPDATED 2026-09-21 by the twenty-third reading.** `p=quarantine` now stands at
**101 reports, 639 messages**, twenty-seven days, every disposition `none`. Two of
the four items moved, in opposite directions, and **the cadence above is
unchanged** — weekly until the Step 21 window, daily across it, then stopped.

**Item 1 was quietly at risk and is now safe.** The over-long-line DKIM class had
been silent for thirteen Google windows, 09-06 through 09-18. Had it stayed
silent, the before/after would have become unmeasurable: a class already at zero
cannot be shown to *go* to zero at the deploy, and the cleanest before/after this
project has would have evaporated without anyone deciding to give it up. **It
recurred on 09-19** — one signed row, `<dkim>` element present, SPF on
`surfguitar101.com`, so the over-long-line class and not the DSN class — taking it
to 4 rows and 5 messages. The test is live again, and this is now the strongest
single reason to keep reading through the cutover.

**Item 4 has changed from a measurement task into a repair task, and the
measurement it asked for is no longer the urgent half.** The mechanism is found:
**there is no second copy of the report XML and has not been since 2026-08-23.**
See the register bullet below. What the item said — that the gap's width is
unmeasured — remains true, and Cloudflare's dashboard is still the control that
can measure it. What it did not know is that the designed redundancy had already
been retired by the MX flip, silently, three days after the amendment that
established its value. **Fixing the path matters more than sizing the hole**, and
the fix should not be built on jaguar, which is being decommissioned.

**One correction to how item 4 was framed.** It reads as though report collection
has no redundancy at all. The `_dmarc` record publishes **two** `rua`
destinations, and Cloudflare receives every report independently — so the
redundancy preserves **totals** but not **detail**: `org_name`, Report-ID,
`envelope_to` and the per-source rows exist only in the copy saved from Gmail.
That asymmetry is exactly what made 09-07 recoverable in aggregate and
irrecoverable endpoint-by-endpoint.

**Items 2 and 3 are unchanged.** `p=reject` stays deferred to after the deploy,
and Postmark has still never appeared in an aggregate report — no message in
fifteen days of mail log relays through `*.mtasv.net`.

**UPDATED again later on 2026-09-21 — item 4 is repaired, and the figures move.**
`tools/dmarc_fetch.py` replaced the manual save and recovered four lost reports
on its first run, so `p=quarantine` now stands at **105 reports, 658 messages**,
twenty-seven days, every disposition `none`. **Item 4 stops being the item to run
first**: the collection path is automated, and the width of the historical gap is
now known to be five reports rather than estimated. What remains of it is a
one-line habit — run the fetcher before each reading — and the standing caution
that totals recorded before today are floors. **Items 1, 2 and 3 still gate the
log's end and all three still close at the Step 21 cutover.**

The UTC−7 aggregation offset is the one live thread that gates no decision. It is
instrument characterization — a report whose day cannot be aligned is a report
that cannot be reconciled — and it should be finished on its own merits, not
because a step is waiting on it.

**CLOSED 2026-09-12 by the twenty-second reading.** The offset is a property of the
reporter, and both halves are now measured on multiple windows: **Google aggregates
on a UTC−7 day**, confirmed by four more exact reconciliations (09-08 through
09-11) with the `02:00` local boundary pinned inside a thirty-seven-minute gap;
**Yahoo, Cox and Microsoft aggregate on the true UTC day**, seven for seven across
the same span. The twentieth reading's Yahoo contradiction was not a contradiction
but the second rule. **A window label cannot be compared across reporters without
applying the right offset**, and every cross-reporter total in this log before the
eighteenth reading was computed without one. Cox is a Yahoo tenancy and follows
Yahoo, not a third rule — a fact the twenty-second reading established only after
its own first cut classified Cox-bound mail by relay name and made Yahoo's 09-10
report look wrong. [[suspect-the-measurer-before-the-record]]

**The cadence, from here:**

| Period | Cadence | Why |
|---|---|---|
| now → ~1 week before Step 21 | **weekly** | the last several readings confirm steady state; daily re-derives "nothing moved" at full cost |
| Step 21 window: ~1 week before → ~2 weeks after | **daily** | all three items above resolve in this interval, and the before/after needs both halves at the same resolution |
| after that | **stopped** | keep `tools/dmarc_report.py` for spot checks; a closed log with an exit condition is worth more than an open one nobody decided to end |

**One constraint that is not negotiable with the schedule: the send-side baseline
dies with jaguar.** Every reconciliation in this log — the endpoint-by-endpoint
agreement, the UTC−7 finding, both falsified DKIM hypotheses — rests on
`/var/log/mail.log`, which rotates at roughly two weeks and exists only while that
host runs. **Anything to be measured against jaguar's own outbound must be
measured before it is decommissioned.** After cutover the sending baseline comes
from Postmark's activity data instead: a different instrument, with different
retention, different granularity and no `status=sent` line to bin.
[[jaguar-decommission-planning]]

## Step 16 — Postmark measured at two receivers, 2026-08-25 — the new path is proven before cutover

**Two test messages sent through Postmark over SMTP as
`no_reply@surfguitar101.com`, before any application change.** This is the first
time the Postmark path has been observed at all: ten DMARC readings measured only
jaguar, and the ninth reading recorded that limit explicitly — *"they are no
evidence at all about Postmark."*

| Receiver | Result |
|---|---|
| **Outlook** | `spf=pass` (50.31.156.118), `dkim=pass header.d=surfguitar101.com`, `dmarc=pass action=none`, `compauth=pass reason=100`, **Inbox** |
| **Gmail** | `spf=pass` (50.31.156.116), `dkim=pass header.s=20260817033844pm`, `dmarc=pass`, `header.from=surfguitar101.com` |

### The Return-Path is in effect, and this settles the ordering question by measurement

```
smtp.mailfrom=pm_bounces@pm-bounces.surfguitar101.com
```

Both receivers evaluate SPF against `pm-bounces.surfguitar101.com`, which CNAMEs
to `pm.mtasv.net` publishing `v=spf1 include:spf.mtasv.net -all`. Both sending IPs
— `.116` and `.118` — are inside `50.31.156.96/27`, verified by range check. The
envelope domain is a subdomain of the header-from domain, so it **aligns relaxed
under `aspf=r`**.

**Postmark therefore arrives two mechanisms deep, not one.** The "ordering
requirement" — the claim that a first Postmark send under `p=quarantine` would
ride on DKIM alone before `include:spf.mtasv.net` reached the apex — was retired
on reasoning this morning and is now retired on measurement. Requirement 3 and
requirement 7 of task 03 both said so in advance; it took two headers to stop
arguing about it.

### The Postmark selector is confirmed signing, and the legacy selector is not involved

Gmail names it explicitly where Outlook did not:

```
dkim=pass header.i=@surfguitar101.com header.s=20260817033844pm
dkim=pass header.i=@pm.mtasv.net      header.s=pm20250806
```

**`20260817033844pm` has appeared in no aggregate report in any window** — that
absence is what ten readings used to conclude the cutover had not happened. It is
now observed signing a real message. The legacy `dkim` selector does not appear,
which is the direct confirmation that Postmark's path does not touch Postfix.

Two signatures ride together: Postmark's own `d=pm.mtasv.net` and this domain's
`d=surfguitar101.com`. Only the second aligns and only the second matters for
DMARC.

### Inbox at Microsoft, which is the premise of the entire step

`compauth=pass reason=100` and **Inbox, not Junk**, at the receiver task 07 names
as the only acceptance test that can distinguish success from failure — *"Gmail
already accepts this site's mail today... a verification that only checks Gmail
would have passed before any of this work."*

**Task 07's headline acceptance criterion is met. Task 07 is not done.**
`tools/email_smoke.py` does not exist. What is proven is the hard part — that a
message from the new path reaches a Microsoft inbox — not the tooling that would
prove it repeatably.

**Correction 2026-08-26: an earlier version of this paragraph said "the warm-up
has not been planned, and the warm-up is the part that matters for a list which
is 63% dormant." The warm-up was dropped on 2026-08-20**, five days before this
paragraph was written, and the 63% headcount is the figure that drop specifically
retired — 11.9% of a year's notification mail reaches 3+ year dormant accounts,
across 35 distinct addresses, and Postmark suppresses each after one hard bounce.
Brian caught it. What task 07 owes here is watching the bounce dashboard for two
weeks, not a staged send; the task file was corrected the same day.

### Consequences

- **`p=quarantine` is now safe for a reason it was not safe this morning.** The
  case for tightening rested on ten clean readings of the sender being *retired*.
  It now rests on the sender being *adopted*, measured at two receivers, aligned
  on both mechanisms.
- **Task 03 requirement 2's recorded limitation is closed.** It read: *"These
  reports are evidence that task 10's repairs worked; they are no evidence about
  Postmark."* There is now evidence about Postmark.
- **Task 02's deliverability risk is retired before a line of it is written.**
  What remains in that task is the retry and timeout on `core.tasks.send_mail`,
  which is application robustness, not deliverability.

### A prediction for the eleventh reading

These two sends should appear in the **2026-08-25 window** aggregate reports as a
**second source IP** — `50.31.156.116` and/or `.118` — with SPF and DKIM both
aligned and passing, alongside jaguar's `173.255.245.115`. That would be the first
non-jaguar sending source in eleven readings. If it does not appear, the reports
are not seeing everything this domain sends, which would matter more than the
result itself.

## Step 16 task 06 Phase 2 — `themadeira.net` MX FLIPPED 2026-08-25 — ✅ 7 of 7 addresses confirmed 2026-08-26

**Ivan verified `member36@example.com` on 2026-08-25**, which was the last gate. All
three destinations read verified in the dashboard — `bgneal@gmail.com`,
`member36@example.com`, `member35@example.com` — and the seven rules had been created
against them. **The longest-standing blocker in either project, open since
2026-08-17, is cleared.**

### The staged-additions ordering worked, and one assigned priority nearly broke it

The plan called for publishing Cloudflare's three MX records while priority 10
still won, making the cutover a single deletion. Cloudflare's assigned priorities
were **3, 46 and 17** — and **3 beats 10**. Adding that record as assigned would
have cut mail over on the spot, before anything was verified and before the
deliberate deletion step, which is precisely the failure the ordering exists to
prevent.

**Resolved by publishing `route1` at 15 instead of 3.** The relative order among
Cloudflare's three is preserved — 15 < 17 < 46 ranks the same hosts in the same
sequence as 3 < 17 < 46 — and MX preference is a number in this zone, not a
setting on Cloudflare's side, so it cannot affect whether Cloudflare accepts. Two
alternatives were rejected: lowering the `_dc-mx` record to win would have edited
the recorded rollback value and made *"put it back"* ambiguous, and adding the
priority-3 record last as the cutover would have moved the flip from a deletion to
an addition mid-execution, leaving the written rollback describing something other
than what would actually be done.

**Verified inert before the deletion:** four MX records on both `ada` and `cash`,
`_dc-mx` at 10 still winning, all three route hosts resolving, exactly one
`v=spf1` at the apex, `cf2024-1` and `_dmarc` untouched, and `surfguitar101.com`'s
MX unchanged as a control.

### `_dc-mx` is not in the DNS panel, and the recorded rollback value was the wrong form

Looking for `10 _dc-mx.658032ac2d3a.themadeira.net` in the dashboard found
nothing, because **it is not a record anyone created**. `mail.themadeira.net` is
proxied (`172.67.169.122` / `104.21.71.48`), and Cloudflare substitutes a
generated alias rather than publish proxy addresses as a mail target. The panel
row reads `MX 10 → mail.themadeira.net`, carrying a warning icon; the published
answer is the `_dc-mx` name, which resolves to jaguar.

**So the rollback value recorded on 2026-08-24 was the published form, not the
form that can be re-created.** The panel form is `MX 10 → mail.themadeira.net`.

**And the distinction is not academic — measured after the deletion:
`_dc-mx.658032ac2d3a.themadeira.net` no longer resolves at all.** Cloudflare stops
generating the alias once the record it derives from is gone. Entering the
`_dc-mx` name by hand as a rollback would have created an MX pointing at a
hostname that does not exist — **a rollback that looks successful and delivers no
mail**. The `mail.themadeira.net` A record was deliberately left in place, so the
real rollback remains one record away.

### After the flip

```
themadeira.net.  300  IN  MX  15  route1.mx.cloudflare.net.
themadeira.net.  300  IN  MX  17  route3.mx.cloudflare.net.
themadeira.net.  300  IN  MX  46  route2.mx.cloudflare.net.
```

Both nameservers agree. SPF, `cf2024-1` and `_dmarc` intact; `surfguitar101.com`
unchanged.

### Both of Phase 1's deliverability defects were pre-fixed, and this is the proof

Phase 1 found its two defects *after* flipping, by reading a delivered message.
This zone carried both fixes in advance — but on reasoning, not measurement. A
test message from Outlook to `admin@themadeira.net`, delivered to Gmail, settles
it from the receiving side:

```
dkim=pass header.i=@themadeira.net header.s=cf2024-1
spf=pass  ... SRS0=9530=sg=outlook.com=bgneal43@themadeira.net
          designates 104.30.10.31 as permitted sender
dmarc=pass (p=NONE sp=QUARANTINE dis=NONE) header.from=outlook.com
```

- **Defect 1 closed.** The key copied byte-identically from `surfguitar101.com` on
  08-23 does not merely resolve — it verifies a real signature on this zone.
- **Defect 2 closed.** The SRS envelope landed in `@themadeira.net` as predicted,
  and `104.30.10.31` is inside `104.30.0.0/19` from `_spf.mx.cloudflare.net`,
  confirmed by range check. Without that include this line reads `spf=fail` under
  `-all`.
- DMARC is evaluated against `outlook.com`, the original `header.from`, which is
  correct for forwarded mail and not a gap in this zone's coverage.

**One incidental worth keeping:** `dkim=pass header.i=@outlook.com
header.s=selector1` survived the hop, so Cloudflare's forwarder did not modify the
body. That is adjacent to sg101's quarantine residual risk — a body-modifying
forwarder is what would break the member's Gmail forward — but it is evidence
about *Cloudflare's* forwarder and says nothing definitive about Gmail's.

### Test results — 7 of 7 ✅

| Address | Destination | Confirmed |
|---|---|---|
| `admin@` | `bgneal@gmail.com` | ✅ received, headers read |
| `abuse@` | `bgneal@gmail.com` | ✅ received |
| `postmaster@` | `bgneal@gmail.com` | ✅ received |
| `madeira@` | `member36@example.com` | ✅ confirmed by Ivan |
| `themadeira@` | `member36@example.com` | ✅ confirmed by Ivan |
| `ivan@` | `member36@example.com` | ✅ confirmed by Ivan |
| `todd@` | `member35@example.com` | ✅ **confirmed by Todd 2026-08-26** |

Sent from Outlook, an external mailbox, not from anything on jaguar.

**`todd@` CLOSED 2026-08-26 — Todd confirmed his mail is being forwarded.** The
record held that the other six were not evidence for the seventh, and it was
right not to assume: this is the seventh measured, not the sixth generalised.
**All seven `themadeira.net` addresses are now confirmed end-to-end**, which is
what task 06's acceptance criteria ask for — *"tested per address, not sampled"*.

Confirmation is Todd's report of receipt, not a header read on this side. That is
the same standard the three `member36@example.com` addresses were closed under and
is what a third-party destination allows; it establishes delivery, not the
authentication result at Todd's receiver. Nothing depends on the latter — `todd@`
is inbound forwarding, and DMARC for forwarded mail is evaluated against the
original sender's domain, as the Outlook capture above showed.

### Still open

- ~~**`todd@themadeira.net` end-to-end.**~~ **CLOSED 2026-08-26** — Todd
  confirmed receipt. Seven of seven; the acceptance criterion is met. **This was
  the longest-standing item in either project, open in one form or another since
  2026-08-17**, and it was the last thing gating `themadeira.net`'s inbound mail.
  Phase 3 is all that remains of task 06.
- **Postfix keeps receiving on jaguar for at least a week** (Phase 3, step 12).
  Senders cache MX beyond the 300s TTL, so a tail of mail will keep arriving at
  the old box and must not be refused.
- **This zone's first DMARC aggregate report ever** should arrive within a day or
  two. `_dmarc` went live 08-24, one day before the flip, so the intended
  jaguar-era baseline window is one day wide at most and may be empty — a known
  limitation recorded when it was published, not a surprise.

  **Still absent as of the eleventh reading, 2026-08-26 — two days on, and the
  delivery path is ruled out as the explanation.** All fourteen files in
  `~/dmarc` are `surfguitar101.com`; not one is `themadeira.net`. That zone's
  record reads `v=DMARC1; p=none; rua=mailto:admin@surfguitar101.com` —
  **`admin@surfguitar101.com` is the same mailbox that just delivered fourteen
  reports**, so "the reports are not reaching us" is not available as an
  explanation. What remains is that no reporter has filed for this zone yet,
  which is unremarkable for a domain that sends almost nothing.

  **Two consequences worth having written down.** Its `rua` names only the local
  copy — no `dmarc-reports.cloudflare.net` destination — so **there is no
  Cloudflare dashboard for `themadeira.net`**, and `tools/dmarc_report.py` over
  `~/dmarc` is the only instrument this zone has. And the record publishes no
  `sp=`, so the subdomain policy inherits `p=none` rather than being stated.
- **Five `ns1`–`ns5.linode.com` NS rows** sit in the panel. Inert — Cloudflare
  publishes only `ada`/`cash` at the apex and the `.net` delegation agrees — so
  they were deliberately not touched during a mail cutover. Belongs to the
  decommission project's DNS end-state question.

## Step 16 task 06 Phase 2 — `themadeira.net` prepared, and the flip is now one deletion — DNS DONE 2026-08-24, MX FLIPPED 2026-08-25, see the section above

**Todd verified `member35@example.com` on 2026-08-24. Ivan has not, and says
tomorrow.** Ivan gates exactly one thing — this zone's MX flip. He gates nothing
else in Step 16, and in particular not the Postmark cutover, which is a different
domain in a different direction and was deliberately built to wait on nobody.

**Four records published by hand, all verified on both authoritative
nameservers.** The zone now carries everything Phase 1 had to add *after* its
flip, so tomorrow's cutover is a single MX deletion with no repairs trailing it.

| Change | Value | State |
|---|---|---|
| `cf2024-1._domainkey` TXT | Cloudflare's shared Email Routing key, 2048-bit | **live**, byte-identical to `surfguitar101.com`'s |
| apex SPF | `v=spf1 ip4:173.255.245.115 include:_spf.mx.cloudflare.net -all` | **live**, `a` and `mx` dropped, `-all` kept |
| `_dmarc` TXT | `v=DMARC1; p=none; rua=mailto:admin@surfguitar101.com` | **live**, first reporting this zone has ever had |
| `themadeira.net._report._dmarc` TXT on **`surfguitar101.com`** | `v=DMARC1` | **live** — without it the `rua` above is inert |
| MX | `10 _dc-mx.658032ac2d3a.themadeira.net.` | **untouched** — the rollback value, recorded before anything moved |

Everything is at **TTL 300**, so rollback is five minutes.

**Every record below was read from `ada.ns.cloudflare.com`, an authoritative
nameserver for the zone, not from a resolver cache**, with a query against
`surfguitar101.com` as a control in the same run.

| Record | Value today | Verdict |
|---|---|---|
| apex TXT | `v=spf1 a mx ip4:173.255.245.115 -all` | **the exact pre-rewrite form Phase 1 had to fix** |
| MX | `10 _dc-mx.658032ac2d3a.themadeira.net.` → `173.255.245.115` | jaguar, through the `_dc-mx` indirection |
| apex A / AAAA | `172.67.169.122`, `104.21.71.48` / `2606:4700:3035::ac43:a97a`, `2606:4700:3034::6815:4730` | Cloudflare's HTTP proxy |
| `_dc-mx…` A / AAAA | `173.255.245.115` / **none** | v4 only |
| `cf2024-1._domainkey` | **absent** | Phase 1's Defect 1, waiting to happen again |
| `_dmarc` | **absent** | no reporting on this zone at all |

### The three changes, and why each was safe before Ivan clicks

**1. `cf2024-1._domainkey`, value copied from `surfguitar101.com`.**
Phase 1 established by test that Cloudflare's Email Routing DKIM key is shared
across customer zones, so the value is already in hand and does not need the API
endpoint that refused the token. 420 bytes, stored as two strings of 255 and 165.
Without it every forwarded message carries a signature for this domain that
permerrors, which is what put Phase 1's first messages in Gmail's spam. Additive
and inert until forwarding starts, so there was no reason to wait.

**Verified three ways, not one.** The published value splits into the same two
strings of 255 and 165 bytes; it is **byte-identical** to the live
`surfguitar101.com` record under `cmp`; and it decodes under `openssl rsa -pubin`
as a well-formed **2048-bit** key. String equality against a key already proven
to sign passing mail is the strongest of the three — the decode only rules out a
mangled transcription.

**2. The apex SPF, one record updated in place, never two coexisting.**

```
before:  v=spf1 a mx ip4:173.255.245.115 -all
after:   v=spf1 ip4:173.255.245.115 include:_spf.mx.cloudflare.net -all
```

Each part of that is measured rather than argued:

- **`mx` is provably redundant.** It resolves to `173.255.245.115`, which the
  explicit `ip4:` already authorizes, and the target has no AAAA. Dropping it
  removes nothing.
- **`a` is already wrong today**, not merely wrong after the flip. It resolves to
  Cloudflare's HTTP proxy over both v4 and v6, so the record currently authorizes
  a large shared pool to send as this domain. This is task 03's Finding 3 in a
  worse form than `surfguitar101.com` had it, where only `mx` went bad and only
  at the flip.
- **The include is required**, per Phase 1's Defect 2: Cloudflare's SRS rewrite
  lands the forwarding hop in the forwarding domain, so it is evaluated against
  this apex and hard-fails under `-all` without it.

**No `ip6:` term, deliberately, despite `surfguitar101.com` carrying one.** That
term was *preserved* from the pre-existing record in Phase 1, not added by it;
this zone's record never had one. Dropping dead mechanisms and adding what
forwarding needs is provable, while authorizing a /64 nothing has been shown to
use is not. If jaguar does send this domain's mail over IPv6 it is failing SPF
today and has always been, and with no `_dmarc` on the zone nobody would know —
which is a thing to measure, not to paper over in this edit. **The `_dmarc`
record published the same day is what turns that from an argument into something
the next reading answers.**

**Verified after publishing:** exactly one `v=spf1` string at the apex, neither
`a` nor `mx` present, `-all` intact, and **one DNS-resolving term against a limit
of ten** — `_spf.mx.cloudflare.net` expands to `ip4:104.30.0.0/19
ip6:2405:8100:c000::/38 ~all`, pure address literals costing no further lookup.
That leaves room for Postmark's include at the cutover.

**3. Record the rollback value before touching MX:
`10 _dc-mx.658032ac2d3a.themadeira.net.`** Note this **inverts the Phase 1
instruction**, which said to write down `10 mail.surfguitar101.com` and
explicitly *not* the `_dc-mx` name, because task 03 superseded that alias on that
zone. Here the `_dc-mx` name is the live value. The additions-before-deletion
ordering is unchanged and still load-bearing: publish the three Cloudflare MX
records while priority 10 still wins, then the single deletion is the cutover.

### 4. `_dmarc`, published before the flip to buy a baseline

The zone had **no DMARC record at all**, so nothing that happens to its mail has
ever been observable. Publishing `p=none` changes no deliverability — it requests
reports and nothing else — which is why it was safe before the MX moves rather
than after.

**The reason to do it a day early is a baseline.** Reports arrive daily, so a
record published today covers today: `themadeira.net` mail still flowing through
jaguar, pre-Cloudflare. Tomorrow's flip then has a *before* to compare against.
That is this document's own lesson, stated in the fourth reading — *"Both
readings were wrong, because neither had a baseline."*

**It takes two records, and the second is easy to miss.** RFC 7489 §7.1 requires
a `rua` destination outside the policy domain to authorize the arrangement in
*its own* zone, at `<policy-domain>._report._dmarc.<rua-domain>`. This document
already recorded that constraint as the reason `rua` cannot point at
`bgneal@gmail.com` — Google's zone is not ours to publish in. It is satisfiable
here because both zones are:

```
_dmarc.themadeira.net                             v=DMARC1; p=none; rua=mailto:admin@surfguitar101.com
themadeira.net._report._dmarc.surfguitar101.com   v=DMARC1
```

**Without the second record conforming reporters silently decline** — no bounce,
no error, no reports, a state indistinguishable from nobody reporting. The
constraint is being exercised here for the first time rather than merely
recorded.

**The destination is deliberate.** `admin@surfguitar101.com` is a live, verified
Email Routing rule landing in the Gmail inbox already being read, so both domains
arrive in one place and one `dmarc_report.py` run covers both — the `Policy   :
domain=` line separates them. Pointing at `admin@themadeira.net` would have
needed no authorization record, being inside the policy domain, and was rejected
for a better reason: that address routes through jaguar, the path being
dismantled.

**No `ruf=`, deliberately.** Forensic reports carry message content, on a domain
that forwards other people's mail. The privacy objection that killed the
holding-pen idea for Todd applies here with more force, and almost no receiver
sends them anyway.

**Two things to expect in the first report, so neither reads as a surprise:**
DKIM may well fail, since jaguar's opendkim signs with the `dkim` selector for
`surfguitar101.com` and whether it signs this domain is unverified; and the
volume will be small, so absent reporters mean fewer filers rather than no
traffic.

### The two open questions, both answered 2026-08-24

- **`themadeira@themadeira.net`** — carried on the Open list since 2026-08-21,
  found in a bounce sample, forwarded by jaguar, and named nowhere in task 06.
  **It is not yet a rule, and is to be added when Ivan verifies.** Named here
  because the same gap found after the MX flip is a dead address.
- **Todd's rule target** — **confirmed pointing at `member35@example.com`**, not the
  address he abandoned. His verification only ever proved the destination exists.
- **How much of Phase 2 is built** — **all seven rules exist except Ivan's**, and
  the **catch-all is Disabled**, so a dropped alias is refused rather than
  silently discarded. Same choice as Phase 1.

### The audit's first run was wrong, and a control caught it

The first pass reported **every** `themadeira.net` record as absent while the
same names answered through a resolver — which reads as "this zone is on
different nameservers than `surfguitar101.com`," contradicting a true statement
already in this document. The cause was the harness, not the zone: the loop
expanded an unquoted variable holding `name type`, and **zsh does not word-split
unquoted parameter expansions**, so `dig` received one malformed argument and
`+short` printed nothing useful. Both zones do share `ada`/`cash`, as recorded.

Nothing was published from the bad run, because the control query in the second
pass had to answer before any of it was believed.
[[suspect-the-measurer-before-the-record]] — the reading that needed no
self-correction was the suspicious one.


## Step 16 — the warm-up, measured and DROPPED 2026-08-20

### The warm-up plan, measured 2026-08-20 — the mechanism is real, the size is not

Brian asked what the graduated warm-up is actually defending against: someone
replying to an old thread and the site mailing addresses that died years ago.
**That is exactly the mechanism, and it is the only one.**
`notify_topic_subscribers()` (`forums/views/subscriptions.py:20`) takes the new
post's topic, pulls `topic.subscribers` minus the poster, and sends one message
per recipient. Subscriptions are explicit opt-in — a POST to `subscribe_topic` —
so nobody was auto-subscribed by posting, and **no mass-mail path exists
anywhere in the tree**: every `send_mail` call site sends to a single recipient
on an individual event. A burst can only come from organic traffic.

**Fan-out is one.** 14,984 subscription rows across 9,608 of 35,693 topics:
median **1** subscriber per topic, mean 1.56, p95 of 3, max 31. A reply to an old
thread mails one or two people.

**The recorded 63% is a headcount, and the risk needs a message count.** Dormant
members subscribe to dead topics that never get replied to, so their rows never
turn into mail. Weighted by subscription rows the picture already inverts —
active members hold **11,023 of the 14,984 rows (73.6%)**. Weighted by mail
actually generated it inverts further. Twelve months of real posting, 4,186 posts
producing **9,041 notification emails (~24.8/day**, which cross-checks the mail
log's 27/day median total outbound):

| Recipient last logged in | Emails | % | Distinct people |
|---|---|---|---|
| Within 1 year | 7,526 | **83.2%** | 81 |
| 1–3 years | 440 | 4.9% | 17 |
| 3–8 years | 712 | 7.9% | 20 |
| 8+ years | 363 | 4.0% | 15 |

**11.9% of notification mail reaches accounts dormant 3+ years, from 35 distinct
addresses** — not the 423 people the headcount implies. The subscriber counts
themselves reproduce (232 at 8+ years against the 231 recorded on 2026-08-16, 191
at 3–8 unchanged); **none of the 668 has never logged in**, so the original
"8+ years or never have" was one category, not two.

**What makes the warm-up unnecessary rather than merely oversized: Postmark
suppresses an address after its first hard bounce.** Exposure is therefore
bounded by *distinct addresses*, not message volume — each dead address bounces
once and is never mailed again. Across a full year of organic posting the ceiling
is 35 bounces from the dormant class, and dormant is not dead: plenty of
decade-old Gmail addresses still accept mail.

**Decision: no staged send.** A warm-up defends against a burst, and nothing here
produces one — no mass-mail feature, median fan-out of 1, ~25 notifications a
day, and suppression capping repeats. Sequencing recently-active members first
would be real work guarding a rate that cannot get high enough to matter. **What
replaces it is watching Postmark's bounce dashboard for the first two weeks**,
which the numbers are small enough to eyeball.

**Two caveats kept attached.** This measures forum notifications only; PM
notifications (`messages/forms.py:159`) can also reach a dormant member, and
registration and password-reset mail goes to an address the user just typed —
none of them bulk. And the graduated warm-up was **volunteered to Postmark in the
approval request**, so this is doing less than was stated, not more. Not a
problem, and worth knowing it was said.


**Promoted to its own section 2026-08-26.** This decision spent five days buried
in task 03's journal, and on 2026-08-25 a status paragraph two thousand lines
away restated the warm-up as still pending, citing the 63% headcount this
measurement had already retired. Brian caught it on 2026-08-26. A decision that
supersedes a task's scope needs to be findable by looking for it — see
`step16/task-07-…code-task.md`, corrected the same day.

## Step 16 task 03 — DNS and email authentication — PARTIALLY EXECUTED 2026-08-17

No code. Four DNS records published by hand in Cloudflare, one Postfix parameter
changed, and **three claims from the previous day's audit corrected against
measurement.** Task 03 was started first because requirement 2 embeds a
mandatory week-long wait; that clock is now running.

### What is live

| Record | Value | State |
|---|---|---|
| `mail` A | `173.255.245.115`, **unproxied** | verified authoritative + two public resolvers |
| `20260817033844pm._domainkey` TXT | Postmark DKIM | verified; green in Postmark |
| `pm-bounces` CNAME | `pm.mtasv.net`, **unproxied** | resolves through to Postmark's AWS IPs |
| `_dmarc` TXT | `v=DMARC1; p=none; rua=…@dmarc-reports.cloudflare.net` | exactly one record, TTL 300 |

Postfix now sets `smtp_helo_name = mail.surfguitar101.com` (`postconf`-confirmed).
The apex SPF and the legacy `dkim` selector are **deliberately untouched** — the
SPF rewrite belongs with the task 02 cutover, and both DKIM selectors must
coexist while Postfix still signs.

**The PTR landed later the same day — FINDINGS 5 AND 6 CLOSED 2026-08-17.**
Linode accepted `173.255.245.115 → mail.surfguitar101.com` immediately but warned
propagation takes up to an hour; the authoritative nameservers for the reverse
zone (`*.akam.net` — Akamai serves it, not Linode) served the old value for
roughly that long, then flipped. Full chain verified:

```
173.255.245.115         ->  mail.surfguitar101.com     (PTR)
mail.surfguitar101.com  ->  173.255.245.115            (A)
=> forward-confirmed.  smtp_helo_name = mail.surfguitar101.com  => HELO matches PTR.
```

Agreed at all three Akamai nameservers and at 1.1.1.1 / 8.8.8.8 / 9.9.9.9. No
AAAA on `mail.`, which is correct given `inet_protocols = ipv4`. **PTR, HELO and
MX now all name the same host, and it resolves to the sending IP and nothing
else.**

*Method note: the check has to go to `*.akam.net`. The old PTR had a 300s TTL and
public resolvers were still serving it after Linode had accepted the change, so a
resolver query cannot distinguish "not applied yet" from "cached" — the same
class of error as reading a DNS answer from a cache during the original audit.*

**This is DNS-verified, not delivery-verified.** The remaining proof is a real
`Received:` header showing the PTR name in the parenthetical that was empty in the
2026-08-12 capture, and acceptance at Outlook. That belongs to task 07.
**— CLOSED on the Gmail side 2026-08-18, see the capture below; Outlook
acceptance was already shown 2026-08-17.**

### Correction 1 — **Postmark issued a 1024-bit DKIM key**

The planning documents said in three places that the 1024-bit key fixes itself on
the move because "Postmark issues 2048-bit." **It does not.** Measured from the
key Postmark published: `Public-Key: (1024 bit)`, 216 base64 characters, DER
header `30 81 9f`. A 2048-bit key is 392 characters and opens `MIIBIjAN`. The new
selector is exactly as strong as the old one.

**Re-measured 2026-08-20, both selectors side by side, after Cloudflare's DMARC
analysis page raised it.** The analysis carries the line *"DKIM record at `dkim`
uses a 1024-bit RSA key. Consider upgrading to 2048-bit keys for better
security,"* and the natural reading — that the provider move retires the problem
along with the old selector — is the same assumption Correction 1 already
refuted. Both published keys, measured from live DNS rather than from this
document:

```
dkim                   len=216  Public-Key: (1024 bit)
20260817033844pm       len=216  Public-Key: (1024 bit)
```

**Identical strength**, so Postmark's key has not been rotated since 2026-08-17
and the cutover changes which selector signs, not how strongly. Task 03 step 8
retires the `dkim` selector once Postfix is confirmed silent, so **that
particular advisory line does disappear at cutover — by the record being
deleted, not by the weakness being fixed.**

**Prediction, and a cheap discriminator for it.** If Cloudflare's analysis scans
published selectors, it should already be flagging `20260817033844pm` too, since
both are in DNS today; if it is driven by observed report data, it flags only
what actually signs, which is currently the old box alone. **Whether the analysis
page names the Postmark selector settles which**, and on the report-driven
reading the advisory returns after cutover under the new selector name.

**The open item cannot be closed from documentation.** Finding 2 left "worth
asking Postmark whether a 2048-bit rotation is offered." Postmark's DKIM support
articles do not state a key length at all, and their published upgrade material
covers the 768 → 1024 move, not 1024 → 2048. **That makes it a support ticket,
not a docs lookup.** If it is offered, the incidental cost is real: a 2048-bit
key is 392 base64 characters, past the 255-byte DNS string limit, so it must be
published as two quoted strings — which the current 224-character value avoids.

**Not a blocker.** 1024-bit RSA still validates everywhere and meets Google's and
Yahoo's published minimums, and key strength was never implicated in the Microsoft
rejections — those are FCrDNS, HELO and the missing DMARC. Worth asking Postmark
about a 2048-bit rotation; not worth blocking on. Task 03's acceptance criterion
requiring 2048 bits has been **withdrawn** rather than left as a permanent
failure.

*This was a vendor's behaviour assumed and then written down as a finding, in
three documents, none of it measured — the same shape as the milter inference
corrected the day before.* See [[measure-before-recording-in-planning-docs]].

### Correction 2 — the `_dc-mx` alias existed because the **MX target** was proxied, not the apex

Finding 8 said the generated `_dc-mx.1431890da307` hostname let MX reach the
origin "while the apex A record stays proxied." Wrong record. The zone's MX row
has always pointed at `mail.surfguitar101.com`; because *that* name was
orange-clouded, Cloudflare substituted its generated unproxied alias in MX
answers. Grey-clouding `mail.` dissolved it within the hour, with nothing edited:

```
before:  10 _dc-mx.1431890da307.surfguitar101.com.   → 173.255.245.115
after:   10 mail.surfguitar101.com.                  → 173.255.245.115
```

Inbound mail is unaffected — same box, and `_dc-mx` still resolves. Confirmed in
the panel that the MX row itself was not edited and no wizard touched it. The
result is strictly better: **MX, HELO and PTR now converge on one real
hostname.** Task 06's requirement 6 and one acceptance criterion referred to
replacing "the `_dc-mx.<hash>` record" and have been reworded.

*A vendor-generated workaround record is evidence of an upstream
misconfiguration. Reading it as "by design" was half right — it was Cloudflare's
design, compensating for a proxy setting that never belonged on a mail hostname.*

### Correction 3 — use `smtp_helo_name`, not `myhostname`

Task 03's requirement 11 said to set `myhostname = mail.surfguitar101.com`. That
works, but the live config makes it needlessly risky:

```
inet_protocols = ipv4
myhostname     = jaguar.deathofagremmie.com
mydestination  = jaguar.deathofagremmie.com, localhost.deathofagremmie.com, , localhost
/etc/mailname  = surfguitar101.com
```

`mydestination` holds **literals**, not the usual `$myhostname, …`. Changing
`myhostname` would leave the new name out of `mydestination`, and Postfix
delivers its own generated mail to `double-bounce@$myhostname` — which, with
`mail.surfguitar101.com` now resolving to this same box, yields `loops back to
myself`. Fixing that means editing local delivery routing on a server carrying 20
live aliases, for a change that is throwaway by design.

`smtp_helo_name` governs exactly the broken thing — the name presented in EHLO on
**outbound** connections — and nothing else. One line, one reload.

**`inet_protocols = ipv4` also closes the IPv6 question I had raised**: Postfix
cannot send over IPv6, so one PTR suffices and no AAAA is needed. The SPF
record's `ip6:` term has been inert throughout, which had made the v6 path look
live.

### Correction 4 — Postmark's free DMARC service is gone; Cloudflare's is used instead

The in-app "Set up DMARC" button now opens `dmarcdigests.com`, a separate product:
14-day trial, then **$14/month per domain**. Rejected — it nearly doubles the
step's running cost ($15 + $14) for a reporting UI on a domain sending ~30/day.
**Cloudflare DMARC Management** (zone → Email) is free, already authoritative for
the zone, and parses the XML into a dashboard. If the richer analysis is ever
wanted, start that trial **at cutover**, so its 14 days cover the window that
matters.

**A constraint neither document recorded:** a `rua` mailbox outside the policy
domain's own organizational domain requires the receiving domain to publish
`<policy-domain>._report._dmarc.<rua-domain>` (RFC 7489 §7.1). So the obvious
fallback — point `rua` at a personal Gmail — is unreliable, because Google
publishes no such authorization and strict receivers drop the reports silently.
**Reports vanishing untraceably is the exact failure DMARC was being published to
end.** Safe destinations: an analyzer that publishes the record for its customers
(Cloudflare's does), or any address on `surfguitar101.com` itself.

### Correction 5 — the `Message-ID` claim, flagged as a hypothesis and then confirmed

Finding 7a said the `<…@jaguar.deathofagremmie.com>` Message-ID is "resolved by
requirement 11's `myhostname` change, or by the move." **Both are false**, now
established rather than suspected. Django stamps its own `Message-ID` from
`DNS_NAME` = `socket.getfqdn()` on the *application* host, so no SMTP-side
setting touches it — not the interim fix, not Postmark.

**Confirmed by format, not by value**, from the Outlook capture below:
`<20260817235321.1920.52741@…>` is `YYYYMMDDHHMMSS.pid.randrange(100000)`, the
signature of Python 2.7's `email.utils.make_msgid()`. Postfix's Message-ID would
embed its queue ID, and that queue ID appears elsewhere in the same message
(`with ESMTP id 0F0BD586565`) but not here.

*The discriminator matters. `myhostname` was deliberately left alone, so both
hypotheses predicted the dead domain would still appear — **the value was
uninformative and only the format separated them.** Recording it as a hypothesis
rather than a finding is what made it testable later.* Cosmetic either way: a
plausibility signal, not an authentication check.

### The interim fix, verified from the receiving side — Outlook, 2026-08-17

A "send a news story to a friend" message to a freshly created Outlook.com
mailbox, sent through the **unchanged** path (Linode Postfix; `EMAIL_HOST` is
still `localhost`, Postmark is not involved). Full capture, trimmed of antispam
blobs, in `research/email-header-captures.md`.

```
dmarc=pass action=none ... compauth=pass reason=100
spf=pass (sender IP is 173.255.245.115)
dkim=pass (signature was verified) header.d=surfguitar101.com
helo=mail.surfguitar101.com
X-Microsoft-Antispam-Mailbox-Delivery: ...jmr:0;...dest:I;...
```

**`dmarc=pass` is the first DMARC evaluation this domain has ever produced** —
the 2026-08-12 Gmail capture had no `dmarc=` clause at all. `compauth=pass
reason=100` is Microsoft's composite-authentication verdict at its strongest.
`helo=mail.surfguitar101.com` confirms the `smtp_helo_name` change in flight.
`dest:I` confirms **Inbox**, in the headers rather than visually, with no
junk-mail rule fired and `BCL:0`.

**The result is not pristine, and that part matters most.**
`X-Message-Delivery` decodes to `SCL=3` — comfortably below the junk threshold,
but not the 0–1 of a trusted sender, despite `X-MS-Exchange-Organization-SCL: 1`.
**Authentication is now perfect; reputation is still neutral.** That is exactly
the predicted split and exactly the argument for Postmark: fixing DNS does not
retroactively build sending history.

**What it does not establish.** One message to a mailbox created minutes earlier
— no history, no contact graph, no user signal, and not equivalent to the
established accounts whose owners reported the problem. Strong evidence about
authentication, weak about reputation. It also does **not** independently confirm
FCrDNS: Microsoft renders `Received` as `from <helo> (<ip>)` and never shows the
PTR separately, unlike Gmail's `from HELO (ptr [ip])`. FCrDNS rests on the `dig`
verification against `*.akam.net`.


### The readings, and the rest of this section

**The eleven DMARC aggregate readings moved to
`research/dmarc-readings.md` on 2026-08-26**, and task 10's host-side repairs to
their own section above. What stays here is the DNS and authentication record —
what is live, the five corrections, the interim fix — and the *Open* register
below, which is the live state this step is steered by.

### Open

- **The local `rua` copy has been a dead collection path since 2026-08-23, and
  eighteen readings were written without noticing** — new 2026-09-21, the
  twenty-third reading. **Measured, not inferred**: over fifteen days of mail log
  `/home/dmarc/mail` received 29 messages and **not one was a DMARC report** — 23
  from `no_reply@surfguitar101.com`, 4 from `root@surfguitar101.com`, 2 from `<>`,
  all jaguar's own mail to `admin@`. The cause is already in this file, stated
  about something else: task 06 Phase 1 records *"Inbound mail for
  `surfguitar101.com` no longer touches jaguar."* The apex MX is Cloudflare's, so
  external report mail is forwarded to Gmail and never enters jaguar's Postfix —
  the `virtual_alias_maps` fan-out that produces the local copy only runs for mail
  jaguar generates itself. **The 2026-08-20 section built that copy as the
  instrument's insurance and proved it end to end; the 2026-08-21 amendment
  established its real value as latency, one report delivered locally in 0.85s
  against 9h25m52s to Gmail. The MX flip retired it three days later.** It served
  the fifth and sixth readings and nothing since. **Consequence: report collection
  has a single point of failure — a manual save out of Gmail — and has had one all
  along**, which is why one missed delivery batch lost the 09-07 window outright.
  **The fix does not belong on jaguar**; automating the Gmail→`~/dmarc` step
  removes the human failure mode and survives the decommission.
  **FIXED the same day — `tools/dmarc_fetch.py`.** Read-only IMAP against Gmail,
  All Mail *and* Spam, detecting reports by parsing the bytes rather than by
  sender, preserving each attachment's own filename, refusing to overwrite, and
  stateless so a missed run self-heals. Its **first sweep recovered four reports
  that had never been saved** — `enterprise.protection.outlook.com` for 09-06 and
  three from `web.de` — taking the corpus from 101 to **105 reports, 658
  messages**. **So the gap was five reports, not the one the twenty-second
  reading identified**, and the four span 09-06 → 09-12 across two unrelated
  reporters, interleaved with windows that saved correctly. **A single lost batch
  cannot produce that shape: the manual save was leaking steadily.** Every total
  in the reading log before 2026-09-21 is a floor for that reason, not only
  because of 09-07. AOL's 09-07 report is still absent and that absence is now
  well evidenced — an exhaustive sweep of the whole reporting era does not find
  it, where before there was only a hand search.
  **`tools/dmarc_report.py` still has `DEFAULT_MAILDIR = '/home/dmarc/mail'`**, so
  run bare on the box it now reads a maildir holding no reports and says so without
  complaining — the same class of silent-success trap the six-traps section
  recorded. [[probes-must-not-perturb-what-they-measure]]

- **A report's `count` is DMARC evaluations, not distinct messages — every
  reconciliation in the log used the wrong unit and got away with it** — new
  2026-09-21, the twenty-third reading, **demonstrated exactly rather than
  argued.** Comcast's 09-17 report reads **16** against **2** messages sent.
  Comcast answered `451 4.2.0 Try Again Later` *in reply to end of DATA* — having
  already taken the whole message — and Postfix retried `6EAF8586505` for four
  hours fifty minutes. Each cycle reaches **both** MX hosts, because Postfix falls
  through to the next MX after the first defers: 7 cycles × 2 = 14 receptions, plus
  two eventual deliveries = **16, exact**. Nothing was duplicated or double-sent;
  the recipient got one copy. **The three inflation mechanisms are one
  mechanism**: a forwarder hop, a multi-recipient fan-out and a defer-and-retry
  loop each have the receiver evaluate a message again, and the report counts what
  it evaluated — the only quantity it can honestly report. **Bearing on the
  reconciliation bullet below**, which is stated in message counts and says "not one
  disagreement": it is correct in fact and wrong in method. Across the whole covered
  log the only `4xx`-at-end-of-DATA events are 40 at `mx{1,2}.mxge.comcast.net` and
  2 at `mx.bt.prod.cloud.openwave.ai`, so no window before 09-17 contained a
  deferral loop and `grep status=sent` happened to give the right answer every
  time. **Counting sends is only valid where nothing deferred — check before
  reconciling, not after a mismatch.** The test is already in the queue: the still-open
  UTC 09-21 window stood at **27 receptions for 2 messages** at the log's end.
  [[suspect-the-measurer-before-the-record]]

- **Record the reporter, Report-ID and window in every reading** — convention
  adopted 2026-08-21. `tools/dmarc_report.py` prints all three and no reading has
  ever captured one, which is the entire reason "is this the report we already
  read?" cost a header dump and a mail-log pull on 08-21. For the record, the
  08-20 window is Google Report-ID **`1291292834730335860`**, and Google addresses
  one message to both `rua` destinations, so the local copy and Cloudflare's
  ingest share it. **Applied in full for the first time in the sixth reading,
  2026-08-22** — five reports tabulated with all three — and it paid immediately:
  the 08-20 Google report was recognised as one already read from its Report-ID
  alone, at no cost.
- **Count jaguar's sends across the rotated logs, not just `/var/log/mail.log`** —
  new 2026-08-31, found in the sixteenth reading. The convention the fifteenth
  reading recorded is right as far as it goes — `grep status=sent | grep -v
  relay=local` — but it was applied to the uncompressed logs only, and jaguar
  rotates weekly at ~06:30. **Aug 23 was recorded as 15 and is 45**: 15 in
  `mail.log.1`, 30 in `mail.log.2.gz`, split across the boundary. Aug 30 has the
  same shape (30 + 7 = 37). The full form is `{ cat /var/log/mail.log;
  cat /var/log/mail.log.1; zcat /var/log/mail.log.*.gz; }` before the greps, and
  any day within ~6h30m of a rotation is truncated without it. **The reason it
  survived two readings is the part to keep**: the fifteenth reading verified its
  numbers by reproducing the fourteenth's and called the agreement corroboration,
  but both ran one command against one truncated file set — two runs of one
  instrument are one measurement. The old figure had 15 sent against 24 reported
  for the 08-23 window, more reports than sends, and nothing flagged it.
  [[suspect-the-measurer-before-the-record]]
- **"Reporting endpoints" is eleven by filename plus `swbell.net` by sender name**
  — **UPDATED 2026-09-01.** `sbcglobal.net` filed for the 08-31 window in the
  seventeenth reading, which puts the filename count back at eleven by a different
  route than the one that was wrong. That reading also corroborated `swbell.net`
  from the *sending* side — jaguar sent it 2 messages in the 08-21 UTC window, and
  the file was never retrieved because `~/dmarc` did not exist yet — so the
  provenance distinction survives and the doubt it carried does not. **Twelve
  receiving domains have been observed; eleven of them as files.** The correction
  below is what the figure meant for one day, kept for its reasoning.

  **UPDATED 2026-09-21 — thirteen by filename, fourteen observed.** Two new
  endpoints in one day. `enterprise.protection.outlook.com` filed for 09-13 and
  09-06 (see the Microsoft tenant bullet below), and **`web.de` turns out to be a
  reporter**, not only the forwarding source the reading log had it down as —
  three reports recovered by the first run of `tools/dmarc_fetch.py`. `swbell.net`
  remains the one observed only as a sender name. **Say thirteen, or
  thirteen-plus-one with the provenance attached.** Four figures now differ and
  none is interchangeable with another: **13 endpoints by filename, 7 `org_name`
  strings, 6 reporter addresses, 5 corporate organizations.** `Enterprise Outlook`
  and `Outlook.com` share `dmarcreport@microsoft.com`; `WEB.DE` and `GMX` use
  different addresses but are one implementation, which the field census below
  identifies rather than assumes.

  <details><summary>The 2026-08-31 correction, superseded</summary>

- **"Reporting endpoints" was ten by filename plus `swbell.net` by sender name — not
  eleven** — new 2026-08-31, corrected in the sixteenth reading and in the
  `dmarc-readings.md` header note. The count and its definition had drifted apart:
  the fifteenth reading defines the figure as *"the receiver field of the
  filename"*, which is the one thing `swbell.net` is not — it was read in the sixth
  reading from report-mail sender names in Gmail and flagged in the eighth as the
  member not read from the filename convention. Measured across all 44 files the
  distinct receiver field yields **ten**, and `swbell.net` has never been a file in
  `~/dmarc`. **This does not say `swbell.net` was not a receiving domain**, and it
  does not disturb the fifteenth reading's `protection.outlook.com` finding. When
  the figure is quoted, say ten, or say ten-plus-one with the provenance attached.
  **One live instance in this document**: step 7's `p=quarantine` justification above
  reads *"eight receiving domains"* for the `p=none` era, and that eight is the ninth
  reading's list, which includes `swbell.net` — so it is seven by filename. Correct in
  context and left as written; noted here so it is not recomputed into a different
  number by a later reader.
  [[measure-before-recording-in-planning-docs]]

  </details>

- **Sends and reports reconcile exactly at every receiver but Google** — new
  2026-09-01, the seventeenth reading. Across ten windows and eleven endpoints,
  every one of the forty-one non-Google reports states exactly the number of
  messages jaguar's mail log says were sent to that endpoint in the UTC window —
  155 messages in all: Yahoo over nine windows and 56, Microsoft over seven and 33,
  Comcast over seven and 24, six smaller endpoints besides. **Not one disagreement.** This is
  the log's strongest check on its own send-side instrument — the rotated-log fix,
  the UTC binning and the verified UTC−5 offset are all load bearing in it, and a
  fault in any would scatter near-misses across ten independent receivers.
  **Consequence for how absences are read**: eight endpoint/window pairs the log
  had treated as a receiver failing to file — Comcast's 08-26 hole above all, plus
  `comcast.net`/`aol.com`/`verizon.net` on 08-30 and GMX on 08-31 — are windows in
  which jaguar sent that domain nothing. Check the send log before predicting a
  filing, and before calling an absence a finding. The only cells with sends and no
  file are 08-22 and 08-23, which are a retrieval gap: the corpus begins with the
  batch saved 2026-08-24.

- **Microsoft appears not to fold tenant domains into its endpoint the way Google
  does** — new 2026-09-08, the twenty-first reading, **one window, stated as such.**
  jaguar sent three Microsoft-bound messages in the UTC 09-06 window; Microsoft's
  report reads `envelope_to: hotmail.com` at count 2 and omits `C23FC5864B2` to
  `member28@example.com`, relayed through `cpp-edu.mail.protection.outlook.com` — a
  Microsoft 365 tenant, confirmed by MX lookup rather than read off the relay
  string. **This runs opposite to the Google result the offset bullet below leans
  on**, where `muohio.edu` was corrected *into* the `google.com` endpoint in the
  nineteenth reading. `cpp.edu` had never appeared in the corpus before this window.
  **One window cannot tell a rule from an absence** — the tenant report may yet
  arrive, or the tenant may have reporting disabled — and two tests are already
  loaded, one per direction: whether a `cpp.edu` report ever arrives for 09-06, and
  whether Google's 09-07 report reads 20 (folding `member24@example.com` in) or 19.
  A 19 falsifies the nineteenth reading's correction rather than this bullet.
  [[measure-before-recording-in-planning-docs]]

  **CLOSED 2026-09-21 by the twenty-third reading — it is a rule, and the tenant
  mail goes to a separate endpoint.** Both loaded tests are answered. Google's
  09-07 report, recovered from Gmail on 09-12, reads **20** and folds
  `member24@example.com` in, confirming the nineteenth reading's correction on a
  third independent window. And a twelfth endpoint has appeared:
  **`enterprise.protection.outlook.com`**, `org_name: Enterprise Outlook`, filing
  under the same reporter address `dmarcreport@microsoft.com` as `Outlook.com`.
  Its single report covers the 09-13 window, reads 1, and carries `envelope_to:
  cooldwelling.com` — matching `8F2C658650C` to `member16@example.com`
  (`Sep 13 14:11:58`), relayed through `cooldwelling-com.mail.protection.outlook.com`,
  MX verified by lookup. One send, one report, exact. **So Google folds tenants
  into its main endpoint and Microsoft splits them onto a separate one** — this
  bullet's finding was right about the behavior and could not say where the mail
  went. ~~**`cpp.edu` still has no report for 09-06**, and that is now a per-tenant
  fact rather than a puzzle.~~ **⚠️ WRONG, corrected the same day.**
  `b600b29c97d4444ca781546148067037` covers 09-06, reads 1 message and matches
  `C23FC5864B2` to `member28@example.com` exactly. It was in Gmail all along and was
  recovered by the first run of `tools/dmarc_fetch.py`. **Both tenants file.**
  The error is worth keeping because of how it was made: it inferred a
  reporter's configuration from an absence in our own corpus, on the same day
  this register recorded that the collection path drops reports. **An absence is
  not a finding until the collection path is ruled out**, which is the
  seventeenth reading's rule applied to the instrument instead of the send log. **The endpoint count is twelve by filename**, plus `swbell.net` by
  sender name; the `org_name` strings are six but the reporting *organizations*
  are still five.

- **Google's aggregate day is not the UTC day its `date_range` claims** —
  new 2026-09-01, **upgraded from hypothesis to result 2026-09-02 by the eighteenth
  reading, which tested it forward.** Google reported 8 messages for the 09-01
  window; jaguar sent 6 into the UTC day and 8 into the UTC−7 day, and the report
  names one source IP — ours — so the surplus cannot be forwarded mail arriving
  elsewhere. Residuals over ten windows now run Σ42 / 3 exact at UTC against Σ14 /
  **7 consecutive exact** at UTC−7, and UTC requires Google to report mail nobody
  sent in three of the ten. **GMX decides the same window the other way** — 1 sent
  at UTC, 2 at UTC−7, 1 reported — so the offset is a property of Google's
  reporting and not of our clock or our binning. *Why* Google stamps
  `00:00:00Z → 23:59:59Z` and aggregates a US Pacific day is **not measured and not
  guessed at.** Next test: Google's 09-02 report must not re-count the four
  messages sent at `Sep 1 20:40:39` local. The original hypothesis form follows.

  <details><summary>Stated as a hypothesis, 2026-09-01</summary>

- **Google's aggregate day may not be the UTC day its `date_range` claims** —
  new 2026-09-01, the seventeenth reading, **open and stated as a hypothesis.**
  Google is the sole receiver whose reports do not match the send log: residuals of
  +14, +2, +14, 0, −5, −1, 0, +4, 0 across 08-23 → 08-31, Σ40 over 166 reported
  messages. Scanning the window offset, a **UTC−7 day** (US Pacific) takes Σ to 14
  and makes the last six consecutive windows exact, including 08-28 at 47 messages,
  while every report is stamped `00:00:00Z → 23:59:59Z`. It is one free parameter
  fitted to nine points; what keeps it above curve-fitting is that no other reporter
  needs an offset at all. **The eighteenth reading tests it forward on the 09-01
  window rather than backward.** Two send-side corrections are already folded in and
  are not hypotheses: `muohio.edu` and `rarr.org.uk` are Google-hosted by MX, so
  their mail is in `google.com`'s report, and readings fourteen through sixteen
  counted `muohio.edu` as non-reporting. Residual not explained by the offset: 14
  messages across 08-23/24/25, all in the direction of jaguar sending more than
  Google reported. One alternative was tested and falsified — every one of the 669
  sends in the corpus has exactly one recipient per queue ID, so postfix logging per
  recipient while Google counts per message is not the cause.
  [[suspect-the-measurer-before-the-record]]

  </details>

- **Correction to that falsification's wording** — 2026-09-02. Five queue IDs in
  jaguar's live log carry `nrcpt=2`; in every one the second recipient is
  `dmarc@localhost` over `relay=local`, the `admin@` alias fanning out to the
  maildir that feeds `~/dmarc`. There is exactly one **remote** recipient per queue
  ID and never two at Google, so the falsification holds — but "exactly one
  recipient per queue ID" was broader than what was measured.
  [[measure-before-recording-in-planning-docs]]

- **The unsigned message from `173.255.245.115` is a Postfix bounce — CLOSED
  2026-09-02**, the eighteenth reading, on the reopen condition the seventh reading
  set. The second occurrence arrived in Google's 09-01 report and the mail log names
  it end to end: site mail to `comporium.net` rejected as spam, Postfix DSN
  `BECCA5869B6` generated `from=<>`, delivered to `admin@surfguitar101.com` and so
  to Brian's Gmail, evaluated by Google with an empty MAIL FROM, SPF falling back to
  the HELO name `mail.surfguitar101.com` and passing on the record published there,
  no signature because DSNs bypass the milters. It is the only `from=<>` message in
  the whole live log and the report carries exactly one such row. **Hypothesis A
  from the seventh reading was correct**; it died there on an absence in one window,
  which was reported correctly as an absence. **The class is every Postfix DSN**,
  not an anomaly — visible in a report only on days something bounces — so a
  `pass`/`fail` row from our IP is expected from here and checkable against
  `grep 'from=<>'` on the mail log. **Bearing on `p=reject`:** DSNs pass DMARC on
  one mechanism with no margin, the mirror image of forwarded mail surviving on DKIM
  alone. Under `p=reject` a DSN that lost its SPF pass is rejected and nobody is
  told. Outbound moves to Postmark at Step 21 and the DSN path goes with it, so
  **re-measure this class after cutover rather than legislating it before.**
- **Cloudflare shows sending sources, not reporters — and Comcast-as-reporter was
  an inference** — noted 2026-08-21, **CLOSED 2026-08-22**. The organization list on the dashboard
  reads **Akamai and Google**, which are the two *sending sources* already on
  record: Akamai owns Linode, so that row is jaguar at `173.255.245.115`, and
  Google is the one member's Gmail forwarding. **Comcast's absence is the tell** —
  the fourth reading established it as a second reporting receiver, so a reporter
  list would name it. Cloudflare appears not to expose reporter identity at all,
  which is why that reading had to deduce Comcast from a +24 delta rather than
  read the name, and why `tools/dmarc_report.py` prints
  `<report_metadata><org_name>`. **Closed by the sixth reading**: the local copy
  delivered a report whose `org_name` reads `comcast.net`
  (`dmarc-admin@alerts.comcast.net`), alongside Yahoo — so the reporter base is
  three organizations, read rather than deduced, and the standing claim that no
  reporter other than Google had been observed directly no longer holds. **The
  finding about Cloudflare stands**: it still exposes sending sources only, which
  is why the local copy remains the instrument for reporter identity.
- **jaguar forwards mail for a second domain — `themadeira.net`** — new
  2026-08-21, found in a bounce sample (`orig_to=<themadeira@themadeira.net>`).
  Nothing in Step 16 names it; the cutover inventory has assumed `admin@` and
  `root@` were the forwarding paths on the box. **When jaguar goes away that
  forwarding needs a destination**, and task 06's Email Routing covers
  `surfguitar101.com` only. Belongs to the cutover inventory rather than to the
  reading log.
- **The activation window is a hard 24 hours and the queue lifetime is days** —
  noted 2026-08-21, **not observed**. `PendingUser.purge_expired()` runs at the
  top of `register_confirm`, so a user clicking at 24h+1s deletes their own row
  before the lookup, while Postfix keeps retrying for days. A confirmation
  delayed past 24h therefore arrives to a row that no longer exists: dead link,
  no bounce, `status=sent` in the mail log, and `register_confirm ... user does
  not exist` in `auth.log` as the only trace. The 08-21 throttle consumed 39% of
  that window and the 07-21 one 10%. Checkable with `grep -c 'register_confirm.*
  user does not exist' logs/auth.log*`. Postmark changes the delivery
  characteristics anyway, so this is a latent property of the code, not a live
  defect.
- ~~Re-verify the PTR at `*.akam.net`~~ — **done 2026-08-17, passes.**
- **Read a week of DMARC aggregate reports** (requirement 2) before tightening
  policy. Receivers send daily; Cloudflare's digest cadence is its own.
  **6 of 7 days read** — 2026-08-17 through 2026-08-22, **with 08-19 re-read the
  same evening and found to have tripled** (see the fourth reading), **08-20
  reproduced exactly from its Report-ID** on 08-22 and again on 08-23, and
  **08-21's four reports all reproduced** on 08-23 while gaining a late filer.
  **Readings now re-check previously recorded days, not only the new one**, and
  the most recent row is provisional until a later reading reproduces it.
  **The gate closes 2026-08-24.**

  **Scope of this gate, stated precisely 2026-08-20 because the daily readings
  had begun to imply more.** Requirement 2 reads *"before tightening policy…
  the only way to learn what is currently sending as this domain."* Against task
  03's own implementation order that is **step 7 (restore `-all`) and step 9
  (`p=none` → `quarantine` → `reject`) — both of which happen after cutover.**
  Steps 3–6 (Postmark's records, the transition SPF, verification, and the
  cutover itself) need nothing from it.

  **Correction 2026-08-20: only one of the two safety valves this paragraph
  claimed is actually published.** `p=none` is live and does mean receivers take
  no action on failures. The second — task 03 step 6 softening the apex to
  `~all` for the duration of the window — **has not run.** Measured at
  `ada.ns.cloudflare.com`: the apex reads
  `v=spf1 a mx ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 -all`,
  one SPF record, no `include:`. The same Open list elsewhere schedules steps 5–7
  with the task 02 cutover, so this document asserted a valve while also
  scheduling it for later, and DNS agrees with the schedule. *(Found while
  reading the apex for an unrelated reason — nothing was watching it, which is
  the property that makes DNS claims worth re-measuring rather than re-reading;
  see [[measure-before-recording-in-planning-docs]].)*

  **What it changes is small.** Under `p=none` a hard SPF fail still produces no
  receiver action, and jaguar has been sending under `-all` for years, so this is
  the status quo rather than an exposure the week introduced. **What it does
  change is the cutover**, where that apex record hard-fails everything but
  jaguar's two addresses and does not name Postmark — which is exactly why steps
  5–7 are pinned there, and why flipping `EMAIL_HOST` ahead of step 5 would hard-
  fail every Postmark message at the apex. **The week is the long pole meant to
  elapse concurrently, not a hold on other work.**

  **What is left to learn from it is narrow.** Three days show one sending
  source — jaguar — plus one member's Gmail forwarding, so the inventory the
  requirement asks for was substantially answered on day one. The residual value
  is a sender on a *weekly* cadence that three days would miss. Two limits, both
  now measured: the reports cover only the **~55% of outbound that goes to
  Gmail**, so a sender that never mails Gmail is invisible here; and the
  inventory that actually governs step 7 is the **post-cutover** one, since
  Postmark becomes the dominant source and changes the picture entirely. The
  complementary instrument is the mail log — all destinations, but only this box;
  DMARC's unique contribution is a source we do not control.
- **Fifth reading done 2026-08-21** (above), **the first taken from our own copy
  rather than a dashboard**, covering 2026-08-20: one report, Google, 5 messages,
  all aligned, **0 failures**. The HELO SPF record reads as a pass in aggregate
  data, on the null-sender row where SPF fell through to the HELO identity.
  **Google addresses one message to both `rua` destinations**, so Cloudflare
  ingests byte-identical input and caveat 1 is closed. **Still no Microsoft** —
  day one of the two-day window. **Partly corrected later that day**: its Gmail-
  forward subsection measured queue state and reported a rejection. The reading
  itself — reporter, window, rows, the HELO pass — is unaffected.
- **Sixth reading done 2026-08-22** (above), covering 2026-08-21: **five reports,
  three reporting organizations**, 10 messages, **0 failures**. **Comcast observed
  directly**, closing the inference above. **swbell is Yahoo, not a third
  receiver** — one generation run emitting two reports, refuted before it could be
  recorded as an independent corroboration. **08-20 re-read from its Report-ID and
  reproduced exactly**, which also establishes that per-report readings only gain
  reports for a window and never revise one — so **08-21's total is a floor**.
  **Still no Microsoft** — day two of the two-day window; *it filed for this same
  window and was read on 08-23, see the seventh reading.* **The ~55%-of-outbound
  blind spot is materially smaller**: the reporter base is no longer Gmail alone,
  which is the first real progress on requirement 2's residual value rather than
  another day of the same view.
- **Seventh reading done 2026-08-23** (above), covering 2026-08-20 through 08-22:
  **nine reports, four reporting organizations**, 0 failures in every window.
  **Microsoft has reported** — `Outlook.com`, one message, aligned — closing the
  standing "still no Microsoft" line carried since the fifth reading. **The floor
  convention is confirmed on a second window**: 08-21 gained the late filer and
  went 10 → 11 while all four earlier reports reproduced byte-identically.
  **08-22's 27 messages agree with the independently measured ~30/day mean**,
  which reframes the smaller earlier windows as reporter participation rather
  than quiet days. **NEW AND UNRESOLVED: the first DKIM failure from
  `173.255.245.115` in seven readings** — one unsigned message on 08-22, which
  passed DMARC on SPF alignment alone. **Hunted and closed as a bounded
  known-unknown the same day**: four hypotheses raised and all four refuted, the
  message never identified. Google emits no SPF `<scope>`, the log covers the
  window and contains no null sender and no subdomain envelope sender in it, and
  opendkim logs nothing when it signs, so elimination is impossible from these
  instruments. **Reopen only on a second occurrence** — one is an anomaly, two is
  a pattern. Full account, including what killed each hypothesis, in the seventh
  reading above. **REOPENED AND CLOSED 2026-09-02 by the eighteenth reading**: the
  second occurrence is a Postfix non-delivery notification, identified from the mail
  log, and hypothesis A was right. See the entry above.

- **The new VM needs a real-client-IP rewrite before cutover** — new 2026-08-21
  (fifth reading above). `mod_remoteip` on jaguar sets `REMOTE_ADDR` from
  `CF-Connecting-IP` for Cloudflare's ranges, and **every `REMOTE_ADDR` reader in
  the codebase is correct only because of it**: `antispam`, `accounts`, `forums`,
  `comments`, `downloads`, `donations`. **Nothing in the repo performs it** — no
  `real_ip`, no `SECURE_PROXY_SSL_HEADER`, no proxy in `docker-compose.yml` — and
  Django does not do it itself. Without a proxy-side rewrite (Apache's
  `mod_remoteip` or nginx's `ngx_http_realip_module`, over the same 15 IPv4 and
  7 IPv6 ranges) every IP the site records silently becomes a proxy address on
  cutover day, with nothing reporting the
  disagreement. **Hung on Step 20 in `plan.md` 2026-08-21** — production
  hardening already owns the Cloudflare front and the gunicorn prod compose, so
  it needs no new step. **Step 17 inherits it**: Turnstile's siteverify takes the
  same `remoteip` the contact form passes today. **The origin-exposure question
  is now measured, not open**: jaguar answers `https://surfguitar101.com/` with
  200 over both IPv4 and IPv6 when reached by address, on a publicly-trusted
  Let's Encrypt certificate, and the address is published four times in the zone
  (`mail` A, apex SPF v4 + v6, `mail` SPF). Cloudflare's WAF and rate limiting
  are therefore advisory today. **Closing it belongs to the new VM** — firewall
  443 to Cloudflare's ranges, IPv6 included — and task 06 removes the reason the
  leak exists, since Email Routing leaves the VM with no MX and no public mail
  name. Recorded in Step 20.
- **First reading done 2026-08-18** (above): Gmail only, 61/65 passing, 4 failures
  hypothesised as unsigned Postfix bounces, forwarded to Brian's Gmail by the
  `admin@`/`root@` aliases. **Tightening past `p=none` stays blocked until those
  4 are identified** — 93.85% from one receiver is not the proof requirement 2
  asks for. Remaining step: read one `MAILER-DAEMON` message's
  `Authentication-Results` from Brian's own inbox.
- **Third reading SUPERSEDED the same evening — see the fourth reading.** Its
  10-message row for 2026-08-19 was a partial report; the day closed at 34, the
  volume never collapsed, and **Comcast turned out to be a second reporting
  receiver**, which retires "Gmail's view alone" everywhere it appears below.
  Original bullet follows. **Third reading done 2026-08-20** (above), covering 2026-08-19: 10 messages,
  1 failure, Akamai row again with pass/SPF/DKIM identical at 88.89% — the
  signature on a third day, and the failure class persists as predicted. **But
  the count fell 4 → 3 → 1 while volume fell 67 → 33 → 10, which reads against
  the second reading's "scheduled, not traffic-driven" argument**; at these
  counts nothing distinguishes the two shapes, and that section claimed more
  than two points could carry. The predicted *passing* class from
  `sender_canonical_maps` did not appear — a quiet cron day is indistinguishable
  from a broken rewrite here, and the rewrite was already verified at the
  receiver on the 18th. Still Gmail's view alone; still blocked past `p=none`.
  **"Gmail's view alone" is no longer an assumption** — over the three report
  days jaguar sent 192 messages, 103 of them to Gmail, and the Akamai row
  reports 106; a second reporting receiver would push that toward 192.
  **The by-date table was read 2026-08-20**: exactly three rows, every
  percentage reproducing from the recorded counts, day totals summing to
  110 / 102 / 8 with the 4-message SPF/DKIM gap accounted for entirely by
  forwarded mail. **Cloudflare's own cumulative header is still unread**, and
  the all-time by-service Akamai IP count — 3 for summing, 1 for
  de-duplication — is the outstanding test of the summing claim.
- **Second reading done 2026-08-19** (above), covering 2026-08-18: 33 messages,
  3 failures, all in the Akamai row with pass/SPF/DKIM identical at 90.63% — the
  17th's signature on an independent day. **The predicted persistence held**, and
  the count staying at 3–4 while volume halved is new support for a scheduled
  class rather than a traffic-driven one. Still Gmail's view alone; still
  blocked past `p=none`. **The cumulative view's "IP count 2" is a summing
  artifact, not a second sender** — per-day rows read 1. **The "scheduled, not
  traffic-driven" inference in that section is corrected by the third reading
  below** — it was written from two points and the third did not follow it.
- ~~**Reconcile the send-volume discrepancy** the first reading exposed (caveat 2
  above)~~ — **CLOSED 2026-08-20 against a month of mail log.** There was no
  discrepancy: a DMARC volume is a *Gmail-destined* count and "~30/day" is
  *total outbound*, two populations differing by ~1.7× since Gmail is 58% of
  send. Both numbers were always right. The 29-day baseline reads **27/day
  median total (31.7 mean), 12/day median to Gmail**, so the 17th was 4.3× the
  median and the 19th is 0.8× — an ordinary day, not a collapse. **Size the
  Postmark tier on total outbound, never on a DMARC figure.**
- ~~**Measure member email domains by registration cohort**~~ — **DONE
  2026-08-20** (above). **Microsoft is 12.1% of members in good standing (347)
  and 10.7% of those active within a year (56) — five times the Comcast share**,
  and the cohort cut shows an 8–14% band across the 20 years of data with no
  attrition signature. The working assumption that few active members use Microsoft is
  refuted, and **the Microsoft rejections keep their priority.** Also kills
  "we send them almost nothing" as the reason they are absent from the reports.
- **Add a second `rua` destination at our own domain** — **PUBLISHED
  2026-08-20** (above), the single edit that separates the three surviving
  explanations for Microsoft's absence from the reports. Landed at
  **`admin@surfguitar101.com`**, not the `dmarc@` first sketched: it is already
  aliased to Brian's Gmail, it has to reach Cloudflare Email Routing at task 06
  regardless, and retiring it later is a text deletion rather than an orphaned
  alias. Verified at both authoritative nameservers, exactly one TXT record at
  `_dmarc`, `p=none` untouched. **`rua` could not have pointed at
  `bgneal@gmail.com`** — RFC 7489 §7.1 would need an authorization record inside
  `gmail.com`'s zone; same-organizational-domain needs none.
  ~~**What is now open is reading it.**~~ — **READ 2026-08-21** (fifth reading
  above). The instrument is **not** the Gmail inbox: the forward bounces
  third-party mail, so a malformed Microsoft report would vanish and manufacture
  a false silence. **A local copy was added the same evening** —
  `/home/dmarc/mail/new/`, read with `tools/dmarc_report.py`. **That forward
  failure is now observed, not predicted**: the same night's Django error mail
  reached Gmail and the Google report did not, differing only in envelope sender.
  **The first local report names its reporter outright** — `google.com` — and
  Google addresses one message to *both* `rua` destinations, so Cloudflare
  ingests byte-identical input. **Still no Microsoft on day one of the
  08-21/08-22 window; a quiet first day is not a signal.** **Still not a
  blocker**: Microsoft deliverability is settled by task 07's Outlook inbox
  check, not by DMARC data.
- **Check what `From:` a real Postfix bounce carries** — new 2026-08-20, and it
  may unseat a hypothesis three readings have leaned on. The null-sender test
  message showed opendkim logging `can't parse From: header value 'MAILER-DAEMON'`
  for a locally submitted message with no `From:`. **If jaguar's own bounces carry
  `From: MAILER-DAEMON@jaguar.deathofagremmie.com`** — what `myhostname` would
  produce — **they appear in that domain's DMARC data and never in ours**, since a
  report only contains messages whose `From:` header domain is the policy domain.
  The four failures would then be something else entirely. **Not asserted**: the
  test's bare `MAILER-DAEMON` came from local submission with no header, and the
  bounce daemon may format differently. The check is to read the `From:` on a real
  DSN.
- ~~**Publish SPF on `mail.surfguitar101.com`**~~ — **DONE 2026-08-20** (above),
  `v=spf1 ip4:173.255.245.115 -all`, verified at both authoritative nameservers,
  exactly one SPF record at the name. **It did not "belong with requirements
  5–7"** as this line used to say: those govern the apex, this is the HELO name,
  and it needed no part of the cutover to publish. **DELIVERY-VERIFIED the same
  evening** rather than waiting for the 08-22 report: a deliberate null-sender
  message returned `spf=pass` with `smtp.helo=mail.surfguitar101.com` and an
  aligned `dmarc=pass` at Gmail. The 08-22 report is now corroboration, not the
  test.
- ~~**Add one requirement to task 03: SPF at the HELO name**~~ — **already done
  2026-08-18**, as task 03 requirement 13; this line outlived the work it asked
  for. Task 10 requirement 4 and task 03 requirement 13 are one record,
  published once. ~~Rewrite requirements 5–7~~ — withdrawn 2026-08-18, they are
  already correct; the claim that they were not came from reading a summary
  instead of the file.
- **Zone cleanup is deferred to the decommission project, deliberately** —
  raised and declined 2026-08-20. A Step 20 zone-wide DNS audit was proposed and
  **Brian's call was that it does not earn its place here**: the mail records
  each retire on a condition already written into the task that owns it (task 03
  step 8 the legacy `dkim` selector, task 06 the MX, task 03 requirement 13 the
  HELO SPF), jaguar is expected gone within about a month, and a separate `/pdd`
  is planned to decommission it alongside several other sites. **A zone audit
  belongs in that project, across all those domains at once**, rather than here
  for this one. The proposal's stated justification — that the non-mail half of
  the zone has never been audited — is true and still not worth a work item on a
  box with weeks to live.

  **What must carry forward is an ordering constraint, not tidiness.** The zone
  does *not* retire with the box: `surfguitar101.com` stays in Cloudflare and
  repoints at the new VM, so `mail` A (`173.255.245.115`) and the `mail` SPF TXT
  survive jaguar unless deleted on purpose. **Linode reassigns IPs.** The moment
  that instance is destroyed, those two records name a stranger's server as
  `mail.surfguitar101.com` and affirmatively authorize its address to send as
  that name — and if MX has not moved yet, hand it inbound mail. **Delete both
  before destroying the instance, not after.** Between the Postmark cutover and
  the decommission they are correct and should stay; the window that matters is
  minutes wide and on the far side of this project. The same trap applies to
  every other site in that move, which is the argument for carrying it as a
  checklist item there rather than a one-off here.
- ~~**Comcast delisting SUBMITTED 2026-08-18**~~ — **CLEARED 2026-08-18,
  20:44:52–20:54:52 CDT**, corrected 2026-08-20 from the Postfix log (above).
  The `220` greeting recorded on the 19th observed a state that had changed ~22
  hours earlier; the log dates the change to a ten-minute window on the 18th,
  the same evening the removal request went in. **All 23 queued messages were
  delivered, not expired** — out between 20:54 and 21:54 CDT, the oldest at
  `delay=424510` clearing Postfix's 5-day lifetime with 2.1 hours to spare — so
  nothing returned to `no_reply@` and no bounces died locally. **Comcast's MX
  accepted 23 messages with `250 … mail accepted for delivery`**, which is well
  past the greeting; inbox placement is still unobserved, since spam-foldering
  is downstream and invisible from here. Original text follows.

  Originally sequenced **after** the backscatter fix rather than before — asking
  while the box still bounces to forged senders invites a second listing. **No
  longer time-sensitive: Brian's call 2026-08-18 is to let the 23 queued
  messages expire** *(they did not expire — see the correction above)*, since Comcast has been blocking for a long time, the mail
  is stale, and no removal request would have completed inside the remaining
  hours anyway. They return to `no_reply@`, which is not in the alias map, so
  the bounces die locally.
- ~~Retire the two dead certs~~ — **done 2026-08-18**, `certbot -q renew` silent.
- ~~Add `root@surfguitar101.com` to the virtual alias table~~ — **done
  2026-08-18**, delivery confirmed in Brian's inbox.
- **All four host-side repairs are now task 10**
  (`task-10-old-host-mail-repairs.code-task.md`, created 2026-08-18): the alias
  entry, the sender rewrite, the HELO SPF record and the backscatter fix, with
  the inventory gated ahead of them.
- ~~Add `root@surfguitar101.com` to the virtual alias table~~ — **done
  2026-08-18**; it points straight at Brian's Gmail, matching the file's style.
- ~~Rewrite local system senders onto `@surfguitar101.com`~~ — **done and
  verified 2026-08-18**; the class turned out to be Django's error reports, lost
  for years. Now `dkim=pass`/`spf=pass`/`dmarc=pass` at the receiver.
- ~~Confirm system mail resumed now the PTR forward-confirms~~ — **withdrawn: it
  will not.** Two of the three faults are unrelated to reverse DNS, and the
  third only changes error code from `5.7.25` to `5.7.26`. 33 rejections in
  three days went unnoticed, which means nothing was watching that path either
  way.
- **Switch opendkim to `Canonicalization relaxed/relaxed`** before SPF reaches
  `-all`, since `simple/simple` breaks on any in-transit modification and
  forwarded mail will then depend on DKIM alone.
- ~~Enable opportunistic outbound TLS~~ — **done and verified 2026-08-18**,
  TLSv1.2 to Gmail, confirmed encrypted at the receiver.
- ~~Backscatter — verify it stopped rather than fix it.~~ **Verified 2026-08-18:
  about one DSN a day reaches an outsider, down from the misread 53-in-three-days
  but not zero. No change on this box; task 06 retires it.**
- **Superseded — backscatter, original framing:** Traced 2026-08-18: one
  DSN, not 53, caused by a forwarded message Gmail refused for the missing PTR.
  That trigger was repaired 2026-08-17, so the expected state is zero. Residual
  risk is inherent to forwarding third-party mail and is retired by task 06.
- ~~Explain `inet:localhost:88888`~~ — **not open.** Finding 7 and requirement 12
  already explain it and decide to leave it alone.
- ~~Postmark is still in Test mode~~ — **approved 2026-08-17, same day.** Live
  sending is unblocked; task 07's live send no longer has an account-state
  dependency. The approval request led with measured volume, the double opt-in
  registration flow, and a volunteered warning that ~63% of notification
  subscribers are 3+ years dormant with a graduated warm-up planned. *(The 63%
  stands as a subscriber headcount; the warm-up was dropped 2026-08-20 once the
  figure was re-measured as mail actually sent. What was said to Postmark is left
  as it was said.)*
- Requirements 5–7 (SPF rewrite, `~all`, then `-all`) belong with the task 02
  cutover, not with this sitting.

**Three corrections in one document in two days is a pattern, not luck: DNS and
mail configuration are unusually easy to reason about confidently and get wrong,
because almost nothing in the system reports a disagreement.** That is the same
property that let the original FCrDNS break go unnoticed for years.

## Step 16 task 10 — jaguar's host-side mail repairs — 2026-08-18 → 2026-08-20

*Split out of task 03's section on 2026-08-26: this work was recorded under a
heading naming a different task, where nothing about the Comcast block, the
cron-mail puzzle or the backup box could be found by looking for it. Content
unchanged; the DMARC readings it was interleaved with are now in
`research/dmarc-readings.md`.*

**Context for the first subsection below, which opens mid-investigation.** "The
4" are the four failing messages in the **first DMARC reading** (2026-08-18,
Gmail's view alone: 61 of 65 passing) — read that reading first, in
`research/dmarc-readings.md`. Everything here follows from chasing those four,
and it ends with all four host-side repairs done and Comcast's block lifted.

### Hypothesis, with the observation that will settle it: the 4 are Postfix bounces

**Labelled a hypothesis on purpose.** The obvious first guess was already wrong:
misaligned envelope senders from cron and root mail on `deathofagremmie.com`.
The detail view rules it out — envelope-from domain is `surfguitar101.com`, and
Cloudflare keys rows by (From domain, source IP, envelope domain), so a different
envelope domain would be its own row.

What fits every column is a **DSN generated by Postfix itself**:

- A bounce carries a **null envelope sender** (`<>`), so SPF has no envelope
  domain and falls back to the **HELO identity** (RFC 7208 §2.3). Until
  2026-08-17 that was `jaguar.deathofagremmie.com` — unaligned with the From
  domain, so SPF fails.
- Its From is `MAILER-DAEMON@surfguitar101.com`, because `/etc/mailname` is
  `surfguitar101.com`. That is why these land in *this* domain's report and read
  as aligned in the From column.
- **Postfix does not apply milters to internally generated bounces**, so opendkim
  never signs them. No signature, no DKIM pass.

**The hole in that story, found while writing the log commands rather than after
running them: a DSN goes back to the *original envelope sender*, and for site
mail that is an address on `surfguitar101.com` — not Gmail.** As stated above the
hypothesis does not explain how Google came to report these at all. It needs one
more step, and the likely one is **the inbound alias forwarding this box still
does for the other domains**: a Gmail user mails an alias here, the forward or
the final delivery fails, and Postfix sends the DSN *back to that Gmail user* —
`From: MAILER-DAEMON@surfguitar101.com`, unsigned, null envelope sender, HELO on
the dead domain. Google then reports it under this domain.

That is a refinement, not a reversal: the bounce mechanism survives, the message
flow changes from site mail to inbound-forward bounces. **It is also the cheaper
thing to check**, because the recipients settle it outright — Gmail recipients on
the null-sender messages confirm it, `surfguitar101.com` recipients kill it.

**The discriminator, which is the point of writing it down before checking:**
now that `smtp_helo_name` is `mail.surfguitar101.com`, this class should begin
**passing on SPF alone while still showing no DKIM.** If the next few days show
that shift, the hypothesis holds. If the failures keep failing both, it is
something else and this paragraph is wrong. See
[[measure-before-recording-in-planning-docs]] — three claims in this document
already went in unmeasured.

**Correction, 2026-08-18, before any observation could arrive: that prediction is
wrong, and alignment was never the missing piece.** A null-sender SPF check
evaluates the **HELO domain**, so it looks up a TXT record *at
`mail.surfguitar101.com`* — and task 03 published that name as an A record only.
No record means the SPF result is `none`, not `pass`, so there is still no
aligned pass and the class still fails DMARC. The HELO change fixed *which name*
is checked; it published nothing for the check to find. **The actual fix is an
SPF record on the mail subdomain** — `v=spf1 ip4:173.255.245.115 -all` — which
belongs with requirements 5–7 rather than here. The revised prediction is
therefore that these keep failing both mechanisms until that record exists.

Faster confirmation is on the box, in three steps of increasing cost. First
`postconf -n | grep -Ei 'milter|internal_mail_filter_classes'` — **one command
that can kill the hypothesis outright**, since an `internal_mail_filter_classes`
listing `bounce` means Postfix *does* sign its own notifications and none of this
holds. Then the queue IDs delivered to Gmail that carry no signing line from the
milter, which should number about 4. Then the null-sender messages and their
recipients, per the paragraph above. Note the log is in local time while a report
day is UTC, so the window spans two log days.

Per-record raw XML would settle all of it outright, and getting it means a second
`rua` on a `surfguitar101.com` mailbox — which, being inside the policy domain's
own organizational domain, needs no `_report._dmarc` authorization, unlike the
Gmail fallback rejected in correction 4.

### What the mail log showed — the premise holds, the flow is a third variant

Run on the box 2026-08-18, in the order of increasing cost written above.

**The premise is established at the config level, and by measurement rather than
memory.** `postconf -n` does not list `internal_mail_filter_classes`, and
`postconf -d internal_mail_filter_classes` prints it empty — the built-in
default. Internally generated `bounce` and `notify` mail therefore reaches
neither milter list: **Postfix's own DSNs go out unsigned.** The same output
established something that *closes* a rival explanation: `non_smtpd_milters` is
set, so mail injected locally through `sendmail(1)` — cron, root, anything from a
shell — **is** signed. Unsigned cron mail is not the answer.

**Null-sender traffic exists in quantity**: 463 queue IDs across the retained
logs. Scoped to 2026-08-16→18 — and scoped deliberately, because *Postfix reuses
queue IDs*, so matching a three-week-old ID against today's log silently mixes
unrelated messages — the recipients are:

| Recipient | Lines |
|---|---|
| `member21@example.com` | 53 — **one message retried, see below** |
| `bgneal@gmail.com` | 33 |
| `admin@surfguitar101.com` | 30 |
| `root@surfguitar101.com` | 6 |
| `root@localhost` | 6 |
| two others | 1 each |

**The flow is a third variant, simpler than either guess.** Not site-mail bounces
(which return to a `surfguitar101.com` sender, never to Gmail), and not bounces
to a stranger at Gmail: `admin@` and `root@` receive the DSNs, **the aliases
forward them to Brian's own Gmail**, and the forwarded copy keeps the null
envelope sender while still bypassing the milters. 36 in, 33 out.

**Two reasons this is confirmed in kind but not yet in number.** Those are log
*lines*, and a deferral or retry logs one each, so 33 lines is an upper bound on
messages. And only bounces *this box generated* carry
`From: MAILER-DAEMON@surfguitar101.com`; a bounce generated by a remote server
and merely forwarded keeps *its* From domain and is reported to that domain, not
this one. That subset distinction is the likely reconciliation of 33 against the
4 Google reported.

**Still open: read one.** The decisive instrument is Brian's own inbox — he
received them. A `MAILER-DAEMON` message from 2026-08-17, with `Return-Path: <>`
and its `Authentication-Results`, settles the class outright.

### The backscatter finding — traced 2026-08-18, and both halves of it were wrong

**Originally recorded here as "53 DSNs to one Korean address in three days", with
the box accepting mail for an address it cannot deliver and bouncing it to a
forged sender.** Tracing one DSN back to its cause corrected the volume, the
mechanism, and the fix.

**The volume was one message, not 53.** Every one of those lines carries the same
queue ID, `4F3A25869C1`, retrying hourly with `status=deferred` because
`uplus.co.kr` does not accept connections. *Log lines counted as messages — the
identical error this document warned about two hours earlier while counting the
33 rejections to Brian's Gmail.* See
[[measure-before-recording-in-planning-docs]].

**The mechanism is forwarding, not unknown recipients**, and the full chain is in
the log:

```
03:44:39  mail.21cpat.com [210.124.121.5] connects
          from=<member21@example.com>  ->  themadeira@themadeira.net    (forged sender)
03:44:41  forwarded on to member36@example.com
          Gmail: 550-5.7.25 ... does not have a PTR record setup
03:44:41  postfix/bounce: sender non-delivery notification: 4F3A25869C1
          -> DSN to the forged address
```

The recipient was **valid**, so rejecting unknown recipients would not have
prevented it — and `smtpd_reject_unlisted_recipient` is already `yes` by default,
so accept-then-bounce for unknown recipients was never happening at all. The
originally prescribed fix addressed a mechanism this box does not have.

**And the trigger is already fixed.** The DSN exists because *Gmail refused the
forwarded message for the missing PTR* — repaired 2026-08-17. With reverse DNS
forward-confirming, that forward now succeeds, no DSN is generated, and no
backscatter leaves. **Task 03's DNS work appears to have closed this without
anyone aiming at it.**

**What remains is inherent to forwarding.** Relaying other people's mail to
third parties (`themadeira.net` forwards to four external addresses) risks a
bounce to a forged sender whenever the destination refuses for *any* reason,
spam content included. No Postfix setting removes that while the box forwards;
task 06's move to Cloudflare Email Routing retires it structurally.

### The Gmail capture, 2026-08-18 — the wrong class of message, and worth it anyway

A "new private message" notification to `bgneal@gmail.com`. `Return-Path:
<no_reply@surfguitar101.com>`, so it is **one of the 61 that passed, not one of
the 4** — it cannot speak to the bounce hypothesis. It settles three other things.

**1. FCrDNS is now delivery-verified.** This is the header that was named as the
missing proof and handed to task 07:

```
Received: from mail.surfguitar101.com (mail.surfguitar101.com. [173.255.245.115])
```

Gmail renders `from <HELO> (<rDNS>. [ip])`, the trailing dot marking the
parenthetical as a PTR lookup. Both names agree, at the receiver, on a hostname
that resolves back to the sending IP — **the parenthetical that was empty in the
2026-08-12 capture, now filled in**, and confirmed from outside rather than by
`dig` against `*.akam.net`.

**2. Correction 5 confirmed a second time, independently.**
`<20260818173830.1921.2790@jaguar.deathofagremmie.com>` — still the dead domain,
still `YYYYMMDDHHMMSS.pid.randrange(100000)`, i.e. Django's `make_msgid()` from
`socket.getfqdn()` on the app host. Neither the interim fix nor anything SMTP-side
touched it, exactly as predicted. The internal `Received: from
jaguar.deathofagremmie.com ... by jaguar.deathofagremmie.com` hop is correction
3's deliberate `myhostname` decision showing through, and is internal-only.

**3. A new fragility that bears directly on requirements 5–7: the signature is
`c=simple/simple`.** Simple canonicalization breaks on *any* modification in
transit — a forwarder's trailing whitespace is enough — where `relaxed/relaxed`
tolerates it. That is cushioned today because SPF also passes. It stops being
cushioned at `-all`, **because the entire argument for tightening SPF was that
DKIM carries forwarded mail through** (the Google row above). Switching opendkim
to `Canonicalization relaxed/relaxed` before tightening removes the brittle link;
it becomes moot for site mail once Postmark signs, since Postmark uses relaxed.

Otherwise clean: `dkim=pass header.s=dkim` (the legacy 1024-bit selector, since
Postmark is not in the path yet), `spf=pass smtp.mailfrom=no_reply@...`,
`dmarc=pass`.

### `inet:localhost:88888` — rediscovered, not discovered

Both milter lists point at a port that cannot exist, and signing works anyway. I
wrote this up as an open anomaly. **It is already in the task file**, in Finding 7
and requirement 12, with the same arithmetic (`88888 − 65536 = 23352`), the same
"both sides truncate identically" explanation, the same `ss -lntp` verification,
and a decision already taken: *do not touch it*, since the milter is being
decommissioned with the box.

**That is the second thing in this sitting I presented as new after not reading
the file** — the other being requirements 5–7. Finding 7 is itself the record of a
correction on this exact config line, which makes rediscovering it a small irony
and a large hint: **when this document and the task file disagree, the task file
has usually already been there.**

### The SPF record, finally read — and it proves what the 4 must be

```
v=spf1 a mx ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 -all
```

Read 2026-08-18, after two days of reasoning about its mechanisms without ever
querying it. Three things fall out, and the first is the important one.

**1. The explicit `ip4:` term makes the 4 failures diagnosable by elimination.**
Any message from `173.255.245.115` with an envelope domain of
`surfguitar101.com` passes SPF, unconditionally — the `a` mechanism's Cloudflare
problem cannot break it, because the literal IP is listed. **So a message from
that IP that failed SPF cannot have had an aligned envelope domain at all.** The
only such class this box produces is null-sender mail, where SPF falls back to
the HELO name — which publishes no TXT record, giving `none`. Combined with the
established fact that bounces bypass the milters and go out unsigned, **that is
both failures accounted for, and no other class on this box fits.** The bounce
hypothesis is now supported by elimination rather than by story.

**2. The live record matches Finding 3's audit exactly**, two days on: `a` and
`mx` both still present, the explicit `ip4:` and the inert `ip6:` both still
there, and the qualifier already `-all`.

**3. And a correction against myself, caught by finally opening the task file.**
I claimed here that requirements 5–7 were wrong — that they assumed a permissive
record needing staged tightening. **They do not, and every point I thought was
missing is already written down**: Finding 3 says remove `a` *and* `mx` and gives
the reasons; requirement 5 supplies both replacement records with `a` and `mx`
dropped; requirement 6 opens with "the current `-all` is a hard fail" and softens
it to `~all` only for the cutover window, explicitly warning not to leave it
there; requirement 7 records that Postmark passes SPF via its Return-Path domain
without the include. **I inferred all of that was absent from a one-line summary
of the requirements in this file, and asserted a document was wrong without
reading it** — the same failure as the 1024-bit key and the `_dc-mx` alias, which
this very document already records twice. See
[[measure-before-recording-in-planning-docs]].

**The one genuine gap is narrower.** Nothing in requirements 5–7 covers an SPF
record at the **HELO name**, `mail.surfguitar101.com`. Every record they discuss
is the apex, which null-sender mail never consults. That single omission is what
leaves this box's bounces unauthenticatable, and it is a one-record addition
rather than a rewrite.

The `ip6:` term remains inert, as recorded earlier: `inet_protocols = ipv4`.

### Gmail states the diagnosis in plain text — `550 5.7.25`

The two sampled messages were both rejected outright, and the refusal is not
generic:

```
550-5.7.25 [173.255.245.115] The IP address sending this message does not have a
550-5.7.25 PTR record setup, or the corresponding forward DNS entry does not
550-5.7.25 match the sending IP.
```

**That is the entire FCrDNS diagnosis, quoted back by a receiver.** Task 03
inferred it from `dig` and from Microsoft's rejections; Google names it. Both
samples predate the PTR landing (2026-08-16 02:55 and 2026-08-17 08:36 CDT), so
this is the *old* state being confirmed rather than a live fault — but it is the
strongest evidence in this document that the diagnosis was right.

**It also exposes a consequence nobody had noticed: system mail was being thrown
away.** Both samples are `orig_to=<root@localhost>` and
`orig_to=<admin@surfguitar101.com>`, i.e. system and admin mail forwarded to
Brian's Gmail by the aliases — 33 attempts in three days, every one rejected.
**Server mail addressed to the administrator has not been arriving**, silently,
for years. See the section below for what it actually is, which turned out to be
three separate faults rather than one.

The second sample also settles the message flow: `postfix/bounce[30855]:
8E9AD5869CC: sender non-delivery notification: 0BB2B58654D` — this box generating
a DSN, which the `admin@` alias then forwarded to Gmail. Exactly the flow this
section hypothesised.

### The years-old cron-mail puzzle, measured — three faults, not one

Brian has several system mails he watches for and **has only ever regularly
received one of them**, a symptom he had puzzled over for a long time. The log
resolves it, and the answer is not the one this document predicted.

**The survivor is his own crontab.** `postfix/pickup: uid=1000 from=<brian>`,
rewritten by Postfix to `brian@surfguitar101.com` — the signing domain — so
opendkim signs it and SPF passes on the `ip4:` term. Delivered every morning at
02:01, accepted by Gmail *even while the PTR was broken*, because authentication
compensates for reverse DNS. That is why it is the one that always arrives.

**Fault 1 — root's cron mail never leaves the machine.** Twice daily, ~2.4 KB,
and every one of them:

```
to=<root@surfguitar101.com>, orig_to=<root>, relay=none,
    dsn=5.1.1, status=bounced (User unknown in virtual alias table)
```

Postfix rewrites bare `root` onto `surfguitar101.com`, which is a **virtual alias
domain with no `root` entry**, so delivery fails locally in 0.06 seconds. This
has nothing to do with DNS, DKIM, SPF or Gmail — **the mail is generated and
discarded on the same box**, and the DSN about it is itself undeliverable. *This
document predicted an authentication failure for this class. It was wrong: the
class never gets far enough to be authenticated.*

**Fault 2 — mail from `root@localhost` is refused as unauthenticated.** Sent to
`admin@surfguitar101.com`, forwarded to Gmail, and rejected with Google saying
exactly why:

```
550-5.7.26 Your email has been blocked because the sender is unauthenticated.
550-5.7.26 Gmail requires all senders to authenticate with either SPF or DKIM.
550-5.7.26  DKIM = did not pass
550-5.7.26  SPF [localhost] with ip: [173.255.245.115] = did not pass
```

`localhost` is on no signing table and has no SPF record, so this class is
unauthenticated by construction.

**Fault 3 is the one already recorded**: the null-sender DSNs, refused with
`5.7.25` for the missing PTR.

**A contradiction was recorded here and then dissolved the same day.** Brian
receives root cron mail every few months, which a 100% measured failure rate
cannot produce — so this section called it an open contradiction and task 10
gated its fixes behind explaining it. **The inventory explained it in one step:
that mail comes from a different machine.** `bobcat.gremmielabs.dev`
(198.58.104.73) rsyncs this box nightly at 03:15 and mails its cron output, which
authenticates on SPF and arrives normally. Jaguar's root mail is not
intermittent; it fails every single time. *The "contradiction" was two servers
being read as one, and the framing overstated what four weeks of log could say
about a months-scale event.*

### The inventory, run 2026-08-18 — complete, and nothing root-originated survives

| Source | Sender | Fate |
|---|---|---|
| Brian's crontab (uid 1000) | `brian@surfguitar101.com` | **delivered**, daily 02:01 |
| site mail to `admin@` | `no_reply@surfguitar101.com` | **delivered**, 23 in the window |
| certbot, `cron.daily`, `cron.weekly` | `root` → `root@surfguitar101.com` | **`5.1.1`, dies on the box** |
| munin, munin-node, sysstat | same | silent, no output observed |
| local notices | `root@localhost` | **`5.7.26`, refused by Gmail** |

No root crontab, no systemd timers, and `/etc/crontab` sets no `MAILTO`, so every
`run-parts` job defaults to `root`. **Not one root-originated message was
delivered in four weeks of retained logs.**

### The certbot job is a dead alarm — and the certificates are fine

The twice-daily 2.4 KB is `certbot -q renew`, where `-q` should print nothing on
success. It prints every time because **two retired domains carry long-expired
certificates it keeps trying to renew** — `briananddebra.com` (2023-07-07) and
`deathofagremmie.com` (2023-12-26) — plus OCSP warnings from a certbot older than
Let's Encrypt's retirement of OCSP.

**The live certificates are healthy**: `surfguitar101.com` 89 days,
`wiki.surfguitar101.com` 40, `themadeira.net` 30. The feared renewal failure is
not happening.

**What is happening is worse in a quiet way: the alarm is stuck on.** A job whose
output is never empty cannot signal anything, and its mail is destroyed before
anyone reads it. Repairing delivery without silencing the noise would deliver
2.4 KB of meaningless output twice a day — the same failure in a different hat.
Task 10 requirement 6 covers it, with the trap noted: **deleting a certificate an
Apache vhost still references stops Apache from starting.**

### An undocumented dependency: the backup box

The mail that solved the puzzle also exposed something the plan has never
recorded. `bobcat.gremmielabs.dev` holds a nightly rsync of this machine —
`sg101<date>.sql.bz2` dumps, the media tree, the moin wiki, `.hg`, and Brian's
other sites. **Step 21 migrates to a new VM and says nothing about the backup box
protecting the old one.** At cutover that rsync keeps backing up a machine nobody
uses, and the new VM has no backup at all until someone notices. Added to the
Step 21 line in `plan.md`.

**Correction to this document's own prediction.** It said this mail "should
resume now that the PTR forward-confirms." **It should not, and mostly will
not.** Fault 1 is a local alias-table miss that DNS cannot touch. Fault 2 fails
Gmail's authentication requirement, which reverse DNS does not satisfy. Even
fault 3 only changes error code: with the PTR fixed, an unsigned null-sender
bounce stops failing `5.7.25` and starts failing `5.7.26`, because Google
requires SPF *or* DKIM to pass and it still has neither.

**The three fixes are small, separate, and none of them is a DNS record — except
one.** A `root@surfguitar101.com` entry in the virtual alias table fixes fault 1.
Rewriting local system senders onto `@surfguitar101.com` so they are signed fixes
fault 2. And **requirement 13's SPF record at the HELO name fixes fault 3 and the
DMARC failures with the same line**, since an SPF pass on the HELO identity
satisfies both Google's authentication requirement and DMARC's need for one
aligned pass.

### Task 10 executed, part one — 2026-08-18, requirements 6 and 2 done

Run on the box with Brian driving, one script at a time. **Both verified from the
receiving side, not from the log.**

**Requirement 6 — certbot is an alarm again.** `deathofagremmie.com` turned out
to be an *enabled* Apache vhost naming all three of its expired cert files, so
the trap this requirement warned about was real: deleting the cert first would
have stopped Apache from starting and taken `surfguitar101.com` down with it.
Order run: `a2dissite`, `configtest` (Syntax OK), reload, confirm both live sites
still answer 200, then `certbot delete` on both dead certs. **`certbot -q renew`
now prints nothing and exits 0** — the twice-daily 2.4 KB is gone, so a future
message from that job means something.

**Correction to a phrase this document has used repeatedly: `deathofagremmie.com`
is not "a dead domain". Brian no longer owns it.** The renewal was failing with a
403 from *Cloudflare addresses belonging to whoever holds it now* — certbot has
been trying twice a day to prove control of someone else's domain. The box still
calls itself `jaguar.deathofagremmie.com` in `myhostname` and stamps that into
every Django `Message-ID`. Cosmetic, since HELO was fixed in task 03, but "dead"
and "someone else's" are different facts and the second is a better argument for
retiring the box.

**Requirement 2 — root's mail arrives, for the first time.** The mechanism is now
fully established from the config rather than inferred:

1. `myorigin = /etc/mailname` = `surfguitar101.com`, so bare `root` becomes
   `root@surfguitar101.com`
2. `virtual_alias_domains` contains `surfguitar101.com`, so that address resolves
   through `virtual_alias_maps`
3. no `root` entry there → `5.1.1 User unknown in virtual alias table`
4. **`/etc/aliases` line 2 is `root: bgneal@gmail.com`** — and it is never
   consulted, because `/etc/aliases` serves `mydestination` domains only

**The intent was there all along.** That line has been trying to deliver root's
mail since before 2017 and stopped working the moment `surfguitar101.com` became
a virtual alias domain. One line added to `virtual_alias_maps`, `postmap`,
`postfix reload`, and:

```
19:23:20  169FB58658E: to=<bgneal@gmail.com>, orig_to=<root>, dsn=2.0.0, status=sent
```

**Brian confirms the message arrived in his Gmail inbox** — receiver-side, not a
`status=sent` line, which is the standard this project holds itself to. It also
passed Gmail's authentication, so `root` (rewritten onto the signing domain) is
signed; only the `root@localhost` sender form is unauthenticatable.

### Fault 3, quoted by the receiver rather than inferred

Gmail's refusals name the exact SPF identity it evaluated:

```
SPF [] with ip: [173.255.245.115] = did not pass          <- null envelope sender
SPF [localhost] with ip: [173.255.245.115] = did not pass  <- root@localhost
DKIM = did not pass                                        <- both
```

**An empty SPF identity is the bounce class**, and it is the strongest evidence
yet for the diagnosis of the 4 DMARC failures: unsigned mail with no envelope
domain to check.

### The IP is blocked by Comcast, and a member has missed 23 emails

Found by accident while testing the root alias — the tail of the mail log was
full of it:

```
554 ... 173.255.245.115 found on one or more DNSBLs
```

**Comcast refuses every message from this IP.** The queue holds 24 messages,
74 KB: 23 site notifications to one member at `comcast.net`, plus one to
`uplus.co.kr`. The oldest carries `delay=416092` — **4.8 days**, against
Postfix's 5-day default queue lifetime, so they begin expiring and bouncing
today. **Left to expire, on Brian's call** — see the Open list.

**Checked against six public blocklists from outside the box — `zen.spamhaus.org`,
`b.barracudacentral.org`, `bl.spamcop.net`, `dnsbl.sorbs.net`,
`ips.backscatterer.org`, `psbl.surriel.com` — and the IP is on none of them.** So
this is Comcast's own internal list, which their `BL000100` code refers to, and
the remedy is their block-removal request rather than waiting.

**This is worse than the reputation reading taken from the Outlook capture.**
That said "authentication perfect, reputation neutral". Neutral is not the
picture: one major consumer ISP refuses outright, and has been doing so long
enough to accumulate a 23-message backlog for a single member. It is also the
sharpest argument yet for moving member mail to Postmark, whose IPs are not this
one.

### Three probes that could not match, in one session

Recorded because it is now a pattern rather than an incident. `grep -r` skips
symlinks during recursion, so the Apache vhost search would have returned nothing
from `sites-enabled` (fixed to `-R` before running). The alias audit looked in
`/etc/postfix/virtual`, `virtual_alias` and `vmailbox` — none of which exist here;
the real file is `virtual_alias_maps`, so its empty output meant "looked in the
wrong place". And a reload step used `systemctl` on a box already established to
be upstart-era. **Each would have produced silence that reads exactly like a
clean result**, which is the same failure as the deprecation gate certifying a
green suite while unbound. See [[measure-before-recording-in-planning-docs]].

### Requirement 5 verified — and the answer was a third thing

The check predicted DSN generation would fall to zero after the PTR repair. **It
did not**, and the raw counts refuse the prediction outright: 22 on 2026-08-17,
6 on 2026-08-18. But the metric counted *every* DSN the box generates, most of
which are internal — root's twice-daily `5.1.1`, and one for each of the Gmail
refusals. Classifying the 28 DSNs from those two days by recipient:

| Recipient domain | Count |
|---|---|
| `surfguitar101.com` | 25 |
| `gmail.com` | 21 |
| `solutions-entreprises-digitales.com` | 1 |
| `mail39.atl71.mcdlv.net` | 1 |
| `localhost` | 1 |

The first two overlap — a DSN to `admin@` is forwarded to Brian's Gmail and logs
under both. **Only two DSNs reached outsiders in two days**, one of them
delivered at 04:06 on 2026-08-18, i.e. *after* the PTR repair.

**So the real backscatter rate is about one a day, and the PTR fix removed the
dominant trigger rather than the mechanism.** Both survivors are the forwarding
pattern, and one is a Mailchimp VERP address, i.e. list mail rather than spam. At
that volume, on a box being decommissioned, requirement 5 stays a verification:
no change here, retired structurally by task 06.

*Three readings in one afternoon — "53 messages, fix it", "one message, already
fixed", "one a day, mechanism intact" — each from measuring something slightly
different. The first two were wrong because the measurement was, not because the
box changed.* See [[suspect-the-measurer-before-the-record]].

### Outbound mail has been unencrypted this whole time

Found inside one of those two bounces, which is the argument for reading them:

```
530 Must issue a STARTTLS command first (in reply to MAIL FROM command)
```

`smtp_tls_security_level` is unset, which on this Postfix vintage means
**outbound TLS is off entirely: every message this box has ever sent left in
plaintext.** Inbound has `smtpd_use_tls = yes` with the snakeoil self-signed
certificate — which is exactly why nobody noticed, since the configuration reads
as TLS-aware at a glance.

**Two consequences, neither visible in any DMARC report**, because this is not an
authentication failure and nothing reports it:

1. Receivers that require STARTTLS refuse outright — the AWS host above did.
2. **Google's bulk-sender guidelines list TLS as a requirement**, so this has
   been quietly counting against the sender at the very receiver whose
   acceptance this step has spent two days measuring.

**FIXED AND VERIFIED the same day.** `smtp_tls_security_level = may` applied,
and the proof is on both sides: `Untrusted TLS connection established to
gmail-smtp-in.l.google.com: TLSv1.2 with cipher ECDHE-ECDSA-AES128-GCM-SHA256`
in the log, and **Gmail reporting the delivered message as encrypted where it
previously reported it was not.** ("Untrusted" is correct and expected —
opportunistic TLS does not verify the peer's chain; the traffic is encrypted
regardless.)

**This is the second finding in this step that no amount of DMARC data would ever
have surfaced**, the first being root's mail dying locally. The reports say what
authentication did; they are silent about everything that stops a message before
authentication is evaluated.

### The `root@localhost` mail was Django's error reports — req 3 done 2026-08-18

Requirement 3 was written to fix an unauthenticatable sender. Identifying what
actually sends that way turned it into the most operationally significant finding
of the day.

**It is `mail_admins()` through `AdminEmailHandler`.** Three signatures agree:
the Message-ID is `YYYYMMDDHHMMSS.pid.randrange(100000)` — Python's
`email.utils.make_msgid()`, the same format task 03's correction 5 used to
identify Django's stamping; submission is `client=localhost.localdomain
[127.0.0.1]`, i.e. SMTP to localhost, which is how the site sends; and the
messages are 5–10 KB, the size of a traceback.

The sender is `root@localhost` **because `SERVER_EMAIL` is unset** — precisely
the defect Step 16 task 01 found in the settings and fixed in code. Task 01
recorded it as configuration that *would* break after cutover. **It has been
breaking all along:** 18 error reports between 2026-07-20 and 2026-08-18, every
one refused by Gmail with `5.7.26`, and the bounce about each also failing.

**Nobody has seen a Django exception report from the live site in years.** The
site could have been throwing errors continuously and the only channel that would
say so was destroying the evidence at both ends.

**Fixed with `sender_canonical_maps`**, one entry, `root@localhost` →
`root@surfguitar101.com`. `sender_canonical_classes` was already at its default
of `envelope_sender, header_sender`, and **the header half is the load-bearing
one** — OpenDKIM signs by From domain, so an envelope-only rewrite would have
fixed SPF and left DKIM failing.

Verified at the receiver, which was necessary rather than ceremonial:

```
dkim=pass header.i=@surfguitar101.com header.s=dkim
spf=pass  smtp.mailfrom=root@surfguitar101.com
dmarc=pass header.from=surfguitar101.com
```

*OpenDKIM logged nothing for that message. The mail log showed delivery and said
nothing about signing, so on log evidence alone this would have been recorded as
"passed on SPF, DKIM unknown". The header answered it in one line.*

**Interim by construction**, and worth flagging so nobody later reads it as
duplication: task 01's `SERVER_EMAIL` setting does this job properly, but
production runs the old code and will for several more steps. The Postfix rewrite
covers the gap and becomes redundant, and harmless, at deploy.

**Expect a consequence:** roughly 18 tracebacks a month now start arriving. If
the site turns out to have been failing quietly, that is this fix working.

### The Comcast block, chased to its actual source — 2026-08-18

Four steps, two of them dead ends, ending in a list no public query can see.

**1. The first delisting request went to the wrong form.** Comcast's Blocked
Provider Request Form covers error `BL000000`; our bounces say **`BL000100`**.
Their reply: *"Of the one IP(s) you submitted, none were on our blocklist"* — an
accurate answer to a question we had not asked.

**2. The block is still live, confirmed without sending mail.** Comcast refuses
at the SMTP *greeting*, so a bare TCP connection from the box settles it. Both
`mx1.mxge.comcast.net` (priority 5) and `mx1a1.comcast.net` returned
`554 … found on one or more DNSBLs … #BL000100` on 2026-08-18, after their reply.

**3. My "not on six public blocklists" claim was never a measurement, and the
conclusion survived anyway.** Re-run from jaguar with a `127.0.0.2` control on
every zone — the test entry that must be listed — eight of nine zones answered
(SORBS did not), and Spamhaus ZEN, SpamCop, Barracuda, CBL, SpamRats, UCEPROTECT,
PSBL and GBUdb all report the IP unlisted. **But the original check, run from a
laptop, had four zones silently refusing to answer it**: Spamhaus and SpamRats
block lookups from public and cloud resolvers, and a blocked query returns
exactly what "not listed" returns. *The answer held; the evidence did not.
Recording both, because the version of this that matters is the one where the
guess is wrong.*

**4. `BL000100` is Validity's Return Path Blocklist.** The link inside the error
leads, after a redirect, to `senderscore.org/assess/blocklist-lookup/` — Validity,
formerly Return Path. **A commercial reputation feed, invisible to every public
DNSBL query**, which is exactly why Comcast's own list is clean, eight public
lists are clean, and the greeting still refuses.

**Removal requested 2026-08-18** through Validity's form, which asked only for
name, business, email, country and a mass-mail declaration — and **did not report
whether the IP was listed**, so its state there is unknown. Re-check the SMTP
greeting in a day or two; that is the only ground truth on this.

**Perspective, so nobody spends a week here:** this IP's reputation dies with the
box. After cutover, member mail leaves from Postmark's addresses and none of this
follows it. What is at stake meanwhile is notifications to `comcast.net` members
between now and then — real, bounded, and not worth a campaign.

### The Comcast block is gone — 2026-08-19, and this one is a clean before/after

Re-checked from jaguar with the same command against the same two MX hosts that
refused the day before:

```
mx1.mxge.comcast.net     220 resimta-a2p-650690.sys.comcast.net resimta-a2p-650690.sys.comcast.net ESMTP server ready
mx1a1.comcast.net        220 resimta-a2p-651040.sys.comcast.net resimta-a2p-651040.sys.comcast.net ESMTP server ready
```

`554 … found on one or more DNSBLs … #BL000100` on 2026-08-18, `220` on
2026-08-19. **Same host, same command, same targets, different answer** — which
*(the mail log later dated the change to the evening of the 18th, not the 19th;
see the correction below)* — which
is the part worth recording, because the blocklist work in this step twice
produced a result that was really an instrument artifact. Here the instrument
was held fixed and only the answer moved. See
[[suspect-the-measurer-before-the-record]].

**What it establishes and what it does not.** Comcast refuses at the SMTP
greeting rather than at `DATA`, so the greeting *is* the block — there is nothing
left to reject at that stage. But a `220` is the connection being accepted, not a
message reaching an inbox: `RCPT TO`, `DATA` and spam-foldering are all still
downstream, and **no delivery to a `comcast.net` mailbox has been observed.**
That is the standard this project has held everywhere else (Gmail inbox confirmed
by Brian, Outlook confirmed by `dest:I` in the headers) and this result does not
meet it.

**On causation, stated at the strength the evidence supports.** Removal was
requested through Validity on 2026-08-18 and the block was gone by the 19th, so
the timing fits. It is not proof: Validity's form never disclosed listing status,
so "cleared within a day of the request" is the claim, and a feed refresh or an
aged-out listing are not excluded. The identification of `BL000100` as Validity's
Return Path Blocklist stands either way — it came from the error's own link, not
from the outcome.

#### CORRECTED 2026-08-20 from the mail log — the block lifted on the 18th, and all 23 messages were delivered

The three paragraphs above were written from telnet probes plus an inference
about the queue. **The Postfix log contradicts all three, and it was on the box
the whole time.** 492 log lines for `to=<…@comcast.net>`, of which 468 are
`status=deferred` and 24 are `status=sent`:

```
Aug 18 20:44:52  delay=340600  status=deferred (… 554 … #BL000100)   <- last refusal
Aug 18 20:54:52  delay=294206  status=sent (250 2.0.0 … mail accepted for delivery)
…
Aug 18 21:54:52  delay=365674  status=sent (250 2.0.0 … mail accepted for delivery)
Aug 19 19:53:36  delay=2.6     status=sent (250 2.0.0 … mail accepted for delivery)
```

**1. The block lifted inside a ten-minute window on 2026-08-18** — last `554` at
20:44:52 CDT, first `250` at 20:54:52 CDT — **not on the 19th.** The `220`
greeting recorded above was taken the following day and merely observed a state
that had already changed roughly 22 hours earlier. Removal was requested on the
18th and took effect the same evening.

**2. All 23 queued messages were delivered, not expired.** They went out between
20:54:52 and 21:54:52 CDT as the queue runs walked them, carrying delays from
`96840` (1.12 days) to `424510` (**4.91 days**). Against Postfix's 5-day default
`maximal_queue_lifetime` of 432000s, the oldest cleared with **7490 seconds —
2.1 hours — of margin.** It is the same message the section above clocked at
`delay=416092`, two hours and twenty minutes earlier.

So *"no removal request could complete inside the remaining hours. It could not
and did not"* is exactly wrong: it could, and it did, by about two hours. And
since nothing expired, nothing returned to `no_reply@` and there were no locally
dying bounces — that whole sentence describes an event that never happened.

**3. Delivery to `comcast.net` is now observed far past the greeting.** Twenty-three
`250 … mail accepted for delivery` responses are Comcast's MX accepting the
messages after `RCPT TO` and `DATA`, not just answering the connection. The
standard this project holds — inbox placement, as with Gmail and the Outlook
`dest:I` — is **still not met**, because spam-foldering remains downstream and
invisible from here. But "no delivery to a `comcast.net` mailbox has been
observed" understates what is now in the log by a wide margin.

**On causation, tightened.** The request went in on 2026-08-18 and the block
lifted the evening of 2026-08-18. The window is hours rather than a day, which
fits the request better than it fits a feed refresh — still not proof, for the
reason already given: Validity never disclosed listing status.

*The process failure, stated plainly.* The queue outcome was **inferred** from a
decision and a deadline, then written as an observation, and it sat in this
document for two days one command away from being checked. The delisting date was
taken from the instrument that happened to be run rather than from the log that
recorded the event. Both are the same failure this document keeps recording. See
[[measure-before-recording-in-planning-docs]] and
[[suspect-the-measurer-before-the-record]].

**What it is worth, kept in proportion.** `comcast.net` members can receive
notifications again from the old box between now and cutover. That is real and
bounded: this IP's reputation dies with the box, and after cutover member mail
leaves from Postmark's addresses, where none of this follows it.

*Only 2 of Comcast's 8 MX hosts were checked — but they are the same 2 that
returned `554`, which is what makes this a comparison rather than a sample.*

### Task 10 requirement 4 — the HELO SPF record, published 2026-08-20

```
mail.surfguitar101.com.  TXT  "v=spf1 ip4:173.255.245.115 -all"
```

Published by hand in Cloudflare. **Task 10 requirement 4 and task 03 requirement
13 are the same record** — flagged as overlapping when task 10 was written, with
the instruction to do it once. Published once; both close.

**Verified at both authoritative nameservers**, `ada` and `cash`, with `1.1.1.1`
and `8.8.8.8` already carrying it. **Exactly one SPF record at the name** — two
would make the result `permerror` rather than something stricter, so the count
was taken rather than assumed. The `mail.` A record still answers
`173.255.245.115` and is still unproxied; a proxied answer would return
Cloudflare addresses and break the forward-confirmation the whole HELO chain
rests on. Apex untouched.

**Self-consistent:** the record authorizes `173.255.245.115` and the HELO name
resolves to exactly that, so a bounce from jaguar now has something to pass on.

**`-all` is correct at this name precisely where it would not be at the apex.**
The only sender that ever HELOs as `mail.surfguitar101.com` is jaguar, at that
one address. There is no third party to hard-fail — which is what lets this name
be strict while the apex cannot be until Postmark is named in it.

**Why this is the *only* route to an aligned pass for the bounce class**, not the
better of two. A null-sender bounce has no envelope domain, so SPF falls back to
the HELO identity (RFC 7208 §2.3); and it has no DKIM either, because Postfix
does not apply milters to internally generated bounces
(`internal_mail_filter_classes` is empty by default). With no TXT at the HELO
name the result was `none` — never `pass` — from both mechanisms at once.

**It yields an *aligned* pass only because `aspf` defaults to relaxed.**
`mail.surfguitar101.com` and `surfguitar101.com` share an organizational domain,
which relaxed alignment accepts, and the `_dmarc` record sets no `aspf` tag, so
the default holds. **Consequence for step 9: `p=none` → `quarantine` → `reject`
is safe, but adding `aspf=s` alongside it is not** — strict alignment demands an
exact domain match, `mail.` is not the apex, and this bounce class would return
to failing under a policy that now acts on it. Recorded because `aspf=s` is an
easy thing to reach for while "tightening."

**Observed the same evening, not merely reasoned:** the test above returned
`dmarc=pass ... header.from=surfguitar101.com` while SPF authenticated
`mail.surfguitar101.com`. Relaxed alignment accepted the pair. That is the exact
pairing `aspf=s` would reject.

**DELIVERY-VERIFIED THE SAME EVENING**, which was not expected — the plan was to
wait for the report covering 08-21, read on 08-22. Instead a null-sender message
was sent deliberately and its headers read at Gmail:

```
Return-Path: <>
Received-SPF: pass (google.com: domain of postmaster@mail.surfguitar101.com
              designates 173.255.245.115 as permitted sender)
spf=pass ... smtp.helo=mail.surfguitar101.com
dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=surfguitar101.com
```

**`Return-Path: <>` makes it the real failing class, not an easier case.**
Gmail fell back to the HELO identity exactly as RFC 7208 §2.3 describes, looked
up `postmaster@mail.surfguitar101.com`, and found the record. **Task 10
requirement 4's acceptance criterion — "SPF passes on the HELO identity and DMARC
reports an aligned pass" — is met at the receiver.**

**`dkim=pass` as well**, since opendkim signs submitted mail, so this does not
prove SPF *sufficient alone*. The claim under test was narrower: that the record
resolves and matches for that identity, which `Authentication-Results` reports
independently of DKIM. Real DSNs carry no signature and now have an SPF pass
available where they previously had nothing.

*Two false starts worth keeping.* The first attempt used
`sendmail -f ''` with **no `From:` header**, so Postfix supplied a bare
`From: MAILER-DAEMON`; opendkim logged `can't parse From: header value` and Gmail
rejected with `5.7.1` for RFC 5322 non-compliance — **the message never reached
an authentication check.** And *acceptance itself was never the discriminator*,
because DKIM alone would have carried it; the header had to be read. **The
message landed in spam**, which is unremarkable and not an auth signal: it had no
`To:` header at all, a one-line body, and a test subject. Placement belongs to
task 07.

**Its lifetime is the old host's.** Once inbound moves to Cloudflare Email
Routing and the new VM keeps no local bounce traffic, the record retires with the
box that needed it.

### Gmail rate-limits jaguar with `421-4.7.28` — found 2026-08-21, two episodes a month apart

The 9h25m52s the correction above refers to. One message, twelve delivery
attempts, every one refused at end of DATA:

```
421-4.7.28 Gmail has detected an unusual rate of unsolicited mail.
           ... mail has been temporarily rate limited.
```

| attempt | 05:43:19 | 05:49 | 05:59 | 06:19 | 06:59 | 08:09 | 09:19 | 10:29 | 11:39 | 12:49 | 13:59 | **15:09** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gap | — | 6m | 10m | 20m | 40m | 70m | 70m | 70m | 70m | 70m | 70m | **sent** |

Textbook Postfix backoff — 300s doubling into the 4000s cap, quantized to the
300s queue run. `delay=33952` on the final line matches the two `Received:`
stamps in the delivered copy to the second.

**Not IP-wide.** All 23 `4.7.28` lines in the day's log belong to this one
message — eleven attempts × two lines each, plus the twelfth attempt's primary-MX
refusal before `alt1` accepted. No member address was touched, and no other
Gmail-bound message that day carried the code.

**Not caused by the authentication work.** Across the rotated logs the code
appears on **Jul 21 (20 lines)** and **Aug 21 (23 lines)** with three empty logs
between — a month of silence spanning the PTR repair (08-17), the DKIM key, the
sender rewrite and the HELO SPF record (08-20). The hypothesis that our own fixes
provoked it is refuted before it cost anything.

**Jul 21, for the record and no more than that.** Three messages throttled: two
to a member (`admin@` → a Gmail address, delivered after **2h27m54s** and
**37m04s**) and one admin notification (**19m20s**). All three delivered, nothing
expired. That member joined **2026-07-14**, a week earlier, so nothing was near a
registration deadline. **The class of those messages is unidentified** — Postfix
logs no subjects, `admin@` is `DEFAULT_FROM_EMAIL`, and `no_reply@` is
`GPP_NO_REPLY_EMAIL@site.domain`. Two checks are left deliberately unrun, the
stakes having evaporated: `grep 'Forgotten username email sent' logs/auth.log`,
and prod forum posts at 12:58:02 / 14:43:52 that day (topic-reply notifications
go out inline at post time, `forums/latest.py:125`).

**Why it matters little, and is recorded anyway.** Postmark replaces the sending
path and task 06 takes `admin@` off the box entirely, so this dies with jaguar.
It is here because it is the mechanism behind the correction above, and because
it is the fourth finding in this step that no DMARC report could ever surface —
after root's mail dying locally, outbound TLS being off, and the `5.7.25` PTR
class. One incidental property: **each message carries its own backoff**, so two
mails to the same person can arrive out of order. On Jul 21 the 14:43 message
landed five minutes before the 12:58 one.

#### Two measurement traps, both producing clean-looking wrong answers

Added to the collection that starts with the six traps of 2026-08-20.

| Trap | How it presented |
|---|---|
| **A time-of-day filter on a multi-day syslog file matches every day in it.** `awk` testing `$3` alone over `/var/log/mail.log`, which holds Aug 17 onward | a tidy three-row table — `5 bounced / 11 deferred / 32 sent` — read as "during the 9h25m window." The bounces were Aug 17 and Aug 18; the 32 is meaningless. The filter needs `$1` and `$2` as well |
| **An envelope sender can look unique because a test pins it.** `contact/tests/test_views.py:41` asserts the contact form sends from `no_reply@` | `no_reply@ → admin@` was read as *the contact form*, and a user-facing narrative was built on it. It is `GPP_NO_REPLY_EMAIL@site.domain`, shared by the contact form, four flag/report paths, the spammer sweep and antispam |

The surviving conclusion — that the throttle is message-specific rather than
IP-wide — rests on the `4.7.28` census, which was date-safe, and not on the
broken count.

## PLANNING — Step 16: Postmark chosen, and the DNS audit that changed the diagnosis (2026-08-16)

Provider decision and a live DNS audit. **No code written; two task files
generated.**

### Volume, measured before choosing — the numbers made cost irrelevant

Almost every site email funnels through one wrapper, `core/functions.py:44`
`send_mail()` → a Celery task (`core/tasks.py:13`), so the provider swap is
close to settings-only.

**Corrected 2026-08-16 — there is one exception, and it is the worst one.**
`accounts/urls.py:48-55` wires Django's **stock `PasswordResetView`** with no
`form_class` override, so password reset sends via
`PasswordResetForm.send_mail()` → `EmailMultiAlternatives` directly: **no
wrapper, no Celery, no retry, and synchronous inside the user's request.**
Sub-millisecond against a `localhost` Postfix; a TLS handshake and a network
round trip against Postmark, inside a page load, on the flow a locked-out member
is already frustrated by. Tasks 02 (requirements 10–11) and 09 both amended.
`defer=False` has no non-test callers, so everything else does go through the
wrapper.

**RE-MEASURED 2026-08-17 against the snapshot database, replacing the inferred
figures below.** Brian challenged "~1,000–1,800/month" as too high. He was right,
and the table had a second problem: it was **inferred from posts × subscriber
counts**, exactly as task 09 says, while reading as measured. Window is the 12
months to 2026-07-26 (the snapshot's most recent post).

| Source | Measured |
|---|---|
| Forum **posts** | 4,487/yr |
| Forum topic-reply **notification emails** | **9,819/yr** — ~2.2 recipients per post |
| Registrations | 376/yr (~31/mo) |
| Private messages sent | 419/yr (~35/mo) — upper bound; not all trigger mail |
| Contact, email-a-friend, flag/approval, Django 500s | low hundreds/yr, not separately measured |

**~900/month typical, all sources. Busiest month ~1,675** (Oct 2025: 1,589
notifications). **Mean ~30/day. Peak day 207** in the 12-month window, **233**
over 24 months. 11 days over 100 in 12 months; 35 of 711 active days over 24
months; **none over 300** in either.

Method, reproducible against the snapshot:

```sql
SELECT count(*) FROM forums_post p
JOIN forums_topic_subscribers s
  ON s.topic_id = p.topic_id AND s.user_id <> p.user_id
WHERE p.creation_date >= '2025-07-26';
```

The join mirrors `notify_topic_subscribers()`, which fires on **every** new post
(`forums/latest.py:125`) and excludes the poster.

**The caveat runs in the honest direction.** This applies *today's* subscriber
set to *past* posts. `auto_subscribe()` adds each poster to the topic after they
post, so subscriptions only accumulate — today's set is larger than the historical
one, and 9,819 is more likely an over-count than an under-count.

**What was and was not wrong.** The notification estimate held up well — 10,494
inferred against 9,819 measured — and the two-year day figures were close (239 vs
233 peak; "45 of 694 days over 100" vs 35 of 711). **The error was the summary
line**: "~1,000–1,800/month" was really average-month-to-peak-month presented as
the normal band, and the typical month is ~900. **The decision is unchanged** —
Resend's 100/day cap still breaks on a 207-message day, so the ranking of options
holds. See [[measure-before-recording-in-planning-docs]]; also
[[suspect-the-measurer-before-the-record]], since the first instinct here was to
defend the recorded figure rather than re-derive it.

### DECIDED: Postmark, Basic, $15/mo

Chosen for transactional-only, actively-policed IP pools — the specific thing
that is broken. Basic not Pro: Pro's additions are inbound processing (Cloudflare
Email Routing handles that) and 365-day retention over Basic's 45.

**Rejected, each on a measured ground:**
- **Resend** — free 3,000/mo but **100/day**, which the peak-day figure breaches
  on ~5% of days (**re-measured 2026-08-17: 35 of 711 active days over 24
  months**; the figure was ~6.5% on the inferred data), and the breach lands on a
  registration confirmation. **The rejection stands on the re-measured numbers** —
  a 207-message day still exceeds the cap by 2×.
- **Brevo** — free 300/day would fit, but the free plan stamps a Brevo logo in
  the footer of every message and removing it costs more than Postmark.
- **Amazon SES** — ~$0.15/mo, and genuinely plausible now that Step 15 restored
  working AWS credentials, which softens the original "no AWS" constraint.
  Rejected because it retains bounce/complaint handling and reputation
  monitoring in-house — it trades $180/yr for keeping the headache this step
  exists to remove.

**NOT CONSIDERED, and found by Brian 2026-08-30: Cloudflare Email Service.**
`https://developers.cloudflare.com/email-service/` — transactional sending over
SMTP (`smtps://smtp.mx.cloudflare.net:465`), a REST API, or a Workers binding,
around $5/mo for 3,000 messages against Postmark's $15.

**It was not an oversight in the comparison so much as a stale premise.**
`research/hosting.md` recorded "Cloudflare **Email Routing is inbound forwarding
only**", which was true of Email Routing and is why Cloudflare never entered the
sending shortlist. Whether the sending product existed on 2026-08-16 has not
been established and is not assumed here.

**Two things rule it out for this step, both on the criteria already used:**

1. **Email Sending is in Beta.** This is the site's entire transactional path —
   registration confirmations, password resets, forum notifications — and the
   cutover is the worst moment to put it on a beta.
2. **The daily quota is unstated and ramped**: *"New accounts start with a
   conservative daily quota and scale up over time based on your sending
   behavior, deliverability rates, and account standing."* **That is the exact
   criterion Resend was rejected on** — a 100/day cap against a measured
   207-message peak day, breached on 35 of 711 active days, with the breach
   landing on a registration confirmation. Cloudflare publishes no starting
   number, so unlike Resend it cannot even be checked against the peak-day
   figure before committing. The monthly 3,000 clears ~900/mo typical and
   ~1,675 peak month comfortably; **the monthly number was never the binding
   constraint.**

**A third cost, less obvious:** this step **dropped the graduated warm-up on
2026-08-20, on measurement**, replacing it with a two-week bounce-dashboard
watch. A provider that imposes its own reputation-based ramp reintroduces
precisely what was measured away.

**REVISIT AFTER MODERNIZATION, and the case for it is real.** Consolidating DNS,
inbound routing and outbound sending at one provider is a genuine
simplification, and Cloudflare already holds two of the three — the apex SPF
would lose an `include:` rather than gain one. Same shape as the PaaS revisit
Step 21 defers to its own `/pdd`. **Preconditions for looking again: GA rather
than beta, and a published daily quota that can be checked against the
peak-day figure.** Against ~$120/yr saved, switching now would redo a step whose
acceptance criterion is already met at a Microsoft inbox, with DKIM published,
SPF and DMARC live and monitored across fifteen readings, the backend written
and tested, and the smoke tool built.

### The diagnosis — found, and it is not what either of us assumed

Brian's standing belief was that SPF/DKIM/DMARC were configured but somehow
wrong. My first hypothesis was that nothing was wrong with the records at all
and the cause was pure IP reputation — a lone origin at ~30/day never
accumulating enough sending history for Outlook to trust it. **Both were wrong,
and the real answer came out of auditing the live Postfix config.** Worth
recording that the correct hypothesis was third, and arrived only after
measuring rather than reasoning.

(Microsoft's May 2025 authentication mandate binds senders above 5,000/day and
does not apply here; that much of the reframing held.)

**Every message leaving `173.255.245.115` presents this way:**

| Check | Result |
|---|---|
| Forward-confirmed reverse DNS | **fails** |
| HELO hostname resolves to sender | **fails** |
| DMARC policy published | **absent** |
| DKIM | passes (1024-bit key, `simple/simple`) |
| SPF | passes |

**A fourth failure was claimed here and then disproved — see the correction
below.** The three that remain are enough: a connecting IP whose reverse DNS
does not confirm, greeting under a domain with no mail records, publishing no
policy.

**FCrDNS — the likeliest primary cause.** `PTR` for `173.255.245.115` is
`surfguitar101.com`, which forward-resolves to `104.21.53.213` /
`172.67.218.217` — Cloudflare's proxy. The pair does not match. **It used to.**
Before the apex A record was proxied, `surfguitar101.com` resolved to the Linode
box and confirmed perfectly. Enabling Cloudflare's orange cloud — a *web* change
with no apparent bearing on mail — broke it silently. Nothing logs it, no bounce
names it, and the two events are far enough apart to defeat correlation. That is
why years of re-checking SPF and DKIM syntax found nothing.

**HELO.** `myhostname = jaguar.deathofagremmie.com` resolves to Cloudflare proxy
IPs too, and that domain has no MX and no SPF. Same failure, same cause.

**CORRECTION 2026-08-16 — the DKIM claim was wrong, and a real header killed
it.** This section asserted that `smtpd_milters = inet:localhost:88888` put the
milter on an impossible port (88888 exceeds the 16-bit port space), so Postfix
must be failing open via `milter_default_action = accept` and sending unsigned.
Brian captured a delivered message and it shows `dkim=pass
header.i=@surfguitar101.com header.s=dkim`, with a valid `DKIM-Signature`.
**Signing works.** Likely because Postfix and OpenDKIM both truncate 88888
identically to 23352 and meet there — self-consistently wrong, hence working for
years. Unverified and now irrelevant; the milter is being decommissioned.

*The process failure: the config value was measured, the consequence was
inferred, and the inference went into three documents as a finding. One header
check — cheap, available the whole time — settles it directly. Flagging an
inference as uncertain, which the original text did, is what caught the error;
it is not what should have prevented it.* See
[[measure-before-recording-in-planning-docs]].

**The same header corroborates two findings from the receiving side**, so the
capture was worth more than the correction cost:
- Gmail wrote `Received: from jaguar.deathofagremmie.com ([173.255.245.115])`
  with an **empty parenthetical where the PTR name belongs** — it renders
  `from HELO (ptr [ip])` when reverse DNS confirms. It did not. FCrDNS failure,
  observed.
- `Authentication-Results` has `dkim=` and `spf=` but **no `dmarc=` clause**,
  because there is no policy to evaluate. Missing DMARC, observed.

**And it explains the receiver split.** Gmail accepted this message without
complaint, because Gmail leans on SPF and DKIM and both pass. Microsoft leans far
harder on connecting-IP reputation and reverse DNS — exactly where this server
fails. *Passing at Gmail while failing at Outlook is the expected signature of an
FCrDNS problem, not evidence against one.*

Two lesser defects visible in the same capture, both moot after the move:
`c=simple/simple` canonicalization (strictest; any rewrite in transit breaks the
signature), and `Message-ID: <…@jaguar.deathofagremmie.com>` — the dead domain
leaking into a third header after HELO and PTR.

**"Both moot after the move" is doubtful for the second one — flagged
2026-08-17.** Django stamps its own `Message-ID` from `DNS_NAME` =
`socket.getfqdn()` on the *application* host, so no SMTP-side change touches it —
neither the interim fix nor Postmark. Recorded as a hypothesis, not a finding;
verify against `django/core/mail/message.py`. Cosmetic either way.

**Why this degraded invisibly** is the lesson worth keeping: the FCrDNS break
came from a *web* change, and the missing DMARC removed the one instrument that
would have reported it. Two silent failures, no alarm on either.

**None of it survives the move.** Postmark owns the IP, its PTR, the HELO and the
signing, and aligns DKIM to the domain. The findings are properties of
infrastructure being decommissioned — which is an unusually clean independent
validation of the provider decision. Task 03 carries an *optional* ten-minute
interim fix worth doing only if cutover is more than ~2 weeks out, and an
explicit instruction **not** to repair the milter — that would only start signing
with a weak key on a server being retired.

**The interim fix was TAKEN 2026-08-17** — cutover is well over two weeks out,
with Steps 17–21 still ahead. Unproxied `mail.surfguitar101.com` → Linode IP
(done), PTR set to match (accepted, still propagating at end of session), and
HELO aligned via **`smtp_helo_name`, not `myhostname`** — the latter would have
disturbed local delivery, because `mydestination` holds literals rather than
`$myhostname`. Correction 3 in the execution section above carries the reasoning.
The milter was left alone.

### DNS audit — 2026-08-16, against `ada.ns.cloudflare.com`, not a resolver cache

Brian suspected two conflicting TXT records. **That suspicion was wrong, and what
is actually wrong is worse.**

- **No DMARC record exists at all.** `_dmarc.surfguitar101.com` is empty from the
  authoritative nameserver. Two-thirds of the belief was right: SPF and DKIM are
  both present and syntactically valid. DMARC was never published. **The
  consequence that matters most is not policy but telemetry** — `rua` aggregate
  reports are the only channel that would have told him which receivers were
  rejecting what. Their absence is why this went undiagnosed for years.
- **DKIM is 1024-bit** (decoded via `openssl rsa -pubin -noout -text`). Below
  current norms. ~~Fixes itself on the move — Postmark issues 2048-bit.~~
  **CORRECTED 2026-08-17: Postmark issued a 1024-bit key as well**, measured from
  the key it published. Not a blocker and not implicated in the rejections — see
  Correction 1 in the execution section above.
- **The SPF `a` mechanism now authorizes Cloudflare's shared proxy IPs**
  (`104.21.53.213`, `172.67.218.217`), because the apex is proxied. Inert in
  practice — Cloudflare's HTTP proxy emits no mail — but unintended, and it
  burns one of SPF's ten lookups. `mx` is redundant with the explicit `ip4:` and
  becomes actively wrong once MX moves to Email Routing.
- **Exactly one apex TXT record**, so no `permerror`. The two TXT records Brian
  was thinking of are the apex SPF and `dkim._domainkey` — two names, which is
  correct and required.
- **DNS is already fully on Cloudflare** (NS `ada`/`cash.ns.cloudflare.com`, apex
  A proxied). Step 20's Cloudflare front is partly in place already, and Email
  Routing is one toggle away. `_dc-mx.1431890da307…` → `173.255.245.115` is
  Cloudflare's generated unproxied hostname letting MX reach the Linode origin;
  not a fault. Stale `mail.` A record points at proxy IPs and is unusable as an
  SMTP host. **Both resolved 2026-08-17:** un-proxying `mail.` made it a usable
  SMTP hostname *and* dissolved the generated alias — MX now answers
  `10 mail.surfguitar101.com`. The alias existed because the **MX target** was
  proxied, not the apex; see Correction 2 above.

Current SPF, for the record:
`v=spf1 a mx ip4:173.255.245.115 ip6:2600:3c01::f03c:91ff:fe70:e820/64 -all`

Note the `-all`: it hard-fails, so a wrong record during cutover bounces
registration mail outright rather than degrading. Task 03 softens to `~all` for
the window and restores `-all` after.

### Inbound needs no Postfix — a separate concern from sending

Postmark is send-only. Receiving moves to **Cloudflare Email Routing** (free,
forward-only, 200 verified destinations per account, 25 MiB cap, one pattern per
rule). The Step 21 VM ends with no MX, no inbound port 25, no spam filtering, and
at most a **send-only null client** (`msmtp` or Postfix in satellite mode) so
cron and root mail are not silently discarded. A null client holds no reputation
and needs no MX — worth distinguishing from the mail server being retired.

`no_reply@` must still be a deliverable address, not a black hole; members reply
to notifications regardless of the name.

### From-address inventory (both on `surfguitar101.com`, so one domain verification covers both)

- **`no_reply@`** — `email_admins`/`email_managers` (`core/functions.py:85,95`),
  contact form (`contact/forms.py:73`), PM notification
  (`messages/forms.py:158`), `messages/views.py:408`, email-a-friend
  (`news/views.py:233`).
- **`admin@`** (`DEFAULT_FROM_EMAIL`, `base.py:197`) — forum topic notifications
  (`subscriptions.py:46`), registration confirmation and password reset
  (`accounts/forms.py:211,230,259,268`).

### Two risks logged for the step

- **The notification list is stale and day one will bounce.** Of 668 distinct
  topic subscribers, **231 have not logged in for 8+ years or never have**, and
  191 more are 3–8 years dormant — **63% stale**. Postmark auto-suppresses, but a
  hard-bounce burst on a new account can trigger their review. Warm up
  deliberately: recently-active users first. **— MEASURED AND CUT DOWN
  2026-08-20 (above). The 63% is a headcount where a message count was needed.**
  Dormant subscribers hold dead topics that never generate mail: 83.2% of a
  year's 9,041 notification emails go to members active within the year, and only
  **11.9% to 3+ year dormant accounts, across 35 distinct addresses**. Since
  Postmark suppresses after one hard bounce, the ceiling is 35 bounces a year,
  not a burst. **The staged warm-up is dropped in favour of watching the bounce
  dashboard.**
- **Email config is still hardcoded.** `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_BACKEND`
  are literals in `base.py:214` and `production.py:68`, and `.env.example` has
  **no mail variables at all**. Step 3's 12-factor pass skipped email; this step
  finishes it.

### Task files — nine, generated 2026-08-16 (04 rewritten, 08 and 09 added after Brian's review)

Sequence: **01 → 02 → 09 → 07** are the spine; **03** runs in parallel and
should start first; **08 → 05** is its own chain; **04** is independent; **06**
is inbound and separable. Numbers are not renumbered on insertion — 08 executes
before 05, and 09 after 02.

- `step16/task-09-email-send-logging.code-task.md` — **added 2026-08-16 after
  Brian asked whether per-send logging would be useful.** It would, and this
  step's own planning proves it twice: task 04's deletion rested on judgement
  because usage was unmeasurable, and the volume figures driving the provider
  choice are *inferred* from posts × subscriber counts, not measured. One INFO
  line per message to a dedicated `email.log` — category, subject, recipient,
  From, outcome, **never the body** — following Step 12's `search.log`
  precedent, which also settles the log-the-address question (that file already
  records usernames and IPs). The work is not the logging; it is threading a
  `category` kwarg through fourteen call sites, popping it before
  `EmailMessage(**kwargs)`, tolerating tasks queued without it across a deploy,
  and covering the two paths outside the wrapper. Also deletes the existing
  DEBUG log at `core/functions.py:60`, which dumps the **entire message body**
  and is one settings change away from production.

**Outgoing mail on the new VM is deliberately *not* a Step 16 task** (Brian
asked, 2026-08-16). The app's mail becomes environment config here, but the null
client for cron/system mail, the outbound-port egress check and confirming
nothing listens on 25 are properties of a host that does not exist yet.
Recorded in `plan.md` under **Step 21**, which provisions the VM.

- `step16/task-01-email-settings-to-env.code-task.md` — finishes the 12-factor
  work Step 3 skipped. Every email setting is a hardcoded literal and
  `.env.example` has **no mail variables at all**. Behaviour-preserving: current
  values become the defaults. **One real defect found: `SERVER_EMAIL` is unset**,
  so Django's `AdminEmailHandler` (`production.py:139,155` — a *different* path
  from `core.functions.email_admins`) sends error mail from `root@localhost`.
  Postfix accepted that; **Postmark will reject it**, so the first thing to break
  after cutover would be error reporting.
- `step16/task-02-postmark-backend.code-task.md` — SMTP, not the API, and not
  `django-anymail`: task 01 makes the swap environment-only, and webhooks are a
  feature this scope excludes. **The substance is not the settings change.**
  `core/tasks.py:11-21` has no retry, no backoff, no timeout — because
  `msg.send()` to a `localhost` Postfix could not realistically fail, and Postfix
  owned queueing and days of retries. **Pointing `EMAIL_HOST` at an external
  service silently deletes that durable queue**, turning a transient blip into a
  lost registration confirmation. `EMAIL_TIMEOUT` defaults to `None`, so a hung
  connection blocks a worker indefinitely. Nothing in the plan caught this,
  because from the app's side it looks like editing a hostname.
- `step16/task-03-dns-email-authentication.code-task.md` — audit findings above
  plus staged remediation. **Start this first**: it contains a mandatory wait for
  a DMARC reporting cycle, making it the long pole. Applied by hand in
  Cloudflare, not by code.
- `step16/task-05-verified-email-change.code-task.md` — the Step 11 REVISIT.
  **This step supplies a second justification the deferral did not have:**
  unverified addresses are now bounces charged to a shared IP pool, and Postmark
  suspends over bounce rates. Duplicate count re-measured 2026-08-16 —
  **13 groups / 26 accounts, unchanged** — and the trap still stands: a naive
  `exclude(pk=…)` locks all 26 out of saving any profile edit forever. Also
  flags **not** copying `PendingUserManager._make_key()`, which builds keys from
  `random.sample` rather than a CSPRNG; new code uses `secrets`.
- `step16/task-07-email-smoke-and-cutover-verification.code-task.md` —
  `tools/email_smoke.py` on the `image_smoke.py --s3` model, opt-in live sends,
  all eight sending paths. **The acceptance criterion for Step 16 is a message
  landing in an Outlook/Hotmail inbox, not a green suite.** Gmail already
  accepts this site's mail with `dkim=pass`/`spf=pass` while Microsoft rejects
  it — so a Gmail-only check would have passed *before* any of this work and
  cannot distinguish success from failure. ~~Also owns the graduated warm-up
  against the 63%-dormant subscriber list, with a stop threshold set in
  advance.~~ **Dropped 2026-08-20 on measurement (above)** — what it owns instead
  is watching Postmark's bounce dashboard for two weeks; the stop threshold idea
  survives, the staged send does not.
- `step16/task-04-remove-email-story.code-task.md` — **rewritten 2026-08-16
  from hardening to deletion, Brian's call**: "I'm perfectly fine with dropping
  it, I don't imagine this gets used at all." `news.views.email_story` is the
  only site path that sends to an **arbitrary external recipient**, with no
  CAPTCHA and no rate limit, carrying `reply_to=request.user.email` — which
  looks trustworthy but is transitively attacker-chooseable via the unverified
  profile-email change task 05 fixes. Harmless on a dedicated IP; not harmless
  on a shared pool, where the provider's answer to abuse is suspension. Deleting
  beats hardening: it removes the surface instead of narrowing it. Full surface
  is view + thanks view + form + 2 URLs + 2 templates + 2 template links + 3
  tests; **866 → 863**. It stays in Step 16 rather than moving to Step 19's
  prune list precisely because of the shared-pool timing. **`contact/forms.py:75`
  is deliberately untouched** — its `recipient_list` is `MANAGERS`, so an
  arbitrary `Reply-To` can only reach Brian's own inbox, the normal
  contact-form pattern.
  *Note the decision rests on judgement, not data: no send log exists, so usage
  was never measurable. Had per-send logging existed, this would have been a
  data question — which is part of why it is now under consideration.*
- `step16/task-08-modern-token-generation.code-task.md` — **added 2026-08-16,
  Brian's call** after `PendingUserManager._make_key()` was flagged as a pattern
  not to propagate. It mints the registration key from `random.sample` (Mersenne
  Twister) mixed with `SECRET_KEY`, a per-process counter and today's date, then
  takes every other character of a SHA-1. **Not an active emergency** — the
  `SECRET_KEY` ingredient carries it — but its security rests on one ingredient
  while appearing to rest on four, which is worse than a short honest token.
  Replaced with `secrets.token_urlsafe(32)` behind a shared helper, plus
  `secrets.compare_digest` at `accounts/views.py:118` and a migration widening
  `PendingUser.key` from 20 to fit 43 chars. Also updates
  `generate_registration_code()`. **Explicitly leaves `wiki/middleware.py`
  alone** — same flawed pattern, but Step 19 deletes the app. **Lands before
  task 05**, which imports the helper rather than writing a second one.

### Inbound aliases inventoried 2026-08-16 → `step16/task-06-inbound-cloudflare-email-routing.code-task.md`

`virtual_alias_domains` holds three domains and 24 entries; **20 are live.**
Checked for the three things that would force a Cloudflare Worker — fan-out to
multiple destinations, a catch-all, alias-to-alias chains — and found **none**.
Every entry is one-to-one, so the migration is plain routing rules.

**The schedule risk is not technical.** The 20 aliases collapse to **six
destinations, five of which are other people's inboxes** (Ivan ×4 across both
domains, Rick ×3, Dane, Todd, Patrick), and Cloudflare will not deliver to a
destination until its owner clicks a verification link. That is the critical
path. Verify everyone *before* touching MX, while Postfix still receives and a
failure costs nothing. Verification is per **account**, not per zone, and
`surfguitar101.com`/`themadeira.net` share the `ada`/`cash` nameservers — so six
verifications serve all twenty aliases.

- **`deathofagremmie.com` drops entirely** — no MX, receives nothing, and it sits
  on a *different* Cloudflare account (`danica`/`ganz`). Two loose ends: it is
  the Postfix HELO identity (see diagnosis above), and `gremmie@` is Brian's
  handle, so dropping the mail is not the same decision as dropping the
  registration.
- **`/etc/aliases` does not migrate.** `root`/`brian`/`www-data` →
  `bgneal@gmail.com` and `postmaster: root` are *local system* aliases for cron
  and package output. Email Routing never sees them; they become the send-only
  null client on the new VM. Confusing the two is how system mail gets silently
  discarded.
- **`no_reply@surfguitar101.com` is absent from the table and there is no
  catch-all**, so Postfix rejects it today — meaning **every member who replies
  to a forum notification, PM alert or contact-form response gets a bounce.**
  Longstanding, not a regression, but bad for exactly the mail that most needs to
  look legitimate. Task 06 adds a rule routing it to Brian's Gmail.
- `recipient_delimiter = +` works today; Email Routing matches literal
  addresses. Test plus-addressing before cutover if it is used.

### Still open

- **No code written yet.** All seven task files exist; execution has not started.
- **Long-pole items to start before any coding**, both gated on other people or
  on elapsed time: publish the DMARC record at `p=none` so aggregate reports
  begin accumulating (task 03), and send the five third-party destination
  verification requests (task 06).
- An **Outlook.com/Hotmail test address** is needed for task 07's acceptance
  criterion and does not exist yet.

## Archive — Steps 1–15 and the original planning record

**Moved to `STATUS-archive-steps-01-15.md` on 2026-08-26.** Steps 1 through 15
are closed, pushed and CI-green; the original 2026-07-04 planning material —
the requirements summary locked in Step 3, the PDD checklist, the seeded
research plan — is closed too. All of it is one file away and nothing was
edited in the move.

Three sections from that span stayed here, because they are pending rather than
finished: the **single-VM host decision** (Step 21), the **ORDER BY collation**
audit (Step 19), and **`tools/pg_snapshot.sh`**, which is in daily use. They
follow below.

## DECISION — the new host is a single VM, not a PaaS (2026-08-15)

**Brian's call**, after the media question forced it. Step 21 had said "late-
binding; recommend single VM on Linode/Lightsail, or Render", and that ambiguity
turned out to be load-bearing: whether `/media` can stay on local disk is
entirely downstream of it, and it changes the size of Steps 15 and 20.

**Three reasons, in the order they matter:**

1. **This project is already a compose stack.** Six services in one
   `docker-compose.yml`, run identically by dev and CI. A VM runs it unchanged; a
   PaaS means decomposing it into a web service, worker, scheduler, managed
   Postgres and managed Key Value — a deployment re-architecture landing at the
   single riskiest moment of the project. Two risks where there should be one.
2. **Render's persistent disks are unusable for user uploads.** From Render's own
   docs: a disk prevents scaling past one instance, **removes zero-downtime
   deploys**, grows but never shrinks, cannot attach to a cron job, and
   **snapshot restore is all-or-nothing** — recovering one deleted photo rolls
   back every upload since. That alone would force media to object storage, i.e.
   the full nine-field migration the VM lets us skip entirely.
3. **Cost, ~4x.** Roughly **$80–115/month** on Render for this stack ($25
   workspace fee before anything runs, $25 web, $7–25 worker, $7 beat, ~$6–20
   Postgres, $10 Key Value, $0.15/GB over 25 GB bandwidth) against **~$24/month**
   for a 4 GB shared-CPU Linode running all of it. Figures from third-party
   pricing trackers on 2026-08-15 — **Render's own pricing page would not render,
   so verify before committing money.**

**A PaaS is explicitly not ruled out.** Brian's framing: revisit it as its own
`/pdd` after the modernization lands. The objection is to doing it *during* the
cutover, not to the idea.

**Knock-on:** Step 20's guidance said "R2 media", which is now wrong twice over —
corrected to media on the VM's disk, with object storage still used for `pg_dump`
backups.

## Step 19 Phase D task 10 — the add-link form takes a bare domain — DONE 2026-09-09, `5ed3a113`, PUSHED

`AddLinkForm.url` is a `forms.URLField`, keeping its `TextInput` widget and
`size`. One line of application code and six tests in a new
`weblinks/tests/test_forms.py`. **Phase D is complete, and with it Step 19.**

### The premise held, checked before it was relied on

The task required verifying rather than assuming that a `CharField` here is not
skipping validation. Exercised directly against the running form, before anything
changed:

| input | valid? | result |
|---|---|---|
| `example.com` | **no** | "Enter a valid URL." |
| `http://example.com/page` | yes | passes through untouched |
| `not a url at all` | no | "Enter a valid URL." |
| `javascript:alert(1)` | no | "Enter a valid URL." |

`ModelForm._post_clean` runs the model `URLField`'s validators, so the bad input
was already refused. **This is a usability fix and closes no hole** — nothing to
stop and report. What changes is only the scheme-less case, which went from
rejected-with-an-unhelpful-message to accepted.

### The task file's `http://` was wrong, and criterion 4 would have failed

**`sg101/settings/base.py:75` sets `FORMS_URLFIELD_ASSUME_HTTPS = True`**, so a
bare domain normalizes to `https://example.com`. The task file said `http://`
throughout, and its acceptance criterion 4 seeded an existing `Link` at
`http://example.com` and expected `example.com` to collide with it. It would not:
`url__iexact` does not bridge the schemes.

**The setting is deliberate, not an accident to correct.** `tools/deprecation_gate.sh`
carries an ignore for the transitional setting's own deprecation warning and says
in as many words that the project opted into https. So the criteria were corrected
in the task file, in place, rather than the setting being changed to match them.
[[measure-before-recording-in-planning-docs]]

### What that costs the task's stated rationale

The task justified testing the duplicate-check side effect by saying a bare
domain would afterwards match an existing `http://example.com`. It will not, and
the corpus makes that the common case:

    Link rows: 571     http:// 475     https:// 94     other 2

**Not a regression** — `example.com` never reached `clean_url` before, because it
failed validation first, so the duplicate check has only ever worked for input
carrying a scheme and still does. But the improvement is smaller than the task
file claimed, and it is worth saying so where the claim lives rather than letting
a later reader infer that bare-domain duplicates are now caught.

Pinned by a test rather than widened: `clean_url` is untouched, and a link stored
as `http://example.com` is *not* matched by a typed `example.com`. Same reasoning
the task file already applied to trailing slashes — deciding what counts as the
same link is a larger question than the url box.

### The rendered page is byte-identical

`URLField` renders `<input type="url">` by default, so the explicit `TextInput`
is what keeps this invisible. The add-link page was rendered through the view as
a logged-in member under both versions of the field and diffed:

    <input type="text" name="url" size="52" required id="id_url">

identical, `size` included.

### Mutation battery, 2026-09-09 — the tests that must NOT fail are the point

Reverting the field to `forms.CharField`:

| Test | Under `CharField` | |
|---|---|---|
| a bare domain is accepted and given a scheme | **FAILS** | "Enter a valid URL." |
| a bare domain reaches the duplicate check | **FAILS** | got "Enter a valid URL." instead of the duplicate message |
| a link stored on another scheme is not a duplicate | **FAILS** | also a bare-domain case |
| gibberish is rejected | passes | `_post_clean` always caught it |
| a `javascript:` url is rejected | passes | same |
| a url that already has a scheme is left alone | passes | unaffected |

**The three passes are the evidence the tests are aimed at this change.** A
battery that reddened everything would mean they were testing URL validation in
general, which was never missing — and the file would then go green again for
reasons having nothing to do with the field.

### One process note, recorded because it cost a run

`git checkout -- weblinks/forms.py` to revert a mutation also reverted the task's
own uncommitted change, and the following full-suite run failed with the three
new tests red. Harmless once seen, and the fix was to re-apply and re-run — but
**reverting a mutation with `git checkout` is only safe when the work it sits on
top of is already committed.** Both earlier tasks got away with it because their
mutations were applied to files they were not themselves editing.

### Verification
- Full suite: **1248 tests, OK** (1242 before; six added).
- Deprecation gate, **a separate run**: **1248 tests, OK** — the gate matters here
  more than usual, since the behaviour depends on a setting that announces its own
  removal at Django 6.0.
- `clean_url` unedited; the only application change is the field's type.

## Step 19 Phase D task 09 — the `ready()` gap was never a coverage gap — DONE 2026-09-09, `fc386c30`, PUSHED

**The three apps already had the tests.** `downloads`, `potd` and `weblinks` each
have a `tests/test_receivers.py` asserting the effects — counts on create, move
and delete, the photo sequence on save and delete — not the fact of a connection.
Run on their own, every one of them **already failed** with `ready()` neutered:
`downloads` 2 failures, `potd` 2, `weblinks` 1.

**What was broken is the suite's ability to see it, and it was one test module.**
`bio/tests/test_receivers.py:15,18,21` imported `downloads.receivers`,
`potd.receivers` and `weblinks.receivers` at module scope. Django's runner imports
every test module before running any test, so those imports executed the
`connect()` calls at the bottom of each receivers module and put back exactly the
wiring a missing `ready()` had failed to establish. Its `tearDown` then reconnected
three of them by hand, unconditionally, a second time.

### The measurement, with a control

Connections registered under each `dispatch_uid`, counted in a fresh process:

| | `post_save` | `post_delete` |
|---|---|---|
| `downloads.ready()` neutered | **0** | **0** |
| ...after `import bio.tests.test_receivers` | 1 | 2 |
| `ready()` intact — control | 1 | 2 |
| ...after the same import — control | 1 | 2 |

**The control is what makes this readable.** The import restores precisely what
`ready()` would have, and every connection carries a `dispatch_uid`, so nothing
doubles up and nothing looks wrong. The masking has no symptom.

**The 2026-08-04 observation is reproduced and stands** — all three apps still go
green under the full suite with `ready()` neutered, confirmed today before
anything was changed. It is the conclusion drawn from it that was wrong, in
`plan.md` and in the task file: "these apps have no coverage" was inferred from
"the suite does not go red", and the second does not imply the first when a test
module can re-arm the subject. [[suspect-the-measurer-before-the-record]]

### Why this mattered more than the missing tests

**Writing what task 09 specified would have produced tests that also pass under
the mutation.** They would then have been "mutation-verified" the only way that
appeared to work — by running the app's own tests, where they fail for the real
reason — and the suite would have stayed exactly as blind as before, now with a
record saying the hole was closed. This is the case `CODEASSIST.md` names: a
mutation that does not reproduce the fault proves nothing.
[[mutation-verify-or-it-is-not-coverage]]

### The fix, and why it restores rather than reconnects

`bio`'s test saves `post_save.receivers` in `setUp` and puts that list back in an
`addCleanup`, instead of importing the three modules and reconnecting by name.
**Restoring what was found puts back nothing when there was nothing** — which is
the whole property. Reconnecting by name asserts a state, and asserting a state
is what established the wiring for every test that ran afterwards.

The four module-scope receiver imports are gone; the model imports stay, because
they are the senders.

### The one real hole underneath it

`downloads`' file deletion, which is among the effects that no re-run recovers —
an orphaned upload just accumulates on disk.

- **`on_download_delete`'s `file.delete(save=False)` was exercised by nothing.**
  The existing test creates a `Download` with no file, so `if download.file:` was
  never true.
- **`on_pending_download_delete`'s was asserted against a `Mock`** assigned after
  the save — `assert_called_with(save=False)` passes whether or not anything
  leaves the disk.

Replaced by `FileDeletionTestCase`, which writes a real file under a temporary
`MEDIA_ROOT`, captures `file.path`, deletes the row and asserts the path is gone.
The `Mock` test was removed rather than kept beside it: the new one subsumes it
and asserts the property the old one only approximated. Net test count +1.

### Mutation battery, 2026-09-09 — run against the FULL suite

Per-app runs were never the right instrument here, which is the point of the fix.

| Mutation | Before the fix | After | Caught by |
|---|---|---|---|
| `downloads.ready()` neutered | OK | **FAILED (3)** | both file tests + the count test |
| `potd.ready()` neutered | OK | **FAILED (2)** | both sequence tests |
| `weblinks.ready()` neutered | OK | **FAILED (1)** | the count test |

Neutering `ready()` drops several connections at once, so each test method fails
at its first assertion and the delete paths are never reached. **Each delete
receiver was therefore dropped on its own**, leaving the rest of `ready()` intact:

| Connection dropped | Caught by |
|---|---|
| `on_download_delete` | `test_the_file_goes_with_the_download`, `test_download_signal_handlers` |
| `on_pending_download_delete` | `test_the_file_goes_with_the_pending_download` |
| `on_photo_delete` | `test_on_photo_delete` |
| `on_link_delete` | `test_signal_handlers` |

Every failure is an assertion about an effect — `True is not false` on a file
still on disk, `'1,2,3' != '1,4,2,3'` on the sequence, `1 != 0` and `1 != 215` on
the counts. No import error, no collection error, nothing failing for an
unrelated reason. All mutations reverted and the files confirmed unmodified.

**`potd` and `weblinks` gained no new tests and are now caught anyway** — which is
the evidence that the leak, not the coverage, was the thing in the way.

### Verification
- Full suite: **1242 tests, OK** (1241 before: two added, the `Mock` test removed).
- Deprecation gate, **a separate run**: **1242 tests, OK**.
- No application code changed; the diff is two test files.
- Real `MEDIA_ROOT` checked after the run: no `downloads/` directory, nothing left
  behind.

**Phase D remaining: task 10 (`weblinks` `URLField`).**

## Step 19 Phase D task 08 — the search-logging test reads settings in a subprocess — DONE 2026-09-09, `8552a922`, PUSHED

`SearchLoggingSettingsTestCase` read `local.LOGGING` and `production.LOGGING` by
importing both modules into the live test process. It now loads each in a
subprocess through `core/tests/test_settings.py`'s existing `_run()`, and asserts
the same two properties about the same two modules.

**Nothing under `sg101/settings/` changed** — `git diff` is two files,
`core/tests/test_settings.py` and `search/tests/test_views.py`. The `LOGGING`
duplication is Step 20's, as split on 2026-09-08.

### The test moved to `core/tests/test_settings.py` rather than importing the helper

Brian's call between three shapes. The deciding argument is where the failures
point: this case fails when `local.py` or `production.py` changes and **never**
when anything in `search/` does. It now sits beside `SettingsImportIsolationTests`,
which guards the same two modules, and needs no cross-app test-module import — a
shape the repo has no precedent for. `search/tests/test_views.py` keeps the three
`assertLogs` tests, which are the ones a search change can break.

`_run()` was not modified. `env_overrides` already overrode
`DJANGO_SETTINGS_MODULE`, exactly as its docstring said.

### The one in-process import that stays, and why the sweep is not empty

Task 08's requirement 1 asked for a suite with **no** in-process settings import.
`SettingsImportIsolationTests` still has one and should: **the import is its
subject**, not a way to read a value out of a module. Deleting it would drop the
guard against Step 13 task 06's defect immediately before Step 20 restructures
both modules — and the hazard is not confined to tests, since `docker.py:23`
reaches `local.py` by `import *` at runtime.

**Its docstring was rewritten because this task made it false.** It claimed "the
suite imports both to read their LOGGING dicts" — the justification for its own
existence, and no longer true as of this change. Left alone it would have been the
next stale claim nobody re-reads.
[[measure-before-recording-in-planning-docs]]

### The subject is the deployment module's own `LOGGING`, and that is mutation-proven

The snippet reads `settings.LOGGING` under `DJANGO_SETTINGS_MODULE=<module>`, so a
`LOGGING = {...}` override later added to `production.py` is what gets read. This
is the property Step 20 needs: when a shared `LOGGING` is extracted, this test is
what stands between "production uses it" and "production quietly stopped."

`search_logging()` asserts the return code is 0, with stderr as the message,
**before** parsing the output — a subprocess that failed to load settings would
otherwise be asserted about vacuously. That single guard covers acceptance
criteria 4 and 5 together: the missing-handler case surfaces as `KeyError:
'search'` and a nonzero exit, not as a passing test.

**Mutation battery, 2026-09-09 — 7 applied, 7 caught, all reverted byte-identical:**

| Mutation | Test that failed | Failed on |
|---|---|---|
| `production` search logger `propagate` → True | `test_search_does_not_reach_the_site_log` | `True is not false` |
| `production` search logger `handlers` → `['file']` | `test_search_does_not_reach_the_site_log` | handlers mismatch |
| `production` search handler `filename` → `sg101.log` | `test_search_gets_its_own_file` | suffix assertion |
| `production` + trailing `LOGGING = {...}`, no search handler | `test_search_gets_its_own_file` | return code, `KeyError: 'search'` |
| `local` search logger `propagate` → True | `test_search_does_not_reach_the_site_log` | `True is not false` |
| `local` search handler `filename` → `sg101.log` | `test_search_gets_its_own_file` | suffix assertion |
| `local` + trailing `LOGGING = {...}`, no search handler | `test_search_does_not_reach_the_site_log` | return code, `KeyError: 'search'` |

**Each failure names the mutated module in its `subTest` label and only that one**
— the other module passed in the same run. That is the check that the battery
reproduced the fault rather than merely producing a red test: a test aimed at a
shared helper instead of the module would have gone green on all four override and
propagate cases. [[mutation-verify-or-it-is-not-coverage]]

### Re-measured rather than trusted

The task's dependency note said production settings had been verified to load
standalone on 2026-08-07 and told the implementer to re-confirm because `base.py`
had changed since. **Re-confirmed 2026-09-09:** both modules load with only
`SECRET_KEY` set and `DOTENV_PATH` pointing at a nonexistent file, and neither
configures logging at settings-load time, so the absent log directory is not a
problem.

### Verification
- Full suite: **1241 tests, OK**, `--settings=sg101.settings.docker_test`.
- Deprecation gate, **a separate run**: **1241 tests, OK**.
- Both moved tests confirmed collected and passing in the full run at
  `--verbosity=2`, along with `SettingsImportIsolationTests`.
- Not browser-tested: the change ships no code, touches no rendered page and no
  deferred work.

**Phase D remaining: task 09 (`ready()` receiver coverage) and task 10 (`weblinks`
`URLField`).** Neither depends on this one.

## Step 19 Phase D — task files generated, and two figures in the plan were stale (2026-09-08)

**Phases 0, A, B and C are all closed and pushed.** Phase D is the last of the
step. Three task files generated into
`.agents/tasks/2026-07-04-modernizing-sg101/step19/`:

| Task | What it is | Complexity |
|---|---|---|
| `task-08-settings-test-isolation` | The search-logging test off in-process settings imports and onto the existing subprocess helper | Low |
| `task-09-receiver-coverage-for-ready` | Tests that fail when `ready()` stops running in `downloads`, `potd` and `weblinks` | Medium |
| `task-10-weblinks-url-field` | `AddLinkForm.url` `CharField` → `URLField` | Low |

**No ordering constraint left.** 09 before 10 still reads nicer — the `weblinks`
form change then lands on an app whose signal wiring is finally under test — but
nothing depends on anything.

### The settings item split, and `local.py` is not what its name says

**Brian asked whether the `LOGGING` extraction was worth doing**, saying some
duplication is acceptable to him and that since Docker he has had no need to run
the site outside a container. Measuring that turned up something the plan item
never accounted for.

**`local.py` is not a bare-metal-only module — `docker.py` inherits from it.**
`sg101/settings/docker.py:23` is `from sg101.settings.local import *`, overriding
exactly three things: the database over TCP rather than a unix socket, Redis and
the Celery broker for the same reason, and making the debug toolbar visible behind
Docker's NAT. **So the dev container's settings *are* `local.py`**, reached through
a shim, under a name describing a workflow that no longer happens. `manage.py:5`
and `sg101/celery.py:11` still default to `sg101.settings.local`, whose MySQL DSN
names a unix socket on a box nobody runs — the default settings module is one
nothing can actually use.

**That makes the real target a dev/prod consolidation, not a de-duplication**, and
`docker.py`'s own docstring already says the dev/prod split lands "at the deploy
step". So the item split:

| Half | Where it went | Why |
|---|---|---|
| Extract `LOGGING` into `logging_config.py` | **Step 20**, with the `local`/`docker` merge and the `manage.py`/`celery.py` default | Extracting now is work Step 20 may redo once it decides what the two configs even are |
| Move the search-logging test onto the subprocess helper | **Phase D, task 08** | Stands on its own, is small, and is the isolation the item was really about |
| Keep task 06's copy fix in `local.py` | Standing constraint | Not a task; nothing in Phase D or Step 20 may undo it |

**This reverses one of the plan's own ordering constraints** — *"the settings
extraction before Step 20, which will touch settings anyway."* That rationale cuts
both ways, and the reversal is deliberate rather than an oversight; both `plan.md`
entries now say so.

**The test half gets *more* important by being separated, not less.** Step 20 will
extract a shared `LOGGING`, and at that moment `search/tests/test_views.py` is the
only thing standing between "production uses the shared config" and "production has
quietly stopped using it" — provided its assertions stay aimed at
`production.LOGGING` rather than at the helper. Task 08 lands that test correctly
aimed before the extraction exists to aim it wrongly at.

### The linter/formatter is OUT OF SCOPE — decided 2026-09-08

Brian's call, and the measurement supports it more than the plan did. **The repo
has no formatter or linter config of any kind** — no `pyproject.toml`,
`setup.cfg`, `.flake8`, `.editorconfig`, no pre-commit — and `ci.yml` has no lint
step, so nothing enforces a style or waits on one. **And the inconsistency it
would fix is small**: across 400 non-migration `.py` files, 118 lines start at
3-space indent against 7,683 at 4-space. It would rewrite overwhelmingly
conforming code to normalize ~1.5% of it.

**The cost is `git blame` and `git bisect` continuity, and Steps 20 and 21 are
exactly when both are load bearing.** Paying that before the riskiest step of the
project, for something with no deadline, is the wrong order. Revisit after cutover
if ever; `ruff format` is the tool, and one isolated commit listed in
`.git-blame-ignore-revs` keeps the blame damage recoverable, so deferring does not
compound. Recorded in `plan.md` rather than left as an open question.

### Two corrections to `plan.md`, both found by measuring before writing the tasks

**The settings item's figures were stale.** It said the two `LOGGING` dicts were
"~95 lines" differing "in exactly six places". Measured 2026-09-08 they are
`local.py:71–214` (144 lines) and `production.py:92–239` (148), differing in
**eight** behavioural places. The two the old count missed are the `email` and
`turnstile` handler levels, **added by Step 16 task 09 and Step 17 after that item
was written on 2026-08-07** — the count drifted because the thing it counted kept
growing, which argues for the extraction rather than against it.
[[measure-before-recording-in-planning-docs]]

**The `ready()` gap's provenance was wrong.** The plan said "measured during the
Django 5.0 rung"; it was the **Django 4.1 rung** — Step 13 task 04, 2026-08-04,
which mutation-tested all eight apps carrying a `default_app_config` removal and
found five caught and three not. The table is in
`STATUS-archive-steps-01-15.md` § "Step 13 task 04". `wiki` was one of the five
and has since been pruned in Phase B; the three uncaught apps remain.

**Neither correction changes any decision** — task 08 and task 09 are the same
work either way. They are recorded because a task file generated from a stale
figure would have carried it into the implementation, and the first thing both
tasks now require is re-measuring rather than trusting the numbers above.

## FINDING — re-rendering stored markup changes 3,877 rows, and a third of that is Markdown getting it right — measured 2026-09-07, DECIDED 2026-09-08: leave it

**Not a task and not a bug report — a measured condition, now decided.**
Found while building Step 19 Phase C task 07, which had to know whether a bulk
`Story.save()` was safe. It is not, and the reason turned out to be archive-wide.

**Nothing here is live.** Production still runs Python 2.7 and
`Markdown==2.6.11`; the new rendering exists only in dev and CI. **This begins
mattering the day Step 21 flips DNS**, and only for rows somebody edits after
that.

### What changed in Markdown

Six models store HTML rendered from user markup and **re-render it on `save()`**,
so every row is one edit away from being rewritten by the current Markdown.
Between 2.6.11 and 3.10.3 two CommonMark conformance rules landed:

- An emphasis delimiter may not have whitespace on the inside, so
  `*** text ***` is no longer bold-italic — the asterisks stay literal.
- Underscores inside a word no longer open emphasis, so `kick_the_reverb`
  survives as typed instead of rendering as `kick<em>the</em>reverb_`.

**The first is a regression for this archive** — authors meant emphasis and the
site has shown emphasis for years. **The second is a fix**, and it repairs
mangled usernames.

### Measured 2026-09-07 across all 492,661 rows carrying markup

Every row rendered and compared, not sampled. Roughly twenty minutes of work,
which is why it is written down.

| model | rows | identical | markup only | **visible text differs** |
|---|---|---|---|---|
| `forums.Post.body` | 462,446 | 242,533 | 216,109 | **3,804** |
| `messages.Message.message` | 17,147 | 10,883 | 6,230 | **34** |
| `comments.Comment.comment` | 10,982 | 7,768 | 3,205 | **9** |
| `gcalendar.Event.description` | 1,366 | 599 | 754 | **13** |
| `news.Story` (both fields) | 720 | 185 | 518 | **17** |

**"Markup only" is the largest column and it is inert**: 226,826 rows differ
solely because `<img>` attributes come out in a different order. Harmless to a
reader, but it means an edit rewrites the row.

### The headline number is misleading, and that is the point of recording it

Of the 3,877 rows whose visible text would change:

| | rows |
|---|---|
| **emphasis lost — marks become literal** (the regression) | **≈1,219** |
| underscores restored inside a word (a **fix**) | ≈326 |
| emphasis gained | ≈195 |
| unclassified | ≈2,137 |

**The unclassified bucket is mostly more of the underscore case.** A
count-of-emphasis-tags classifier could not see it, because the emphasis moved
rather than disappeared; sampling eight of them found seven were
`kickthe_reverb_` becoming `kick_the_reverb` and one was a stray `</rant>` being
stripped. **"3,804 posts would change" is true and would mislead anyone who read
it alone**, which is why the classification is here beside it.

### How often this would actually fire, from production data

| measure | value |
|---|---|
| forum posts ever edited | **38,538 of 463,219 — 8.3%** |
| edits per year, recent | ~750–1,900 |
| posts over 3 years old edited in the last 3 years | 1,226 |
| posts that would lose emphasis | 1,177, or **0.26%** |

At roughly a thousand edits a year meeting affected posts at the base rate,
**on the order of two or three posts a year** would visibly gain asterisks after
cutover — each only when a member happens to re-save one.

### The decision — Brian, 2026-09-08: option 1, leave it

1. **Leave it**, and fix a post if anyone ever reports one. The expected rate is
   two or three a year and the fix is to delete two spaces. ✅ **CHOSEN.**
2. **Repair the ~1,219 sources** so a re-render is stable — mechanical, and
   verifiable by re-running this measurement to zero.
3. **Pin the pre-3.3 emphasis behaviour** in `core/markup.py`, which keeps the
   archive frozen but also keeps the username mangling.

**Recommendation was option 1 and Brian took it**, on the reasoning it was
offered with: the rate is low, the damage is cosmetic and self-evident when seen,
and options 2 and 3 both spend real effort to prevent something that has never yet
happened to anybody.

**Nothing is scheduled by this decision** — no Phase D task, no cutover-runbook
item, no code change. That is the whole content of "leave it", and it is recorded
here so the question is not reopened from the headline number alone. **What would
reopen it** is a rate materially above the measured base — several reports in a
year rather than the predicted two or three — at which point option 2 is the one
to take, because it is mechanical and this measurement re-runs as its own
verification.

**Related, and the reason this was found:** `news/retag.py` documents why the tag
commands use `bulk_update` rather than `save()`. Any future bulk operation over
these models faces the same question, and the answer is the same.

## Step 19 Phase C task 07 — `rename_tag` and `merge_tags`, BUILT 2026-09-07, `60826bd9` + `ade1e047`, PUSHED

Two management commands, and **new capability rather than restored capability.**
The admin form these replace half-worked: it renamed the shared tag row while
each story kept its own copy of the old string, so the next save of any affected
story quietly put the old tag back and split the set across two tag pages.
Merging was impossible outright — the tag name was a unique column, so renaming
one onto another raised an `IntegrityError`. Measurement and detail in
§ "Step 19 Phase C task 04", finding 5.

**The pair is exhaustive on purpose:** `rename_tag` refuses when the target
already exists, `merge_tags` refuses when it does not, so for any two tags
exactly one of them is the right command and neither can silently become the
other. Each refusal names the other command.

### What decided the implementation: these must not call `Story.save()`

`StoryBase.save()` re-renders `short_text` from `short_markup` whenever
`version >= 2`. Measured 2026-09-07 across all 706 such stories, read-only:

| re-rendering the stored HTML | stories |
|---|---|
| identical | 182 |
| differs **only** by attribute order (`src`/`alt` swapped) | 510 |
| **differs in visible text** | **14** |

The 14 are the Markdown 3.3 emphasis conformance change Step 13 task 08
recorded — `**bold **` with a trailing space becomes literal — so a bulk save
would put visible `*` and `***` onto the live site. **Step 13's own note that
"stored HTML means it only surfaces when a post is edited" is the trap**: a tag
rename would count as editing 567 stories at once.

**The first measurement of this was 74% and looked alarming**; normalising
attribute order before comparing is what separated 510 cosmetic differences from
14 real ones. The alarming number was true and useless.

Also found: `save()` sets `short_text = ''` and restores it only
`if self.short_markup`. **0 stories** currently have `version >= 2` with empty
markup, so nothing would be lost today — recorded because the guard is one
data-entry accident from mattering.

So the commands use `bulk_update`, which writes named columns and fires no
signals — and then do by hand the two things `save()` would have done.

**`update_date` is moved deliberately, and it is not cosmetic.**
`search/reconcile.py` finds a stale index row by comparing `update_date` against
`indexed_at`. A tag change that left `update_date` alone would be **invisible to
the one sweep that exists to catch a reindex that did not happen** — which is not
hypothetical, since today's worker was silently dropping every
`reindex_document` (cutover-runbook C4a).

**The reindex is queued explicitly**, reusing `search.receivers.queue()` rather
than reimplementing the `transaction.on_commit` dance. **Only `Story` is
queued**: `search/documents.py` registers no document for `PendingStory`, so a
pending submission is not searchable, though both models still get their tags
updated.

### Verification

- **Suite 1,241** and the **deprecation gate 1,241**, two separate runs (from
  1,222, so 19 new). `check` clean, `makemigrations --check` clean.
- **Mutation battery: 12 behaviours, 12 caught**, every file restored
  byte-identical — including that going through `save()` rewrites the body, that
  dropping the `update_date` bump hides the change from reconcile, that nothing
  queues the reindex without the explicit call, and that removing
  `transaction.atomic` leaves half a rename applied.
- **Exercised against the converted production database, then restored from a
  snapshot taken first.** `rename_tag video clips` moved 57 stories; the **real
  Celery worker** logged 57 `reindex_document ... succeeded` and 0 failures, and
  `update_date > indexed_at` returned **0 stale rows** afterwards — the bump and
  the reindex agree.
- **The merge was exercised on the case that matters.** `merge_tags clips
  release` on 57 stories, **11 of which already carried `release`**: the count
  went 567 -> 613 (567 + 57 - 11), **no story anywhere ended with a duplicate
  tag**, and story 855 kept `release` in its original position rather than at the
  end — `{2013,mullet-monster-mafia,release,clips}` became
  `{2013,mullet-monster-mafia,release}`.
- **`--dry-run` verified against real data**: reported the 57 and left
  `video=57 clips=0` untouched.
- **All four refusals read as instructions**, not diagnostics:
  ```
  "release" is already in use, so this would merge the two rather than rename
  one. Use `merge_tags clips release` if that is what you meant.
  No story carries "nosuchtag", so this would rename rather than merge.
  Use `rename_tag clips nosuchtag` if that is what you meant.
  No story carries the tag "nosuchtag".
  A tag cannot contain a space: "two words".
  ```
- Snapshot restored afterwards and the index rebuilt to **516,861 documents**,
  `reconcile_search` clean across all 8 types.

### Not done here

Nothing schedules or automates these; they are run by hand when Brian wants a tag
changed. There is no admin surface for them, which is the deliberate trade
recorded in task 04's decision 1.
## Step 19 Phase C task 06 — the vendored `tagging` app is gone, BUILT 2026-09-07, `01a94a32` + `13ff1097`, PUSHED

The package, its two tables, the `tags_legacy` column task 05 kept as a safety
net, the migration history that named the app, and the content types and
permissions Django had created for its models. **No rendered page changes** — the
site has been reading tags from the array since task 05.

`django-tagging` was vendored in Step 13 task 03 because 0.5.0 imports
`smart_text`, which Django 4.0 removed, and the import failure aborted
`django.setup()`. It has needed hand-fixing on two rungs since. The retirement
has been carried in the plan ever since; this closes it.

### Two things the task file did not list, both found by measuring first

**1. Content types and permissions.** The database held 2 `django_content_type`
rows for `tagging` and **8 `auth_permission` rows** hanging off them, 0 of them
granted to any user or group. Left behind they would have offered
`tagging | tag | Can add tag` in the admin's permission picker forever, naming a
model that no longer exists.

**2. The requirements notes had become false.** Both `requirements.txt` and
`requirements-docker.txt` carried a paragraph explaining that django-tagging "is
vendored into the repo as `tagging/`". Both removed — and both, because
`requirements.txt` already warns at the top that the two files are hand-mirrored.

### The DDL has no cascade, and raw SQL does not get one

The first version of the migration deleted the content types directly and failed:

```
IntegrityError: update or delete on table "django_content_type" violates foreign
key constraint "content_type_id_refs_id_728de91f" on table "auth_permission"
```

**This is the same fact Phase A recorded about `Forum.last_post`:
`on_delete=CASCADE` is enforced by Django's deletion collector in Python and
never reaches the DDL**, so the database's own foreign keys are plain
`NO ACTION`. The ORM would have cascaded; raw SQL in a migration does not. The
migration now deletes `auth_group_permissions`, `auth_user_user_permissions`,
`auth_permission` and `django_content_type` in dependency order.

Nothing holds those permissions today, so the group and user rows delete nothing
— they are there because the migration must not depend on that staying true
between now and the cutover, and one of the mutations below proves the
dependency was real.

### Four of the six tests were vacuous, and only the mutation battery said so

The obvious tests — *a migrated database has no tagging tables, no migration
history, no content types* — **cannot fail.** Once the app leaves
`INSTALLED_APPS`, a fresh database never creates any of it, so those assertions
hold whether the migration does anything at all or nothing. A fifth read
`Story._meta` for `tags_legacy`, which reflects `models.py` — where the field was
removed in the same change — rather than the schema.

All four passed on the first run and all four survived having the migration's
statements deleted. **They were rewritten to build the rows the migration is
supposed to remove and then run it**, which is the only database this migration
will ever meet in production, and to read the column list out of the database
rather than out of the model.

**This is the rule earning its keep twice in two tasks.** Task 05's version was a
mutation that reproduced no fault; this one was four tests that could not fail.
Both looked green.

### Two findings from Brian's browser session, one of them a cutover hazard

**1. Celery does not autoreload, and a stale worker fails silently.** Brian found
a traceback in the worker log: every `search.tasks.reindex_document` for a news
story raising `AttributeError: 'list' object has no attribute 'lower'` from
`/app/tagging/fields.py:75` — **a file that no longer existed on disk.** The web
container had picked up the new code because `runserver` autoreloads; the worker
had been up 18 hours and was still holding the deleted module, so its cached
`TagField` descriptor kept calling `.lower()` on what is now a list.

Not a defect in this change — `--force-recreate worker beat` cleared it and the
same save reindexed cleanly — **but a real cutover hazard, and worse there than
a traceback.** A story saved after the flip would simply not reach the search
index, and `reconcile_search` would report it as drift days later rather than as
a deploy fault. Nothing in the site's own output says a word about it. **Added to
`cutover-runbook.md` as C4a**, which had no worker item at all.

**2. `/news/tag/Thalasses/` served the page rather than redirecting.** Correct as
designed — every case variant resolves to the same lowercase tag, as
`name__iexact` did before — but it meant one page had many URLs, each rendering a
heading echoing whatever casing was typed: *Stories with tag: "Thalasses"*. Two
addresses for one page, and a title naming a spelling no tag has.

**Now a 301 to the canonical URL, on Brian's call**, with the query string
carried so a visitor on page 4 of a paginated tag stays on page 4. A mixed-case
unknown tag redirects and then 404s. Permanent rather than temporary, because the
lowercase URL is the only correct address and always will be — the model
lowercases on save.

### Verification

- **Suite 1,220** and the **deprecation gate 1,220**, two separate runs.
  1,210 - 3 (`test_tag_queries.py`, whose subject no longer exists) + 13 new.
  `check` clean, `makemigrations --check` clean.
- **Mutation battery: 11 behaviours, 11 caught**, every file restored
  byte-identical — including that a granted permission blocks the content-type
  delete without the manual cascade, and **that task 05's `0001_initial` fix is
  load-bearing**: restoring `import tagging.fields` to that migration makes
  `migrate` from zero die with
  `ModuleNotFoundError: No module named 'tagging.fields'` before it applies
  anything.
- **Migrate from zero** on a scratch database with the package deleted: clean,
  `news_story.tags` is `_varchar`, both GIN indexes present, no `tags_legacy`, no
  tagging content types. **This is the check the whole task exists to protect**,
  because Step 21 migrates a freshly converted snapshot.
- **On the dev database:** 0 tagging tables, 0 `tags_legacy` columns, 0
  `django_migrations` rows, 0 content types, **0 orphaned permissions**, and the
  tags themselves untouched at 1,208 stories / 3,931 pairs.
- **The reverse refuses rather than pretending**: reversing raises
  `RuntimeError` naming the snapshot and `news.0010` as the two real recovery
  paths, instead of recreating two empty tables that would look like a restore.
- **Browser**: the cloud still renders 1,001 tag links, story 1539 its 3, and the
  colophon's library list reads `PIL, pytz, django-elsewhere,
  gdata-python-client` — no stray comma where the entry came out.
  `/news/tag/Thalasses/` 301s to `/news/tag/thalasses/`,
  `/news/tag/RELEASE/?page=3` keeps its page, `/news/tag/asdf/` 404s.

### Found, out of scope, and worth its own change

**The colophon is stale well beyond django-tagging, and it is a live page.** It
still credits **pytz** (removed in Step 13 task 09), **python-memcached**
(dropped in Step 13 task 05 when memcached became Redis), **Haystack** and
**xapian-haystack** (removed in Steps 4 and 12), **MySQLdb** (the site runs on
PostgreSQL; `mysqlclient` survives only for conversion tooling), **html5lib** and
**Blueprint**.

Its next paragraph is worse, because it is present tense: the site "runs on" an
**Apache server** with **mod_wsgi**, a **MySQL database**, the **Xapian** search
engine and **memcached** — four claims, none of them true today, and Step 21
changes the first two again. **A rewrite wants to wait for Step 21**, since the
host and the web server are decided there.

## Step 19 Phase C task 05 — news tags are a PostgreSQL `ArrayField`, BUILT 2026-09-07, `7064614b` + `7fc3c37c`, PUSHED

Task 04's decision, implemented. The vendored `tagging` app is still installed
and both its tables are still populated: that is what the equivalence check
below runs against, and task 06 is what removes them.

**Two decisions Brian took before any code was written:**

1. **Rename the old column rather than drop it.** `tags` -> `tags_legacy`, a
   plain `CharField` so the `TagField` descriptor and its `post_save` hook stop
   firing, and the array arrives under the real name. PostgreSQL cannot cast
   `varchar` to `varchar[]`, so something had to give; this way the only copy of
   what an author actually typed survives all of task 05, and the reverse
   migration is complete rather than dependent on a snapshot. Task 06 drops it.
2. **`news/migrations/0001_initial.py` is fixed here, not in task 06**, so
   migrate-from-zero is verifiable at the end of this task.

### The blocker explore found, which would have fired at cutover

`news/migrations/0001_initial.py` did `import tagging.fields` and declared
`('tags', tagging.fields.TagField(max_length=255, blank=True))` for both models.
**Deleting `tagging/` in task 06 would therefore have made `migrate` from zero
raise `ModuleNotFoundError` before reaching migration 0001** — and the only place
this project migrates from zero is Step 21, converting a fresh production
snapshot on cutover day. Nothing here would have caught it: the dev and CI
databases are already migrated.

`TagField` is a `CharField` subclass whose `__init__` only defaults `max_length`
and `blank`; the descriptor and the signal are runtime behaviour that migration
state never reads. So `models.CharField(max_length=255, blank=True)` is
state-equivalent and emits identical DDL. This is the case Django's own
documentation sanctions for editing a historical migration.

**The same trap a second time, in the new data migration.** The obvious way to
write the backfill is `apps.get_model('tagging', 'TaggedItem')` with a dependency
on `tagging.0003`. Both are stranded the moment task 06 deletes those files — a
`LookupError` and a `NodeNotFoundError`. `0010` therefore addresses the tables by
name in SQL, declares no dependency on that app, and guards on table existence,
which is correct in both directions: from zero the tables are empty or absent and
there is nothing to copy; on the converted production database they exist and are
full.

### Four defects found while building, none of them predicted

**1. `FORCE_LOWERCASE_TAGS` had no replacement, and the gap was invisible.**
`TagField.__set__` lowercased on assignment; an `ArrayField` does not. The tag
page lowercases the name it looks up, so a tag typed `Surf` in the admin would
have been stored capitalised and **had no reachable page** — no error, just a tag
whose link 404s. `StoryBase.save()` now lowercases, which is what keeps the
invariant the collation audit rests on (all 1,001 production tags lowercase, no
case variants).

**2. Django's per-item array validation drops the reason.** The space validator
started on the base `CharField`, which is the obvious place. Through a ModelForm
that produces `Item 1 in the array did not validate:` **and nothing else** — the
`RegexValidator`'s message is lost by the wrapper. Moved onto the `ArrayField`
itself, validating the list as a whole, which also allowed a better message:

```
'surf reverb twang'  ->  Tags cannot contain spaces; separate them with commas.
                         Did you mean "surf, reverb, twang"?
```

**3. A string assigned to the array silently becomes one tag per character.**
`search/tests/test_documents.py:91` passed `tags='surfabilly'`; iterating a
string yields characters, each a valid `CharField` value, so it would have stored
ten single-letter tags rather than raising. The suite caught it immediately —
recorded because the same mistake in application code would not announce itself.

**4. The first query-count tests passed for the wrong reason.** They counted
whole pages, and the pages render a sidebar whose queries are cached in locmem;
whichever test ran first warmed the cache for the rest. `archive` sorts before
`index`, so `archive` saw 9 queries and `index` saw 2 — and the fix that made
both "pass" would have been to write down 9 and 2. They now count queries against
`news_story`, which is what the claim is actually about.

### One deliberate behaviour change

**A tag no story carries now returns 404** where it previously rendered an empty
page with a 200. A `Tag` row could outlive every story using it; there is no row
to outlive anything now. This affects the five tags reachable only through dead
`pendingstory` rows, and nothing links to them — the cloud lists live tags only.

### A prediction from task 04 that measurement disproved

The task 04 record said taking the join table's spelling would mean **"search
stops matching the accented spelling"**. **It does not.** Both stories carry the
accented form in their *title and body*, which are indexed at higher weight than
the tags, so after the reindex `thálasses`/`thalasses` and `poisön`/`poison` all
still match their stories. The accent decision costs nothing in search after all.

### Verification

- **Equivalence against the join table, on production data** — the cloud
  identical across all **1,001 tags** on name, count, font size *and order*; the
  tag pages identical for `release` (567), `video` (57) and `thalasses` (2); and
  **every one of the 1,694 stories agreeing tag for tag**.
- **Suite 1,210** (from 1,181, so 29 new) and the **deprecation gate 1,210**, two
  separate runs. `check` clean, `makemigrations --check` clean.
- **Mutation battery: 12 behaviours, 12 caught**, every file restored
  byte-identical. **The thirteenth attempt was thrown out rather than recorded**:
  changing `attach_extra_attrs`' guard to `if True:` left the test passing,
  because `Comment.objects.filter(object_id__in=[])` is optimised by Django into
  no query at all — the mutation reproduced no fault, so it proved nothing about
  the test. Replaced with one that drops the version filter and does query.
- **Migrate from zero** on a scratch database: applies cleanly, `news_story.tags`
  is `ARRAY/_varchar`, both GIN indexes present.
- **The reverse was run against real data, not just written.** Reversing `0010`
  rebuilt the join table at **3,931 rows, 0 missing, 0 extra** against the live
  rows captured beforehand, with the 630 orphans correctly absent; re-applying
  returned the arrays to 1,208 stories / 3,931 pairs / 1,001 tags.
- **Reindexed to 516,858 documents** in 1:20, `reconcile_search` clean across all
  8 types.
- **Walked in a browser**: the cloud renders 1,001 links with font sizes actually
  varying (876/102/22/1 across the four sizes), `/news/tag/Release/` resolves
  case-insensitively, `/news/tag/nosuchtag/` 404s, story 1539 shows `jay-poison`,
  and the admin box renders `2021,jay-poison,release` with its help text.

### Query counts, measured before and after

| page | before | after |
|---|---|---|
| `/news/tag/<name>/` | 4 | **2** |
| `/news/story/<id>/` | 2 | **1** |
| `/news/date/` | 3 | **2** |
| `/news/archive/<y>/<m>/` | 3 | **2** |
| `/news/tags/` | 1 | 1 |

### Not done here

`tagging/` is still installed, both tables still hold their 4,561 rows,
`news/tests/test_tag_queries.py` still passes against the fork, and
`tags_legacy` still holds every original string. All of that is task 06.

## Step 19 Phase C task 04 — `django-tagging` is replaced by a PostgreSQL `ArrayField`, DECIDED 2026-09-07

The task changed no schema, moved no data and shipped no code: its output is
this record and the numbers under it. The implementation is task 05, which can
now be written because the shape is settled.

**Brian's call on both questions, put to him with the measurements below: the
`ArrayField` wins, and the join table is the migration's source of truth.**

### What was measured, 2026-09-07, on the converted production database

Both read paths, at the ORM level rather than through the templates, because the
templates are the part that does not change. Warm, min of 11 runs. A throwaway
`varchar(50)[]` column on `news_story`, populated from `tagging_taggeditem` and
GIN-indexed, is what the right-hand column measures; it was dropped before the
task closed.

| path | today (join table) | `ArrayField` + GIN |
|---|---|---|
| `/news/tag/release/` (567 stories) | 4 queries, 1.94 ms | **2 queries, 1.04 ms** |
| `/news/tag/video/` (57) | 4 queries, 1.79 ms | **2 queries, 0.82 ms** |
| `/news/tag/thalasses/` (2) | 4 queries, 1.44 ms | **2 queries, 0.67 ms** |
| `/news/tags/`, 1,001 tags incl. `calculate_cloud` | 1 query, 2.41 ms | **1 query, 1.69 ms** |

**The two shapes return identical results** — the same story sets on every tag
page, and a cloud of 1,001 tags with identical counts *and* identical font
sizes. That equivalence is what makes the timings comparable at all.

Whole pages, through the test client with the debug toolbar removed from
`MIDDLEWARE`: `/news/tag/release/` 5.0 ms, `/news/tags/` 13.5 ms. **So the SQL is
a small share of either page** — the cloud's real cost is rendering 1,001 links,
not counting them. Nobody should expect this change to be visible in a browser.

Query surface across the whole app, which is the number that actually moves:

| page | today | `ArrayField` | `taggit` |
|---|---|---|---|
| `/news/date/` | 3 (1 tagging) | **2** | 3 |
| `/news/story/<id>/` | 2 (1 tagging) | **1** | 2 |
| `/news/archive/<y>/<m>/` | 3 (1 tagging) | **2** | 3 |
| `/news/categories/` | 12 (0 tagging) | 12 | 12 |
| `/news/tag/<name>/` | 4 (4 tagging) | **2** | 4 |
| `/news/tags/` | 1 | 1 | 1 |

Storage: the change removes 928 kB (`tagging_taggeditem` 720 kB,
`tagging_tag` 208 kB) and adds a 96 kB GIN index. The migration was rehearsed
end to end inside one transaction and rolled back: **70 ms total** — `ALTER` 0.6 ms,
backfill of 1,694 rows 65.5 ms, `CREATE INDEX` 3.2 ms.

**`django-taggit` is alive** — 6.1.0 is current on PyPI, checked from the
container rather than assumed. It was rejected on shape, not on health.

### The performance argument runs the other way, and the decision does not rest on it

**In raw SQL the join table wins where the two differ.** The common-tag `COUNT`
is 0.26 ms through the join and **0.96 ms** on `tags @> ARRAY['release']`: at
567 of 1,694 rows the tag is 33% selective, so the planner ignores the GIN index
and sequentially scans a 5,568 kB table instead of a 720 kB one. The GIN index
only earns its place at the tail — the rare tag is a 0.023 ms bitmap scan.

The `ArrayField` is faster *at the ORM level* for a different reason: it deletes
two round trips per tag page — the `Tag` lookup and `attach_extra_attrs`' bulk
`TaggedItem` fetch — along with the Python that assembles them. **That is a
structural saving, not a faster query**, and it is worth recording that way
because the raw-SQL number would mislead anyone who re-measures only the `WHERE`
clause later.

### Five findings that were not predicted, and two of them changed the case

**1. 630 of the 4,561 join rows are orphans — 13.8%.** 616 point at
`news_pendingstory` rows that no longer exist and 14 at deleted stories. The
mechanism is in the source: `news/admin.py:85`, `_approve_story`, ends with
`pending_story.delete()`, and django-tagging registers no delete handler, so
every story ever approved left its pending tag rows behind. **The live figures
are 3,931 rows across 1,208 stories and 1,001 tags**, not the 4,561/1,006 the
plan has carried since 2026-08-04. The 1,001 is the same number the Step 14
rungs recorded for the rendered cloud, which is the cross-check that the live
set is the set the site displays.

**This is the argument the measurement produced and taste would not have.** The
`ArrayField` makes the failure mode structurally impossible: tags live on the row
they describe, so deleting the row deletes them. `taggit` keeps
`content_type_id`/`object_id` and a `GenericForeignKey`, so nothing at the
database level stops the next 630 — whatever it does or does not do in Python.

**2. Two models are tagged, not one.** `Story` **and** `PendingStory`, both
inheriting `tags` from `StoryBase` (`news/models.py:49`). The task file's
premise — "this site tags exactly one model" — is wrong, and it was the premise
the whole `ArrayField` case rested on. It survives the correction: two concrete
models in one app is still not what a content-type indirection is for, and each
takes its own array column. But the record should say the case was re-argued
rather than confirmed.

**3. The `tags` column is four characters from its cap.** `TagField` is
`CharField(max_length=255)`; story 635 (2011, *Instro Summit returns to Chapel
Hill*) holds 20 tags in 251 characters. Production's MySQL runs a permissive
`sql_mode`, so a 21st tag would truncate there silently rather than raise. One
story, from 2011, and nobody is editing it — the caveat belongs with the number.
The `ArrayField` removes the cap rather than raising it.

**4. Two stories' tags disagree between the column and the join table.** Story
1539 holds `jay-poisön` in `news_story.tags` while the join table says
`jay-poison`; story 1730 holds `thálasses` against `thalasses`. **Cause: MySQL's
accent-insensitive collation on the `tagging_tag.name` unique index.** In both
cases an ASCII-spelled tag already existed — `jay-poison` from 2020-11-08,
`thalasses` from 2024-06-04 — and `Tag.objects.get_or_create()` matched the later
accented submission to it, so the join table points at the ASCII tag while the
column keeps what the author typed. Four other accented tags (`bárujárn`,
`diabolico-coupè`, `electrohúmedos`, `taner-öngür`) kept their accents precisely
because each has exactly one story and never had an ASCII twin to be folded into.

**The MySQL snapshot was checked before this was written down, and holds exactly
the same bytes** (`tagging_tag.name` = `jay-poison`, `news_story.tags` =
`jay-pois\xc3\xb6n`). The conversion is faithful; this is production data, and it
predates PostgreSQL.

**It is also a latent behaviour change from the engine switch.** PostgreSQL's
`name` index is not accent-insensitive, so re-saving story 1539 today would
create a *second* tag and split the two spellings across two tag pages. Nothing
has re-saved it, so nothing has fired.

**5. The admin's tag rename half-applies, and then erodes.** Found because
Brian asked whether the old system could rename or merge tags at all — the claim
that it could was mine and it was wrong. `tagging/admin.py` registers `Tag`, so
`/admin/tagging/tag/` does offer a rename form. Measured 2026-09-07 in a
rolled-back transaction:

```
BEFORE            /news/tag/video/ -> 57 stories   /news/tag/clips/ -> 0

AFTER THE RENAME  /news/tag/video/ -> 0            /news/tag/clips/ -> 57
   story 634   page shows clips,eliminators    column holds 'eliminators video'
   story 717   page shows chicchi,clips        column holds 'chicchi video'

AFTER STORY 634 IS SAVED (its tags untouched)
   /news/tag/video/ -> 1 story      /news/tag/clips/ -> 56 stories
```

The rename reaches all 57 stories at once, which is why it looks like it works.
But it never touches `news_story.tags`, so every one of those stories still holds
the old string — and `TagField._save` re-runs `update_tags` from that column on
the next save, recreating the old tag and pulling that story back. **A renamed
tag does not revert; it erodes, one story at a time**, splitting the set across
two tag pages with nothing going red. **Merging is not possible at all**:
renaming a tag onto an existing name raises `duplicate key value violates unique
constraint "idx_600078_name"`.

**Exposure, with the caveat attached to the number:** 779 of 1,694 stories (46%)
have been edited after posting at some point, but only **8 in the last two
years** — so the erosion is real, slow, and permanent. It is a live defect in
production today.

**No separate fix.** The `ArrayField` deletes the mechanism: there is no second
copy of the string to go stale. Task 07 supplies a correct rename and merge as
management commands, which is **new capability rather than restored capability** —
a distinction worth keeping, because the first version of this record had it
backwards.

### Decision 1 — a PostgreSQL `ArrayField` with a GIN index

```python
# news/models.py
class StoryBase(models.Model):
    ...
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
```

with `GinIndex(fields=['tags'])` on the concrete models. `tagging_tag`,
`tagging_taggeditem` and the vendored `tagging/` package all go.

The reasons, in the order they weigh:

1. **Referential integrity.** Finding 1, above. This is the one difference
   between the candidates that is about correctness rather than shape.
2. **Half the queries on five of six news pages**, including the story page,
   which drops from 2 to 1.
3. **No dependency at all**, rather than a maintained dependency in place of a
   dead one. The generic machinery exists to tag *any* model; two concrete models
   in one app do not need it.
4. The 255-character cap goes away with it.

**What it gives up, stated plainly:** a tag is no longer an addressable row, so
a tag cannot exist with zero stories — 3 such tags exist today, plus 5 reachable
only through the dead `pendingstory` rows, and none is missed. Renaming or
merging a tag stops being an admin edit and becomes
`UPDATE news_story SET tags = array_replace(tags, 'old', 'new')` — one statement
either way, but it needs a management command rather than a form. And the admin's tag box changes
separator, since `SimpleArrayField` splits on commas where today's `TagField` box
is space-separated.

**Brian's call 2026-09-07, after the task files were generated: no custom form
field for that — help text instead.** The stock `SimpleArrayField` already
renders existing values comma-separated and strips whitespace around the commas,
so the only exposure is habit. **It is a silent exposure, which is why a
validator goes in beside the help text**: measured, typing `surf reverb twang`
*validates* and stores one tag named `surf reverb twang`, which no URL resolves.
A validator rejecting a space cannot reject existing data — 0 of the 1,006 tags
contain one, and no story ever used django-tagging's quoted multi-word syntax.

**The PostgreSQL tie is not a new commitment.** Step 11 moved the engine and Step
12 put `/search/` on native full-text search; this adds nothing that was not
already load-bearing.

### Decision 2 — the join table is the migration's source of truth

For the two stories in finding 4, the migration takes `jay-poison` and
`thalasses`. **The join table is what every page renders today** — the tag page
and the news index through `attach_extra_attrs`, the story page through
`{% tags_for_object %}` — so migrating from it produces no visible change
anywhere on the site. The accented spellings survive only in the admin edit box,
and in `tags_legacy` until task 06.

**The cost this paragraph originally named turned out not to exist.** It said
search would stop matching the accented spelling, since `search/documents.py:256`
indexes the tags. Measured in task 05 after the reindex: both stories carry the
accented form in their *title and body*, which are indexed at higher weight, so
every spelling still finds its story. The accent decision costs nothing at all.

### Decision 3 — the tag-cloud half of the collation audit is released

`tagging_tag` does not survive, so the finding about `tagging_tag.name` has no
table to be about. Recorded in `research/collation-audit.md`, along with finding
4, which is the concrete instance of the same claim and is worth keeping after
the table is gone: **the two folded pairs are the surviving trace of MySQL's
accent-insensitive index, and the ASCII spelling is the one the array keeps.**

### What task 05 has to build

1. `ArrayField` on `StoryBase`, `GinIndex` on `Story` and `PendingStory`.
2. A data migration from `tagging_taggeditem` (content type `news.story` /
   `news.pendingstory`), reversible back into the join table for the live rows;
   the 630 orphans are not recreated by the reverse, and the record should say so.
3. `news/views.py`: the tag page loses its `Tag` lookup and 404s on
   `paginator.count == 0`; `.lower()` on the URL segment reproduces
   `name__iexact` faithfully, since all 1,001 live tags are lowercase with no
   case variants (`FORCE_LOWERCASE_TAGS`, already pinned by a test at
   `news/tests/test_display_views.py:94`). The cloud becomes `unnest` + `GROUP BY`
   feeding the existing `calculate_cloud`.
4. `news/utils.py`: `attach_extra_attrs` loses its tag query entirely.
5. Templates: `story.html:52`'s `{% tags_for_object %}` and
   `story_summary.html:81`'s `story.tag_list` both become `story.tags`; the two
   `{% load tagging_tags %}` lines go.
6. `search/documents.py:256`: `obj.tags` is a list now, so `' '.join(obj.tags)`.
   **A reindex is required** — the two accented stories change in the index.
7. Delete `tagging/` and its `INSTALLED_APPS` entry; drop both tables; port
   `news/tests/test_tag_queries.py` and the tagging tests in
   `test_display_views.py` to the new shape.
8. An admin form field that splits the tag box on whitespace.
9. A `rename_tag` / `merge_tags` management command, since the admin loses it.
10. `sg101/templates/fixed/colophon.html:14` credits django-tagging with a link
    to `code.google.com/p/django-tagging/`, dead for years, on a live page.

### Verification

- Suite **1,181 tests, OK**, and the deprecation gate **1,181, OK** — two
  separate runs, both after the throwaway column was dropped.
- `git status` clean: no model, migration, dependency or template changed.
- The throwaway column is gone (`information_schema.columns` returns 0 rows for
  `news_story.tags_arr`), and `news_story` / `tagging_tag` / `tagging_taggeditem`
  hold 1,694 / 1,006 / 4,561 rows, identical to the pre-task counts.
- Snapshot `sg101-20260907-131203-step19-task04-pre.dump` taken before any write.

### Three task files generated 2026-09-07

`/agent-sops:code-task-generator`, into
`.agents/tasks/2026-07-04-modernizing-sg101/step19/`:

- **`task-05-news-tags-as-an-arrayfield`** — the field, both migrations, every
  read path, the search document, and the admin's comma separator with its
  help text and space validator. **`tagging/` stays installed and its tables stay populated at the end of
  this task**, deliberately: that is what lets the old and new shapes be compared
  on the same 1,208 stories, the same argument that put a populated index before
  the code reading it in Step 12. It also has to carry `calculate_cloud` out of
  `tagging/utils.py:250` into `news/`, or the cloud loses its font sizes one task
  later.
- **`task-06-remove-the-vendored-tagging-app`** — delete the package and its
  `INSTALLED_APPS` entry, drop both tables *and* the `tagging` rows in
  `django_migrations`, delete `news/tests/test_tag_queries.py` (its subject
  ceases to exist), and take django-tagging out of the live colophon. Two admin
  pages go with it, `Tag` and `TaggedItem` — named explicitly there so it is a
  decision rather than a surprise.
- **`task-07-rename-and-merge-tag-commands`** — `rename_tag` and `merge_tags`,
  both models, `--dry-run`, transactional, de-duplicating on merge.

**The split puts the deletion after the equivalence check**, which is the same
shape Phase B used for the wiki (`4dc6da25` then `bb37bcef`). The admin form
field sits in task 05 rather than 06 because the separator changes the moment
`TagField` becomes `ArrayField`, so it cannot wait a task.

### Not done here

No code. Tasks 05–07 are written but not run.

## Step 19 Phase C task 03 — the `elsewhere` seed list, DECIDED AND BUILT 2026-09-06, `cd2e93e7`, PUSHED

The task file carried three decisions. Two more came out of the investigation
before any of the three could be answered honestly, so five were taken in one
sitting. Nothing is built yet; this is the decision record, and the build
follows it.

### What was measured, 2026-09-06

Against the dev database holding the converted production snapshot, by querying
`SocialNetwork` / `InstantMessenger` directly rather than through
`get_social_network_data()` — that function reads a 24-hour cache, and a cache is
not a measurement.

| | social | IM |
|---|---|---|
| seeded rows | 57 | 6 |
| profile rows | 327 | 19 |
| members holding one | 222 | 18 |
| distinct `network_id` in use | 15 | 5 |
| seeded but never used | 42 | 1 (`icq`) |
| **`network_id` values that resolve to no seeded network** | **0** | **0** |

Identical to the 2026-09-05 audit in the task file. **Not refreshed against
production** — Brian's call, the figures being one day old.

Social usage, all 327 rows: `facebook` 181, `twitter` 51, `youtube` 47,
`myspace` 15, `tumblr` 9, `linkedin` 8, `reddit` 3, `lastfm` 3, `flickr` 3,
`foursquare` 2, `pandora` 1, `goodreads` 1, `multiply` 1, `github` 1,
`redbubble` 1. IM, all 19: `msn` 7, `skype` 6, `gtalk` 3, `aim` 2, `y` 1.

### Three findings that changed the shape of the options

**1. Deleting a `Network` row that any profile points at 500s that member's
page.** `Profile._get_data_item` is `self.data_manager.data[self.network_id]`
with no guard, and the KeyError is not silenced by template rendering. Verified
rather than reasoned, against an unsaved profile with a bogus slug:

```
direct .name raises KeyError 'no-such-net'
template raises KeyError 'no-such-net'
```

So pruning is safe only for a network with zero profile rows. All 42 unused
social networks qualify; nothing in use does.

**2. A shorter seed list does not shrink an existing database.** A data
migration only creates. Production already holds all 57 rows, put there by the
`post_migrate` receiver on every `migrate` for years. "Seed only what is used"
therefore leaves production at 57 and a fresh database at 15 — permanent
divergence, and a profile form that differs by environment — unless the
migration also prunes.

**3. `network_id` has nothing for a foreign key to point at.** The slug is
`slugify(network.name)`, computed at read time inside
`get_social_network_data()`; `Network` stores `name`, `url`, `identifier`,
`icon` and no key. An FK is therefore not a field swap — it needs a new stable
column first. The latent bug this exposes is worth stating on its own:
**renaming a network in the admin silently re-slugs it and orphans every profile
row pointing at the old slug**, which by finding 1 means 500ing those members'
pages.

A fourth, smaller one: **the IM half has no fetchable URLs at all.** Its five
templates are protocol handlers — `aim:goim?screenname=%s`,
`msnim:chat?contact=%s`, `ymsgr:sendim?%s`, `gtalk:chat?jid=%s`, `skype:%s?chat`
— so there was nothing to liveness-check on that side.

### The liveness check, 2026-09-06 — measured and assessed, kept apart

**Measured** is the HTTP status of the domain, by `curl` with a browser
user-agent. **Assessed** is whether the service still exists and whether the
stored path still names a profile.

| network | rows | measured | assessed |
|---|---|---|---|
| facebook | 181 | 200 | alive |
| twitter | 51 | 301 → `x.com`, and `twitter.com/jack` → `x.com/jack` | alive, renamed; stored domain stale |
| youtube | 47 | 200; `/user/PewDiePie` and `/user/Google` both 200 | alive, legacy `/user/%s` still resolves |
| myspace | 15 | 301 `www` → bare | alive |
| tumblr | 9 | 301 → `www` | alive |
| linkedin | 8 | 200 | alive |
| reddit | 3 | 301 → `www`, `/user/spez` resolves | alive |
| lastfm | 3 | root 200; `/user/rj` probe failed | alive; path unverified |
| flickr | 3 | 200 | alive |
| foursquare | 2 | `playfoursquare.com` 301 → `foursquare.com`; `/user?uid=` 308 → `app.foursquare.com` | alive; stored domain and path both stale |
| pandora | 1 | 301; `/people/%s` → `/profile/%s` | alive; stored path stale |
| goodreads | 1 | 200 | alive |
| **multiply** | **1** | **302 → `system1.com`** | **dead** — parked, shut down 2013 |
| github | 1 | 200, `/torvalds` 200 | alive |
| redbubble | 1 | 403 | alive; 403 is bot-blocking, not death |

**Two caveats that stay attached to this table.** A live domain is not a correct
profile template: only youtube, twitter, pandora, foursquare, github and reddit
had their `%s` shape spot-checked, and those with public handles rather than
members' stored usernames. And the first youtube probe returned 404 on a badly
chosen subject — a handle with no YouTube channel — which would have read as
"legacy `/user/` is retired" had it not been re-probed against two channels known
to have one.

Every one of the 15 stored templates is plain `http://`.

### Decision 1 — seed the 15 in use, and prune the 42

The migration seeds only the networks members actually use, and deletes the 42
that nobody ever picked. Safe on the data by finding 1 — all 42 hold zero profile
rows — and it is the only option under which production and a fresh database end
up holding the same thing.

**It is a display change and is recorded as one:** the profile form's dropdown
goes from 57 choices to 15. That is the point rather than a side effect; the 42
include Pownce, Jaiku, Dodgeball, Tagworld and Zooomr, and writing them into a
versioned migration would be recording dead choices as current ones.

`multiply` is kept despite being the one dead service, because a member has a row
pointing at it and deleting the network would 500 their profile page. Its
retirement belongs with decision 3's URL refresh, not here.

### Decision 2 — the IM half stops being offered, and stays readable

The IM networks members actually hold are seeded from the migration, so the 19
existing rows keep rendering for the 18 members who hold them. The
instant-messenger section comes off the profile edit form, so no new one can be
added.

**Amended the same day, at Brian's challenge: five, not six.** The option as it
was put said "seed the 6 IM networks", and he asked why `icq` — never chosen by
anyone, for a service as dead as the rest — was being written into a migration
at all. It should not have been. The only reason to seed an IM network is so an
existing profile row resolves instead of taking the member's page down, and
`icq` has no rows; it is the IM equivalent of the 42 social networks decision 1
prunes for exactly that reason. The option had carried the count across from the
audit instead of applying decision 1's own logic to it. `icq` is pruned, on the
same zero-rows guard, and its icon with it.

Retiring the half outright was rejected on the data: it would delete something 18
members entered, for services whose being dead costs them nothing while the row
merely sits there. Keeping the form as it is was rejected on the same fact from
the other side — every one of MSN, AIM, Yahoo, Google Talk and consumer Skype is
gone, and there is no live service left in that half of the app to add.

### Decision 3 — the URL templates are refreshed

The seed list is written with `https://` throughout, and with the four stale
paths corrected: `twitter.com/%s` → `x.com/%s`, pandora `/people/%s` →
`/profile/%s`, foursquare `playfoursquare.com/user?uid=%s` →
`foursquare.com/user?uid=%s`, and `multiply` pointed nowhere useful — it is the
one case where the link is dead whatever it says.

**Also a display change**, and the largest by reach: the links on 222 members'
profiles change, 51 of them from `twitter.com` to `x.com`.

### Decision 4 — a stable `slug` column, and not the foreign key

**The measurement that settles it: 0 unresolvable `network_id` values**, both
halves, and the prune in decision 1 keeps it at 0 because every network being
removed has zero rows. Nothing forces the FK.

So the FK is declined for now and the useful half of it is taken instead:
`Network` gains a unique `slug`, backfilled from today's `slugify(name)`, and the
lookup dict is keyed on that column rather than recomputing the slug from the
name at read time. That fixes the real bug finding 3 exposed — a rename can no
longer silently orphan rows — without touching the form `ChoiceField`s, the
cached-dict machinery or `data_item`, and it is the prerequisite if the FK is
ever wanted.

**The FK stays available, not discarded.** What was rejected is doing a
form-and-cache rework in the step before cutover for a problem measuring zero
rows.

### Decision 5 — the unresolvable-slug KeyError gets a guard

`data_item` returns `None` for a slug that resolves to nothing, the template
skips that entry, and a warning is logged. A bad slug then costs one missing link
instead of the whole profile page.

This is a small addition beyond the task file's scope, taken deliberately:
finding 1 is the reason three of the options above were constrained, and leaving
the crash in place means the next person who prunes a network by hand in the
admin discovers it the way we nearly did.

### What task 03 has to build

1. A data migration in `elsewhere/migrations/` seeding the 15 social and 6 IM
   networks with refreshed `https` URLs, safe on a database that already holds
   the rows, and pruning the 42 unused social networks.
2. Reversible, with the reverse deleting no network any profile refers to.
3. `Network.slug`, unique, backfilled; `get_social_network_data()` and
   `get_instant_messanger_data()` keyed on it.
4. The `post_migrate` receiver and `elsewhere/management.py` deleted. **Nothing
   else imports it** — `migrate` and `flush` auto-import each app's `management`
   submodule, which is the only reason it has ever fired.
5. The IM section off the profile edit form, with the models and rows intact.
6. The `data_item` guard.
7. The 42 orphaned icon files in `elsewhere/static/elsewhere/` decided — 62 files
   are there today.

### What was built — 2026-09-06, unstaged

Two migrations, and the app around them.

**`0003_network_slug`** adds `Network.slug`, a unique `SlugField(max_length=16)`,
backfilled from each network's current `slugify(name)` so no stored
`network_id` moves. The width is not arbitrary: it is the width of
`SocialNetworkProfile.network_id`, the column that has to hold these values.
The `AddField` carries `db_index=False` — SlugField's own index and the unique
one added after the backfill are the same index on PostgreSQL, and creating
both fails on `relation ... _like already exists`.

**`0004_seed_networks`** seeds the 15 social and 5 IM networks with the
refreshed URLs and deletes the rest. The delete is guarded twice — not in the
seed list **and** holding no profile rows — so a network someone picks between
this being written and being run survives it. Reversing restores the previous
`http://` templates on the survivors and re-creates nothing; that is stated in
the migration's docstring rather than left to be discovered. Both directions
bust `elsewhere_sn_data` and `elsewhere_im_data`, which matters in production
where the cache is Redis and shared.

`elsewhere/management.py` and `elsewhere/default_list.py` are deleted, and 42
icon files with them; the 20 that remain are exactly the ones the seeded rows
name.

### Three defects found while building, none of them predicted

**1. The managers memoized the network dict for the life of the process.**
`SocialNetworkManager._data` was a dict populated on first read and never
invalidated. `SocialNetwork.save()` clears the *cache* entry, so the 24-hour
expiry looked like the upper bound on staleness — but the memo sat in front of
it, and a running web process kept serving whatever list it happened to read
first until it was restarted. The memo is gone; the cache is now the only one.
Without this the seeding migration would have changed the dropdown and the
running site would not have noticed.

**2. `edit_elsewhere` returned the `HttpResponseServerError` class, not an
instance** (`return HttpResponseServerError`, no call). Django then fails inside
`set_cookie` with `AttributeError: 'str' object has no attribute 'cookies'`.
Pre-existing, on the "WTF?" branch a POST reaches when it names no known form —
reachable before this change by a bare POST, and reachable more often now that
`im-form` names nothing. Fixed to `HttpResponseBadRequest('Unknown form.')`,
which is also the honest status: it is a bad request, not a server fault.

**3. `Profile.icon`, `WebsiteProfile.icon` and `GOOGLE_PROFILE_URL` were dead
and broken.** `_get_icon` called `reverse('elsewhere_img', ...)` for a URL name
that exists nowhere in `sg101/urls.py`, so anything calling it would have raised
`NoReverseMatch`. Both templates use `icon_name` with `{% static %}` instead.
Removed.

### Two display changes beyond the three that were decided

Recorded here because this site's convention is that display changes are
Brian's call, and these were taken while implementing rather than put as
questions.

- **The network dropdown is now ordered by name.** It had no ordering at all —
  `SocialNetwork.objects.iterator()` with no `order_by`, so the order was
  whatever PostgreSQL returned. With 15 entries alphabetical is the obvious
  choice, but it is a change.
- **The instant-messenger section disappears for members who hold no IM rows**,
  rather than showing an empty "No instant messenger profiles." heading with no
  way to add one. Members who hold a row see it, with a note saying the services
  have shut down and no new ones can be added.

### Verification

**Suite 1,181, green** — 33 more than before: a new `elsewhere/tests/` package
of 30 (the app had none) and 3 net-new in `bio`. Deprecation gate green as its
own run.

**Mutation battery, 17 mutations, every one watched to fail the test that claims
to cover it**, then restored byte-identical. Three of them did not work first
time, and that is the part worth recording:

| | mutation | first attempt |
|---|---|---|
| M1 | key the dict off the name again | anchor matched both builders; re-aimed at the social one |
| M5 | drop `order_by('name')` | **passed** — the seeded list is alphabetical in insertion order, so the ordering test proved nothing. The test now inserts a network that sorts first and is created last |
| M10 | seed an over-long slug | the column refused it before the test ran. Re-aimed at `network_id`'s width, which is the disagreement the test actually guards |

M5 is the one that mattered: it was a green test asserting nothing, and only the
battery showed it.

A fourth is worth stating because it is *not* a gap. Removing the instant
messenger prune (M15) left `test_only_the_networks_in_use_are_seeded` passing,
because a freshly migrated database never had `icq` to remove — the prune only
does anything to a database that already holds it, and
`test_an_unused_messenger_is_removed`, which sets that up, does fail. The pairing
was wrong, not the coverage.

**Against the dev database** (the converted production snapshot, restored to its
pre-work state and re-migrated after the `icq` amendment): **57 social networks →
15 and 6 messengers → 5**, all **327 social and 19 IM profile rows intact**,
**0 unresolvable `network_id`**, every social URL `https`. A real row now renders as
`Twitter → https://x.com/matt_heaton`.

**Every affected page rendered**, not sampled: all 224 members holding an
elsewhere entry, 223 of them HTTP 200 (the 224th is the viewer's own profile,
which redirects to `/profile/me/`). The edit page checked for a member holding
an MSN entry — entry listed with its delete button, add-form gone, notice shown
— and for one with none, where the section is absent.

**Acceptance criterion 8, on a freshly converted snapshot.** `sg101_pristine`
converted with `tools/pgloader/convert.sh` into a scratch database and taken
through `post_convert.py`: the whole chain applied including `0003` and `0004`,
ending at 15/6 networks with all 327 + 19 rows resolving. Scratch database
dropped afterwards.

### The cutover hazard the icon deletion created, and what closes it

Raised by Brian on 2026-09-06: production stays on the old code until the DNS
flip, so a member could add an `icq` entry — or one of the 42 retired social
networks — in the weeks between now and cutover. He asked for a check only if it
was cheap. It turned out to be worth more than that, because the obvious answer
was wrong.

**The data is already safe: the prune's zero-rows guard keeps any network someone
picked.** What is *not* safe is the icon. Those 42 files were deleted here, and
production serves static files through **`ManifestStaticFilesStorage`**, which
does not degrade to a broken image — `{% static %}` on a file missing from the
manifest raises `ValueError`. A network rescued by the guard would therefore
render its owner's profile page as a **500**, not as a missing picture.

`_prune` now logs a warning for every network it rescues, naming the icon file
to restore from git history. The message appears in the `migrate` output at
cutover, which is the moment it is needed and the one place nobody can forget to
look. Two tests cover it — that a rescue is reported with its filename, and that
nothing is logged when nothing needed rescuing — and both mutations against the
reporting are caught.

**To get the answer in advance rather than at cutover**, a query against
production settles it. It lives in `cutover-runbook.md` as **A1**, not here — the
decision is this document's, the cutover-day action is that one's. Brian asked
for the checklist on 2026-09-06 and this item is why the file now exists.

### Not done here

**`Twitter` keeps its name while its URL points at `x.com`.** Decision 3 was
about URL templates, and renaming the network is a further display change that
was not asked for.

**`multiply` is still offered and still dead.** It has one profile row, and
deleting the network would take that member's profile page down with it, so it
stays until either the row goes or the guard makes it safe.

## Step 19 Phase C task 02 — the donations are recorded at the instant Paypal reported — DONE 2026-09-06, `f2dd761d` + `85338132`, PUSHED

`donations/views.py` gains `parse_payment_date()`, and
`donations/migrations/0002_payment_date_pacific_backfill.py` moves every existing
row forward two hours. Both halves in one change, for the reason Phase 0 gave:
correcting new rows alone would leave the column holding two conventions two
hours apart with nothing marking which row is which.

### The boundary: the moment the migration is applied, not a date chosen in advance

Decided at the planning checkpoint, and it corrects an assumption in the task
file. The task offered "a hardcoded UTC timestamp chosen at release" as an
obvious candidate; **a timestamp chosen today would be wrong.** jaguar runs
Django 1.9.13 on Python 2.7 and the corrected parse cannot be deployed there, so
the fix first runs at the Step 21 cutover, and every donation recorded between
now and then is written by the old handler — *after* any constant chosen now.

So the boundary is the migration's own application time. This is safe rather
than merely convenient: the corrected parse ships in the same deploy, so no
database can hold a correctly-stamped row before the migration is applied, and
each database it runs against is a full conversion of a pre-cutover snapshot.

**The assumption it rests on is stated in the migration's docstring:** a full
rebuild, not an incremental top-up. Topping up an already-migrated database with
donations the old site recorded later would smuggle in uncorrected rows, and
nothing here would find them. That hole is not particular to this choice — an
applied migration does not re-run whatever its constant says — but it is the one
thing that would break the design, so it is written down where it will be read.

### Refusing an unknown zone has to reach a person

`ipn()` answers Paypal `HttpResponse()` unconditionally (`views.py:141`), so a
refusal returns 200, Paypal never retries, and the donation record is lost for
good. Every other rejection branch in `process_donation()` only logs, which is
right for the cases where the notification was not ours to record; this one is a
donation we could not read. It logs *and* calls `email_admins()`.

### Why the two abbreviations are mapped and everything else raises

Measured against this machine's tzdata rather than assumed: **`PST` is not
unique.** Ten IANA zones use it, at two offsets sixteen hours apart —
`America/Los_Angeles` at -08:00 and `Asia/Manila`, Philippine Standard Time, at
+08:00. `CST` is worse, spanning -06:00, -05:00 and +08:00 across 45 zone/season
pairs. The stdlib offers no decoder and cannot: `strptime` with `%Z` refuses
`'PST'` outright, and for `'UTC'`, which it accepts, returns `tzinfo=None`.

So the mapping is legitimate because of the *source*, not the token: this
merchant's IPN reports Pacific. The abbreviation selects the zone, and the date
selects the offset — which is why a summer `PDT` reading lands at -07:00 with no
branch of its own.

**`fold` is set from the abbreviation.** For one hour a year the wall clock is
ambiguous: when the clocks go back, `01:30` happens twice, and the abbreviation
is the only thing that says which pass is meant. Ignoring it would mean
discarding the abbreviation's information a second time, in a fix about
discarding it the first time.

### The reverse recovers the forward's boundary from `django_migrations.applied`

Not from a fresh `now()`. The case is a rollback *after* cutover: the site would
have taken new, correctly-stamped donations in between, and an unbounded reverse
would walk those back two hours as well.

### One acceptance criterion could not be met as written, and why

Criterion 6 asks that running the migration twice not shift a row four hours.
With an apply-time boundary a second *manual* call of the helper would shift
again — nothing in the row distinguishes a corrected donation from an
uncorrected one, which the task file states itself. The guarantee therefore
comes from Django's applied-migrations record, and that is what is tested. A
marker column would make the helper self-guarding and is more schema than the
problem is worth.

### Rehearsed on the snapshot the figures were measured on

`MYSQL_DB=sg101_pristine PG_DB=sg101_rehearsal tools/pgloader/convert.sh`, then
`post_convert.py` against that target with `DB_NAME` overridden. `sg101_pristine`
holds 1,421 donations spanning 2011-03-01 to 2026-07-06, which is the task file's
2026-08-09 measurement exactly, so it is the snapshot those figures came from.

| After the chain | |
|---|---|
| rows moved | **1,421** — all of them |
| distinct deltas | **one bucket, exactly +2:00:00** |
| changed calendar month | **5** (ids 241, 290, 361, 381, 912) |
| changed calendar year | **0** |
| the five, read through `in_month()` | each now files under the later month, and no longer under the earlier one |

All five month-crossers are late-evening on the last day of a month, which is
what makes them the only rows a two-hour shift can move. **The single delta
bucket is the load-bearing number**: it says no row moved by any other amount,
which a count of affected rows alone would not.

### Two existing tests were pinning the defect

`test_ipn_post_1` and `test_ipn_post_2` asserted
`timezone.make_aware(datetime(2011, 1, 21, 4, 14, 8))` — which *is* the defect,
the Pacific clock stamped with `TIME_ZONE`. They now state the instant Paypal
reported, written as the reported clock in the zone it was reported in rather
than as a UTC literal. Nothing else in the suite had an opinion about the column.

### The mutation battery found a test of mine that proved nothing

Nine mutations, each aimed at one assertion. **One survived on the first pass**,
and it was the test for the requirement that the abbreviation's length not be
assumed. Restoring the `[:-4]` discard leaves the zone as `KDT` instead of
`AKDT`, and the assertion was `assertIn('AKDT', str(exception))` — which passed,
because the message echoes the whole input string and the echo supplied the
letters. The assertion was satisfied by data the mutation had not touched.
Tightened to `assertIn('timezone "AKDT"', ...)`, which names it as the zone.
[[mutation-verify-or-it-is-not-coverage]]

**A coverage gap turned up while designing the battery, before it was run.** The
reverse's boundary recovery had no test at all: the existing reverse tests call
the helper with an explicit boundary, so swapping `applied` for `now()` in
`back_to_chicago()` would have survived untouched. Two tests were added that
discriminate — the discriminator is a row dated *after* the recorded apply time,
which the correct implementation leaves alone and the mutant shifts.

Second pass: **nine of nine caught**, each by the test that claims to cover it,
both files byte-identical after restore.

### Verification

- Suite: **1,148 tests, OK**
- Deprecation gate (separate run): **1,148 tests, OK**
- `makemigrations --check --dry-run`: no changes detected
- 20 tests added, and `sg101_rehearsal` is left in the Postgres service holding
  the converted snapshot with `0002` applied

### Confirmed outside the suite, on the dev database — 2026-09-06

The migration was applied to the working database and the correction checked on
the two surfaces a person actually reads. **`donations_report` is a management
command, not a page** (`donations/management/commands/donations_report.py`); the
rendered page is `/donations/`, which calls `monthly_stats()` with no arguments
and so reports the *current* month — empty, since the snapshot ends 2026-07-06.
That page is therefore not where this is visible, which is worth knowing before
anyone goes looking there for it.

**Admin.** `DonationAdmin` sets `date_hierarchy = 'payment_date'`, so its
drill-down buckets by exactly the semantics the shift affects. Donation 241 now
reads `2013-06-01 00:06:39`, having been `2013-05-31 22:06:39`.

**`donations_report`, run for all three years holding a crosser.** Nine month
rows moved across the three, and **no annual total moved a cent** — which is the
"0 changed year" claim made visible rather than asserted, since money
redistributed between months of the same year cannot alter the year.

| Year | Months that moved (gross, before → after) | Annual total, unchanged |
|---|---|---|
| 2013 | May 185.00 → 160.00, Jun 135.00 → 160.00; Nov 190.77 → 188.77, Dec 190.00 → 192.00 | 1945.88 / 1853.52 |
| 2014 | Jul 155.00 → 150.00, Aug 160.00 → 165.00; Sep 132.00 → 127.00, Oct 130.00 → 135.00 | 1763.30 / 1672.77 |
| 2020 | Apr 180.00 → 170.00, May 78.00 → 88.00 | 1530.00 / 1452.01 |

The "before" figures are not from memory: they were derived by shifting the
rehearsal data back two hours in SQL, so the printed output could be checked
against a computed expectation rather than eyeballed. Every row matched.

All five crossers are accounted for: 241 and 290 in 2013, 361 and 381 in 2014,
912 in 2020.

### Not done here

**No live IPN was posted.** The parse is covered by the suite against the real
payloads, but nothing here has exercised the path with Paypal actually sending —
that belongs with the Step 21 cutover, not before it.

## Step 19 Phase C task 01 — an address has one owner, and the thirteen pairs are cleared

**Committed and pushed 2026-09-05.** *(No hash, and the state is in the body
rather than the heading. Both deliberate. The 2026-09-04 sweep found eight
headings still claiming `UNCOMMITTED` for pushed work, and a heading is the line
nobody re-reads — but the fix that sweep prescribed, naming the commit, cannot
be applied by the commit to itself: stamping a hash and amending changes the
hash. It works when a later commit names an earlier one. `git log --
<path>` finds this one.)*

`accounts/migrations/0008_auth_user_email_lower_unique.py` blanks the losing
address in every duplicate group and creates
`UNIQUE (LOWER(email)) WHERE email <> ''`, in that order, in one migration.
Decision record: *Step 19 Phase C — the duplicate-email pairs, DECIDED
2026-09-05*.

### Verified on a freshly converted production snapshot, which is the real gate

`MYSQL_DB=sg101_pristine PG_DB=sg101_rehearsal tools/pgloader/convert.sh`, then
`post_convert.py` against that target. **`PG_DB` must be overridden** — it
defaults to `DB_NAME`, so an unqualified run drops and recreates the working
database.

The pristine snapshot reproduced the 12-vs-13 story exactly, which is the first
time it has been observed rather than reasoned about:

| On the pristine pre-conversion data | |
|---|---|
| byte-identical duplicate groups | **12** |
| case-insensitive duplicate groups | **13** |

`0003` folds the case variant on its way past, and that is what makes the
thirteenth byte-identical. After the chain:

| After `post_convert.py` | |
|---|---|
| remaining duplicate groups | **0** |
| rows blanked | **13** |
| blank-address accounts | 4 → **17** |
| total users | 15,227, unchanged |
| index present | yes |
| **all 13 keepers** | **match the decided table exactly** |
| second pass would blank | **0 rows** — idempotent on real data |
| posts still on the blanked accounts | **55**, untouched |
| blanked accounts deactivated | **none** — 12 active, 1 already inactive |

### The suite found the real consequence, and it was not the 13 rows

Adding the index broke **29 existing tests**, all from one cause: three places
build "one address, two accounts", which the index makes unrepresentable.

| Where | Errors | Why it existed |
|---|---|---|
| `RegistrationTest.setUp` | 27 | a second account on one address, so the duplicate check met more than one match |
| `ForgotUsernameTest.test_email_shared_by_two_accounts` | 1 | pins the multi-match listing; a 500 before the lookup stopped calling `get()` |
| `bio` `test_member_sharing_an_address_can_still_save` | 1 | **the trap test itself** |

**The point worth keeping: after this migration the trap cannot occur.**
`EditUserForm.clean_email`'s early return protects nobody, `ForgotUsernameForm`'s
multi-match handling can never fire, and registration's `.count()` can never see
two. All three stay — they are still correct, and the state is still reachable
from a backup taken before the index and on MySQL, which does not get it — but
their tests can no longer build the world they assert about.

Resolved on Brian's call: `RegistrationTest.setUp` drops its second account,
which those 27 tests never needed. The other two keep their coverage by dropping
the index inside their own transaction and letting the rollback restore it.

### Tests, and what the battery taught

The task's acceptance criteria were **amended before any code was written**, on
Brian's challenge that migrations mostly do not need tests. He is right: a
migration is append-only, so a test guards a regression that cannot happen, and
the snapshot rehearsal is stronger evidence than a unit test. What is kept is
narrow — the branches production data cannot reach (a never-logged-in account, an
exact tie, a group of three), because the rehearsal is blind to them.

**The index guarantee is tested, and that reversed an earlier judgement of mine.**
I claimed neither `0002` nor `0003` had any coverage. `0002`'s does — as
`UsernameUniquenessTests` in `accounts/tests/test_models.py`, which never names
the index, so a grep for the index name missed it. Its docstring makes the case
this project had already settled: the assertion is not about PostgreSQL, it is
about the guarantee holding on every engine, by a different mechanism on each.
`EmailUniquenessTests` now mirrors it, plus the blank case that has no username
equivalent. [[search-the-artifacts-before-claiming-new]]

**Ten mutations, all caught, file restored byte-identical.** Two rounds, because
the first found two problems that were not in the tests:

- **A mutation that changed nothing.** Removing `last_login is not None` from the
  ranking key did not fail anything — and could not, because `last_login or
  _NEVER` already partitions the same way and `_NEVER` sorts below every real
  timestamp. **The term was redundant**, and the battery is what found it. It is
  gone.
- **A mutation aimed at the wrong test.** `len(members) < 2` → `< 3` skips
  *two*-member groups, which the three-member test never exercises, so its
  passing proved nothing. Replaced by a mutation that blanks only the first
  non-keeper — which the three-member test does catch — and the original paired
  with a two-member test, which catches it. [[mutation-verify-or-it-is-not-coverage]]

### Verification

- Suite: **1,129 tests, OK**
- Deprecation gate: **1,129 tests, OK**
- `makemigrations --check --dry-run`: no changes detected
- `tools/pg_snapshot.sh dump before-0008-rehearsal` taken first, 129 MB

### Left behind deliberately — and cleaned up 2026-09-07

`sg101_rehearsal` held the converted snapshot with `0008` applied, kept because
it costs nothing and is the artifact any re-check would want. **Dropped on
2026-09-07 at Brian's request**, along with `sg101_reference` and
`sg101_frommigrations`, once Phase C was finished and pushed. Rebuilding it is
the same `convert.sh` line recorded above.

Dropping `sg101_reference` is worth doing on its own account rather than only to
reclaim space: a **stale** copy of it once reported 31 phantom schema
differences, every one naming a table created by a migration that postdated it.
DOCKER.md's procedure drops and rebuilds it before comparing, so the one that
survives between runs can only mislead.

## Step 19 Phase C — the duplicate-email pairs, DECIDED 2026-09-05

Phase 0's six decisions did not cover this item; it was carried into Phase C as
"data hygiene" with no resolution chosen. Decided here, in one sitting, on data
measured from production rather than from the July snapshot. The per-pair
evidence lives in `research/collation-audit.md`; this is the decision record.

### What was already true, and nearly closed the item outright

**The trap this item is famous for has been handled since 2026-08-22.** Step 16
task 05 wrote `bio.forms.EditUserForm.clean_email` the way the trap requires: it
returns early when the address is unchanged, so none of the 26 is locked out of
saving a profile edit, and it rejects only *changing to* an address another
account holds. `accounts.forms.RegistrationForm.clean_email` has checked
`email__iexact` all along, and `ForgotUsernameForm` deliberately lists every
match rather than calling `get()`. **No new pair can be created through the
site**, and the standing cost of the existing 13 is one extra password-reset
email per member, each naming its own account.

So the item could have closed as done. It did not, for one reason:

**The admin and the shell go around both form checks, and this maintainer uses
them.** `c4logic` was deactivated by hand in production during this very
conversation. That is exactly the argument
`accounts/0002_auth_user_username_lower_unique.py` already makes for usernames —
*"the admin, a management shell, and two registrations racing each other all go
around it"* — and it has never been stated for email.

### Decision 1 — build the partial unique index

```sql
CREATE UNIQUE INDEX auth_user_email_lower_uniq ON auth_user (LOWER(email))
    WHERE email <> ''
```

Same shape and the same MySQL guard as `0002`. **It has to be partial, and not
because of the pairs.** Four accounts hold a blank address and one of them is
`Anonymous` — the phpBB-era sentinel this site inherited, which absorbed the
posts of every deleted user and today owns **796 posts and 78 topics**. It must
never hold an address, so `WHERE email <> ''` is the permanent correct shape
rather than a workaround. The other three blanks are `c4logic` (inactive),
`Huatulphonic` (last seen 2006-12-30) and `Clevedale_Renamed_By_Admin`.

**This reverses the Step 11 collation audit's Decision 1** — *"No unique index on
`auth_user.email`. The data cannot satisfy one in either direction."* That was
correct as a statement about a *plain* unique index on the column, which the four
blanks alone defeat. A partial functional index was not considered there.

### Decision 2 — the losing account keeps everything except its address

`email = ''`, and nothing else. No deactivation, no merge, no content moved. The
account keeps its posts, its profile and its ability to log in; the one thing it
loses is self-serve password reset, until someone gives it an address back.

**This is why decision 3 is cheap.** With blanking, the keeper rule does not
decide which content survives — it decides which of two accounts can use the
reset form. Both accounts belong to the same person reading the same mailbox, so
the other one is recoverable by asking.

### Decision 3 — most recent login wins

The two candidate rules — most posts, most recent login — **agree on 12 of the 13
pairs.** They differ only on `member08@example.com`, and the tie is broken toward the
account the member actually uses:

| Address | Keeps the address | Blanked |
|---|---|---|
| `member13@example.com` | `terma_reverb` 6177 · 2026-05-31 · 52 posts | `ymastorak` 11446 · 0 posts |
| `member07@example.com` | `sdubose` 1114 · 2026-03-15 · 9 | `scoot` 540 · 1 |
| `member02@example.com` | `Jester` 10107 · 2025-04-08 · 17 | `JesterR` 7707 · 0 |
| `member12@example.com` | `Turnip` 142 · 2024-11-07 · 30 | `Turnip_Returns` 14260 · 0 |
| `member06@example.com` | `Admiral_Fishwich` 4456 · 2024-01-20 · 118 | `MajorReverb` 2922 · 4 |
| `member08@example.com` | **`kinghawaii` 892 · 2023-07-21 · 4** | **`kinghawaii50` 1279 · 15** |
| `member11@example.com` | `alphaking` 6981 · 2022-06-17 · 195 | `alphaking1` 13092 · 1 · inactive |
| `member09@example.com` | `NothingDiesWithBlueSkies` 4045 · 2020-01-04 · 36 | `TastyGrog` 3757 · 11 |
| `member03@example.com` | `SurfBeat` 2373 · 2019-03-18 · 285 · inactive | `Joey` 2947 · 11 · inactive |
| `member04@example.com` | `knucklesnuclear` 5180 · 2016-06-06 · 60 | `guitarbrad` 379 · 0 |
| `member10@example.com` | `SpitfireMkI` 4053 · 2015-03-01 · 30 | `UnmannedBassPlayer` 2592 · 6 |
| `member01@example.com` | `Hydronaught` 3566 · 2013-08-19 · 12 | `Drippy` 3111 · 6 |
| `member05@example.com` | `LouSeefer` 5898 · 2012-04-05 · 1 | `mudbone99` 4769 · 0 |

**`member08@example.com` is the only pair where the rules disagree**, and the losing
account has more history than the winner: `kinghawaii50` keeps its 15 posts and 9
topics and stays active, and only loses the address it has not used since 2007.

**`member03@example.com` is immaterial either way** — Brian deactivated
`Joey` on 2026-09-05 and `SurfBeat` was already inactive, and Django's
`PasswordResetForm` only considers active users, so neither account could reset
regardless of which holds the address.

### What Phase C has to build

A data migration that **computes the groups rather than hardcoding them**, applies
the rule, and creates the index in the same migration, so it is self-consistent on
any database it meets — including the fresh production snapshot Step 21 loads. A
hardcoded list would silently skip a fourteenth pair created between now and the
cutover; a dynamic rule handles it by the same standard.

Points the task file must settle rather than discover:

- **Tie-breaks.** No account in the current 13 has a null `last_login`, but the
  migration will meet databases where one does. A null must lose, and equal
  timestamps need a deterministic fallback (lowest `id` keeps the address).
- **Idempotency comes free** — once the groups are gone the migration finds
  nothing — but it must be verified rather than assumed.
- **Reverse.** Blanking cannot be undone from the row itself. Either the reverse
  restores from addresses written into the migration, or the migration declares
  itself irreversible and says why. Decide it, do not leave it to `RunPython`'s
  default.
- **MySQL guard**, as in `0002`: no functional indexes in 5.7, and none needed.

## Step 19 Phase B — the four dead `tools/` scripts are gone and `flag_data.py` reads JSON — DONE 2026-09-05

**Phase B is complete.** Phase 0 decided this item on 2026-09-03 — delete four,
port one — and left one thing unverified, which turned out to be the only part
of it worth measuring.

### The four deletions

Compile status re-verified first-hand before deleting anything, since a script
that had quietly started working would change the decision. All five still fail
on Python 3.12, each at the syntax the record predicted:

| Script | Fails on | Why it goes |
|---|---|---|
| `filter_posts.py` | `print reader.next()` | fixed orphaned posts after a migration that finished years ago |
| `load_ygroup.py` | `except MySQLdb.DatabaseError, e:` | feeds `mysqlimport`, which Step 21 retires with the MySQL box |
| `post_sub.py` | `except IOError, ex:` | same |
| `translate_yahoo_group.py` | `print "Processing "` | same |

### The unverified assumption was the whole job, and it was half right

Phase 0 flagged that the script reads Debian's ISO-3166 **XML** and that
`iso-codes` was *believed* to have moved to JSON — recorded as a thing to
measure rather than a finding. Measured in a `python:3.12` container against
`iso-codes` **4.18.0-1**:

- **The XML still ships.** `/usr/share/xml/iso-codes/iso_3166.xml` exists and the
  old parser still works against it — 249 `iso_3166_entry` elements, every one
  with `alpha_2_code`.
- **And it is a symlink to `iso_3166-1.xml`, whose own header reads `WARNING:
  THIS FILE IS DEPRECATED. PLEASE USE THE JSON DATA INSTEAD.`**

So "the port is one line" was right about the *code* and wrong about the
*target*. The one-line version would have compiled, run, produced correct output
today, and left the script reading a file upstream has marked for removal. The
port reads `/usr/share/iso-codes/json/iso_3166-1.json` instead; the attribute
names are the only real difference (`alpha_2_code` → `alpha_2`, same 249
countries, same 11 carrying a `common_name`).

**This is the second time in three days that an item's "unverified" note was the
only interesting thing in it.** Phase 0 was right to record it as a measurement
rather than resolve it from memory. [[measure-before-recording-in-planning-docs]]

### Verified against the real package and the real icons, not a fixture

Regenerated in the container against `iso-codes` 4.18.0-1 and the repo's 241 PNGs
in `static/flags/64`:

| Check | Result |
|---|---|
| Entries produced | **222** — the same count as the committed `bio/flag_data.json` |
| Key set vs. committed | **identical**; no country added, none removed |
| Countries reported as missing an icon | 27, which is 249 − 222 |
| Under `LC_ALL=C` | byte-identical output, so `print(s)` on a non-ASCII payload is not a hazard here |

**Mutation-checked rather than assumed:** dropping the `common_name` fallback
changes 11 of the 222 entries, so that branch is load-bearing and the port
preserves it. [[mutation-verify-or-it-is-not-coverage]]

### Thirteen country names have changed since 2013 — NOT applied

Regenerating would change what renders on every profile and forum post, so it is
Brian's call and the data file is untouched. The 13 split into two causes, which
is worth knowing before deciding:

**Genuine renames** — `cv` Cape Verde → Cabo Verde, `cz` Czech Republic →
Czechia, `mk` Macedonia, Republic of → North Macedonia, `sz` Swaziland →
Eswatini, `tr` Turkey → Türkiye, `ps` Palestinian Territory, Occupied →
Palestine, State of.

**`common_name` added upstream after 2013** — `ir` Iran, `kp` North Korea, `kr`
South Korea, `la` Laos, `sy` Syria, `tz` Tanzania, `vn` Vietnam all shorten. The
2013 data already had `common_name` for `bo`, `md`, `tw` and `ve`, which is why
those four read short in the committed file and do not move.

**Nothing is at risk in the stored data either way.** `UserProfile.country` holds
the two-letter code and `bio/flags.py` maps code → name at render time, so a
rename is display-only. What it does change is the dropdown's order, since
`FLAG_CHOICES` sorts by name under the active locale.

### Two files the deletions emptied

**`pyrightconfig.json`'s exclude block is gone entirely.** It listed exactly these
five files, with a comment explaining they were "still Python 2 and unparseable by
a py3 checker" — so porting one and deleting four removes the reason for the
block, not just its entries. pyright now analyses 464 files and `tools/flag_data.py`
contributes **zero** diagnostics; the errors that remain under `tools/` are
pre-existing ones in `email_smoke.py` and `image_smoke.py`.

**`DOCKER.md`'s `mysqlclient` note** named `tools/load_ygroup.py` as one of three
`MySQLdb` importers. Two remain, both under `tools/pgloader/`, and the reasoning
for omitting the pin from the local venv is unchanged.

**Gate: 1117 tests, OK**, under the deprecation gate on `docker_test`.

## Step 19 Phase B — the seven model-less tables are dropped — DONE 2026-09-04, `6fccdc4a`, PUSHED

`core/migrations/0002_drop_legacy_tables.py`. They arrived with the MySQL→Postgres
conversion, which copied the old database as it stood rather than pruning it, and
nothing has ever described them in Python.

| Table | Rows | What made it |
|---|---|---|
| `core_userlastvisit` | 540 | superseded tracking |
| `membermap_mapentry` | 524 | `membermap`, pruned in Step 4 |
| `core_anonlastvisit` | 472 | superseded tracking |
| `irc_ircchannel` | 1 | an `irc` app that no longer exists |
| `gcalendar_accesstoken` | 1 | the OAuth credential the calendar stopped using when it moved to a service account |
| `auth_message` | 0 | Django's own, from before 1.4 |
| `mailer_message` | 0 | a mail queue this project does not use |

**1,538 rows, matching the ~1,540 the conversion recorded.** No table references any
of them — the only foreign keys run the other way, into `auth_user` — so nothing
depended on them and no `CASCADE` was needed. It is deliberately absent: a table
that turns out to have a dependent should stop the migration rather than take the
dependent with it.

### Two decisions in the migration worth keeping

**`DROP TABLE IF EXISTS`, because almost no database has them.** A test database, or
any database built by running the migrations, starts from the models and contains
none of these — verified by building one and counting: zero of seven. Without
`IF EXISTS` the migration would fail everywhere except the single place it has work
to do. This also means **the 1,117-test suite exercises the migration on every run**,
which is where its real coverage comes from.

**Deliberately irreversible.** Recreating seven empty tables would restore the shape
and none of the contents, which is a worse answer than an error: the rows are still
in the MySQL database this one was converted from.

### No unit test, and the reason is that one would have no teeth

A test asserting the tables are absent passes on a migrations-built database
*without* the migration, because that database never had them. The verification
that means anything is running it against the converted production data, which is
what the dev database holds: **seven tables before, zero after**.
[[mutation-verify-or-it-is-not-coverage]]

### The drop closes the schema gap the conversion left

`compare_schema.py` compares the converted database against one the migrations
build. Against a freshly built reference, after the drop:

| Dimension | Converted | Reference |
|---|---|---|
| columns | 537 | **537** |
| foreign keys | 90 | **90** |
| indexes | 277 | 278, the 1 difference already accepted |

**One difference remains, and it is not from this work:**
`accounts_pendingemailchange_id_seq` is a sequence not owned by its column. That
table postdates the conversion and the migration here only drops tables. Recorded
for Step 21 rather than chased.

**A stale reference database briefly made this look worse than it was.** The first
run reported 31 differences and exit 1 — every one of them naming
`accounts_pendingemailchange`, `accounts_pendinguser` or `search_searchdocument`,
all tables created by migrations that postdate the leftover `sg101_reference`
database in the dev stack. DOCKER.md's procedure drops and rebuilds that reference
before comparing; running it as documented cut 31 differences to 1. **None of the 31
ever named a legacy table**, which is what said the staleness was not this work.
[[suspect-the-measurer-before-the-record]]

`compare_schema.py`'s `LEGACY_TABLES` set stays. Its comment was corrected: whether
the converted database still holds these tables now depends on whether migrations
have run against it, and the filter keeps the comparison honest at both moments.

**Verification:** `check` clean, `makemigrations --check` clean, 1,117 tests green
under `docker_test` and again under the deprecation gate. Live smoke against the
converted dev database — home, forums, news, calendar, downloads, links, podcast,
contact, member list — all 200 or an expected redirect.

**Remaining in Phase B:** delete four `tools/` scripts and port `flag_data.py`.
*(Closed 2026-09-05 — Phase B is complete; see the section above.)*

## Step 19 Phase B — the wiki is archived and the bridge is gone — DONE 2026-09-04, `4dc6da25` + `bb37bcef`, PUSHED

**Brian's call: shelve it.** The wiki content is copied into the repo, and MoinMoin
keeps running on jaguar until the host is decommissioned. No static publication, no
redirect — `archive/wiki/` is a shelf copy, not a replacement.

### What the wiki actually was, measured before anything was touched

| | |
|---|---|
| Pages with content | **30**, of 8,670 page directories — the rest are empty shells from MoinMoin's shipped help system |
| Last edit of any kind | **2022-06-07**; 17 of the 30 untouched since the wiki's setup day in 2013 |
| Data directory | 1.7 GB, of which **1.5 GB is `event-log`** — an append-only record of page views |
| Traffic, 5 days | 15,281 requests; the two most-requested things are `action=login` (7,670) and `action=newaccount` (5,680), across 5,463 IPs |
| Real content reads, same window | `ReverbFaq` 81, `GearFaq` 69, `FrontPage` 46 |
| Accounts | 994, essentially all residue of that `newaccount` hammering |

**The irreplaceable part is 8.6 MB, not 1.7 GB** — 158 KB of current markup, 1.7 MB
across all 261 revisions, and 6.9 MB of attachments. Everything fits in the repo, so
"which pages are worth keeping" stopped being a question.

**A planning question is answered by this.** `implementation/plan.md` asked on
2026-08-24 whether the wiki retirement had been code-only and the vhost was stale.
It is not stale: Apache is serving MoinMoin through mod_wsgi right now.

### The archive — `archive/wiki/`, 10 MB, 399 files

Five layers: `markdown/` (the usable copy), `moinmoin/` (**authoritative**, all 261
revisions), `html/` (MoinMoin's own rendering), `attachments/`, `mirrored/` and
`static/`. `MANIFEST.json` records every page's current revision and a SHA-256 of
its markup, so before jaguar is destroyed one command says whether anything was
edited after today rather than anyone having to remember.

**Conversion went MoinMoin renders → HTML → Markdown**, never through a
hand-written MoinMoin parser: MoinMoin is the only thing that correctly reads its
own dialect, and HTML→Markdown is well-trodden. A bespoke parser for `||tables||`
is how a row goes missing silently.

#### Fetching through Cloudflare would have silently destroyed content

The first capture went through the public hostname. **Cloudflare's email obfuscation
had rewritten all 30 pages** — 61 occurrences — replacing real addresses with
`/cdn-cgi/l/email-protection` links, so `info@therevomatics.com` and its like were
simply absent from the result. Caught only because the converted Markdown looked
wrong. Re-fetched from the origin on jaguar with a `Host` header: zero occurrences.
**The obvious way to take this archive loses data, and nothing would have reported
it.** [[probes-must-not-perturb-what-they-measure]]

#### A dead hotlink recovered, from the wiki's own edit-log

`BandDatabase/TheRevomatics` hotlinked a photo from `therevomatics.com` that now
404s, and carried a 6.7 MB attachment **no revision ever referenced** — 70% of the
archive's size, and it had been written up here as junk worth deleting. Brian
remembered an image on that page. The edit-log settles it:

```
2017-08-31 01:33:21Z  SAVE    192.0.2.2
2017-08-31 01:35:55Z  ATTNEW  192.0.2.2  TheRevomatics.jpg
```

Same editor, 154 seconds after their last edit, never linked in because the hotlink
still worked in 2017. EXIF copyright is Joe Weigel, a guitarist the page lists.
**This archive holds the only surviving copy**, and `markdown/` now shows it in
place of the dead link; `moinmoin/` is untouched. *The record nearly threw it away
because it asked the revisions and not the log.*

#### The hotlinks, counted rather than assumed

An earlier draft of the archive's README claimed the Google Photos links were "gone
long before today." **Wrong — 11 of the 16 external images still serve an image**,
checked one by one with content types, because a `200` can be a parked domain (one
was). The 11 live ones are now mirrored into `mirrored/` (808 KB); the 5 dead ones
keep pointing where they always pointed, since rewriting them would hide that the
image is gone. `mirrored/` is deliberately separate from `attachments/`: one was
uploaded *to* the wiki, the other pulled *from* elsewhere.

**Link validation had a hole worth remembering.** The first check reported 54 links
and 0 broken — it only examined `.md` links and never images, and all four
attachment paths were wrong by one directory level. Checking both classes found 73
broken. Now: **73 page links and 16 images, zero broken.**

### The bridge removal

`wiki/` (5 modules, 3 tests), `WikiMiddleware`, the `'wiki'` app, the
`expire_wiki_cookies` beat entry, four `WIKI_*` settings, and stale comments in
`docker-compose.yml`, `production.py`, `docker_test.py`, `README.md` and
`AGENTS.md`. No models, so no migration; `makemigrations --check` clean.

**Verified by asking the running settings object, not by reading the diff** — which
is what caught `WIKI_COOKIE_DOMAIN` still defined in `local.py` after the first
pass. The sweep had been `grep -rn "wiki"`, case-sensitive, which never matches
`WIKI_`. For a removal, ask the system what it still has rather than the source what
it still says.

### The three template links went too, and the reasoning that nearly kept them

`base.html` and `v3/base.html` carried a Wiki menu entry; `contact_form.html`
pointed at `Sg101Faq`. **They were nearly left in place on the argument that the
wiki is still live and removing them would cut off readable content early — which
confuses this branch with production.** jaguar serves its own templates from the hg
`default` branch and keeps its links until decommission; nothing here is deployed
anywhere. Leaving them would only have meant launching the new site with menu
entries aimed at a hostname about to stop resolving. Brian caught it; the same
error had been made about the bridge itself an hour earlier.

The contact page's FAQ sentence was **removed rather than repointed** — there is no
other FAQ on the site to point at.

`core/tests/test_navigation.py`, 3 tests, modelled on the calendar's navigation
tests: render real pages in both live designs rather than grepping templates.
Mutation battery 3 of 3, each caught by the expected test. Restoring the link to
`v3/base.html` also fails the contact test, since `contact_form.html` extends it;
the third mutation isolates the contact page.

#### The mutation battery destroyed a template, and its own check said otherwise

**The first run of that battery overwrote `sg101/templates/base.html` with the
contents of `sg101/templates/v3/base.html`.** It saved each file's backup under
`$(basename $f)` — and `sg101/templates/base.html` and `sg101/templates/v3/base.html`
share the basename `base.html`, so the second copy clobbered the first's backup and
the restore wrote v3's content into the forums design. The two files ended up with
the same git blob.

**Three separate checks failed to notice.**

1. The battery's own "restored byte-identical?" step used the same colliding name,
   so it compared v3's backup against the file that now held v3's content and
   reported `ok`. *The verification shared the defect it existed to catch.*
2. The full suite stayed green at 1,117. Nothing asserts that the forums design
   renders the forums design; the new tests only ask whether a string is absent,
   and it was absent from both.
3. The write-up above was drafted claiming "files restored byte-identical",
   sourced from that check rather than from the diff.

**Caught by Brian reading the diff** — a 413-line change to a file whose intended
diff was one line. Restored with `git checkout` and the single line re-applied; the
diffstat is now 6 deletions across the three templates, which is what it should
always have been. The battery was re-run with backup names derived from the full
path and all three mutations caught again.

**The rule this earns: a mutation battery must verify against `git`, not against
its own copies.** A backup scheme is state the battery itself manages, and it can
be wrong in exactly the way the battery is meant to detect. `git diff --stat` knew
the truth the entire time. [[mutation-verify-or-it-is-not-coverage]]
[[suspect-the-measurer-before-the-record]]

**Verification:** 1,117 tests green under `docker_test` and green again under the
deprecation gate. Count unchanged — 3 wiki tests removed, 3 navigation tests added.

### Still open for Step 21

The vhost, the Let's Encrypt certificate and the DNS record for
`wiki.surfguitar101.com` all live on jaguar and die with it. Nothing in this repo
references the hostname any more.

**Remaining in Phase B:** the 7 model-less legacy tables; delete four `tools/`
scripts and port `flag_data.py`.
*(Closed 2026-09-05 — Phase B is complete; see the section above.)*

## Step 19 Phase A — the delete paths are safe — DONE 2026-09-03, `b24b4286`, PUSHED

`forums/tests/test_delete_paths.py`, 12 tests. Suite **1,101 → 1,113**, green
under both runs, `makemigrations --check` clean. The hazard that cost forum 3 and
its 4,626 topics / 24,107 posts cannot fire any more.

**Four changes, and one of them is a deletion nobody planned.**

| File | Change |
|---|---|
| `forums/models.py` | `CASCADE` → `SET_NULL` on both `last_post` fields |
| `forums/models.py` | `Post.delete()` override **removed entirely** — see below |
| `forums/tools.py` | null guards on `topic.last_post` / `forum.last_post` |
| `forums/migrations/0004_…` | `AlterField` ×2, and `sqlmigrate` prints `(no-op)` for both |

### The tests failed by destroying the forum, which is the point

Group A was written first and run under `CASCADE`: 3 failures and 2 errors, the
errors being `Forum.DoesNotExist` raised while *reloading* the forum the test had
just deleted a post from. The fault reproduced itself rather than being argued
for. After `SET_NULL`, 4 of 5 passed — and the fifth found something.

### `Post.delete()`'s topic rule had never once run

```python
first_post_id = self.topic.posts.all()[0].id
super(Post, self).delete(*args, **kwargs)
if self.id == first_post_id:      # self.id is None by now
    self.topic.delete()
```

**Django nulls the instance's primary key during `delete()`**, so the comparison
is always False. Measured on this exact model: `p.id = 1` before,
`first_post_id = 1`, `p.id = None` after, comparison `False`.

**The cascade was standing in for it, which is why nobody noticed.** Deleting a
topic's only post meant deleting the post `Topic.last_post` pointed at, so the
topic vanished by cascade and the dead branch looked alive — while the same
cascade took the forum. For a *multi-post* topic the masking never applied, so
that half has been visibly wrong for years: deleting the opening post of a thread
leaves the thread. Removing the cascade is what exposed it.

**And the real path never used it.** `forums/views/main.py:491` decides
explicitly, on a *different* rule — `delete_single_post()` routes on **sole
post** (`post_count == 1 and post == topic.last_post`), where the override tested
**first post**.

**DECIDED (Brian, 2026-09-03): delete the block, do not repair it.** Repairing it
— capturing `self.id` before the super call — would *introduce* a destructive
behaviour that has never actually run: deleting the first post of a 200-reply
thread would silently delete the thread. That is shipping a new hazard, not
restoring an intended one. With the block gone the override was a pure
pass-through, so the whole method went; `Model.delete()` already returns the
`tuple[int, dict]` that the original item asked for.

**This dissolved a question the plan was going to ask** — what the return value
should report when the topic is also deleted. There is no second delete to
account for.

### The pointer heals itself, so the tests assert the new value

`forums/receivers.py:on_post_delete` recomputes `last_post` on both the topic and
the forum after a post goes. Django's collector applies `SET_NULL` *before*
deleting rows and *before* sending `post_delete`, so the sequence is: null the
pointer, delete the row, recompute from the survivors. **Surviving is not the
assertion — being repointed at the previous post is.**

`last_post_pre_delete()` is untouched and stays the normal path. It repoints
before; the receiver repoints after.

### One worry that turned out to be already handled

`sg101/templates/forums/last_post_info.html` has always branched
`{% if post %}…{% else %}<i>No posts</i>{% endif %}`, so a null pointer renders
"No posts" on the forum index. That earned an assertion rather than a fix.

### The null-guard asymmetry, fixed

`forums/tools.py` reached through `last_post` unguarded where
`views/main.py:_delete_topic` guards the same access. Both loops now read
`if X.last_post is None or X.last_post.pk in post_ids:` — **treating null as
drift to repair rather than a state to step around**, since that branch is
exactly the code that recomputes counts and requeues an emptied topic. Guarding
with `and` instead would have skipped the one row that was already wrong.

### Mutation battery — 12 behaviours, 12 caught, but one needed two mutations

Eleven fell to a single mutation each. The twelfth survived and was worth
chasing: setting `forum.last_post = None` inside `delete_user_posts` left the
test green, and so did neutering the `post_delete` receiver — **each alone**.

**Neither mutation reproduced a fault, because the two mechanisms are
independent and either suffices.** `tools.py` repoints before the delete; the
receiver recomputes after it. Breaking both at once fails the assertion
(`AssertionError: None != <Post: theirs>`), so the test has teeth and the
behaviour simply has two guarantors. Consequence worth recording: **after
`SET_NULL`, `tools.py`'s inline repointing is no longer load-bearing** — it is
belt-and-braces, like `last_post_pre_delete()`. It was left in place.

That is the third time this project has met a mutation that did not reproduce its
fault, and the second in two days.

## Step 19 Phase A — corrected before it started: it is not schema work (2026-09-03)

**Phase A had been described as schema changes, and it is not.** The framing came
from the entry that scheduled the `last_post` fix — *"schema changes belonging
with the other model-level work"* — and it survived into the phase table
unexamined until Brian asked why Phase A was a schema migration. It is not.
Corrected at source in `plan.md`, which is where the item detail lives.

**`on_delete` never reaches the DDL.** Django enforces it in the deletion
collector, in Python. The live constraints say so:

```
forums_topic   last_post_id_refs_id_a0749907   ON DELETE NO ACTION
forums_forum   last_post_id_refs_id_e3773179   ON DELETE NO ACTION
```

The database does not cascade at all. And both fields are already
`blank=True, null=True`, with `information_schema` confirming `last_post_id` is
nullable on both tables — so `SET_NULL`, which needs a nullable column, already
has one. **The fix is a two-word model edit and a state-only migration**: Django
still generates an `AlterField`, `on_delete` being tracked in migration state,
but it emits no SQL. All of Step 19's schema work is in Phase C.

### What the cascade living in the collector does and does not imply

It fires on **any** delete that runs the collector, `QuerySet.delete()` included.
Consequence for Phase A: the tests have to exercise a queryset delete as well as
`post.delete()`, or they prove `SET_NULL` only for the path that goes through the
model override.

**A claim written here on 2026-09-03 went further than that and was wrong.** It
said `forums/tools.py:71` was therefore an unguarded live application path into
the hazard. Retracted the same day, on reading the function rather than the line:
`delete_user_posts()` **is** guarded, and says so in its docstring — *"This
function adjusts the last post foreign keys before deleting the posts to avoid
the cascading delete behavior."* The sixty lines before its bulk delete repoint
`topic.last_post` and `forum.last_post`, defer topic deletions into
`pending_delete` explicitly *"as it could cascade and take out a forum"*, and
close with *"All foreign keys are accounted for."* It does the guard work inline
instead of calling `last_post_pre_delete()`.

**How the wrong claim was reached, since that is the reusable part:** the plan
entry quotes exactly one line of that function, and the reasoning was done on the
quoted line plus general knowledge of queryset-delete semantics, without opening
the file. The entry's own verdict — *"It reads as deliberate"* — was correct, and
was overwritten by a worse one. **Suspect the measurer before the record applies
to a record you are about to improve, not only to one you are about to trust.**

### A None-guard asymmetry, found by reading it properly — folded into Phase A

`forums/tools.py` reaches through `last_post` unguarded (`topic.last_post.pk`,
`forum.last_post.pk`) while `views/main.py:_delete_topic` guards the same access
(`if parent_forum.last_post and ...`). The field is nullable on both models and
is set to `None` whenever a count reaches zero, so a `None` there is an
`AttributeError`.

**Stated to the limit of what was checked:** the asymmetry is read off the source
and the `None` is reachable through denormalization drift. Whether ordinary use
can produce it was not established — a topic in that set has at least one of the
user's posts, which normally implies a non-null `last_post`. Brian's call to fold
it into Phase A rather than record and defer, since the phase already opens that
function.

### One worry removed: `SET_NULL` has no rendering surprise

`sg101/templates/forums/last_post_info.html` already branches on it —
`{% if post %}…{% else %}<i>No posts</i>{% endif %}` — so a NULL `last_post`
renders "No posts" on the forum index and topic lists today. That earns an
assertion in Phase A's tests, not a fix.

## Step 19 Phase 0 — the six decisions — DONE 2026-09-03

All six questions answered in one sitting, asked one at a time at Brian's
request. **Three items closed outright with no work carried, and a fourth was
verified rather than pruned**, taking the step from eighteen items to fifteen —
which is what Phase 0 was for. Structure and phase assignments live in
`implementation/plan.md`; this section is the decision record.

### 1. ORDER BY collation — **keep PostgreSQL's ordering**

Closed on the audit already recorded below; no fresh measurement needed. It is
cosmetic and deterministic — same rows, same counts, same page count — and
Postgres filing `-Bong-` under B beats MySQL exiling it to page 1. `C` was
rejected on the record: it sorts by byte, making it case-*sensitive*, which is a
larger change than the one it would be fixing and does not reproduce MySQL's
case-insensitive order either. The tag-cloud half of the audit still waits on
Phase C, since the `ArrayField` option deletes the table it is about.

### 2. `repoze.timeago` — **replaced by `django.utils.timesince`** (Phase D)

**This reverses the recommendation standing in `requirements.txt`,** which
argued for vendoring the 79 lines because it would mean no display change. The
measurement is what turned it around — "no display change" is the *cost* here,
not the benefit:

| age | `repoze.timeago` | `django.utils.timesince` |
|---|---|---|
| 90 seconds | 2 minutes ago | 1 minute ago |
| 45 minutes | 45 minutes ago | 45 minutes ago |
| 3 days | 3 days ago | 3 days ago |
| 40 days | 40 days ago | 1 month, 1 week ago |
| a 2015 post | **3800 days ago** | 10 years, 4 months ago |

Measured in the container against both libraries, not read from documentation.
`repoze.timeago` rounds to nearest and **never escalates past days**, so every
forum listing older than roughly 2023 currently renders a four-digit day count.
`timesince` is already in the stack, so this is a deletion rather than a swap:
the dependency goes, and so does the deprecation gate's last third-party ignore
(`_NOW = datetime.utcnow`). **It restyles the whole archive, which is why it was
Brian's call rather than a cleanup.** The call site is single —
`core/templatetags/core_tags.py:154`. `colophon.html:17` credits the library on a
live page and needs updating with it.

### 3. The five Python 2 `tools/` scripts — **delete four, port one** (Phase B)

Compile status re-verified first-hand rather than taken from the earlier record:
all five still fail, `filter_posts.py` / `flag_data.py` /
`translate_yahoo_group.py` on `print` statements and `load_ygroup.py` /
`post_sub.py` on unparenthesized `except`.

**Deleted:** `load_ygroup.py`, `translate_yahoo_group.py` and `post_sub.py`, all
three of which exist to feed `mysqlimport` — which Step 21 retires with the MySQL
box — and `filter_posts.py`, which fixed orphaned posts from a migration that
finished years ago.

**Ported:** `flag_data.py`, the one with a live output. It generates
`bio/flag_data.json` — 222 countries, rendered on every profile and forum post —
and reports missing flag icons, a job that recurs whenever a country changes.
The port is one line. **One thing to check before doing it:** it reads Debian's
ISO-3166 **XML**, and `iso-codes` is believed to have moved to JSON some years
ago. That is unverified — flagged as a thing to measure, not a finding.

### 4. `oembed` **kept** (verified), `banners` **kept dormant** (Brian's call)

`oembed` was never really in question once measured: **14,751 rows behind 14,581
forum attachments, most recent embedded post 2026-07-10**. It is live
infrastructure for forum media, not a peripheral app.

`banners` measured as dead: one campaign, *Radio Free Bakersfield*, created
2012-02-03, eleven images, rendered by `core/rfb_block.html` — **which is
included by no other template**, and whose last commit was a 2012 Django 1.4
restructure. So it has rendered on zero pages for over a decade.

**The measurement supported pruning and Brian chose to keep it dormant**, for the
option of a future ad or promo campaign without rebuilding the app. Recorded with
the downside attached, because it is the honest one: leaving it installed is how
it reached fourteen years dormant in the first place. Nothing changes — the app
stays in `INSTALLED_APPS`, the orphaned template stays, and the twelve rows ride
the Step 21 snapshot to the new host.

### 5. PayPal `payment_date` — **fix forward and backfill** (Phase C)

**The deciding argument was that "do nothing" is not static.** The amounts and
dates are right and only the times are off, by a constant two hours across all
1,421 donations — but the code keeps recording every *new* donation two hours
early, so the error grows rather than sitting still. And because Step 21 loads a
fresh production snapshot, the correction has to be a data migration rather than
a one-off script in any case, which is what the plan already specified.

"Fix forward only" was put up and **rejected on the record** rather than by
omission: it would leave the column holding two conventions two hours apart with
nothing marking which row is which, and `monthly_stats()` summing across both.

Constraints carried into Phase C: map `PST`/`PDT` to `America/Los_Angeles` and
**raise on anything else rather than guessing**; the backfill keys on
`payment_date < <cutover>` and must be idempotent, since nothing distinguishes a
corrected row from an uncorrected one.

### 6. The timezone dropdown — **leave it, item closed**

Nothing is broken: all 95 distinct values stored across 15,227 profiles resolve,
and `clean_time_zone` already rejects junk including path-shaped input.
Regenerating is purely additive (401 zones across 11 areas → 553 across 16) but
is **not obviously an improvement** — a longer picker whose additions are mostly
`Etc/*`, `Brazil/*` and `Mexico/*`.

The `ChoiceField` option keeps its argument — it would make invalid input
impossible by construction rather than by a hand-written validator — and is
**recorded as a future improvement rather than carried as an open question**,
since it was the most work in Phase 0 for the least risk removed.

## PLANNING — Step 19 restructured into five phases (2026-09-03)

**The step was a junk drawer, and the giveaway was its objective.** "Complete
pruning per the triage" described four of the eighteen items it had accumulated.
The other fourteen arrived as deferrals out of Steps 11–18, each with a reason of
the form *not a version bump*, *belongs with the other model-level work*, or *app
modernization, not an engine switch*. **Every one of those is a reason not to do
something then, and none of them is a reason the work belongs together** — so the
step was grouped by provenance rather than by kind. That is why it read as a list
instead of a claim, and why nobody could say what finishing it would mean.

Full restructure in `implementation/plan.md` under Step 19, which is the one home
for it; this section records only why, and what was decided rather than deferred
again.

**The numbers could not move**, which shaped the fix. The Jaguar decommission
project (`~/workspaces/bgn/jaguar-decommission/`) names "SG101
Step 19" for the wiki retirement and declares a hard dependency edge into Step 21
**by number**. Renumbering would break another project's plan, so the restructure
is internal: five ordered phases inside the step, an idiom this plan already uses.

| Phase | What it is |
|---|---|
| **0 — Decide** | Six open questions, no code |
| **A — Delete-path safety** | The three items that can lose data |
| **B — Prune** | The step as originally designed |
| **C — Schema and data migrations** | Four migrations against real production data |
| **D — Cleanups** | Independent one-diff items, formatter last |

**Four ordering constraints, each with a reason rather than a preference:** A
before B, because bulk-deleting 1,540 legacy rows while a cascade hazard that has
already eaten a forum is live is the wrong order. `django-tagging` before the
collation decision's tag-cloud half, because that finding is about a table the
`ArrayField` option deletes. The formatter dead last, because it rewrites every
file — run early it formats code about to be deleted, run mid-step it gives every
later bisect two candidate causes. And the settings extraction before Step 20,
which will touch settings anyway.

**Phase 0 is the recommendation, not just the first phase.** It is an afternoon of
measuring and deciding, it needs Brian more than it needs an agent, and it
plausibly removes four to six items outright: the collation audit is already
measured and needs only a decision written down, the five `tools/` scripts are
likely "delete four, port one", and both the `banners`/`oembed` verification and
the timezone dropdown could legitimately close as "leave it". **Shrinking the step
before generating task files is much cheaper than generating tasks for work that
turns out not to exist.**

**Two items flagged as probably not belonging here at all.** The timezone dropdown
is explicitly quality rather than correctness — its own measurement found nothing
broken and nothing at risk, and "leave it" is one of the three answers on offer.
And the linter/formatter may want to be its own step between 19 and 20, since it
touches every file in the repo and nothing else here does.

**Task files: per phase, not per step.** So that what Phase A learns can change
Phase B.

## ORDER BY collation — audited 2026-08-13 (`4d5104a`, pushed), scheduled into Step 19

**Brian noticed `/profile/members/user/` listing members in a different order
than production, and asked whether it was collation. It is.** Row sets are
identical everywhere; this changes order, never membership or counts.

**The finding behind the finding: Step 11 task 02's collation audit was scoped to
lookups.** Its method was an AST scan of keyword arguments to
`get`/`filter`/`exclude`/`get_or_create` — which is what caught the 12
case-sensitivity bugs — so `ORDER BY` was never examined. A fresh AST sweep finds
**22 orderings on text columns, 14 of them `Meta.ordering`**, which is the half a
call-site grep could never show since it applies to every unordered queryset for
the model.

**The rule:** MySQL's `utf8_general_ci` gives punctuation a real sort weight by
code point (`-` at 0x2D before digits, `_` at 0x5F after every letter), while
PostgreSQL's `en_US.utf8` treats it as **ignorable at the primary level**, so
`-Bong-` sorts as "Bong" and `_mo_` as "mo". Both engines are case-insensitive,
so case is not the driver. Demonstrated on six strings against all three
collations rather than asserted.

**Measured on real data, same column both engines: 8 of 15 differ**, worst
`weblinks_link.title` at 1/571 positions identical, `auth_user.username` at
3,288/15,227 (22%). The 7 that match are exactly the columns with no leading
punctuation — country codes, spam phrases, file extensions. `-Bong-` moves from
page 1 of the member list to page 68; a download titled `"Yellow Jacket" Backing
Track` moves from #25 to #716 of 716.

**Recommendation recorded in `plan.md` under Step 19: keep PostgreSQL's ordering.**
It is cosmetic and deterministic, its answer is arguably better, and **`C` is not
the parity option it appears to be** — measured, it sorts by byte and is
case-*sensitive*, which would put every capitalised name ahead of every lowercase
one. Full table and reasoning in the plan; the glibc collation-version hazard
this raises for the deploy went into Step 21.

**Two measurement traps, both of which produced a wrong answer first.** `mysql -B`
escapes control characters where `psql -At` does not, so a news title containing
a literal tab read as a *data* difference between the engines until the escaping
was undone — a difference in the measurement, not the data, and the kind that
would have been written up as drift. And a `while read` loop feeding
`docker compose exec` silently processes only its first line, because `exec`
consumes the loop's stdin; redirect from `/dev/null`. That one produced a table of
fourteen "missing dump" rows before it produced anything true.

## PostgreSQL snapshots — `tools/pg_snapshot.sh`, added 2026-08-05

Shipped with the rung: `d482413` (4.2), `dfe53b4` (Redis cache), `d153249`
(planning), `efc8605` (this tool), `0961ad5` (the Step 21 Redis note) — **all
pushed to `modernize`, CI green on GitHub 2026-08-05**, the first CI run on
Django 4.2.

Brian's suggestion, after a scratch script deleted a forum during task 05 and
recovery ran through MySQL for an hour. `dump` / `list` / `restore` / `scratch`,
documented in DOCKER.md §8, with a "take one first" note added to the four
remaining Step 13 task files.

**The whole round trip was exercised, not just written**, because an untested
restore is not a restore:

| step | measured |
|---|---|
| `dump` | **8 s**, **128 MB** (database is 1,681 MB) |
| `restore` (full) | ~1 min, every row count identical afterwards |
| `reindex_search` | **1 m 35 s**, back to 516,858 documents |
| `reconcile_search` | clean |
| `smoke.py` after | 35/35 |

**The search index is dumped schema-only** (`--exclude-table-data`). It is
**1,104 MB of the 1,681 MB database** — two thirds — and it is derived. A stale
index is worse than an empty one, since `reconcile_search` would then report
drift to reason about rather than a rebuild to run.

**Custom format (`-Fc`) is the point**, not compression: it lets `pg_restore`
pull individual tables out of the archive. But a whole-table restore into a live
table collides on the rows still there, so the useful shape is `scratch` —
restore the tables into a scratch database beside the real one and `\copy` rows
across. Both databases sit in the same cluster, so that pipe carries every column
type intact, which is exactly what the cross-engine copy had to reconstruct by
hand. **Verified end to end** into a throwaway table: 5 rows, timestamps intact
with their offsets.

**Two things found while building it:**

- **`./snapshots` is mounted read-only into the `postgres` container**, so a dump
  cannot be written from inside it. Dumps stream out over `exec -T` stdout;
  restores read from the mount, which read-only permits.
- **Do not `source .env` to read two values out of it.** The file holds a
  `SECRET_KEY` containing `$8`, and sourcing under `set -u` aborts on it — the
  script would also be running whatever else the file contains as shell. It
  reads the two keys with `sed` instead.

**A full restore stops `web`/`worker`/`beat` first** — they hold connections and
those block the drops `--clean` performs — and starts them again after. It also
asks for the database name to be typed, since it is not reversible.

**The limitation worth stating plainly: a snapshot only helps if it is older than
the damage.** Today's deletion went unnoticed for an hour, and a snapshot taken
on noticing would have captured the loss. Hence the note in the task files: take
one at the start, not when something looks wrong.
