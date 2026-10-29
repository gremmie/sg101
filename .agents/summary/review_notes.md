# Review Notes

**Generated 2026-10-21**, for Step 21 task 10 requirement 7: the summary
regenerated after the cutover, so that it describes production as it runs.

## Why this regeneration happened

The 2026-08-27 generation described a codebase that had not been deployed.
Since then, 771 files changed outside `.agents/`, most of it the deployment
itself: `docker-compose.prod.yml`, the `Makefile`, and the host-side
directories `apache/`, `backup/`, `fail2ban/`, `firewall/`, `logrotate/` and
`msmtp/`, none of which existed. The cutover put that stack in production on
2026-10-08.

## Claims dropped as false

| The 2026-08-27 claim | Now |
|---|---|
| Apache + `mod_wsgi` in front of Django | gunicorn behind Apache in its own container; `RealClientIP` takes the client address the second hop |
| CI on `modernize` only; `main` is legacy history | CI on every branch; `main` is deployed |
| Deployment is Step 21 and has not happened | live since 2026-10-08 |
| Settings `local.py`, `docker.py` | `dev.py` and `production.py`, one per deployment; `logging_config.py` builds `LOGGING` |
| `wiki` mints a cookie for MoinMoin | the app is gone; content archived under `archive/wiki/` |
| `tagging` app | gone; news tags are a PostgreSQL array |
| registration is multi-stage, without Turnstile | one page, with Turnstile |
| `User.email` is not unique | unique on `LOWER(email)`, blanks exempt |
| `gcalendar` carries a stub | a service-account client pushing approved events |
| `contact/forms.py` passes no HTTP timeout | the form is on Turnstile; reCAPTCHA is retired |
| `sg101.log` holds ~5 months | that was jaguar; on leopard it holds **about three weeks** |

## Claims carried forward, re-verified

| Claim | Verified |
|---|---|
| `messages` collides with `django.contrib.messages` | `sg101/apps.py`, `INSTALLED_APPS` |
| split moderation models | `downloads`, `weblinks`, `news` |
| rendered HTML in sibling fields | `core/markup.py` and the model fields |
| the deprecation gate prints a filter only | `tools/deprecation_gate.sh`, `Makefile` |

**One carried-forward claim failed its re-check: "`core` imports nothing
in-repo".** A grep of `core`'s non-test modules for imports of every project
app finds four that do: `markup.py` (`smiley`), `tasks.py` (`accounts`, inside
a function), `templatetags/core_tags.py` (`bio`) and
`templatetags/custom_admin_tags.py` (seven apps). All four were present on
2026-08-27, when both this tree and `AGENTS.md` called `core` import-free; the
`smiley` import dates from 2015. The claim was never measured. What holds is
narrower — `core`'s library modules import no app — and that is what the
documents now say.

## Found while regenerating

- **The forums are not on the post box yet.** A commit subject ("every post
  box on the modules") reads as if every posting form moved; the forum
  templates still load markItUp. `components.md` says so.
- **Two page designs coexist.** 26 templates still extend the old `base.html`
  (forums, shoutbox, `ygroup`, the flatpage template) against 56 on
  `v3/base.html`. An agent changing a template has to know which.
- **`AGENTS.md`'s log-retention line was jaguar's**, not production's. See
  `interfaces.md`, measured on leopard 2026-10-21.

## Known gaps

- **Per-app detail is shallow for the long tail.** `forums`, `elsewhere` and
  `news` carry real complexity that is summarised in a line or two. Read the
  models directly when working in them.
- **The host is described from the repo, not audited.** What is installed on
  leopard (systemd units, `/etc` files) was compared with the repo only where
  the 2026-10-21 watch reading had already looked: logrotate and the backup
  unit.
- **The edge is partly outside the repo.** Cloudflare's request-buffering
  rule, WAF settings and Email Routing exist only in the Cloudflare dashboard.
  `AGENTS.md` names the buffering rule; nothing else here can verify them.
- **`donations`' PayPal IPN integration was not verified** against PayPal's
  current API.
- **Transitional state will date fastest**: the two page designs and the
  forum editor change with the V3 forums project.

## Not verified, and deliberately not asserted

- Whether every `tools/` script still runs. This regeneration saw
  `cloudflare_block_list.py`, `dmarc_fetch.py` and `dmarc_report.py` run on
  2026-10-21, and CI runs `deprecation_gate.sh` on every push; the rest were
  not run.

## Recommendations

1. **`README.md`'s Deployment section is stale.** It still says deploying "has
   not happened yet". It is user-facing prose, so it was left out of this
   regeneration and needs its own edit.
2. **`fabfile.py` and `tools/xapian_installer.sh` should go**; both are named
   as stale in `AGENTS.md` and nothing uses either.
3. **Regenerate after the V3 forums project retires `base.html`**, the largest
   change still pending in what this tree describes.
