# Task: Seed `elsewhere` from a Data Migration, and Decide What Is Left Worth Seeding

## Description
`elsewhere` seeds its `SocialNetwork` and `InstantMessenger` tables from a
`post_migrate` receiver that re-runs on **every** `migrate` in every
environment. Replace it with a real data migration, the way the rest of this
project's seeded data works.

Two decisions have to be taken before the seed list can be written down, and an
audit run 2026-09-05 says both of them are live questions rather than
formalities: **42 of the 57 seeded social networks have never been used by a
single member, and every one of the five instant-messenger services in use is a
service that no longer exists.**

## Background

### What is there now
`elsewhere/management.py` registers a `post_migrate` receiver that loops over
`default_social_networks` and `default_im_networks` in
`elsewhere/default_list.py` (440 lines) calling `get_or_create()`. The app has
two migrations, `0001_initial` and an `alter` — the seed data has never been in
one.

This is Step 11 leftovers: `elsewhere` was one of the 21 apps whose initial
migration was backfilled, and the deeper rework was deferred, first to "Step 11
or 19" and then settled as 19.

### The audit, run against production 2026-09-05
Brian asked whether the canned choices still correspond to services that exist.
They largely do not.

**Social networks — 57 seeded, 15 ever used**, 327 rows across 222 members:

| network | rows | | network | rows |
|---|---|---|---|---|
| `facebook` | 181 | | `flickr` | 3 |
| `twitter` | 51 | | `lastfm` | 3 |
| `youtube` | 47 | | `foursquare` | 2 |
| `myspace` | 15 | | `redbubble` | 1 |
| `tumblr` | 9 | | `github` | 1 |
| `linkedin` | 8 | | `multiply` | 1 |
| `reddit` | 3 | | `goodreads` | 1 |
| | | | `pandora` | 1 |

**42 of 57 have never been used by anyone.** Facebook alone is 55% of all rows.

**Instant messengers — 6 seeded, 5 used**, 19 rows across 18 members:
`msn` 7, `skype` 6, `gtalk` 3, `aim` 2, `y` 1.

**Every service in that second table is gone.** MSN Messenger, AIM, Google Talk
and Yahoo Messenger all shut down years ago, and Microsoft retired consumer
Skype in 2025. There is no live service in the IM half of this app.

**Separate the measured from the assessed.** The row counts above are measured.
*Which services still exist* is an assessment — `multiply` shut down in 2013 and
`myspace` is not the thing those URLs point at any more, but `lastfm`,
`goodreads` and `github` are alive and well. Anything acted on should be checked
rather than assumed, and the check is cheap: the stored `url` templates are
fetchable.

### Decision 1 — what goes in the seed list
A data migration makes the seed list an explicit, versioned artifact, which is
the moment to decide what belongs in it. Three defensible answers:

- **Seed all 57**, unchanged. Faithful, and preserves the option of a member
  picking one of the 42. Also writes 42 dead choices into a migration.
- **Seed only what is used** (15 social, 5 IM). Nothing existing breaks —
  `network_id` is a `CharField` holding a slug, so an unseeded network's rows
  still store and still render as long as the row exists.
- **Seed what is used and still alive.** Smallest and most useful list, and the
  only one requiring a live check of each URL.

**This is not the agent's call.** Present the audit and the three options and
take Brian's answer, the way Phase 0's six questions were taken.

### Decision 2 — the IM half
19 rows, 18 members, five dead services. The options are to keep it, to stop
offering IM on the profile form while leaving existing rows readable, or to
retire the half of the app entirely. **Also Brian's call**, and it should be put
as its own question rather than folded into the first.

### Decision 3 — `network_id` → FK, the smallest of the three
`SocialNetworkProfile.network_id` and `InstantMessengerProfile.network_id` are
indexed `CharField(max_length=16)` holding a slug of the network's name, with no
referential integrity. The plan carries "possibly `network_id`→FK" and never
settled it.

The measurement that decides it is whether every stored `network_id` resolves to
a seeded network. If it does, the FK is a schema tidy-up; if it does not, the FK
would either fail to build or silently drop rows, and the orphans have to be
dealt with first. **Measure before choosing.** Note that this interacts with
decision 1: seeding fewer networks creates orphans that do not exist today.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase C]` block on the `elsewhere` rework
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS-archive-steps-01-15.md` —
  Step 11 task 04's carried-forward list, where this was deferred and why
