# Search design — Step 12 (PostgreSQL full-text search)

The design settled for restoring `/search/`, from the requirements clarification
in `../step12-idea-honing.md` (Q1–Q11, 2026-07-26). That file holds the reasoning
and the rejected alternatives; this one states what is being built.

Companion to `search-stack.md`, which established *that* Postgres FTS replaces
Xapian/Haystack. This establishes *what* gets built.

---

## 1. What the old search did

Step 4 deleted the Xapian/Haystack stack but left its templates, and the removed
code is recoverable at the `pre-step-4-prune` tag. Prior behavior is therefore
documented rather than remembered:

| Aspect | Old behavior | Source |
|---|---|---|
| Access | **Login required** — anonymous users redirected to `/accounts/login/` | `custom_search/views.py` |
| Form | Three boxes: keywords / exact phrase / exclude, AND-ed | `templates/search/search.html` |
| Query built | `terms "exact phrase" -excluded` — **one synthesized string** | `custom_search/forms.py` |
| Type filter | Checkbox group; none checked meant all | `CustomModelSearchForm` |
| Ordering | **Newest first** (`SearchQuerySet().order_by('-pub_date')`) | old `sg101/urls.py` |
| Results | One blended list: `verbose_name: title (score)` + highlighted 200-char summary | `search.html` |
| Logging | One `INFO` line per search: terms, models, username, IP | `forms.py` |
| Known gap | Indexer stripped punctuation — `FRV-1` found nothing | tips block |

Two details from that table shaped the design more than anything else. **The old
search was date-ordered, not relevance-ordered**, despite rendering a score. And
**the three boxes were only ever a UI over websearch syntax** — the form
synthesized `terms "exact phrase" -excluded` and handed Xapian a single string,
which is exactly what `websearch_to_tsquery` parses.

Still on disk and reusable: `search_title` / `search_summary` properties on every
searchable model, `templates/search/indexes/*/*.txt` recording precisely which
fields were indexed, the results template, the quick-search fragment, and the
masthead search box at `v3/base.html:49`.

---

## 2. Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Result ordering | Relevance (`ts_rank`), newest as tiebreak |
| 2 | Search form | Single box, `websearch` syntax; type checkboxes kept, all checked by default |
| 3 | What's searchable | All 8 documents; member profiles at full parity |
| 4 | Private content | Private categories not indexed at all |
| 5 | Index freshness | All updates via Celery, queued on `transaction.on_commit` |
| 6 | Typo tolerance | Skipped for now; additive later |
| 7 | Forums quick search | Restored, reusing the existing fragment template |
| 8 | Score scaling | `normalization=1` (÷ `1+log(len)`) + `setweight` A/B/C |
| 9 | Comments | Not indexed — parity; additive later |
| 10 | Abuse defence | Login gate only; rate limiting deferred |
| 11 | Query logging | Kept — existing behavior, moved to a dedicated `search.log` |

**Revised 2026-07-27, after Q5:** author **full names** are indexed only on the
`bio.UserProfile` document, not on content documents, which removes the
author-rename fan-out entirely. See §3, "Index maintenance".

---

## 3. Architecture

One denormalized search table. Q1 (relevance ordering) and Q4 (private content
excluded) between them force it: a blended, relevance-ordered, *paginated* list
across eight document types cannot be assembled by querying eight models and
merging in Python, because global ordering would require fetching every match
from every model before slicing a page.

```mermaid
flowchart TD
    subgraph sources["Source models (8 documents)"]
        A["forums.Topic"]
        B["forums.Post"]
        C["news.Story"]
        D["bio.UserProfile"]
        E["weblinks.Link"]
        F["downloads.Download"]
        G["podcast.Item"]
        H["ygroup.Post"]
    end

    A & B & C & D & E & F & G & H -->|"post_save / post_delete<br/>transaction.on_commit"| Q["Celery task<br/>reindex_document(ct, pk)"]
    Q -->|"skips private categories"| T[("SearchDocument<br/>tsvector + GIN index")]

    U(["Member<br/>(login required)"]) --> V["/search/ view"]
    V -->|"SearchQuery(websearch)<br/>SearchRank(normalization=1)"| T
    T -->|"ORDER BY rank, -date"| W["Blended results<br/>+ SearchHeadline snippets"]
    V -.->|"one INFO line"| L[["search.log"]]
```

### The search table

One row per indexed document:

| Column | Purpose |
|---|---|
| `content_type` + `object_id` | What this row indexes (generic pointer to the source) |
| `search_vector` | Weighted `tsvector`, **GIN-indexed** |
| `title` | The document's **weight A** text, and the result heading |
| `summary` | The document's **weight B** text, and the snippet source |
| `author` | The document's **weight C** text |
| `url` | From `get_absolute_url`, so results render without touching source tables |
| `date` | The document's own date, for the recency tiebreak |
| `indexed_at` | When this row was last rebuilt — the reconcile sweep's watermark |

