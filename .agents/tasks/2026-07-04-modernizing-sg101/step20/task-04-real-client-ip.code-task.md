# Task: Restore the Real Client IP Behind Cloudflare

## Description
Configure the Apache proxy service to rewrite the client address from
`CF-Connecting-IP`, so that every application that reads `REMOTE_ADDR` keeps
recording the visitor rather than the Cloudflare edge. This is a stated
prerequisite of Step 21's fail2ban rebuild.

**This task is exercisable locally.** The proxy is a service in the compose stack
(task 03), so the rewrite is built and verified against the local stack. Nothing
here waits on a provisioned VM.

## Background
**Behind a proxy, `REMOTE_ADDR` is the proxy unless something rewrites it, and
Django does not do this itself.** Six applications read `REMOTE_ADDR` directly —
`antispam`, `accounts`, `forums`, `comments`, `downloads`, `donations` — and every
one of them is correct today only because of host configuration that does not live
in this repository.

**jaguar already solves it**, in `/etc/apache2/conf-enabled/remoteip.conf`,
verified against Cloudflare's published list on 2026-08-21 with no drift. The
whole file is three directives, read 2026-09-12:

```apache
RemoteIPHeader CF-Connecting-IP

RemoteIPTrustedProxy 173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18 108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17 162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22

RemoteIPTrustedProxy 2400:cb00::/32 2606:4700::/32 2803:f800::/32 2405:b500::/32 2405:8100::/32 2a06:98c0::/29 2c0f:f248::/32
```

**15 IPv4 CIDRs and 7 IPv6 CIDRs**, matching the count the plan records. Task 03
chooses a Debian-based image precisely so this ports as a file rather than being
rewritten into another server's syntax.

**It is reproduced here as a starting point, not as the answer.** It is evidence
about 2026-08-21; requirement 3 below is what makes it current.

**The trusted-range list is the security boundary, not the header name.** Without
it the header is client-supplied and anyone can claim any address. A list carrying
only the IPv4 ranges fails open for IPv6 clients, which is the silent-wrong-answer
version of this bug.

**Why the ordering is load-bearing.** Between 2025-06-19 and 2025-08-10 the host
saw only Cloudflare edge IPs, and enabling fail2ban in that state would have
banned Cloudflare. Step 21 rebuilds fail2ban's edge blocking; this task is what
makes that safe, so it must land first.

**DECISION, recorded so it can be reversed deliberately: Apache, not nginx.** The
plan states the requirement proxy-agnostically and names `ngx_http_realip_module`
only as an example; `research/docker-strategy.md` still lists the proxy choice as
open. Apache is chosen because a verified working configuration already exists for
exactly this requirement, and because fail2ban's existing jail filters are
log-format specific.

**A second decision: origin TLS uses a Cloudflare Origin CA certificate** rather
than Let's Encrypt — long-lived, no renewal job, and only trusted for proxied
traffic. **Installing that certificate needs the provisioned VM and is deferred to
the cutover runbook.** This task runs on a self-signed certificate locally, which
is sufficient for everything it verifies: `mod_remoteip` does not care which
certificate terminated the connection.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step 20,
  *the real-client-IP rewrite*, which states the requirement and the jaguar config
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *Cloudflare dated,
  and 35% of the layer measurement had no client IPs*, for what the 52-day window
  cost

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Configure the Apache proxy service from task 03 as a reverse proxy to
   gunicorn, with `mod_wsgi` playing no part.
2. Enable `mod_remoteip` with `RemoteIPHeader CF-Connecting-IP` and
   `RemoteIPTrustedProxy` covering **both** Cloudflare's IPv4 and IPv6 ranges.
3. **Re-verify the range list against Cloudflare's published list at the time of
   implementation.** The 2026-08-21 check is evidence about that date, not this
   one.
4. Set `SECURE_PROXY_SSL_HEADER` so Django knows the request arrived over TLS, and
   `CSRF_TRUSTED_ORIGINS` for the scheme-qualified origins Django 5 requires.
5. Terminate TLS at the proxy, using a self-signed certificate locally. The
   Cloudflare Origin CA certificate is a cutover-runbook item, not this task's.
6. Serve `/media` from the VM's disk through Apache; static files stay with
   WhiteNoise.
7. Keep the configuration in this repository so it travels with the code — the
   stated reason the jaguar configuration was lost to the plan — delivered by
   bind mount as task 03 establishes.
8. **Because it is bind-mounted, the running file can drift from the committed
   one.** Add the Apache configuration to the cutover runbook's A2 working-copy
   audit, which today covers only the Django settings.

## Dependencies
- Task 02 — gunicorn listening for the proxy to reach
- Task 03 — the compose stack that carries the Apache service and mounts this
  configuration
- Cloudflare's published IP range list, fetched at implementation time

## Implementation Approach
1. Fetch Cloudflare's current IPv4 and IPv6 ranges and diff them against the
   list recorded in the plan; record the result either way.
2. Port `remoteip.conf` from jaguar, extending rather than retyping it.
3. Add the Django proxy settings, and a test that asserts what `get_ip()` returns
   under a trusted and an untrusted peer.
4. Verify from a real request, reading what the application recorded — not by
   reading the configuration back.

## Acceptance Criteria

1. **A proxied request records the client address**
   - Given a request arriving from a Cloudflare range with `CF-Connecting-IP` set
   - When the application reads `REMOTE_ADDR`
   - Then it is the client address from the header, not the peer

2. **A spoofed header from an untrusted peer is ignored**
   - Given a request from an address outside the trusted ranges carrying a
     `CF-Connecting-IP` header
   - When the application reads `REMOTE_ADDR`
   - Then it is the peer address and the header is disregarded

3. **IPv6 clients are covered**
   - Given a request arriving over one of Cloudflare's IPv6 ranges
   - When the application reads `REMOTE_ADDR`
   - Then the client address is recorded, proving the IPv6 ranges are trusted

4. **Django knows the request was secure**
   - Given a request arriving over TLS terminated at the proxy, self-signed
     locally
   - When `request.is_secure()` is evaluated
   - Then it is true, and CSRF checks accept the site's own origins

5. **The range list was verified, not assumed**
   - Given Cloudflare's published list at implementation time
   - When it is compared with the configured ranges
   - Then they match exactly, and the comparison is recorded with its date

6. **The six readers are covered by tests**
   - Given the applications that read `REMOTE_ADDR`
   - When the suite runs
   - Then tests assert the address they observe under a proxied request

## Metadata
- **Complexity**: High
- **Labels**: Apache, Cloudflare, Reverse Proxy, Security, Production Hardening
- **Required Skills**: Apache configuration, mod_remoteip, Django proxy settings, TLS
