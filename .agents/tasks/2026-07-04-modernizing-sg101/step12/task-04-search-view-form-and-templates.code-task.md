# Task: Restore `/search/` — the View, the Form, Ranking, and Query Logging

## Description
Build the search page itself: a single-box form using websearch syntax, a
relevance-ranked blended result list with highlighted snippets and pagination, the
login gate, the rewritten tips block, the route rename off the dead `haystack_*`
names, and the dedicated `search.log`.

This is the task that makes search visible to members for the first time since
Step 4 stubbed it out.

## Background
**The old search, recovered from surviving artifacts** rather than memory (Step 4
deleted the stack but left the templates, and `pre-step-4-prune` has the code):

| Aspect | Old behavior |
|---|---|
| Access | **Login required** — anonymous users redirected to `/accounts/login/` |
| Form | Three boxes: keywords / exact phrase / exclude, AND-ed |
| Query built | `terms "exact phrase" -excluded` — **one synthesized string** |
| Type filter | Checkbox group; none checked meant all |
| Ordering | **Newest first**, despite the template rendering a score |
| Results | One blended list: `verbose_name: title (score)` + highlighted 200-char summary |
| Logging | One `INFO` line per search: terms, models, username, IP |

**Two of those shaped this task.** The old search was *date-ordered*, so relevance
ranking is a deliberate change, not a restoration. And the three boxes were only
ever a UI over websearch syntax — `custom_search/forms.py` synthesized
`terms "exact phrase" -excluded` and handed Xapian one string, which is exactly
what `websearch_to_tsquery` parses. Collapsing to one box changes the interface,
not the query language.

**The login gate is an anti-abuse measure, not an afterthought.** Bots were
hammering search hard enough to hurt the site, and the old view's error handler
carries a contemporaneous comment about someone probing for SQL injection. It
carries forward. Rate limiting was considered and deferred — a GIN lookup over
490k rows is milliseconds where Xapian was doing disk-backed index reads, so the
old load may simply not hurt now. If it does, a decorator over the existing Redis
cache is an afternoon's work.

**Query logging already exists and is wanted.** This is preserved behavior, not a
new feature — its purpose is letting the site owner see what members search for.
It gains a dedicated `search` logger with its own `RotatingFileHandler` writing
`logs/search.log` and `propagate: False`, exactly parallel to the existing `auth`
logger and `auth.log` in `sg101/settings/local.py` and `production.py`.

```python
logger = logging.getLogger('search')
logger.info('Search: %s in %s by %s [%s]', query, models, username, ip)
```

IP via the existing `core.functions.get_ip` (`core/functions.py:122`). Keep the
username `ANONYMOUS`-aware even though the login gate makes it moot — cheap, and
correct if the gate is ever relaxed.

**Route rename.** Both routes are still named after a library that no longer
exists. `haystack_search` has **eight callers across seven templates**:
`navbar.html:7`, `base.html:61`, `bio/members.html:10`, `v3/base.html:49` and
`:154`, `ygroup/thread_list.html:10`, `ygroup/v3/thread_list.html:10`. All must
move together. Note the *URL path* `/search/` stays — only the route name changes.

**The masthead box already fits.** `v3/base.html:49` is already a single `q`
input posting to the search page, and it submits no `models` — so under
"all types checked by default" a masthead search searches everything. No template
work needed there beyond the rename.

**Ranking, decided during design:** `SearchRank(vector, query,
normalization=Value(1))` — divide by `1 + log(document length)` — so a 900-word
forum post does not outrank a tight news headline on bulk alone. Order by rank,
then `-date` as the tiebreak. Normalization is a *query-time* argument, so it is
cheap to revise later; the weights baked into the vector by task 01 are not.

**Recovered details to honor:**
- Checkbox labels and order, verbatim: Forum Topics, Forum Posts, News Stories,
  User Profiles, Links, Downloads, Podcasts, Yahoo Group Archives.
- Empty query is rejected with "Please supply some search terms".
- The landing state (no query yet) shows the form and the tips block.
- **All boxes render checked** — the old form followed Haystack's convention that
  checking none meant everything. Same default behavior, but visible rather than
  implicit, and it makes "check none" mean something honest.
- The old template's `query_parser_error` branch can go: `websearch_to_tsquery`
  never raises on malformed input.
