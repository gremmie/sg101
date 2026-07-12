# Idea Honing: Modernizing SG101

Requirements clarification through iterative Q&A.

## Q1: What does "done" mean for this project — what is the primary goal and scope?

Is the goal purely to get onto **supported, secure, maintainable infrastructure**
(current Python + current Django + modern hosting) with the site behaving
exactly as it does today? Or does "modernize" also include some amount of
**feature / UX / architecture change** (e.g., dropping dead features, replacing
the search stack, refreshing the front end, moving off MySQL, etc.)?

Considerations to weigh:
- Scope discipline: a pure "lift to modern stack, no behavior change" project is
  far lower risk and easier to test/verify than one that also changes behavior.
- But some legacy pieces (old search stack, custom `queues`, dead apps) may be
  *cheaper to remove than to port*, which argues for at least some pruning.

### Answer:
**(b) Lift + prune.** Modernize the stack (current Python / Django / hosting),
and allow *removing* dead or expensive-to-port legacy (e.g., the old search
stack, dead apps) where porting isn't worth it — but do **not** add new features
or do a broad UX/architecture refresh as part of this project.

Alternatives considered: (a) pure lift with zero behavior change (too rigid —
some legacy is cheaper to delete than port); (c) lift + prune + selective
refresh (out of scope for now — keep the project focused).

## Q2: Which apps/features are "sacred" (must keep) vs. suspected dead weight (prune candidates)?

Given the many local apps in the repo (forums, news, downloads, bio, weblinks,
potd, polls, membermap, bandmap, shoutbox, messages, comments, podcast,
gcalendar, wiki, ygroup, irc, contests, countdown, donations, banners,
bulletins, smiley, oembed, custom_search, antispam, legacy, tools, user_photos,
core, accounts) — which are core to the site's identity and must be preserved,
and which do you already suspect are unused / candidates for removal?

Also: are there known-legacy integrations that may already be dead (e.g., the
Yahoo group `ygroup`, `irc`, `gcalendar`, `oembed`, the `legacy` app) that we
should confirm and possibly drop rather than port?

### Answer:
- **`irc`** — not used. **Drop it.**
- **`gcalendar`** — **keep and revive** using newer libraries / updated Google
  API client (the old `google-api-python-client 1.3.1` + `oauth2client` stack is
  deprecated and must be replaced).
- **Search stack (haystack + xapian)** — **keep if possible.** Prefer to preserve
  django-haystack + xapian-haystack, but open to alternatives if the Python 3 /
  modern-Django port proves too painful.
- Remaining apps (`ygroup`, `oembed`, `legacy`, `countdown`, `contests`,
  `banners`, `bulletins`, `donations`, and the rest) not yet explicitly
  triaged — **verify actual usage during research** before deciding keep vs.
  prune. Default assumption: keep unless research shows it's dead or blocking.

## Q3: What's the testing strategy and "enough coverage" bar before you start upgrading?

You said step 1 is "increase unit test coverage." To plan this concretely:

- What is the **current** state of the test suite (does it run at all on Py2.7 /
  Django 1.9 today, and do you have any coverage numbers)?
- What's the **goal** — a hard coverage % (e.g., 70/80%), or a risk-based target
  (cover the critical paths: auth, forums, posting, permissions, payments/
  donations, search indexing) rather than a blanket number?
- Do you favor **fast unit tests**, higher-level **integration/functional tests**
  (Django test client hitting views/URLs end-to-end), or both? For a
  lift-and-shift, view/URL smoke tests often catch regressions more cheaply than
  deep unit tests.
- Is there any existing CI, or is testing run manually today?

### Answer:
1. **Unit tests do run**, but current coverage is unknown — **needs measuring**
   during research.
2. **Risk-based target** is the goal (cover critical paths thoroughly; accept
   lower coverage on peripheral apps rather than chasing a blanket %).
3. **Bias toward integration/functional tests** (Django test client hitting
   real URLs/views end-to-end), with **unit tests backfilling tricky logic**.
4. **No CI today.** Interested in setting one up but has no specific plan —
   needs a recommendation (this becomes a research/design topic).

