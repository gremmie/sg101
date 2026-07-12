# Research: Hosting Options

**Status:** Options + preliminary recommendation (web-verified pricing, July
2026). Final provider choice is **low-urgency** (deploy-at-end) but the *shape*
must be settled early enough to build the container compatibly.

## Constraints (from requirements)
- **Budget:** ~$94/mo donations + some out-of-pocket; hobby project → keep it modest.
- **Ops:** wants *simpler* than a hand-built dedicated box; somewhat comfortable
  managing a server.
- **AWS:** *(amended 2026-07-04)* now **open to AWS if it opens options, as long
  as configuration stays simple** — i.e., the *simple corner* (Lightsail),
  not raw EC2/ECS/EKS.
- **Incumbent:** Linode (Akamai) dedicated VMs today.
- **Workload:** Django web + Celery worker + Celery beat + Redis + a database +
  object storage for media + transactional email. (Xapian's persistent-disk need
  goes away if we adopt Postgres FTS.)

## Key cost finding (reshapes the decision)

**Managed PostgreSQL on Linode/Akamai starts at ~$81.60/mo** (1-node, 4 GB) —
that alone nearly consumes the entire donation budget. So **fully-managed DB on
Linode is out**; either self-host Postgres in a container or use a cheaper
managed-DB provider.

Linode is still attractive for two cheap building blocks:
- **Object Storage** (S3-compatible): **$5/mo** min (<250 GB), $0.02/GB — a clean,
  no-AWS home for user/forum photos via `boto3`/`django-storages`. Keeps us in the
  Linode ecosystem.
- **Compute VMs** from ~$5–24/mo.

