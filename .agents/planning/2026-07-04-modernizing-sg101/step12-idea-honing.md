# Step 12 — Idea Honing: PostgreSQL full-text search (restore `/search/`)

Requirements clarification for Step 12, following the same one-question-at-a-time
process as the parent project's `idea-honing.md`. Decisions here feed
`research/` and the Step 12 section of `implementation/plan.md`; the build itself
gets code-task files under `step12/`, as Step 11 did.

## Recovered prior behavior (not from memory — from surviving artifacts)

Step 4 deleted the Xapian/Haystack stack but left the templates, so what search
*did* is still on disk:

- **`sg101/templates/search/search.html`** — the form is three text boxes (`q`,
  `exact`, `exclude`) AND-ed together, plus a "Search in" checkbox group over the
  searchable types, with check-all/check-none. Results are **one blended list**,
  each row `verbose_name: title (score)` over a highlighted 200-char summary,
  paginated with a hit count.
- **The tips block says results are "displayed newest first"** — so the old
  search was **date-ordered, not relevance-ordered**, despite rendering a score.
- **`sg101/templates/search/indexes/*/*.txt`** — exactly what text was indexed
  per model. Eight documents across seven apps: `bio.UserProfile`,
  `downloads.Download`, `forums.Topic`, `forums.Post`, `news.Story`,
  `podcast.Item`, `weblinks.Link`, `ygroup.Post`. Most include
  `user.username` and `user.get_full_name` (this is how "search by author"
  worked) and, for news, `tags`.
- **`search_title` / `search_summary` properties still exist on the models** —
  the display contract for a result row survived the prune intact.
- Tips also record two known limitations: the indexer stripped punctuation (so
  `FRV-1` found nothing) and users were told to search `FRV 1` instead.

---

## Q1: Should results be ordered by relevance, or newest-first as before?

The old search ordered by date. Postgres FTS's main offering over `LIKE` is
`ts_rank` — relevance — so this is a real fork, and it decides how much of the
design has to care about score comparability across content types.

**Answer: relevance-ranked, with newest as the tiebreak.** Considered and
rejected: newest-first parity (simpler, but throws away the main thing Postgres
FTS offers over `LIKE`), and a user-facing sort toggle (deferred — can be added
later without rework, since both orderings fall out of the same query).

**Consequence — this largely settles the central-table question.** A blended,
relevance-ordered, *paginated* list over eight document types can't be built by
querying eight models and merging in Python: global ordering would require
fetching every match from every model before slicing a page. One denormalized
search table with one `tsvector`, one GIN index, and one `ORDER BY rank` gives
the ordering and the pagination directly. The parent project's
`research/search-stack.md` already leaned this way; Q1's answer makes it close to
forced. Recorded here rather than asked as its own question.

The open sub-problem it leaves: **score comparability across types.** `ts_rank`
is computed per document, and a 40-word news blurb and a 900-word forum post do
not produce comparable raw scores without normalization. That's a design
question for the task files, not a requirements question — flagged, not decided
here.

---

## Q2: Keep the three-box form, or move to a single search box?

The old form had three inputs — keywords, exact phrase, exclude — AND-ed
together, with a tips block explaining that `AND`/`OR`/`NOT` were unnecessary.
Postgres's `websearch_to_tsquery` (exposed as
`SearchQuery(..., search_type='websearch')`) parses all three of those from a single
box using syntax people already know from Google: bare words, `"quoted phrases"`,
and `-excluded`. It never raises on malformed input, which also retires the
`query_parser_error` branch the old template carries.