**Critical constraint surfaced:** The dev machine (macOS, Python 3.14) **cannot
easily run Python 2.7** anymore. Older laptops could, but the primary machine
can't. This blocks running the legacy stack / test suite locally. A
**containerized (Docker) dev environment for the legacy Py2.7 + Django 1.9 +
MySQL stack** is likely a prerequisite for everything else — you can't grow
test coverage on a stack you can't run. This also ties into CI (the same
container can run tests) and hosting (containers inform the deployment target).

## Q4: Containerized dev environment — scope and comfort with Docker?

Since Py2.7 won't run natively on the main machine, a Docker-based dev
environment for the *legacy* stack looks like the true first step. To scope it:

- How comfortable are you with **Docker / docker-compose** today?
- The legacy environment needs: Python 2.7 + pinned deps, **MySQL**, likely
  **Redis** and **memcached**, and the **xapian** search index. Some deps come
  from **private hg/git repos** (`queues`, `django-elsewhere`, `xapian-haystack`
  pinned to old commits) and old versions that may no longer install from PyPI.
  OK with the plan including work to **vendor / mirror / pin** those for a
  reproducible build?
- Do you have a **production data snapshot** (or sanitized dump) to load into the
  dev DB for realistic testing, or do we need fixtures/seed data?
- Should this containerization **carry forward** into the Python 3 / modern stack
  (invest in a docker-compose setup that evolves), or is the legacy container
  **throwaway scaffolding** just to enable testing?

### Answer:
1. **Limited Docker experience** — will need help. Plan/design should include
   clear, well-commented Docker/docker-compose setup and explanation, not assume
   prior expertise.
2. **Reproduce the legacy build as faithfully as possible** in Docker;
   **willing to vendor/mirror/pin** deps only if problems arise (don't pre-emptively
   fork everything — try faithful reproduction first, fall back to vendoring).
3. **Production DB snapshots are easily available** — use a real (ideally
   sanitized) snapshot for realistic dev/test data rather than synthetic fixtures.
4. **Evolve it if worthwhile** — if Docker looks like a good choice to carry
   forward for future testing and/or deployment, design the compose setup to
   evolve across the migration rather than throwaway. Decide based on research
   into hosting (i.e., whether the target host is container-friendly).

## Q5: Hosting — what are the priorities and constraints for the new home?

You want off the aging Ubuntu 14.04 dedicated server and to avoid maintaining a
separate dedicated box. To steer the hosting research/design:

- **Budget** — Roughly what monthly cost is acceptable? (Current dedicated
  server cost is a useful anchor.) SG101 is a community site — is it funded by
  donations, out of pocket, or does it need to stay cheap?
- **Ops appetite** — On a spectrum from "fully managed PaaS, I never touch a
  server" (e.g., a platform that runs your container/app for you) to "a single
  managed VM I still admin but that's patched/modern" — where do you want to
  land? You said you'd rather *not* maintain a dedicated server, which points
  toward managed, but how far?
- **Provider preferences / constraints** — Any provider you already use, trust,
  or want to avoid (AWS, GCP, DigitalOcean, Hetzner, Fly.io, Render, Railway,
  a Platform-as-a-Service, etc.)? Any data-residency or account constraints?
- **Managed backing services** — Comfortable moving MySQL to a **managed
  database** (and Redis to a managed cache)? That removes a lot of the ops
  burden but may cost more and affect the DB engine choice.

Note two technical wrinkles that will constrain the options:
- **Xapian search needs a persistent local filesystem** for its index, which
  many stateless PaaS platforms don't provide well — this may force a specific
  hosting shape or a search rethink.
- **Media/user uploads** (photos, downloads) — the stack already includes `boto`,
  suggesting S3 is/was used; where files live affects the hosting choice too.

### Answer:
1. **Budget:** Funded by donations, ~**$94/month** typical. Willing to pay some
   **extra out of pocket**, but it's a **hobby project** — keep costs sane.
2. **Ops appetite:** Somewhat comfortable managing a dedicated server, but
   **interested in simpler/more-managed options** if the dedicated box isn't
   necessary.
3. **Provider:** Currently on **Linode** — but only their **dedicated VM**
   servers, not their cloud/managed products. **Prefers something simpler.**
   **Not interested in learning AWS** (no time). (Note: staying in the Linode/
   Akamai ecosystem — e.g., their managed DB, object storage, or a simpler
   managed compute option — may satisfy "simpler" without a new provider or the
   AWS learning curve; worth researching.)
