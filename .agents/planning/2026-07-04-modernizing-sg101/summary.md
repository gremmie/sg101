# Summary: Modernizing SG101 — Planning Complete

**Date:** 2026-07-04 · **Method:** Prompt-Driven Development (`/agent-sops:pdd`)

This document wraps up the planning process that turned a rough idea into a
detailed design and an actionable, test-driven implementation plan.

## Artifacts produced

```
.agents/planning/2026-07-04-modernizing-sg101/
├── rough-idea.md              # original concept + observed starting state
├── idea-honing.md             # Q1–Q11 requirements Q&A + amendments
├── STATUS.md                  # process tracker + resume notes
├── summary.md                 # this document
├── research/
│   ├── codebase-and-coverage.md   # inventory, Py2→3 surface, Celery jobs, tests
│   ├── app-triage.md              # per-app keep/prune/revive/verify verdicts
│   ├── search-stack.md            # Xapian/Haystack analysis; Postgres FTS plan
│   ├── database-migration.md      # MySQL→Postgres analysis & tooling
│   ├── upgrade-path.md            # LTS ladder + dependency modernization map
│   ├── docker-strategy.md         # containerization & dev/prod parity
│   ├── hosting.md                 # hosting shapes, costs, Cloudflare, email
│   └── vcs-migration.md           # hg→git, going public, CI design
├── design/
│   └── detailed-design.md         # standalone design (R1–R29, C1–C10, diagrams)
└── implementation/
    └── plan.md                    # 21 numbered TDD steps + progress checklist
```

## Design overview

Modernize SG101 from **Django 1.9 / Python 2.7 / MySQL** on an unpatched Ubuntu
14.04 dedicated server to **Django 5.2 LTS / Python 3.12 / PostgreSQL**, re-hosted
on modern late-bound infrastructure — **lifting and pruning** (no new features).

Core strategy:
- **Containerize the legacy stack** (only way to run Py2.7 on the modern Mac).
- **hg→git + GitHub Actions CI + a characterization-test safety net** before upgrading.
- **Climb the LTS ladder** `1.9 → 1.11 → 2.2 → 3.2 → 4.2 → 5.2`, switching to
  Python 3 on Django 1.11 (the last dual-runtime version).
- **Remove the fragile search stack early** (Xapian/Haystack/queued_search/queues,
  already disabled); **swap MySQL→Postgres and build Postgres FTS mid-ladder**
  (after 3.2, on Py3).
- **Modernize subsystems:** media→**Cloudflare R2** (zero egress), email→a
  transactional provider, CAPTCHA→**Cloudflare Turnstile**, revive `gcalendar`,
  fold memcached into Redis, secrets→env vars, boto→boto3.
- **Deploy once at the end** behind Cloudflare, with the old box as fallback.

## Implementation plan overview

**21 steps in 6 phases**, each a working/shippable/demoable increment:
- **A. Foundation** (1–5): Docker, git/CI/coverage, env-var config, prune dead
  code, safety-net tests.
- **B. Python 3 crossing** (6–8): →1.11, dual-runtime, flip to Py3.
- **C. Modern LTS + engine swap** (9–12): →2.2, →3.2, MySQL→Postgres, Postgres FTS.
- **D. Finish the ladder** (13–14): →4.2, →5.2 (target).
- **E. Subsystems** (15–19): R2 media, email, Turnstile, gcalendar, final pruning.
- **F. Ship** (20–21): production hardening + Cloudflare, deploy + cutover.

The site is shippable at every rung; work is small-step and resumable for a solo,
weekend-burst cadence. An optional early cutover is possible after Step 14.

## Suggested next steps

1. **Review** `design/detailed-design.md` and `implementation/plan.md`.
2. **Begin Step 1** (Dockerized legacy environment) — the enabler for everything.
   Consider using the `code-task-generator` / `code-assist` SOPs to execute steps.
3. When you start Step 1, **load a production DB snapshot** and resolve the early
   decisions (Postgres vs. Xapian, DB charset/case-sensitivity findings).
4. Track progress via the checklist at the top of `implementation/plan.md`.

## Areas that may need further refinement
- **Open decisions to resolve in-flight:** Postgres-vs-Xapian & DB specifics
  (Step 1 snapshot), peripheral-app prune + MoinMoin retirement (Step 19), and
  the final **hosting provider/shape** and **email provider** (Steps 20–21).
- **PayPal IPN longevity:** confirm PayPal still supports classic IPN, or plan a
  move to Webhooks (affects the donations work in Step 7 / later).
- **Optional data migrations:** `django-tagging`→`taggit` and picklefield→JSON are
  flagged but not mandatory — decide whether to include.
- **Front-end asset pipeline** (gulp/bower) is out of scope per R1 but is aging;
  revisit only if it blocks a rung.
- **Step granularity:** the Django-rung steps (esp. 9, 13) may each warrant
  splitting into smaller sessions in practice.
