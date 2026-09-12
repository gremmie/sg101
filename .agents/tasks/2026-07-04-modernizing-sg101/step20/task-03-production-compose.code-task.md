# Task: A Production Compose Stack, Apache Included

## Description
Add a production compose file that runs the application, worker, beat,
PostgreSQL, Redis and the Apache reverse proxy with production settings, health
checks and restart policies — and without the MySQL service the development stack
still carries.

## Background
There is one compose file today, `docker-compose.yml`, and it is development
shaped. Its services are `db` (MySQL), `postgres`, `redis`, `web`, `worker` and
`beat`. The MySQL service is still present because the conversion chain is
retained deliberately, gated on decommissioning the old box — that retirement is
Step 21's, not this task's, but the production stack has no reason to carry it.

### DECISION: the proxy is a service in this stack, not a host daemon

**Recorded so it can be reversed deliberately.** An earlier draft of this step put
Apache on the host. That was wrong for three reasons, and the decision is Apache
*in the compose stack*:

1. **No host exists yet.** The host *shape* was decided 2026-08-15 — a single VM
   with persistent disk — but nothing is provisioned, and the project's sequencing
   is *"do everything locally, deploy once at the end."* A host-daemon proxy makes
   this step unexercisable until Step 21.
2. **`docker-strategy.md` always said so:** the prod compose is *"gunicorn + a
   reverse proxy (nginx/Caddy) or the platform's router."*
3. **The configuration travels with the code**, which is the exact complaint the
   plan makes about jaguar: the working `remoteip.conf` there *"is not in the repo
   and does not travel with the code."* Putting Apache on the new host repeats it.

**The one argument that would have favored a host daemon does not apply.** A
host-level proxy earns its place when several sites share a box. The jaguar
decommission project is capturing the other sites as static mirrors bound for
Cloudflare Pages, so **this VM is single-purpose.**

**fail2ban does not need the proxy to be a host service.** It bans by pushing
addresses into a Cloudflare IP list that a WAF rule drops at the edge — an API
call, not local packet filtering. It needs to *read an access log*, which a bind
mount provides. Step 21 owns fail2ban; this task owns making the log reachable.

### Traffic, measured — why container overhead is not a concern

From jaguar's `/svr/www/surfguitar101.com/log/access.log`, **572,177 requests over
6.3 days**, 2026-09-06 06:48 → 2026-09-12 14:09 local:

| | Rate |
|---|---|
| Average | **~1.05 req/s** |
| Busiest hour (09-10 17:00) | 5,062 req/hr = **~1.4 req/s** |
| Busiest minute (09-08 13:18) | 506 req/min = **~8.4 req/s** |

Bridge-network NAT costs tens of microseconds per packet. At these rates it is
immaterial, and **Apache will do less work than it does today** — it currently
runs `mod_wsgi` with Python embedded in its workers, and becomes a pure reverse
proxy here.

**Three overhead notes that are worth acting on anyway**, none of them about CPU:

- **Bind-mount I/O is slow under Docker Desktop on macOS and native on the Linux
  VM.** Local `/media` serving will feel sluggish and production will not. Do not
  read a slow local test as a production problem.
- **Do not send the access log to the json-file driver.** Bind-mount it to a host
  path instead — unbounded growth avoided, and fail2ban needs that path anyway.
- **Set `EnableSendfile` explicitly** rather than inheriting a default, given the
  overlay filesystem underneath.

### The base image and how config reaches it

**Use a Debian/Ubuntu image with the distro `apache2` package, not the official
`httpd` image.** The two have different config layouts — `httpd` keeps a single
`/usr/local/apache2/conf/httpd.conf` plus `conf/extra/`, with no `conf-enabled`
and no `a2enmod` — and jaguar's configuration is Debian-shaped. Matching the
layout is what lets `conf-enabled/remoteip.conf` port verbatim instead of being
rewritten, and a rewritten security boundary is one that has to be re-verified.

Only two of jaguar's enabled files are this site's: `conf-enabled/remoteip.conf`
and `sites-enabled/surfguitar101.com.conf`. The rest are distro defaults or other
vhosts that are not moving.

**Deliver the config by bind mount, not by `COPY` into the image.** The repository
is checked out on the VM already, since that is how compose runs. A bind mount
makes a proxy fix an edit plus `apachectl -k graceful`, rather than an image
rebuild and redeploy — which is worth a great deal on cutover day specifically.