4. **Managed backing services:** **Unsure** — needs options/recommendation.
5. **Search:** **Open to replacing Xapian**, but unsure — decision deferred to
   research (weigh porting xapian-haystack vs. alternatives that fit the chosen
   hosting shape, e.g., a managed/hosted search or a Postgres/DB-backed option).
6. **Media/uploads:** Previously used **S3 via boto**, but switched to **local
   storage on the dedicated server** because **Python 2.7's outdated TLS/secure-
   comms support** made S3 painful. **OK returning to S3 (or another hosted
   object store) during migration** — this pairs naturally with getting onto
   modern Python where TLS is no longer a problem, and with stateless hosting.

### AMENDMENT (2026-07-04, during research revisit):
The user is now **open to AWS** *if it opens up hosting options*, **provided
configuration stays simple**. This relaxes the earlier "no AWS" constraint.
Implication: keep to the **simple corner of AWS** (e.g., **Lightsail** — has a
Django blueprint, containers, and managed DB; predictable pricing — not raw
EC2/ECS/EKS). AWS notably makes **managed Postgres affordable** (RDS
`db.t4g.micro` ~$12–22/mo, or Lightsail managed Postgres from $15/mo) versus
Linode's ~$81/mo, and adds first-party **S3** (media) and **SES** (cheap email).
The **portable docker-compose architecture keeps provider choice late-binding**,
so this widens candidates (Linode VM, DigitalOcean, Render, **AWS Lightsail**)
without changing the design. "Simple config" remains the guardrail. See
`research/hosting.md`.

### AMENDMENT (2026-07-04, Cloudflare in the mix):
User already uses **Cloudflare** and is open to its ecosystem. Strong fits folded
into the design:
- **Cloudflare R2** for user media — S3-compatible (same `boto3` code via custom
  `endpoint_url`), **zero egress fees** (ideal for an image-serving community
  site), $0.015/GB, 10 GB free. Preferred over Linode Object Storage / S3.
- **Cloudflare Turnstile** to replace **reCAPTCHA** — free, unlimited, privacy-
  preserving; timely since reCAPTCHA moved to Enterprise (10k/mo free cap then
  paid). Official reCAPTCHA→Turnstile migration guide exists.
- **Cloudflare in front of the origin** (DNS/CDN/edge-TLS/DDoS) — simplifies the
  origin and makes the **DNS cutover** a fast low-TTL flip; complements any host.
- **Caveat:** Cloudflare **Email Routing is inbound-only** → still need a
  transactional email provider (Postmark/Brevo/SES) for outbound.
Also confirmed: DB engine migration sequenced **mid-ladder** — *not* an early
step, but *not* deferred to the very end either. Placement: **right after Django
3.2 LTS on Python 3**. The already-disabled search stack (Xapian/Haystack/
queued_search/queues) is **dropped early** (so native/private deps never need
Py3 porting); the **Postgres FTS replacement is built with the DB migration at
the mid-ladder step**. User clarified: fine tackling MySQL→Postgres sooner if it
helps retire Xapian/Haystack/queues — just not in one of the earliest steps.
User now understands **12-factor env-var config** (`os.environ` instead of
`secrets.json`).

## Q6: What's the target end-state (the finish line) for Django and Python?

The upgrade ladder needs a defined top rung. Options:

- **Django target:** The pragmatic choice for a hobby project is the **latest
  Django LTS** (long-term-support) release rather than the absolute newest,
  because LTS gets ~3 years of security fixes and lets you sit still afterward.
  As of mid-2026 that's around **Django 5.2 LTS** (with **4.2 LTS** as a possible
  intermediate resting point / fallback). Do you want to target the **latest
  LTS**, or ride **latest stable** and keep chasing releases?
- **Python target:** Land on a **currently-supported Python 3** (e.g., 3.11 or
  3.12 — both well-supported and compatible with modern Django). Any preference,
  or "whatever the target Django + hosting supports best"?
- **Resting points:** Are you happy to define **intermediate LTS checkpoints**
  where the site could safely run in production for a while if you need to pause
  the project (e.g., ship on 1.11 LTS → later 2.2 LTS → 3.2 LTS → 4.2 LTS →
  5.2 LTS), rather than one long march? This matters for a hobby project that may
  span months with interruptions.