Denormalizing title/summary/url means a result page renders from this table
alone — no N+1 fan-out across eight models to display ten rows.

**Revised 2026-07-28, building task 01: the three text columns hold the text to
be *indexed*, and the vector is a function of them** — `setweight(to_tsvector(
title),'A') || ... (summary),'B') || ... (author),'C')`. This is the pattern in
the Django FTS docs; passing the text in from Python as `Value()` literals is the
variant off the beaten path. It costs one column beyond the sketch above
(`author`) and means a vector can be rebuilt from this table alone.

The models' existing `search_title` / `search_summary` therefore go unused, except
on `bio.UserProfile` where `search_title()` already returns the wanted A text.
They do not survive contact with weighting: `forums.Topic` and `forums.Post` embed
the username *and* a formatted date in their title, which would put the author at
A instead of C and tokenize `12-Jan-2020` into every post's high-weight terms, so
`2020` would match half the forum. Result lines are composed instead by the
template from `title` + `author` + `date`, uniformly for all eight types — a forum
topic loses its "; 3 posts", while news, links, downloads and podcasts gain a
visible author. Byte-identical parity with the Xapian result lines was explicitly
not a requirement.

Defining `summary` as *what should be indexed* also closes three gaps that
`search_summary()` had: `news` regains its `tags`, `weblinks` regains its `url`,
and `bio` sheds the username and full name that belong at A. HTML is stripped
from body text on the way in — every news story stores rendered HTML rather than
the markup it came from, as does 40% of the Yahoo Group archive, and this text is
both indexed and shown in snippets.

### Weighting and ranking

`setweight` is applied when the vector is built:

| Weight | Content |
|---|---|
| **A** | Title / topic name |
| **B** | Body / description |
| **C** | Author **username** (not full name — see below) |

On the `bio.UserProfile` document the author *is* the document, so username and
full name both sit at **A**, with location, occupation, interests, profile text
and linked sites at **B**.

Ranking is `SearchRank(vector, query, normalization=Value(1))` — divide by
`1 + log(document length)` — so a long forum post does not outrank a tight news
headline on bulk alone.

**Know which knob is which.** Normalization is a *query-time* argument: revising
it is a one-line change. Weights are baked into the stored vector: changing those
requires recomputing every row. Get the weights right first; tune normalization
freely afterwards. (Since task 01 built the vector from the row's own columns,
that recompute is one `UPDATE` over the search table rather than a re-read of
eight source models — but it is still 490k rows either way.)

### Index maintenance

Every write goes through Celery, queued on commit:

```python
transaction.on_commit(lambda: reindex_document.delay(ct_id, pk))
```

Never queue directly in `save()` — the worker can pick the task up before the
transaction commits, read a row that does not exist yet, and index nothing. That
failure is intermittent and load-dependent. Queueing on commit also gives correct
rollback behavior for free.

