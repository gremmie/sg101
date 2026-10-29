# Knowledge Base Index

**Generated 2026-10-21**, thirteen days after the cutover. Start here. This file
is designed to be the only one an assistant needs in context to know where to
look next.

## How to use this

1. Read the "Read this first" facts below — they are the ones most likely to
   make an assistant wrong if it assumes otherwise.
2. Pick the file that matches the question from the table.
3. For *why* something is the way it is, go to
   `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`. It is
   authoritative, and it records measurements, not just decisions.

## Read this first

- **This repo is what production runs.** Since the 2026-10-08 cutover the site
  is the Docker Compose stack in `docker-compose.prod.yml` on the host leopard,
  behind Cloudflare. **`main` is the deployed branch**; work happens on
  short-lived branches cut from it. The old host, jaguar (Python 2.7, Apache +
  `mod_wsgi`, MySQL), is frozen and is not where anything runs.
- **Python 3.12, Django 5.2 LTS, PostgreSQL 16, Redis, Celery, git.** gunicorn
  serves the application, behind Apache in its own container. Any document
  saying Python 2, Django 1.x, MySQL, `mod_wsgi`, Mercurial, `secrets.json`,
  Xapian or Haystack is describing jaguar or something older.
- **Deploys are `git pull`, then `make prod-up`** on leopard, or
  `make prod-deploy` when the pull carries migrations. `fabfile.py` is stale
  (`hg pull`) and is not the deploy path.
- **Two test runs, not one.** The suite, then the deprecation gate. See
  `workflows.md`; the gate script only prints a filter.
- **`.env` is the config surface.** No `secrets.json`. `.env.example` is
  committed and has working defaults.
- **The v3 stylesheet is a committed build artifact.** Change the Sass in
  `sg101/scss/`, run `make css`, commit both. Deploys do not build CSS.

## The files

| File | Consult it for |
|---|---|
| `codebase_info.md` | stack, repo layout, app inventory, what was removed |
| `architecture.md` | production's runtime shape, the client-IP path, settings modules, static files, search, dependency direction |
| `components.md` | what each app does, grouped by role; the `core` kernel; the host-side directories (`apache/`, `backup/`, `fail2ban/`, ...) |
| `interfaces.md` | URL prefixes, external services, the mail paths, **logging and its retention in production** |
| `data_models.md` | user/profile relationship, the email uniqueness constraint, split moderation models, rendered-HTML siblings, search index |
| `workflows.md` | dev setup, **the two test commands**, browser tests, CI, **deploying**, backups, the Sass build |
| `dependencies.md` | package versions, front-end libraries, what is deliberately absent |
| `review_notes.md` | what changed since the last generation, and what this one did not verify |

## Example questions and where they go

| Question | File |
|---|---|
| "How do I run the tests?" | `workflows.md` |
| "How do I deploy this?" | `workflows.md` |
| "Why does `assertLogs` see nothing?" | `workflows.md` |
| "Why is `REMOTE_ADDR` the real client?" | `architecture.md` |
| "Where does search indexing happen?" | `architecture.md`, then `components.md` |
| "Can I add an `is_approved` field?" | `data_models.md` (no — split models) |
| "How far back do the logs go?" | `interfaces.md` |
| "Who bans an address, and where?" | `components.md` (`fail2ban/`), `interfaces.md` |
| "Why was X done this way?" | `STATUS.md`, not this tree |

## Relationship to the planning record

This tree describes **what the code is**. `.agents/planning/` describes **how it
got that way and why**, with measurements attached. When the two disagree,
`STATUS.md` is the more reliable, because it is maintained continuously while
this tree is regenerated only occasionally. `AGENTS.md` at the repo root is
maintained by hand and is newer than this tree whenever they disagree.