### Answer:
1. **Target the latest Django LTS** (≈ 5.2 LTS as of mid-2026), and rest there
   applying only security updates afterward — not chasing latest-stable forever.
   4.2 LTS is an acceptable fallback/pause point.
2. **A modern, well-supported Python 3** is ideal (e.g., 3.11/3.12 — pick what
   the target Django + hosting support best).
3. **Yes — laddered approach with safe LTS resting points**, because this project
   may take a long time (months, with interruptions). Never be stranded on an
   unshippable version. Planned ladder:
   `1.9 → 1.11 LTS → 2.2 LTS (Python 3 migration happens here) → 3.2 LTS →
   4.2 LTS → 5.2 LTS`.
   Python 3 becomes mandatory at the 1.11 → 2.0 boundary, matching the original
   plan to migrate to Py3 "at the point where required."

   Design note: Django **1.11 is the last version supporting both Py2 and Py3**.
   Recommended technique — make the code Py2/Py3-compatible *while still on
   1.11*, switch the interpreter to Py3 (still on 1.11), then continue the Django
   ladder on Py3. Never change two big variables (Django major + interpreter) at
   once.

## Q7: Version control and CI platform — stay on hg, or move to git/GitHub?

You currently use **Mercurial (hg)**, with some deps pulled from a **private hg
server** (`queues` from `bobcat`). You also want CI but have no plan yet. These
are coupled, because most modern CI is git-centric.

- Are you open to **migrating the repo from hg to git** (e.g., hosted on
  **GitHub**), or do you want to **stay on Mercurial**? Staying on hg is
  possible but narrows CI options considerably; moving to git/GitHub unlocks the
  most common, free-for-small-projects CI (GitHub Actions) and simplifies pulling
  modern dependencies.
- If open to GitHub: is a **public** repo acceptable (SG101 is already an open
  hobby project with a LICENSE), or does it need to be **private**? (Public repos
  get unlimited free Actions minutes.)
- Where should **CI** run — GitHub Actions is the default recommendation if you
  move to git. Any preference or constraint?
- The **private-repo dependencies** (`queues`, `django-elsewhere`) will need a
  home the CI/build can reach. Are you OK **vendoring them into the repo** or
  mirroring them to the same host as the main project?

Note: this is the project already noted as being worked on the hg `modernize`
branch, so an hg→git move would need to preserve that history/work.

### Answer:
1. **Convert hg → git**, but **preserve branch history** (don't lose the
   `modernize` branch and other lines of work). Use a history-preserving
   conversion (e.g., `hg-fast-export` / `git-cinnabar`) rather than a flat import.
2. **GitHub is fine, public is acceptable** — user already has other public
   projects on GitHub.
3. **GitHub Actions** for CI (accepted recommendation).
4. **Vendoring is fine.** `django-elsewhere` may **already be forked on GitHub**
   by the user — confirm and reuse that fork. `queues` (from private `bobcat` hg)
   will need vendoring or its own GitHub home.

## Q8: Who's doing the work, how much time, and is there any urgency/deadline?

This calibrates step size and sequencing:

- **Team:** Is this a **solo** effort (just you), or are there other contributors/
  moderators who can help test or review? (Solo → the plan should favor small,
  self-contained, resumable steps.)
- **Time budget:** Roughly how much time can you put in — a few hours on
  weekends, evenings, bursts? (Affects how granular each step should be so you
  can stop/resume cleanly.)
- **Urgency:** Is there a **security or operational deadline**? Ubuntu 14.04.6
  reached end-of-standard-support in 2019 and end of ESM around 2024, so the
  current server is **running unpatched** — is that an active worry pushing for a
  faster hosting cutover, or is the box firewalled/low-risk enough that you can
  take the methodical laddered path without pressure?
- **Sequencing preference:** Given the two parallel tracks (code modernization
  vs. hosting), do you want to **fix hosting first** (get onto a modern, patched
  server running the *current* app to stop the security bleeding), **modernize
  the code first**, or **interleave**? There's a strong argument for re-hosting
  the legacy app early to eliminate the unpatched-OS risk, decoupled from the
  slower code ladder.

### Answer:
1. **Solo effort** (just the user). → Favor small, self-contained, resumable steps.
2. **Time:** some evenings, **mainly weekend bursts**; large uninterrupted blocks
   are rare. → Steps must be small enough to finish/checkpoint in a short session.