**Answer: a single box using websearch syntax.** `"quoted phrase"` and `-exclude`
replace the second and third inputs; the tips block gets rewritten to teach that
syntax instead of explaining why `AND`/`OR`/`NOT` are unnecessary. The
`query_parser_error` branch goes away with it — `websearch_to_tsquery` never
raises on malformed input, it just does its best. Considered and rejected:
three-box parity (no loss of capability, but three fields to render and test for
a shape people no longer expect), and single-box-plus-advanced (two forms, two
view branches, two sets of tests, for a case that hasn't been shown to exist).

The "Search in" checkbox group is **kept** — it's orthogonal to how the query is
typed, and filtering by content type is genuinely useful.

Side benefit: a one-field form is small enough to drop into the site header
later without a redesign.

---

## Q3: Which content types stay searchable?

The old index covered eight documents across seven apps. Two are worth an
explicit decision rather than carrying forward by default:

- **`bio.UserProfile`** — indexing member profiles means the search box finds
  *people*. Its index template pulled in `username`, `get_full_name`, `location`,
  `occupation`, `interests`, `profile_text`, `signature`, and the name and URL of
  every linked site from the `elsewhere` app. **This is not redundant with the
  live member search**: `bio.member_search` (`/members/search/`) is a username
  lookup that redirects to a profile, so the global index was the only way to
  find members *by profile content* — everyone in Texas, everyone who mentions
  Mosrite. Every one of those fields is already public on the profile page, so
  the question is about discoverability, not new exposure.
- **`ygroup.Post`** — the archived Yahoo Group posts. Static historical content;
  keeping it searchable is cheap, but it's the least-visited corner of the site.

The other six (`forums.Topic`, `forums.Post`, `news.Story`, `weblinks.Link`,
`downloads.Download`, `podcast.Item`) look like straightforward keeps.

**Answer: all eight documents stay searchable, member profiles at full parity** —
username, full name, location, occupation, interests, profile text, signature,
and linked site names/URLs. Rationale: every field is already public on the
profile page, and find-by-profile-content ("anyone in Austin", "who plays a
Jazzmaster") is a community feature nothing else on the site provides.
Considered and rejected: trimming signature and linked URLs (less noise, but
loses "members with a bandcamp page" for a noise problem that hasn't been
observed), and dropping profiles entirely (no replacement for the capability).

Consequence: real names and locations become findable from the search box, not
only on the profile page. Accepted knowingly.

---

## Q4: How should search handle content the user isn't allowed to see?

The forums have **private categories gated by group membership** — the parent
project's Step 5 added `forums/tests/test_permissions.py` specifically to lock
down anon / member / superuser / group-moderator / private-category access. A
search index is a second path to that content, and an index that ignores the
gate will happily show a private topic's title and a highlighted snippet of its
body to someone who would get a 403 clicking through.

Whether the old Xapian search got this right is unknown and, since the stack is
deleted, not cheaply recoverable. This needs deciding on its merits regardless.

**Real numbers, not a hypothetical.** Production has five categories, four public
and one gated: **`Kahunas`, restricted to the `Kahunas` group — 487 topics and
19,088 posts**, about 4% of the forum.

**Answer: private categories are not indexed at all.** The indexer skips any
category with groups assigned. No access key in the search table, no per-user
query branch, and no way for the index to leak restricted content.

Considered and rejected: per-user filtering at query time (strictly more capable
— Kahunas members could search their own category — at the cost of an access key
on every row and a query branch that has to be right every time), and a
public-only first pass with filtering added later (defers a schema change onto a
populated table).

**Accepted tradeoff:** those 19,088 posts are findable only by browsing, *including
for the Kahunas members who are allowed to read them*. Revisitable later — adding
the access key and the filter is additive — but not planned.

**Implementation notes this creates:**
- The indexer must key off `Category.groups` being non-empty, so a category that
  *becomes* private has its rows removed, and one that becomes public gets
  indexed. A category's privacy is not a fixed property of the data.
- Worth a design-time sweep of the other seven documents for equivalent
  visibility rules. Expected to be a non-issue — news, downloads and weblinks
  hold submissions in separate `Pending*` models, so the indexed models should
  contain approved content only — but it should be confirmed, not assumed.

---

## Q5: How does the index stay up to date?

The search table is denormalized, so something has to maintain it. The obvious
answer is "update the row when the object is saved", and at this site's write
volume that's cheap. One case complicates it:

**Author names are part of each document.** The old index templates put
`user.username` and `user.get_full_name` into forum posts, topics, downloads and
links — that's how "search by author" worked, and Q3 keeps it. So a member
changing their display name invalidates the indexed text of **every post they
have ever written**. The heaviest posters here have five figures of posts, which
turns a profile edit into a large update.

**Sizing, from production data:** 134 forum posts in the last 30 days (~4–5/day),
2,235 so far in 2026. Ordinary indexing is inline-cheap. The heaviest poster,
`bigtikidude`, has 25,768 posts — the upper bound on a rename fan-out.

**Answer (revised): every index update goes through Celery.**

*Originally recorded as "synchronous on save, Celery only for the rename
fan-out". Revised when Brian asked whether Celery should own the whole job. It
should — the original answer was the weaker call.*

The deciding argument is **failure isolation, not performance**. Indexing a post
costs milliseconds and at 4–5 posts a day nobody would feel it either way. But
with indexing inline in `save()`, a bug in vector building breaks *posting* — an
unacceptable coupling on a site one person maintains. Through Celery the post
succeeds, the index lags, and the fix is a reindex rather than an outage.
Secondary: the original answer created two code paths for one job, and that seam
is where bugs live. Retries and backoff come free.

**Non-negotiable implementation detail:** queue with
`transaction.on_commit(lambda: reindex_document.delay(pk))`, never directly in
`save()`. Otherwise the worker can pick the task up before the transaction
commits, read a row that does not exist yet, and index nothing — an intermittent,
load-dependent bug that is miserable to diagnose. It also gives correct rollback
behavior for free: transaction rolls back, no task fires.

**Accepted cost:** a downed worker means a silently stale index, where the
synchronous version would have kept working. A periodic reconcile sweep on beat
was offered and not taken; revisit if it ever bites. — **Revisited and reversed
2026-07-27; see the second Q5 addendum below.**

Considered and rejected: the original sync/async split (instant findability, no
worker dependency, but two paths and posting coupled to indexing), and moving
author names out of the document (dissolves the rename cascade entirely, but
breaks the documented "`SurferDood101 Gnarly` in one box" behavior Q3 kept).

### Q5 addendum — the rename fan-out is gone (revised 2026-07-27)

Brian raised second thoughts on the fan-out during task generation, which sent me
to check what can actually *trigger* a rename. The answer reframed the question:

- **`username` is immutable.** Written once, at activation
  (`accounts/utils.py:20`). No form edits it — `bio.SearchUsersForm` is a lookup,
  not an edit — so only an admin can change one, and the admin is Brian.
- **`first_name` / `last_name` are the only user-editable author text**, via
  `bio.EditUserForm` (`bio/forms.py:26`).

So the whole 25,768-row cascade traced to one pair of form fields. Measured
against the snapshot: **2,937 of 15,227 members (19%) have a full name at all**,
284 of them posted in the last two years — and `bigtikidude` has both a full name
and those 25,768 posts, so the upper bound was real and reachable *by an ordinary
user editing their own profile*. That last part is what decided it: the fallback
of "notice the rename, run the reindex command" has nothing to notice with.

**Decision: index full names only on the `bio.UserProfile` document.** Content
documents keep `username` at weight C; the profile document carries username and
full name at A. A name change rebuilds one row through the ordinary
`reindex_document` path. No fan-out task, no batching trigger, no test surface.

This is a *narrower* cut than the alternative Q5 rejected above, which was
all-or-nothing — it removes author names from content documents while keeping
find-a-member-by-real-name working through profiles. That variant wasn't on the
table when Q5 was answered.

**Accepted cost:** forum posts are findable by handle, not by the author's real
name. Additive later, at the price of reinstating the fan-out.

### Q5 addendum 2 — the reconcile sweep is taken after all (revised 2026-07-27)

Also raised by Brian during task generation: what would a weekly reconcile job
cost? He noted that manual reindexing was what Haystack/Xapian required, so a
periodic sweep would be parity rather than a new burden.

The question that mattered turned out to be **whether a reconcile has to reindex
everything.** It does not, and that reframes the cost entirely. A reconcile
compares sets and timestamps in SQL — source rows with no index row, index rows
with no source, and rows whose `indexed_at` predates the source's `update_date`.
It computes no vectors. **Its cost scales with the drift it finds, not the size
of the corpus**, so a healthy system does essentially no work.

Measured, against the real data: scanning `id, update_date` for all 463,222
forum posts — the dominant term, 94% of the corpus, in a 417 MB table — takes
**170 ms**. The full eight-type sweep is a handful of anti-joins; expect low
single-digit seconds. Weekly is free.

Two facts made this available, neither of which was in view when the sweep was
first declined:

- **Seven of eight documents carry a `db_index=True` `update_date`**, so *stale*
  is detectable, not just *missing*. The eighth, `ygroup.Post`, has no
  modification timestamp — and needs none, being a frozen archive.
- **Nothing in the codebase bulk-updates an indexed model.** A check across the
  seven relevant apps found no `.update()`, `bulk_create` or `bulk_update`
  against any indexed model, so signals genuinely see every application write
  today. The sweep is what would notice if that ever changed.

**Decision: take it, as a reporting job that repairs nothing.** Task 03's
incremental indexing is supposed to make drift impossible; the sweep exists to
find out whether that holds. Auto-repair would mask exactly the bugs worth
finding, and is a small change later once the numbers are known. It turns the
accepted cost above — *silently* stale — into merely stale.

**Consequence for task 01:** `SearchDocument` needs an `indexed_at` column from
the start. Adding it afterwards means a migration plus a backfill over 490k rows.

Tests are unaffected either way — `CELERY_TASK_ALWAYS_EAGER` is already set.

---

## Q6: Typo tolerance — is "did you mean" wanted?

`research/search-stack.md` flagged this as the one capability with no direct
Postgres FTS equivalent. FTS matches *stemmed lexemes*, so `revreb` matches
nothing at all — no results, no suggestion. The usual fix is the `pg_trgm`
extension: on a zero-result search, find the closest indexed terms by trigram
similarity and offer them.

**Answer: not for now.** A zero-result search says so plainly and offers advice
(check spelling, fewer words, try another section). It is the most speculative
feature in this step, needs its own tuning to avoid suggesting nonsense, and is
cleanly additive later — the suggestion query only ever runs on the zero-result
path, so nothing has to be built with it in mind.

Considered and rejected: `pg_trgm` "did you mean" suggestions (needs the
extension, a distinct-term table, and a hand-tuned similarity threshold), and a
silent fuzzy fallback (no suggestion UI, but results look arbitrary when the
match is poor).

If zero-result searches later prove common, revisit — worth logging enough to
know.

---

## Q7: Does the forums' "quick search" come back?

`/search/ajax/` is not a general feature — it is a **duplicate-topic check on the
new-topic form**. `forums/static/js/forums.js:302` sends the topic title being
typed, restricted to `models=forums.topic`, and renders the matches inline so the
poster can see whether their question already exists.

The button, the JavaScript, and `templates/search/search_ajax.html` all survived
Step 4. Only the view behind them is gone, and the route is currently a
placeholder like `/search/`.

**Answer: restore it,** as a small view returning the existing fragment template.
It reuses the same search machinery restricted to `forums.Topic`, and it is the
one place where search prevents work rather than merely finding things.

Considered and rejected: rebuilding it as a JSON endpoint with client-side
rendering (cleaner, but rewrites working JavaScript for no user-visible gain),
and dropping it (the new-topic form loses its duplicate check with no
replacement).

**Carried into implementation:** `templates/search/search_ajax.html` has a
pre-existing markup bug — `</fieldset>` and `</div>` sit inside the `{% else %}`
branch, so neither closes when there *are* results. Fix while restoring.

Also noted, not asked: both routes are still named `haystack_search` and
`haystack_search_ajax`, after a library that no longer exists. Renaming them
means updating every `{% url %}` and `reverse()` caller — worth doing, and a
task-file detail rather than a requirements decision.

---

## Q8: How should scores compare across content types of very different lengths?

The open sub-problem from Q1. `ts_rank` counts matches and their weights; by
default it does **not** account for document length, so a 900-word forum post
that mentions "reverb" five times outranks a news story whose *title* is about
reverb. Blended relevance ordering makes that a visible ranking problem rather
than a theoretical one.

Postgres exposes normalization options on `ts_rank` (a bitmask Django surfaces as
`SearchRank(..., normalization=...)`): divide by document length, by `1 + log`
of it, by unique-word count, and so on. Field weighting (`setweight`, A–D) is a
separate and complementary lever — it says a title hit matters more than a body
hit, regardless of length.

**Clarified first:** the "Search in" checkbox group from Q2 is kept, so a user
*can* narrow to a single type — and when they do, cross-type comparability stops
mattering. But the default is everything, so the common path is exactly the
blended case this question is about.

**Answer: length normalization plus field weights.** `SearchRank(...,
normalization=Value(1))` — divide by `1 + log(document length)` — so long posts
don't win on bulk alone, together with `setweight`: **A** title/topic name, **B**
body/description, **C** author username and full name.

Considered and rejected: weights alone (simplest, and defensible given the corpus
is 94% forum posts, but weblinks and podcast items would rarely surface), and
per-type boost multipliers (real editorial control, but the constants are guesses
and become a permanent maintenance surface).

**Worth knowing which knob is which:** normalization is a *query-time* argument,
so revising it later is a one-line change. Weights are baked into the stored
vector, so changing those means recomputing every row — get the weights right
first, tune normalization freely afterwards.

**Small related decision, folded in:** the old form followed Haystack's
convention that checking no boxes meant searching everything. The new form should
render with **all boxes checked** instead — same default behavior, but visible
rather than implicit, and it makes "check none" mean something honest.

---

## Q9: Should comments be searchable?

The old index did not cover them, so parity says no. But comments are real
discussion attached to news stories, downloads, links and podcast items, and
they're the one content type a member might reasonably expect a search to find.

**Corpus, for the record:** 10,987 comments — `potd.photo` 7,936 (72%),
`news.story` 1,569, `downloads.download` 1,231, `polls.poll` 225,
`contests.contest` 26.

**Answer: no — parity.** Comments stay out of the index. Nearly three-quarters
are one-line commentary on the daily photo; they have no `search_title` /
`search_summary` contract; and `Comment.is_public` / `is_removed` would introduce
a second moderation-state rule to honour, of the same class as Q4's category
gate.

Considered and rejected: indexing the ~3,051 non-POTD comments (the substantive
discussion, without the chatter — the strongest alternative, and the shape to
revisit if this is ever wanted), and indexing all 10,987 (dilutes results on
common words).

Additive later, like Q6.

---

## Noted, not asked

Small items decided by parity or obvious default, recorded so they aren't
mistaken for oversights:

- **Search requires login — CORRECTED.** An earlier draft of this file recorded
  "stays public, as before". That was wrong. `custom_search.views.UserSearchView`
  redirected anonymous users to `/accounts/login/?next=…`, and the gate exists
  for a reason: **bots were hammering search hard enough to hurt the site.** The
  same file's `QueryParserError` handler carries a contemporaneous comment about
  someone probing for SQL injection. The login requirement is a deliberate
  anti-abuse measure and carries forward.
  - Consequence for Q3: profile content is searchable **by logged-in members
    only**, which makes indexing real names and locations a materially smaller
    exposure than it first appeared.
  - Worth considering alongside it: whether the gate alone is enough, or whether
    a logged-in-but-abusive client also needs rate limiting.
- **A global search box already exists** — `v3/base.html:49` puts a single `q`
  input in the masthead (and `base.html:61` links to the search page). It is
  already the one-field shape Q2 chose, and it submits no `models`, so under
  "all types checked by default" a masthead search means search everything. No
  new template work; both files do need the route rename.
- **The old view passed `user` into the form "for logging, etc."** — so there was
  at least a hook for query logging. Relevant to Q6's deferred "did you mean".
- **Snippets** use `SearchHeadline` to reproduce the old highlighted ~200-char
  summary.
- **The landing state** (no query yet) shows the form and the tips block, as
  before; the tips are rewritten for `websearch` syntax per Q2.
- **A reindex management command** is needed regardless, for the initial backfill
  of ~490k rows and for rebuilding after a weight change.
- **Route names** `haystack_search` / `haystack_search_ajax` get renamed, with
  their `{% url %}` and `reverse()` callers updated.

---

## Q10: Given the bot history, is anything needed beyond the login gate?

Search was login-gated because bots were hammering it hard enough to hurt the
site. That gate carries forward — but a logged-in scraper still pays nothing to
run expensive queries, so the question is whether Step 12 also needs rate
limiting, query logging, or both.

**Answer: the login gate only.** The old cost was Xapian doing disk-backed index
reads per query; a GIN index lookup over ~490k rows is milliseconds. The load
that hurt before may simply not hurt now, and adding machinery against a problem
that can be measured first is the wrong order.

Considered and rejected for now: a per-user rate limit at the view (cheap — one
decorator over the Redis cache already running — and defensible given the history
actually happened).

**Query logging was also deferred here, then reinstated — see Q11.** It turned
out not to be a new feature at all: it already exists and Brian wants it kept.
Which also means Q6's "did you mean" *can* be decided on evidence later, since
the zero-result rate will be visible in the log.

Both remain additive. **If search load becomes a problem again, rate limiting is
an afternoon's work at the view** — no schema or index implications.

---

## Q11: Query logging — keep it, and where does it go?

**Brian: "we currently log user queries to a separate log, just so I can see what
users are searching for. I'd like to keep this behavior."** This supersedes
Q10's deferral of query logging — it is not a new feature, it is existing
behavior to preserve.

**Recovered from `custom_search/forms.py` at `pre-step-4-prune`:** one `INFO`
line per search, emitted from `CustomModelSearchForm.search()`:

```python
logger.info('Search executed: /%s/%s/%s/ in %s by %s [%s]',
    q, exact, exclude, models, username, get_ip(self.request))
```

— the three query fields, the selected models, the username (`ANONYMOUS` when not
logged in, `UNKNOWN` when no user was passed), and the client IP via
`core.functions.get_ip`. There was no dedicated handler: the logger was
`custom_search.forms`, which propagated to root and landed in the shared
`logs/sg101.log`.

**A neat confirmation of Q2 found in the same file.** The old form did not hand
Xapian three separate fields — it *synthesized* `terms "exact phrase" -excluded`
and passed that as one string. That is websearch syntax. Q2 did not change the
query language; it exposed directly what the three boxes were already building.

**Also recovered, for implementation:** the exact checkbox labels and their order
— Forum Topics, Forum Posts, News Stories, User Profiles, Links, Downloads,
Podcasts, Yahoo Group Archives — and two validation behaviors: an empty query is
rejected with "Please supply some search terms", and the old `exact` field
rejected quotes (moot with one box).

**Answer: keep it, and give it a dedicated `search.log`** — a `search` logger with
its own `RotatingFileHandler`, `propagate: False`, exactly parallel to the
existing `auth` logger and `auth.log`. That makes "what are people searching for"
a grep of one file rather than a filter over the shared log, which is what the
behavior is *for*.

The line keeps its content but loses two fields, since Q2 collapsed three inputs
into one:

```python
logger = logging.getLogger('search')
logger.info('Search: %s in %s by %s [%s]', query, models, username, ip)
```

Username stays `ANONYMOUS`-aware even though Q10 keeps the login gate — cheap,
and correct if the gate is ever relaxed. IP still via `core.functions.get_ip`.

Considered and rejected: strict parity into the shared `sg101.log` (no settings
change, but leaves the queries mixed in with everything else), and logging to
stdout for Docker (fits where Step 21 is heading, but would split the logging
strategy mid-project when `auth.log` is still file-based).

**Flagged for Step 21:** file-based logging needs a mounted volume and
in-container rotation under Docker. Step 12 follows the existing house style
deliberately; moving *all* logging to stdout is a single coherent decision for the
deploy step, not something to do piecemeal here.

---

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Result ordering | Relevance (`ts_rank`), newest as tiebreak |
| 2 | Search form | Single box, `websearch` syntax; type checkboxes kept, all checked by default |
| 3 | What's searchable | All 8 documents; member profiles at full parity |
| 4 | Private content | Private categories not indexed at all |
| 5 | Index freshness | **All updates via Celery**, queued on `transaction.on_commit`; full names indexed on profiles only, so there is **no rename fan-out** (revised 2026-07-27) |
| 6 | Typo tolerance | Skipped for now; additive later |
| 7 | Forums quick search | Restored, reusing the existing fragment template |
| 8 | Score scaling | `normalization=1` (÷ `1+log(len)`) + `setweight` A/B/C |
| 9 | Comments | Not indexed — parity; additive later |
| 10 | Abuse defence | Login gate only; rate limiting deferred |
| 11 | Query logging | **Kept** — existing behavior, moved to a dedicated `search.log` |

Access is **login-required** throughout (corrected from an earlier draft of this
file, which wrongly recorded search as public).

**Architecture that falls out of these:** one denormalized search table, one
`tsvector` column with weighted sections, one GIN index, one `ORDER BY rank,
-date`; every row written by a Celery task queued on `transaction.on_commit`,
with a second task for author-rename fan-out; private-category rows never
written; the whole thing behind a login gate.

