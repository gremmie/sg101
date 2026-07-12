# Review Notes

Notes from generating and cross-checking this documentation set. No
language-support gaps apply here — the entire codebase is Python, which
is fully supported by the analysis tooling used.

## Corrections made during review

- Initially guessed the `elsewhere` third-party app powered
  cross-posting/sharing. Verified via `grep` that it actually backs the
  "elsewhere" section of a user's `bio` profile (social network/IM/
  website links) — corrected in [components.md](components.md) and
  [dependencies.md](dependencies.md).
- Initially attributed Celery integration to a `django-celery` package.
  No such package appears in `requirements.txt`; only `celery` + `kombu`
  are present. Corrected in [architecture.md](architecture.md).
- Added the `irc` app's Redis-based channel-roster read
  (`irc/channel.py`) to [interfaces.md](interfaces.md) after noticing it
  during the models survey — it's an external integration point (an
  IRC bot outside this repo writes the `irc:channel_members` key) that
  wasn't captured in the first pass.

## Known documentation gaps

- **Management commands are not individually catalogued.** Nearly every
  app has a `management/commands/` directory (e.g. `forums/forum_cleanup`,
  `bio/avatar_cleanup`, `donations/donations_report`,
  `legacy/import_old_*` — a whole family of one-time phpBB migration
  commands). [workflows.md](workflows.md) and [components.md](components.md)
  mention the ones invoked by Celery tasks, but a full command-by-command
  reference was judged too granular/volatile for this documentation set.
  If you need to know what a specific management command does, read it
  directly — `grep -rn "class Command" <app>/management/commands/`.
- **Frontend/static asset structure is not documented.** `static/`
  (`css/`, `js/`, `themes/`, `store/`) and the templating conventions in
  `sg101/templates/` + per-app `templates/<app>/` directories exist but
  weren't analyzed in depth — this docset is backend/architecture
  focused. The `V3_DESIGN` context flag set by `HomePageView`/`StoreView`
  (`sg101/views.py`) suggests an in-progress or dual frontend design
  system worth investigating if you're doing frontend work.
- **Test coverage is uneven across apps.** Tests exist for roughly half
  the apps (see the `tests/` or `tests.py` list found during the survey);
  apps like `bandmap`, `bulletins`, `contests` (partial), `polls`,
  `smiley`, `countdown`, and several others have no test directory at
  all. Not called out per-app in the docs since this is more of a
  project-health observation than an architectural fact.
- **`legacy` app's exact migration scope** (phpBB → this Django app) is
  inferred from filenames (`phpbb.py`, `html2md.py`, the
  `import_old_*` management commands) rather than fully read
  line-by-line. Treat [components.md](components.md)'s description of
  `legacy` as a reasonable summary, not an exhaustive one.
- **`legacy/tools/tz.py` and other one-off `tools/` scripts** are listed
  by filename in [components.md](components.md) but their internals
  weren't read — they appear to be scripts run once for historical data
  migrations rather than ongoing operational tools.

## Consistency check

Cross-referenced app names, model class names, URL prefixes, and
settings keys mentioned in `architecture.md`, `components.md`,
`interfaces.md`, `data_models.md`, `workflows.md`, and `dependencies.md`
against each other and against the source — no remaining contradictions
found as of this generation. If the codebase changes significantly,
re-run this SOP rather than hand-editing individual generated files, to
avoid drift between them.