3. **Urgency:** The box is **low traffic**; user is **fine building the new system
   in parallel** with the existing one (no forced in-place cutover; a blue/green
   style parallel build is acceptable and preferred).
4. **Sequencing — RESOLVED (option B, refined):** **Modernize the code first,
   deploy hosting once at the end.** Rationale: the user does **not** want to pay
   for a second server to iterate on during a potentially months-long effort.

   Chosen approach:
   - **Leave the current production system in place, untouched**, on the old
     Ubuntu 14.04 box for the duration of the project.
   - **Do all modernization work locally on the Mac in Docker**, iterating up the
     Django ladder, testing against **production DB snapshots**.
   - **Provision the new host and cut over only near the end** (deploy-at-end),
     loading a fresh prod snapshot and switching DNS.

   **Accepted tradeoff (eyes-open):** the unpatched Ubuntu 14.04 box keeps running
   in production for the whole project. Acceptable because the site is low-traffic
   and the user is comfortable with the risk.

   **Design implications (baked into the plan):**
   - Build the **Docker setup for eventual production use from day one**
     (dev/prod parity, env-driven config), so the final deploy is not a separate
     productionization scramble.
   - Keep the **option to cut over at an intermediate rung** — since the container
     is deploy-ready throughout, the user isn't forced to wait until Django 5.2;
     they *may* deploy earlier (e.g., once on a modern Python + supported Django)
     to claim the security/hosting win sooner, then finish the ladder in prod.
     Default remains deploy-at-end.
   - **Hosting-shape research is lower-urgency but not skippable:** pick the
     strategy now, choose the actual provider/shape later, but research it early
     enough to ensure the container is built compatibly with the eventual target
     (esp. the xapian persistent-disk constraint).

## Q9: Database engine — stay on MySQL, or consider PostgreSQL?

You're on **MySQL** (mysqlclient). This question matters because it intersects
with three other decisions:

- **Search:** PostgreSQL has **built-in full-text search**. Moving to Postgres
  could let you **replace xapian/haystack entirely** with Django's native
  Postgres search (`SearchVector`/`SearchQuery`) — deleting a whole fragile,
  hard-to-host subsystem and solving the persistent-disk problem. That's very
  much in the spirit of "prune."
- **Hosting:** Managed Postgres is ubiquitous and cheap everywhere; it's often
  the best-supported managed DB on simpler platforms.
- **Django affinity:** Postgres is Django's best-supported database and unlocks
  fields/features MySQL can't do.

BUT — switching engines is a **real migration** (schema/data port, quirks around
data types, and the current low MySQL support cost). It also means changing two
things (engine + versions) so it must be **sequenced carefully** (ideally done at
a single deliberate step, not mid-Django-jump).

Options:
- **(a) Stay on MySQL** — least migration work now; keep xapian or find a
  MySQL-compatible search; upgrade MySQL server version as part of hosting.
- **(b) Move to PostgreSQL at a deliberate point** — more upfront work, but lets
  you delete the xapian/haystack search stack (using Postgres FTS), simplifies
  hosting, and aligns with Django best practices. Strong synergy with "prune."
- **(c) Defer/decide during research** — measure how entangled MySQL and xapian
  are in the code first, then choose.

### Answer:
**(c) Decide during research, leaning toward PostgreSQL** if it can simplify the
stack. Research must assess: (1) how MySQL-specific the current schema/queries
are; (2) how entangled and xapian-specific the search code is, and whether
**Postgres full-text search can replace xapian/haystack** without losing
important behavior; (3) the data-migration effort MySQL → Postgres. If Postgres
lets us delete the xapian/haystack/`queues` search subsystem and simplify
hosting, that's the preferred direction. If not, staying on MySQL is an
acceptable fallback. Engine switch (if chosen) is its own deliberate,
well-tested step — not folded into a Django version jump.

## Q10: What's the acceptance/verification bar per rung, and the rollback story?

Each step of the eventual plan needs a clear "this rung is done and safe" bar.

- **Per-rung acceptance:** Is it enough that (a) the **test suite passes** on the
  new Django/Python version and (b) the app **boots and serves key pages** in the
  container? Or do you also want a **manual smoke-test checklist** of critical
  user flows (log in, post to a forum, upload a photo, search, make a donation,
  admin) that you personally run each rung?
