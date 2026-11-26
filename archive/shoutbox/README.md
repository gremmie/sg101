# The SurfGuitar101 shoutbox, shelved

The shoutbox was the one-line chat box in the sidebar of the site's old page
design. Members' shouts scrolled past on every page, and a history page listed
them all. It left the pages members see when the forums moved to the new
design, and the app was removed after this capture. This is every shout it
held, captured **2026-11-25** from production.

## What is here

| File | What it is |
|---|---|
| `shouts.json` | all 1,894 shouts, 2011-02-26 to 2026-11-11, by 332 members |
| `MANIFEST.json` | the count, date range, byte count and SHA-256 of `shouts.json` |

Each entry is one shout, in Django's `dumpdata` format:

| Field | What it is |
|---|---|
| `pk` | the shout's id; the old history page linked shouts as `/shout/view/<id>/` |
| `user` | the author's username, as a one-item list |
| `shout_date` | when it was posted, in UTC |
| `shout` | the text as typed |
| `html` | the text as the site rendered it, with smileys and links |

## How it was made

On the production host, against the code then deployed:

```
docker compose -f docker-compose.prod.yml exec -T web \
    python manage.py dumpdata shoutbox.Shout --natural-foreign --indent 2
```

`--natural-foreign` writes each author as a username rather than a user id, so
the archive reads correctly on its own and after accounts are deleted. The
shout count taken at the export was 1,894, and the file holds 1,894.

## What was left out, and why

This repository is public, so the archive holds only what the site already
showed publicly.

- **The flags.** Members could report a shout to the moderators. Who reported
  what was never public, so the flags were not exported and were dropped with
  the tables.
- **Four email addresses.** Shouts 116, 667, 757 and 1854 (2011 to 2018) each
  gave a member's email address, as text and as a `mailto:` link. Each is
  replaced with `[email removed]`; the rest of those shouts is as posted.
  `MANIFEST.json`'s SHA-256 is of the redacted file.

Nothing else was changed. The shouts hold no IP addresses.
