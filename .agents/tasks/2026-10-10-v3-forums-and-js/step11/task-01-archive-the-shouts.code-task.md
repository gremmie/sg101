# Task: Archive the shouts

## Description
Export every shout from production and commit it to `archive/shoutbox/`,
with a README and a manifest, before the shoutbox's tables are dropped.
**Brian runs the export on leopard.** This session prepares the commands,
checks the file he brings back, and writes the archive's README and manifest.

## Background
**The shoutbox is already invisible to members.** Only the old `base.html`
includes its widget, and since forums release 3 the only templates extending
`base.html` are the shoutbox's own. But the app is installed, `/shout/` is
mounted with seven routes (the history and single-shout pages still render
every shout; the `shout`, `edit`, `delete` and `flag` endpoints still accept
POSTs from signed-in members), and its two tables still hold their data. Step
11 archives the data, drops the tables, and removes the code.

**What the archive holds: shouts only (Brian, 2026-11-25).** The repository
is public. A `Shout` is `user`, `shout_date`, `shout` (the text) and `html`
(rendered): what the site showed publicly, with no IP or email address. A
`ShoutFlag` records which member reported which shout, which members never
saw; flags are not exported and go with the tables. The design's `dumpdata
shoutbox` (§4.5, item 1) is narrowed to `shoutbox.Shout` accordingly.

**`--natural-foreign`** writes each shout's author as a username, not a bare
user id, so the archive still reads correctly after accounts are deleted. On
dev (data to 2026-10-07) there are 1,890 shouts and no flags; production
will have more shouts.

**The export command, for Brian on leopard** (from `/svr/sg101`):

```
docker compose -f docker-compose.prod.yml exec -T web \
    python manage.py dumpdata shoutbox.Shout --natural-foreign --indent 2 \
    > shoutbox.json
docker compose -f docker-compose.prod.yml exec -T web \
    python manage.py shell -c "from shoutbox.models import Shout; print(Shout.objects.count())"
```

`-T`, not `make prod-manage`: that target runs `exec` without it, so with a
terminal attached the JSON would come back through a TTY with CRLF line
endings. Brian copies the file to the Mac (`scp`) and gives this session the
count; check that the JSON parses, that it holds that many
`shoutbox.shout` objects, and that every `user` is a username.

**The archive's shape follows `archive/wiki/`**: the data, a README saying
what it is, when and how it was taken, and what was left out (the flags, and
why), and a `MANIFEST.json` with the row count, the date range, and the
file's byte count and sha256. Don't quote shouts in the README.

**`.agents/` and the archive are public**, so nothing here quotes an email
address or an IP. Usernames are fine (AGENTS.md).

**Branch.** Step 11 ships on one branch cut from `main`; the plan's
placeholder is `retire-shoutbox`.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5, items 1–3)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 11)
- `archive/wiki/` (the precedent: its README and `MANIFEST.json`)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Hand Brian the export and count commands above.
2. The JSON he brings back parses, holds exactly the count he measured, and
   names every author by username.
3. `archive/shoutbox/` holds the JSON, a README and a `MANIFEST.json`.
4. No flag, email address or IP is in the archive.

## Dependencies
- Brian's access to leopard.

## Implementation Approach
1. Cut the branch from `main`. Hand Brian the commands; stop until he returns
   the file and the count.
2. Check the file, then write the README and manifest.
3. Leave the archive unstaged for Brian's review.

## Acceptance Criteria

1. **Every shout is archived**
   - Given production's shout count, measured at the export
   - When the archive's JSON is counted
   - Then it holds the same number of shouts

2. **The archive reads on its own**
   - Given `archive/shoutbox/`
   - When it is opened without the database
   - Then each shout names its author, and the README says what was kept and left out

3. **Nothing private is archived**
   - Given the archive
   - When it is searched for flags, email addresses and IPs
   - Then none is found

## Metadata
- **Complexity**: Low
- **Labels**: shoutbox, archive, production data
- **Required Skills**: Django dumpdata, JSON