- **Deprecation handling:** As you climb, Django emits deprecation warnings for
  APIs removed in the *next* version. Do you want the plan to treat **resolving
  all deprecation warnings as part of each rung** (so the next jump is clean), or
  fix them lazily when they break? (Treating warnings-as-errors per rung is the
  disciplined path and pairs well with CI.)
- **Rollback:** Since work is local in git until the end, rollback during
  development is just version control. But for the **final production cutover**,
  what's your comfort: keep the **old box running as instant fallback** (flip DNS
  back) for some window after cutover? Any acceptable **downtime window** for the
  cutover itself (e.g., a maintenance window to do the final DB snapshot →
  restore → DNS switch)?

### Answer:
Agreed with the recommended approach:
- **Per-rung acceptance:** test suite passes on the new Django/Python **plus** a
  **short manual smoke-test checklist** of critical flows (log in, post to a
  forum, upload a photo, search, make a donation, admin) run by the user each rung.
- **Deprecations:** **clear all deprecation warnings as part of each rung**
  (CI-enforced, warnings-as-errors) so each next jump starts clean.
- **Cutover/rollback:** **Some downtime at the final cutover is acceptable** —
  a planned maintenance window (site read-only / "back soon") to do final DB
  snapshot → restore → DNS switch. **Keep the old box warm as instant fallback**
  (flip DNS back) for a week or two after cutover. No need for complex
  zero-downtime data sync.

## Q11: External services/integrations and secrets — what needs porting & re-wiring?

Modernizing and re-hosting means every external integration and secret has to be
accounted for. Based on the dependency list I can see, the site likely touches:
**email/SMTP** (registration, notifications), **donations/payments** (PayPal?),
**Google APIs** (gcalendar — being revived), **S3** (returning to it), **Redis +
memcached**, **antispam/CAPTCHA** (there's an `antispam` app — reCAPTCHA?), and
possibly others (`oembed`, podcast feeds, IRC being dropped).

- Which external services does the site **actually depend on today** that must
  keep working after migration? (I'll confirm specifics in research, but your
  knowledge is faster.)
- **Donations** — what processes them (PayPal IPN, Stripe, other)? Payment
  integrations are often the most fragile thing across a modernization and may
  need SDK/library updates.
- **Email** — how is mail sent today (local sendmail/postfix on the box, or an
  SMTP relay)? Moving off the dedicated server usually means switching to a
  **transactional email provider** (deliverability from a fresh host IP is poor),
  which is a real migration task.
- **Secrets management** — secrets presumably live in Django settings files today.
  Are you OK moving to **environment-variable-based config** (12-factor style),
  which is needed for clean Docker/prod parity and to keep secrets out of a now-
  public GitHub repo? (This also means auditing git history for committed
  secrets before going public.)

### Answer:
1. **Services that must keep working / desired:**
   - **Email — critical.**
   - **Google APIs — important**, to revive the `gcalendar` app (modern client libs).
   - **S3 — desired**, to stop hosting user files locally (pairs with modern Py3 TLS).
   - **Redis & memcached — important, but candidates to consolidate:** user asks
     whether they can be **combined**. → Yes: **Redis can serve as both cache and
     Celery broker**, letting us **drop memcached entirely** (prune win).
   - **CAPTCHA/antispam — desired, open to a better solution** (e.g., modern
     reCAPTCHA v3, hCaptcha, or Django honeypot/spam-filter approaches).
2. **Donations:** handled by **PayPal IPN**. (Note for research: PayPal IPN is
   legacy — PayPal now steers toward Webhooks/newer APIs — so this integration
   may need updating, not just porting. Confirm current PayPal support status.)
3. **Email:** currently sent via a **local mail server** on the box, which **has
   been a headache**. User is **open to alternatives** → strong case for a
   **transactional email provider** (better deliverability from a fresh host,
   removes a maintenance burden). Treat as explicit migration scope.
4. **Secrets:** currently an **uncontrolled `secrets.json`** (not in VCS) read by
   `settings.py`. User is **open to switching** if it helps with Docker →
   move to **environment-variable / 12-factor config** (works cleanly with Docker
   and a public repo). Still **audit git history** for any historically committed
   secrets before going public, and rotate anything exposed; `SECRET_KEY` and DB
   creds should move to env.