- `elsewhere/management.py`, `elsewhere/default_list.py`, `elsewhere/models.py`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **Put the three decisions to Brian before writing the seed list**, one at a
   time, with the audit figures attached. Record the answers in `STATUS.md` as a
   decision record, in the shape Phase 0 used.

2. **Replace the `post_migrate` receiver with a data migration** in
   `elsewhere/migrations/`. The receiver and its registration go; check whether
   anything else imports `elsewhere.management` before deleting it.

3. **The migration must be safe on a database that already has the rows**, which
   every existing environment does — the receiver has been creating them on every
   `migrate` for years. `get_or_create` semantics or an explicit existence check,
   not a blind insert.

4. **Reversible**, and the reverse must not delete a network a member is using.

5. **Do not change what members see without saying so.** If the seed list
   shrinks, an existing profile row whose network is no longer seeded must still
   render, or the change must be shown to Brian as a display change before it
   ships — this site's convention is that display changes are his call.

6. **Settle `network_id`→FK on the measurement**, and if the FK is taken, do it
   in the same migration file series with the orphan handling stated.

7. **The icons are part of the data.** `elsewhere/static/` holds the icon files
   named by `default_list.py`. If the seed list shrinks, decide whether the
   orphaned icons go too, and do not leave a seeded row pointing at a file that
   was deleted.

## Dependencies
- Production read access for the audit refresh (the figures above are 2026-09-05)
- `tools/pgloader/convert.sh` and `post_convert.py` for snapshot verification
- Brian, for three decisions — this task cannot be completed without them

## Implementation Approach

1. Re-run the audit against current production so the decisions are taken on
   fresh numbers, and check the URL templates of any network proposed for
   retention.
2. Put the three decisions, record the answers.
3. Write the data migration for whatever list was chosen; remove the
   `post_migrate` receiver.
4. Measure `network_id` orphans against the chosen seed list, then take or
   decline the FK.
5. Verify on a freshly converted snapshot, and confirm the 327 social rows and
   19 IM rows still render on the profiles that carry them.

## Acceptance Criteria

1. **The seeding is a migration, not a signal**
   - Given a fresh database
   - When `migrate` runs
   - Then the chosen networks exist, and no `post_migrate` receiver in
     `elsewhere` fires

2. **Existing databases are not disturbed**
   - Given a database that already holds the 57 social and 6 IM rows
   - When the migration runs
   - Then no duplicate row is created and no in-use network disappears

3. **Members' existing entries still render**
   - Given the 327 social and 19 IM profile rows in production
   - When a member's profile page is rendered after the migration
   - Then every entry that rendered before still renders

4. **The decisions are recorded, not implied**
   - Given the completed task
   - When `STATUS.md` is read
   - Then the seed-list decision, the IM decision and the FK decision each appear
     with their reasoning and their date

5. **Reversible without data loss**
   - Given the migration has run
   - When it is reversed
   - Then no network row that a member's profile refers to has been deleted

6. **The FK decision rests on a measurement**
   - Given the chosen seed list
   - When `network_id` values are checked against it
   - Then the count of unresolvable values is known and recorded, and the FK is
     taken or declined on that number

7. **No icon is referenced but missing**
   - Given the seeded rows after the migration
   - When each `icon` is resolved against `elsewhere/static/`
   - Then every referenced file exists

8. **Verified on a freshly converted production snapshot**
   - Given a pristine dump converted by `tools/pgloader/convert.sh`
   - When `post_convert.py` runs the chain
   - Then it completes without error and the profile rows are intact

9. **The suite is green and the tests are mutation-verified**
   - Given the full test suite under the deprecation gate on `docker_test`
   - When it is run in the container
   - Then it passes, and each new assertion has been observed to fail against a
     deliberate mutation

## Metadata
- **Complexity**: Medium
- **Labels**: elsewhere, data migration, seeding, post_migrate, audit, Step 19 Phase C
- **Required Skills**: Django migrations and signals, data modelling, SQL aggregation
