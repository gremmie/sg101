# Knowledge Base Index

**Generated 2026-08-27.** Start here. This file is designed to be the only one
an assistant needs in context to know where to look next.

## How to use this

1. Read the "Read this first" facts below — they are the ones most likely to
   make an assistant wrong if it assumes otherwise.
2. Pick the file that matches the question from the table.
3. For *why* something is the way it is, go to
   `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md`. It is
   authoritative, and it records measurements, not just decisions.

## Read this first

- **Python 3.12, Django 5.2 LTS, PostgreSQL 16, git.** Any document saying
  Python 2, Django 1.x, MySQL, Mercurial, `secrets.json`, Xapian or Haystack is
  stale. `README.md` currently says several of these.
- **The repo is mid-modernization.** Steps 1-16 done, Step 17 in progress. Some
  subsystems are transitional — both reCAPTCHA and Turnstile settings exist
  right now. Check `STATUS.md` before assuming which is live.
- **Two test runs, not one.** The suite, then the deprecation gate. See
  `workflows.md`; the gate script only prints a filter.
- **`.env` is the config surface.** No `secrets.json`. `.env.example` is
  committed and has working defaults.
- **`fabfile.py` is stale** — it still runs `hg pull`. Deployment is Step 21 and
  has not happened.

## The files

| File | Consult it for |
|---|---|
| `codebase_info.md` | stack, repo layout, app inventory, modernization status |
| `architecture.md` | runtime shape, dependency direction, search design, settings inheritance, the `mod_remoteip` dependency |
| `components.md` | what each app does, grouped by role; the `core` kernel; the `messages` app collision |
| `interfaces.md` | URL prefixes, external services, the mail path, **logging and its retention limits** |
| `data_models.md` | user/profile relationship, split moderation models, rendered-HTML siblings, search index |
| `workflows.md` | dev setup, **the two test commands**, test gotchas, CI, deployment status |
| `dependencies.md` | package versions, what is deliberately absent |
| `review_notes.md` | known gaps in this documentation and what was not verified |

## Example questions and where they go

| Question | File |
|---|---|
| "How do I run the tests?" | `workflows.md` |
| "Why does `assertLogs` see nothing?" | `workflows.md` |
| "Where does search indexing happen?" | `architecture.md`, then `components.md` |
| "Can I add an `is_approved` field?" | `data_models.md` (no — split models) |
| "Why is `REMOTE_ADDR` trusted?" | `architecture.md` |
| "How far back does the log go?" | `interfaces.md` |
| "Why was X done this way?" | `STATUS.md`, not this tree |

## Relationship to the planning record

This tree describes **what the code is**. `.agents/planning/` describes **how it
got that way and why**, with measurements attached. When the two disagree,
`STATUS.md` is the more reliable, because it is maintained continuously while
this tree is regenerated only occasionally — this generation replaced one that
had been wrong for six weeks.