**The cost of that choice, and it is one this project has already paid once.** A
bind mount means the running configuration is whatever is on disk at that path,
which can silently diverge from what is committed. That is exactly the
`USER_PHOTOS_LOCAL_UPLOAD = True` story: an uncommitted edit to `production.py`
that ran in production for roughly 20 months and would have disappeared on a fresh
clone. **The cutover runbook's A2 working-copy audit must therefore cover the
Apache configuration too**, not only the Django settings.

**`sg101/apache/` currently holds one file, `sg101.wsgi`**, which gunicorn makes
redundant. Decide deliberately whether the new configuration takes that directory
over or whether it retires with `mod_wsgi`.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§3.2 target state; C10 production hardening & deployment)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/docker-strategy.md`
  (*Dev vs. prod parity* — the build-locally sequencing this decision rests on)
- `.agents/planning/2026-07-04-modernizing-sg101/research/hosting.md`
  (Shape 1 — the single VM this stack targets)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add a production compose file running `proxy` (Apache), `web` (gunicorn),
   `worker`, `beat`, `postgres` and `redis`, and no MySQL service.
2. Base the proxy service on a Debian/Ubuntu image using the distro `apache2`
   package, so jaguar's config layout ports rather than being rewritten.
3. Keep the Apache configuration in this repository and deliver it by bind mount,
   not baked into the image. State where in the tree it lives, and whether
   `sg101/apache/` is reused or retired.
4. Publish 443 and 80 from the proxy service only; `web` must not be reachable
   from outside the compose network.
5. Bind-mount the Apache access and error logs to a host path, so fail2ban can
   read them in Step 21 without the json-file driver in the way.
6. Run with `DEBUG` off and production settings, reading configuration from the
   environment as Step 3 established.
7. Give every service a health check that fails when the service is genuinely
   unusable, not merely when the process is absent.
8. Set restart policies appropriate to an unattended VM, and make proxy config
   changes a reload rather than a restart.
9. Document how the stack is started, stopped and reloaded, in `DOCKER.md`.
## Dependencies
- Task 01 — the `prod` image target and production settings
- Task 02 — gunicorn as the entry point
- Task 05 — Redis memory policy, which this file's `redis` service must carry

**Not a dependency, deliberately: task 04.** This task stands the proxy service up
with a minimal working configuration — reverse proxy to gunicorn, TLS, logs on a
bind mount. Task 04 then adds the `mod_remoteip` substance to that configuration.
Listing 04 here would make the two circular; the order is 03 then 04.

## Implementation Approach
1. Derive the production file from the existing compose file, removing rather
   than duplicating what does not belong.
2. Add the proxy service with its config and log mounts.
3. Add health checks that exercise the service — a database connection, a Redis
   ping, an HTTP request through the proxy to the application.
4. Start the stack against a restored snapshot and confirm the site serves,
   rather than confirming the containers are up.
5. Record the start/stop/reload procedure where the cutover runbook can reference
   it.

## Acceptance Criteria

1. **The production stack serves the site through Apache**
   - Given the production compose file and a restored database snapshot
   - When the stack is started and a page requested on 443
   - Then Apache serves it from gunicorn and `DEBUG` is off

2. **No MySQL service is present**
   - Given the production compose file
   - When its services are listed
   - Then `db` is absent and only `postgres` provides a database

3. **The application is reachable only through the proxy**
   - Given the running stack
   - When gunicorn's port is probed from the host
   - Then the connection is refused, and the same request through Apache succeeds

4. **Access logs land on a host path**
   - Given the running stack
   - When a request is served
   - Then the access line appears in the bind-mounted file, in a format fail2ban
     can parse

5. **Health checks detect a broken service, not just a missing process**
   - Given a running stack
   - When PostgreSQL is stopped
   - Then the database health check reports unhealthy and the dependent services
     report it

6. **Config changes reload without dropping connections**
   - Given a live request stream against the proxy
   - When the Apache configuration is reloaded
   - Then no request fails

7. **The procedure is written down**
   - Given `DOCKER.md`
   - When the production section is read
   - Then starting, stopping, reloading and inspecting the stack are documented

## Metadata
- **Complexity**: Medium
- **Labels**: Docker Compose, Apache, Deployment, Health Checks, Production Hardening
- **Required Skills**: Docker Compose, Apache configuration, service health checking