**There is no author-rename fan-out, by construction** (revised 2026-07-27 —
supersedes Q5's "a rename is its own task"). Two facts settle it:

- **`username` is immutable.** It is written exactly once, at account activation
  (`accounts/utils.py:20`). No form anywhere edits it; only an admin can, and
  the admin is the site owner, who can run the reindex command.
- **`first_name` / `last_name` are user-editable** via `bio.EditUserForm`, and
  they are the *only* mutable author text — which is why they are indexed **only
  on the `bio.UserProfile` document**, never on posts, topics, news, downloads
  or links. A name change therefore rebuilds exactly **one row**, handled by the
  same `reindex_document` path as any other edit.

Had full names stayed embedded in content documents, one profile edit by
`bigtikidude` would have rebuilt **25,768 rows**, triggered by an ordinary
user-facing form — so the "we'll notice and re-run the command" fallback would
not have held. Dissolving the cascade beat managing it.

**Accepted cost:** forum posts are findable by author *handle*, not by the
author's real name. Only 2,937 of 15,227 members (19%) have a full name set at
all, and finding *people* by real name still works through the profile document.
Additive later if wanted: it needs the embedding plus a batched fan-out task.

A downed worker means a stale index. **A weekly reconcile sweep was originally
declined and is now taken** (revised 2026-07-27), because measuring it changed
the picture: a reconcile does not have to rebuild anything.

It compares sets and timestamps in SQL — missing rows, orphaned rows, and rows
whose `indexed_at` predates the source's `update_date` — so **its cost scales
with the drift it finds, not with the corpus**. The dominant term, scanning
`id, update_date` across all 463,222 forum posts, measures **170 ms**; the full
eight-type sweep should land in the low single-digit seconds. Weekly is free.

Two facts made the timestamp comparison available: seven of the eight documents
carry a `db_index=True` `update_date`, and the eighth, `ygroup.Post`, is a frozen
archive that cannot drift. `SearchDocument` therefore carries an `indexed_at`
column from the start — adding it later would mean a migration plus a backfill
over 490k rows.

**It reports; it does not repair.** Task 03's incremental indexing is supposed to
make drift impossible, and the sweep exists to find out whether that holds.
Auto-repair would mask exactly the bugs worth finding, and becomes a small change
once there is evidence. It also reports any index row pointing into a private
category separately, since that is a privacy defect rather than staleness.

### Access and exclusions

- **Login required**, carried forward from the old view. It is an anti-abuse
  measure: bots were hammering search hard enough to hurt the site.
- **Private categories are never indexed.** The indexer keys off
  `Category.groups` being non-empty. Production has one such category —
  `Kahunas`, 487 topics and 19,088 posts — and those are unfindable by search
  even for the members allowed to read them. Deliberate; revisitable additively.
- A category's privacy is **not fixed**: one that becomes private must have its
  rows removed, and one that becomes public must gain them.

### Logging

A `search` logger with its own `RotatingFileHandler` writing `logs/search.log`,
`propagate: False` — parallel to the existing `auth` logger and `auth.log`:

```python
logger.info('Search: %s in %s by %s [%s]', query, models, username, ip)
```

---

## 4. Corpus, measured

| Document | Rows |
|---|---|
| `forums.Post` | 463,221 (less 19,088 private) |
| `forums.Topic` | 35,692 (less 487 private) |
| `bio.UserProfile` | 15,227 |
| `news.Story` | 1,694 |
| others (links, downloads, podcast, ygroup) | remainder |

Roughly **490k rows** to index. Write rate is low — 134 forum posts in the last
30 days — so steady-state indexing is trivial; the initial backfill is the only
bulk operation.

Not indexed: 10,987 comments (72% of them Photo-of-the-Day chatter), and the
private category above.

---

## 5. Deferred, with reasons

| Item | Why deferred | Cost to add later |
|---|---|---|
| "Did you mean" (`pg_trgm`) | Speculative; needs a tuned threshold | Additive — only runs on the zero-result path, and `search.log` will show the zero-result rate |
| Comments in the index | 72% is POTD chatter; needs `is_public`/`is_removed` handling and a title/summary contract | Additive |
| Private-category search | Would need an access key per row and a per-user query filter | Additive column + backfill |
| Rate limiting | Login gate may be sufficient now that queries are milliseconds | An afternoon at the view |
| Sort toggle (relevance/newest) | Both orderings fall out of the same query | Form field + query branch |
| Finding posts by author's *real* name | Embedding it in content documents brings back a 25,768-row rename fan-out for a field only 19% of members set | Embed at weight C + a batched fan-out task on `bio.EditUserForm` saves |

---

## 6. Carried into implementation

- `templates/search/search_ajax.html` has a **pre-existing markup bug**:
  `</fieldset>` and `</div>` sit inside the `{% else %}` branch, so neither closes
  when there *are* results.
- Routes are still named `haystack_search` / `haystack_search_ajax`, after a
  library that no longer exists. Renaming touches `v3/base.html` (twice),
  `base.html`, and any `reverse()` callers.
- Checkbox labels and order, recovered verbatim: Forum Topics, Forum Posts, News
  Stories, User Profiles, Links, Downloads, Podcasts, Yahoo Group Archives.
- Validation: an empty query is rejected with "Please supply some search terms".
- A reindex management command is needed regardless — for the initial ~490k-row
  backfill and for rebuilding after any weight change.
- The old tips block apologises that `FRV-1` finds nothing. Postgres's parser
  emits both the whole hyphenated token and its parts, so **this limitation may
  simply be gone** — confirm against real data, and if so, say so in the
  rewritten tips.
- `'english'` is the assumed text search configuration. Band and song names are a
  large share of queries and not all are English; `'simple'` (no stemming) is the
  alternative if stemming proves to hurt more than help.

**Flagged for Step 21:** file-based logging needs a mounted volume and
in-container rotation under Docker. Step 12 follows the existing `auth.log` house
style deliberately — moving all logging to stdout is one coherent decision for
the deploy step.

---

## 7. References

- [Django: full-text search](https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/search/)
  (3.2 — the version this is built on)
- [Django: `django.contrib.postgres` indexes](https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/indexes/)
- [PostgreSQL 16: full text search](https://www.postgresql.org/docs/16/textsearch.html)
- [pganalyze: efficient Postgres full-text search in Django](https://pganalyze.com/blog/full-text-search-django-postgres)

**Version note.** `SearchHeadline`, `search_type='websearch'` and `SearchRank`'s
`normalization` all require Django ≥ 3.1 and PostgreSQL ≥ 11 — satisfied by 3.2
and PG 16, so nothing here waits on the remaining rungs. Django 5.0's
`GeneratedField` could later let Postgres maintain the vector itself, retiring
some of the Celery machinery; revisit at **Step 14**.