- The tips block currently explains why `AND`/`OR`/`NOT` are unnecessary; rewrite
  it to teach `"quoted phrases"` and `-exclusion` instead. It also apologises
  that `FRV-1` finds nothing — leave that claim alone for now, task 07 determines
  whether it is still true.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§1 what the old search did, §3 weighting/ranking/logging)
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q1 ordering, Q2 the single box, Q8 score scaling, Q10 abuse, Q11 logging)
- `sg101/templates/search/search.html` — the surviving results template and tips
  block; `git show pre-step-4-prune` for the deleted view and form

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Build the search form: one query field plus the eight type checkboxes, all
   checked by default, with the recovered labels and order. Reject an empty query
   with the recovered message.
2. Build the view behind `/search/`, **login required**, querying
   `SearchDocument` with `SearchQuery(q, search_type='websearch')` and
   `SearchRank(..., normalization=Value(1))`, ordered by rank then `-date`.
3. Filter by selected types. Render results as one blended list with the existing
   row contract, paginated with a hit count, using the site's existing paginator.
4. Produce snippets with `SearchHeadline` to reproduce the highlighted ~200-char
   summary the template expects.
5. Rename the routes off `haystack_search` / `haystack_search_ajax` and update all
   eight `{% url %}` callers. Keep the URL paths unchanged. Delete the `FixedView`
   stub and its explanatory comment in `sg101/urls.py`.
6. Add the `search` logger and its `RotatingFileHandler` to both
   `sg101/settings/local.py` and `sg101/settings/production.py`, mirroring the
   `auth` logger, with `propagate: False`. Emit one line per executed search.
7. Update the tips block for websearch syntax and drop the `query_parser_error`
   branch.
8. Do not add rate limiting, a sort toggle, or "did you mean" — all explicitly
   deferred.

## Dependencies
- Task 01 (the model and vector) and task 02 (a populated index to query)
- Task 03 is not strictly required, but without it results go stale as you test
- `core.functions.get_ip` for the log line

## Implementation Approach
1. Recover the deleted view and form from `pre-step-4-prune` for reference, then
   write the new ones against `SearchDocument`.
2. Get a working ranked query in a shell against the backfilled index before
   touching templates — confirm ordering looks sensible on real terms.
3. Build the form and view, then adapt `search.html` to the new context.
4. Do the route rename as its own reviewable change across the seven templates.
5. Add the logger to both settings modules and confirm lines land in
   `logs/search.log` and *not* in `sg101.log`.

## Acceptance Criteria

1. **Search Returns Ranked Blended Results**
   - Given a populated index and a logged-in member
   - When they search a term appearing in several document types
   - Then results from multiple types appear in one list ordered by relevance,
     with newest first among equal scores, paginated with a hit count

2. **Websearch Syntax Works**
   - Given the single query box
   - When a member searches `"exact phrase"` or `term -excluded`
   - Then phrase matching and exclusion behave accordingly, and malformed input
     produces results rather than an error page

3. **Title Hits Outrank Body Hits**
   - Given a news story with a term in its title and a long forum post with the
     same term in its body
   - When the term is searched
   - Then the news story ranks above the forum post

4. **Type Filtering Works and Defaults to Everything**
   - Given the search form
   - When it renders, all eight boxes are checked; and when a member unchecks all
     but one type and searches
   - Then only that type's results are returned

5. **Login Gate Holds**
   - Given an anonymous visitor
   - When they request `/search/` or submit a query
   - Then they are redirected to the login page with `next` preserved, and no
     query executes

6. **Query Logging Lands in Its Own File**
   - Given a member performing a search
   - When the search executes
   - Then one INFO line recording query, types, username and IP is written to
     `logs/search.log`, and nothing is written to `logs/sg101.log`

7. **No Dead Route Names Remain**
   - Given the codebase
   - When it is searched for `haystack`
   - Then no route names, `{% url %}` tags or `reverse()` calls reference it, the
     `FixedView` stub is gone, and every one of the eight former callers resolves

8. **Empty Query Rejected**
   - Given the search form
   - When it is submitted with no terms
   - Then "Please supply some search terms" is shown and no query executes

9. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then ranking, type filtering, websearch syntax, the login gate, pagination,
     empty-query validation and log emission are covered, and the suite is green

## Metadata
- **Complexity**: High
- **Labels**: Search, PostgreSQL, Views, Forms, Templates, Logging, Step 12
- **Required Skills**: Django views/forms/templates, `django.contrib.postgres`
  search (`SearchQuery`, `SearchRank`, `SearchHeadline`), Django logging config
