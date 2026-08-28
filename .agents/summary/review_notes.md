# Review Notes

**Generated 2026-08-27.**

## Why this regeneration happened

The previous generation was written in one commit on **2026-07-12**, during
Step 1. Between then and now the codebase changed by **638 files, ~23,000
insertions and ~6,300 deletions**; four apps were removed (`custom_search`,
`irc`, `legacy`, `membermap`) and five added (`.github`, `elsewhere`, `search`,
`snapshots`, `tagging`).

Ten of the eleven documents still described Python 2, Django 1.8, Mercurial,
MySQL, memcached, Xapian/Haystack or `secrets.json`. They did not describe a
drifted codebase; they described one that no longer exists.

**The most harmful content was the most confident.** The old `AGENTS.md`
"Non-obvious things" section told agents `secrets.json` was required and that
the `queues`/`queued_search` system was live — both removed in Steps 3 and 4.
Those are precisely the claims an agent acts on without checking.

## Claims carried forward, each re-verified

| Claim | Verified |
|---|---|
| `messages` app collides with `django.contrib.messages` | yes — `sg101/apps.py:7-8`, `base.py:158` |
| `wiki` has no models | yes — no `models.py` in `wiki/` |
| Split moderation models | yes — `downloads`, `weblinks`, `news` |
| Rendered HTML in sibling fields | yes — `core/markup.py` and the model fields |

## Claims dropped as false

`secrets.json` required · Mercurial · Python 2 / Django 1.8 · MySQL ·
`custom_search` and the `queues`/`queued_search` system · Xapian/Haystack search
· "no CI pipeline and no linter config" (CI now exists; the linter half is still
true).

## Known gaps

- **Per-app detail is shallow for the long tail.** `elsewhere` (13 models) and
  `forums` (9) carry real complexity that is summarised in a line each. An agent
  working in them should read the models directly.
- **`gcalendar` carries a Step 8 stub** whose current state was not examined;
  Step 18 revives it.
- **Frontend/static assets were not analysed.** Templates, CSS and JS are
  described only where they bear on a documented behaviour.
- **`donations`' PayPal IPN integration was not verified against PayPal's
  current API.** The planning record flags it as a legacy API.
- **Transitional state will date fastest.** The reCAPTCHA/Turnstile overlap is
  true on 2026-08-27 and will not be true for long.

## Not verified, and deliberately not asserted

- Whether `tools/` scripts beyond those named in `STATUS.md` still run.
- Whether the `snapshots` app is developer tooling or user-facing — its name and
  the `tools/pg_snapshot.sh` script suggest the former, but this was not
  confirmed, so no claim is made in the other documents.

## Recommendations

1. **`README.md` is worse than `AGENTS.md` was.** Its setup steps instruct a new
   contributor to create `secrets.json` and run MySQL, and its stack section is
   wrong in six particulars. It was deliberately left out of this regeneration
   because it is user-facing prose; it needs a decision, not a generator.
2. **`fabfile.py` should go or be marked**, since it runs `hg pull --update`.
3. **A `CODEASSIST.md` would pay for itself** — the two test commands and this
   project's scratchpad/commit conventions are rediscovered on every code-assist
   run.
4. **Regenerate after Step 21**, not before. Steps 17-21 are comparatively small
   deltas; the expensive churn is already behind this generation.
