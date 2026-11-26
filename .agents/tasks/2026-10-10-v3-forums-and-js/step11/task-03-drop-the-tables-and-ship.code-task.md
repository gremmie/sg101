# Task: Drop the shoutbox tables and ship the removal

## Description
Ship step 11 in the order that keeps production consistent: the archive
committed and checked, then the tables dropped on leopard while the deployed
code still has the app, then the removal merged and deployed. Then check the
live site and record it.

## Background
**The order** (design §4.5, items 1–3; the flatpages removal, `fdb9b5f5`,
#33, went the same way):

1. **The archive is committed** (task 01), and its count matched production's
   at the export.
2. **Re-count, then drop the tables.** On leopard, against the code still
   deployed, Brian runs:

   ```
   docker compose -f docker-compose.prod.yml exec -T web \
       python manage.py shell -c "from shoutbox.models import Shout; print(Shout.objects.count())"
   make prod-manage cmd="migrate shoutbox zero"
   ```

   If the count differs from the archive's, members shouted between the
   export and now (the endpoints still accept POSTs): re-export (task 01)
   before dropping. `migrate shoutbox zero` drops `shoutbox_shout` and
   `shoutbox_shoutflag` and removes the app's row from `django_migrations`.
   It must run before the removal deploys: once the app is gone, Django can't
   unapply its migration.
3. **Merge, CI, deploy.** `main` merged into the branch, pushed, CI green;
   `main` fast-forwarded after Brian says to, CI green; Brian deploys with
   `git pull` and `make prod-up`. The removal adds no migration.

**Brian runs everything on leopard.** This session doesn't ssh there.

**Between steps 2 and 3**, the deployed code still has the app and its URLs,
but its tables are gone: a request to `/shout/` errors (500) until the
deploy. Keep the gap short; nothing links there.

**After the deploy, check live**: `/shout/` and `/shout/view/history/` answer
404, and the admin dashboard, the home page and the forums render. (No page a
member can reach uses the old `base.html` any more, so its shoutbox lines
can't be checked live; the tests cover them.)

**Record in `STATUS.md`**: the export's count and date, the re-count before
the drop, the drop, the deploy, and Brian's live check. Tick step 11 in
`implementation/plan.md`. Delete the branch when Brian says to.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§4.5)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 11 demo)
- .agents/planning/2026-07-04-modernizing-sg101/cutover-runbook.md § D9 (deploys)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. The tables are dropped only after the archive is committed and the
   re-count matches it.
2. The removal deploys only after the drop.
3. The full suite passes under the gate; CI green on the branch and on
   `main`.
4. `STATUS.md` records the counts, the drop, the deploy and the live check;
   step 11 is ticked.

## Dependencies
- Tasks 01 and 02.

## Implementation Approach
1. Confirm the archive is committed and pushed; hand Brian the re-count and
   the drop; stop for his results.
2. Run the full suite under the gate; tick the step; write `STATUS.md`; leave
   the docs unstaged for review.
3. Merge `main` in, push, check CI; fast-forward `main` when Brian says to,
   check CI; Brian deploys and checks live; record it; delete the branch when
   he says to.

## Acceptance Criteria

1. **Nothing is lost**
   - Given the archive's count and the re-count before the drop
   - When they are compared
   - Then they match, or the archive is retaken first

2. **The drop precedes the removal**
   - Given the deploy
   - When `STATUS.md` is read
   - Then the drop is recorded before it

3. **The shoutbox is gone live**
   - Given the deployed removal
   - When `/shout/` and `/shout/view/history/` are requested
   - Then each answers 404, and the dashboard and forums render

## Metadata
- **Complexity**: Low
- **Labels**: shoutbox, release, production
- **Required Skills**: Django migrations, Docker Compose, git