Sources: [Linode/Akamai review & pricing 2026](https://betterstack.com/community/guides/web-servers/linode-akamai-review/),
[Akamai managed databases](https://www.akamai.com/lp/managed-databases).

## Two realistic hosting shapes

### Shape 1 — Single modern VM + docker-compose  ⭐ (cheapest, closest to current)
- A current **Ubuntu LTS** VM on Linode (or DigitalOcean) running the prod
  docker-compose: app + worker + beat + **Postgres (container)** + **Redis
  (container)**, behind Caddy/nginx (auto TLS via Let's Encrypt).
- Media → **Linode Object Storage**; email → transactional provider (below).
- **Cost:** ~$24/mo VM + $5 object storage + $0–15 email ≈ **$30–45/mo**.
- **Pros:** cheapest; you keep Linode; xapian-or-Postgres both viable (has a
  disk); reproducible/disposable (unlike today's bespoke box) — the "simpler"
  comes from containerization, not from a new platform. Modern auto-patched OS.
- **Cons:** still "a server" you patch (but far less bespoke); you own Postgres
  backups (scriptable: `pg_dump` to object storage).

### Shape 2 — Managed PaaS (Render)  (most hands-off)
- **Render**: web service + background worker + cron (for beat) + **managed
  Postgres** + **Key Value/Redis**, git-deploy or Docker, predictable pricing,
  accessible to teams new to containers. Media → Render disk/object storage or
  Linode Object Storage; email → transactional provider.
- **Cost:** roughly **$25–60/mo** depending on instance sizes + managed Postgres
  tier (Render Postgres is far cheaper than Linode's managed DB).
- **Pros:** no server to patch; managed DB backups; simplest ops; **requires
  Postgres FTS** (no persistent local disk for Xapian — reinforces the search
  decision). Git-push deploys pair well with the GitHub move.
- **Cons:** more new concepts than a VM; costs scale with add-ons; some vendor
  lock-in. Alternatives in the same class: **Railway** (usage-based),
  **DigitalOcean App Platform** (managed PG/Redis + Spaces object storage +
  persistent volumes).

Sources: [Django hosting options 2026 (LearnDjango)](https://learndjango.com/tutorials/django-hosting-deployment-options),
[Python hosting compared 2026](https://www.nandann.com/blog/python-hosting-options-comparison),
[Render alternatives 2026 (DigitalOcean)](https://www.digitalocean.com/resources/articles/render-alternatives).

### Shape 3 — AWS, kept simple (Lightsail)  *(added after "open to AWS" amendment)*
AWS is now on the table if kept simple. The **simple corner of AWS** that fits:
- **AWS Lightsail** — AWS's predictable-price, DO/Linode-style tier. Has a
  **Django blueprint**, **Lightsail Containers**, and **managed databases**
  (PostgreSQL from **$15/mo**, Micro 1 GB). Instances from $3.50–5/mo. Real bills
  land ~$35–90/mo with DB + snapshots. Two sub-shapes:
  - a Lightsail **instance** running the prod docker-compose (like Shape 1), or
  - **Lightsail Containers** running the app + worker + beat services.
- **Managed Postgres, affordable:** **RDS `db.t4g.micro` ~$12–22/mo** — far
  cheaper than Linode's ~$81/mo managed DB — or Lightsail's $15/mo managed DB.
  This removes the earlier "managed DB is unaffordable" blocker.
- **S3** for media (native, mature; `boto3`/`django-storages`) and **SES** for
  transactional email (very cheap; must leave the sandbox + verify domain).
- **Watch-outs (to preserve "simple"):** **avoid App Runner as the sole
  compute** — it's fine for the web process but has no clean **Celery
  worker/beat/cron** model (AWS Celery guides fall back to EC2+systemd or
  Beanstalk). Prefer a Lightsail instance running docker-compose (all processes
  in one place) or Lightsail Containers. Avoid ECS/EKS/Terraform-heavy setups —
  they violate the simplicity guardrail. IAM/SES sandbox are the main new
  concepts to learn.

Sources: [AWS Lightsail pricing 2026](https://cloudburn.io/blog/amazon-lightsail-pricing),
[Lightsail features (Django blueprint)](https://aws.amazon.com/lightsail/features/),
[RDS db.t4g.micro pricing](https://instances.vantage.sh/aws/rds/db.t4g.micro),
[Django on App Runner vs EC2 w/ Celery](https://dev.to/yokwejuste/deploying-a-django-app-ec2-vs-app-runner-with-external-celery-2pne).

## Cloudflare ecosystem (user already uses Cloudflare)

Cloudflare fronts the site today, so several of its products slot in cleanly and
are **provider-neutral** (work with any origin shape above):

- **R2 (object storage)** for user media — **S3-compatible** (boto3 with a custom
  `endpoint_url`), **zero egress fees** ($0.015/GB storage, 10 GB + 1M/10M ops
  free tier). For an **image-heavy community site**, zero egress is a real
  ongoing saving vs. S3/Linode Object Storage (which bill egress). **Preferred
  media store.**
- **Turnstile** — free, unlimited, privacy-preserving **CAPTCHA** replacing
  reCAPTCHA (which is now reCAPTCHA Enterprise: 10k/mo free then paid). Official
  reCAPTCHA→Turnstile migration guide. Drop-in for the `antispam` app.
- **DNS + CDN + edge TLS + DDoS/WAF** — already in use; fronting the origin means
  the origin can stay simple (CF terminates TLS, caches static/media), and the
  **final DNS cutover is a fast low-TTL flip** with the old box as fallback.
- **Caveat — email:** Cloudflare **Email Routing is inbound forwarding only**; it
  does **not** send outbound transactional mail. Still need Postmark/Brevo/SES.

Sources: [Cloudflare R2 pricing (zero egress)](https://developers.cloudflare.com/r2/pricing/),
[R2 vs S3](https://www.cloudflare.com/pg-cloudflare-r2-vs-aws-s3/),
[Turnstile](https://www.cloudflare.com/products/turnstile/),
[reCAPTCHA→Turnstile migration](https://developers.cloudflare.com/turnstile/migration/recaptcha/).

## Transactional email (replaces the local mail server)

Moving off the dedicated box tanks deliverability from a fresh IP → use a
provider. Modest volume (registration, notifications) fits free/cheap tiers:

| Provider | Free tier | Notes |
|----------|-----------|-------|
| **Postmark** | ~100/mo free, then ~$15/mo | **Best inbox placement** in 2026 tests (~83%); great for transactional |
| **Brevo** | **300/day (~9k/mo)** free | Most generous free tier; transactional + marketing |
| Mailgun | trial then paid | EU/US regions, validation |
| Amazon SES | very cheap | but it's AWS (user wants to avoid) |

Sources: [Best transactional email services 2026 (EmailToolTester)](https://www.emailtooltester.com/en/blog/best-transactional-email-service/),
[Email API pricing July 2026](https://www.buildmvpfast.com/api-costs/email).

Recommendation: **Postmark** (deliverability) or **Brevo** (free volume) via SMTP
or API through Django's email backend. Use a dedicated sending subdomain +
SPF/DKIM/DMARC.

## Preliminary recommendation  *(updated after "open to AWS" amendment)*

The **portable docker-compose architecture makes provider choice late-binding**,
so all three shapes remain open; the container is built identically for any of
them (12-factor config, object storage for media, Postgres). Ranking for *this*
project (hobby budget + simple ops):

1. **Shape 1 — single modern VM + docker-compose** (Linode **or** AWS Lightsail
   instance): cheapest, simplest mental model (one box, all processes incl. Celery
   worker/beat), you keep full control. ~$30–45/mo. **Top pick for cost + Celery
   simplicity.** Works on Linode today or Lightsail if consolidating on AWS.
2. **Shape 2 — Render** (managed PaaS): most hands-off; native worker + cron for
   Celery; managed Postgres cheaper than Linode's. Requires Postgres FTS. ~$25–60/mo.
3. **Shape 3 — AWS Lightsail + RDS/S3/SES**: viable now that AWS is allowed;
   **RDS makes managed Postgres affordable (~$12–22/mo)** and S3/SES are mature.
   Keep to Lightsail (not App Runner-only, not ECS/EKS) to stay simple.

- **Managed-DB blocker resolved:** affordable managed Postgres now exists (RDS
  ~$12–22/mo, Lightsail $15/mo, Render's tier) — the only expensive option was
  Linode's own managed DB (~$81/mo), which we simply don't use.
- **Object storage:** Linode Object Storage ($5/mo) *or* AWS **S3** — both
  S3-compatible via `boto3`; pick to match the chosen provider.
- **Email:** Postmark or Brevo (provider-neutral) or **SES** if consolidating on AWS.

Final choice deferred until near deploy time. **Decision needed later:** pick a
provider/shape (recommend Shape 1 on Linode or Lightsail) and whether to
consolidate media/email onto the same cloud (S3/SES) or keep them independent.

## Open items
- Confirm current dedicated-server monthly cost (budget anchor).
- Confirm DNS/registrar + TLS approach (Let's Encrypt via Caddy/nginx, or platform-managed).
- If Shape 1: define Postgres backup routine (`pg_dump` → object storage, retention).
