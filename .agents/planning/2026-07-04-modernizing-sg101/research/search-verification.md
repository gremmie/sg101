# Search verification against production data — Step 12 task 07

What a green test suite cannot tell you: whether the results are *good*, whether
the queries are fast, and whether two assumptions carried through the design
survive contact with 516,858 real documents.

Everything below was measured against the converted production snapshot on
`postgres:16`, through `search.query.search_documents` — the code path the view
actually uses — except where a plan or a lexeme is being shown, which is `psql`.

Precedent: `step11/task-05` found four defects invisible to row counts, column
diffs and the whole suite. This pass found one of comparable weight, in ranking.

---

## 1. The corpus, as indexed

| type | rows | share | avg title | avg summary | avg vector |
|---|---:|---:|---:|---:|---:|
| forums.post | 444,134 | 85.93% | 38 | 365 | 480 |
| forums.topic | 35,206 | 6.81% | 38 | **0** | **71** |
| ygroup.post | 21,032 | 4.07% | 40 | 1,435 | 1,481 |
| bio.userprofile | 13,590 | 2.63% | 12 | 34 | 68 |
| news.story | 1,694 | 0.33% | 46 | 1,035 | 1,226 |
| downloads.download | 673 | 0.13% | 34 | 282 | 373 |
| weblinks.link | 514 | 0.10% | 22 | 210 | 318 |
| podcast.item | 15 | 0.00% | 9 | 1,269 | 1,635 |

Lengths in characters; the vector column is `length(search_vector::text)`.

**That table is the finding.** `forums.topic` carries no summary at all — a topic
document *is* its title — so it is the shortest document type in the corpus by a
factor of five. `podcast.item` is the longest, at 23×. Section 3 is about what
length normalization does with that.

---

## 2. Settled questions

### 2.1 Hyphenation: the `FRV-1` limitation is gone — by two different mechanisms

The old tips block apologised that the Xapian indexer stripped punctuation, so
`FRV-1` found nothing and members were told to search `FRV 1` instead. Against
real data:

| query | hits |
|---|---:|
| `FRV-1` | **2,024** |
| `FRV 1` (the old advice) | 114 |
| `frv` alone | 2,229 |

Typing the model number as written now finds **18× more** than the workaround the
tips used to recommend. The limitation was Xapian's, not Postgres's.

**The design's stated reason was wrong, though, and the difference matters.** The
design said "Postgres's parser emits both the whole hyphenated token *and* its
parts." That is true only for letter–letter hyphenation:

```
to_tsvector('english', 'surf-rock go-go double-neck')
  → 'surf-rock':1 'surf':2 'rock':3 'go-go':4 'go':5,6 'double-neck':10 ...
```

For word–digit it is not. `FRV-1` parses as an `asciiword` plus a *signed
integer*, and `websearch_to_tsquery` makes those adjacent:

```
ts_debug('english','FRV-1')  → asciiword "FRV", int "-1"
websearch_to_tsquery('english','FRV-1')  → 'frv' <-> '-1'
```

It works — better than the alternative — because it is a **phrase match on an
adjacency**, not because the compound token is indexed. Two consequences follow
that would otherwise be surprising:

- A document written `FRV 1` will **not** match a query for `FRV-1`. The document
  tokenizes `1` (positive int); the query wants `-1`. The two are different
  lexemes. This is why `FRV 1` returns 114 rather than a subset of 2,024.
- `surf-rock` returns **1,328** hits where `surf rock` returns **14,993**. The
  hyphenated query compiles to `'surf-rock' <-> 'surf' <-> 'rock'` and so demands
  the compound token; documents that spell it with a space are excluded.

Neither is a defect — hyphenating is a *narrowing* act and the results are
precise. But "hyphenated names work as written" means "work exactly as written",
not "work as a looser phrase".

**Tips block: already correct.** Task 04 retired the `FRV-1` apology early. Its
replacement line and every other claim in the block were re-verified here — the
`A/B box` example holds (`a/b` survives as one `file` token, 89 hits), exclusion
holds, phrase quoting holds, and author search holds (§2.3). No change needed.

### 2.2 `'english'` beats `'simple'`, decisively — keep it, no reindex

Recommendation: **stay on `'english'`.** The evidence runs one way.

Stemming pays for itself on this corpus because member vocabulary is relentlessly
plural and inflected, and band names here are overwhelmingly plural nouns:

| written | `'english'` | `'simple'` |
|---|---|---|
| The Ventures | `ventur` | `the`, `ventures` |
| The Bomboras | `bombora` | `the`, `bomboras` |
| The Tornadoes | `tornado` | `the`, `tornadoes` |
| Satan's Pilgrims | `satan`, `pilgrim` | `satan`, `s`, `pilgrims` |
| surfing / surfed / surf | all → `surf` | three distinct lexemes |
| tabs | `tab` | `tabs` |
| reverbe *(typo)* | `reverb` | `reverbe` |

Three things in that table are worth naming:

- **Stemming silently fixes a common typo.** `reverbe` stems to `reverb` and
  returns all 54,065 reverb documents. Under `'simple'` it returns nothing.
- **`'simple'` indexes the stop words.** "The Ventures" would carry a `the`
  lexeme whose posting list is most of the table — dead weight in the index and
  in every query that includes an article.
- **`'simple'` manufactures junk lexemes.** `Satan's Pilgrims` yields a bare `s`.

The cost of stemming — a stem colliding with an ordinary English word — was
measured on the worst case in the query set, `The Ventures` → `ventur`, which
collides with *venture / ventured / venturing*:

- 11,534 documents match the stem
- 10,990 (**95.3%**) contain the literal plural "Ventures", i.e. the band
- 48 (0.4%) contain no form of "venture" in title or summary at all

So contamination is under 5%, and ranking pushes the band to the top regardless —
the top 10 for `The Ventures` is band content without exception. Set against
losing plural/singular unification across every band name on the site, this is
not a close call.

**No reindex is required**, since nothing changes.

One genuine `'english'` cost, recorded rather than fixed: a query made only of
stop words returns zero results with a `NOTICE`, so a member searching `the the`
gets nothing.

### 2.3 Author search works

The tips block promises it; `Pyronauts Kickstarter`, `simoncoil Astronaut` and
`Brian Sundazed` all return the expected rows. Note it is a *blended* match, not
a filter — `Pyronauts Kickstarter` also returns posts by other members in a
thread whose title contains "Pyronauts", because the vector spans title, summary
and author together. The tip's wording ("most content is searchable by author")
describes that correctly.

---

## 3. THE FINDING: `normalization=1` is a document-length sort in disguise

### 3.1 What was expected, and what is actually happening

`search/query.py` explains the choice this way:

> normalization=1 divides by 1 + log(document length), so a 900-word forum post
> does not outrank a tight news headline on bulk alone.

**The premise is wrong in both halves.** `ts_rank` without normalization does not
reward bulk — repeated occurrences of the same lexeme add sub-linearly, and eight
documents matching `Sundazed Music` in their titles scored `0.9910322`, all but
identically, at `normalization=0` regardless of being 0 or 677 characters long.
And a "tight news headline" is not the short document here: `forums.topic` is,
with a summary of exactly zero characters (§1).

So the normalization is not protecting brevity from bulk. It is *creating* an
ordering where `ts_rank` saw a tie, and that ordering is length, ascending.

The clean demonstration is one query, `Sundazed Music`, where a forum topic and a
weblink carry byte-identical titles and therefore identical weight-A matches:

| type | title | summary len | `norm=1` | `norm=0` |
|---|---|---:|---:|---:|
| topic | Sundazed Music | 0 | **0.4955** | 0.9910 |
| post | Sundazed Music | 39 | 0.3834 | 0.9910 |
| post | Sundazed Music | 19 | 0.3834 | 0.9910 |
| post | Sundazed Music | 53 | 0.3322 | 0.9967 |
| **link** | **Sundazed Music** | 96 | **0.2678** | 0.9910 |
| post | Sundazed Music | 175 | 0.2425 | 0.9910 |
| post | Sundazed Music | 236 | 0.2020 | 0.9910 |
| post | Sundazed Music | 677 | 0.1636 | 0.9959 |

`norm=1` orders those eight rows **monotonically by length and by nothing else**.
The curated weblink for Sundazed Music — the actual thing a member searching that
phrase probably wants — places fifth, behind a topic and three posts, purely
because it has a 96-character description and they do not.

### 3.2 What it costs, measured

Where the best non-forum answer actually lands, out of the full result list:

| query | #1 result | first weblink/download/podcast |
|---|---|---|
| `backing track` | topic "Backing Tracks?" | **download at #47** |
| `Treble Spankers` | topic "New Treble Spankers footage" | **link at #36** |
| `space surf podcast` | post "Episode #7 - Space Surf!" | **item at #29** |
| `surf guitar tabs` | topic "Surf Christmas Guitar Tab?" | **link at #26** |
| `tablature` | topic "Torquays Tablature" | download at #10 |
| `Sundazed Music` | topic "Sundazed Music" | link at #5 |
| `Ali Baba backing track` | **download** "Ali Baba Backing Track" | download at #1 |
| `Link Wray Creepy tablature` | **download** | download at #1 |

The pattern is sharp. **Specific queries are fine** — name the track and the
download wins outright. **Categorical queries bury the curated types**, which is
precisely backwards: a member typing `backing track` almost certainly wants the
downloads section, and gets 46 forum rows first while 115 matching downloads sit
behind them.

`space surf podcast` is the extreme case, and it compounds two causes: podcast
titles are literally "Episode 7" with the show's name in the summary (weight B),
so the forum posts *announcing* the episode carry "Space Surf" at weight A and
outrank the episode itself, and then length normalization pushes the 1,635-byte
item down for good measure.

### 3.3 Why `normalization=0` is not the fix either

Tempting, because it lifts the first `backing track` download from #47 to #2 and
gives a genuinely blended, non-date-ordered list. But over the 20-query set, the
top-10 type mix moves like this:

| type | `norm=1` | `norm=0` |
|---|---:|---:|
| forums.topic | **121** | 5 |
| forums.post | 71 | **177** |
| download + link + item + story | 6 | 17 |

It nearly triples curated-type surfacing — and it all but eliminates forum
topics, 121 → 5, by removing the only thing that was distinguishing them. Thread
titles are the site's natural navigational answer and the old search's primary
result; trading them away to rescue 11 rows is a bad exchange. Inspection agrees:
`surf music` under `norm=0` returns long-titled posts where `norm=1` returns the
threads actually named "Surf music".

Modes 2, 16 and 32 were measured too (first `backing track` download at #47, #33
and #2 respectively; 32 is order-equivalent to 0, being monotonic in rank).

### 3.4 Recommendation

**Keep `normalization=Value(1)`. Nothing to change in code, and no reindex.** It
serves the dominant case — finding threads about a subject — well, and the query
set confirms it: `spring reverb`, `tremolo picking`, `Los Straitjackets`,
`Fender Jaguar`, `outboard reverb tank`, `Surfy Bear` and `6G15` all return top
tens that are hard to fault.

**Fix cross-type burial with task 09 (per-type counts) instead.** A member
searching `backing track` who sees `Downloads (115)` beside `Forum Posts (3,256)`
gets there in one click, and the counts cost +0.9% if they replace the
paginator's `COUNT` rather than being added alongside it. That is a better
instrument than re-tuning a global ranking knob, because the burial is not a
ranking error within a type — it is a *volume* problem between types, and 444,134
forum posts against 673 downloads is not something a rank multiplier fixes
honestly.

**If a boost is wanted anyway**, the magnitude needed is small and is recorded
here so the option stays open: lifting the first `backing track` download
(`0.3530`) past that query's tenth result (`0.4268`) needs **≈1.21×**. Applying a
per-type multiplier is a query-time change, so it is cheap to try and cheap to
revert — but it is tuning by hand, and it should not be done without the counts
in place to tell whether it helped.

**Weights are untouched.** No evidence emerged for changing the A/B/C bands, and
doing so costs a full reindex (§5).

---

## 4. Performance

### 4.1 The GIN index is used

Every plan captured — top-10 slice, paginator `COUNT`, and `OFFSET 1000` — is a
`Bitmap Index Scan on search_sear_search__b5d516_gin` feeding a bitmap heap scan.
**No sequential scan on `search_searchdocument` appears anywhere.** For the
worst-case term the index scan itself returns 166,388 rows in **7.9 ms**; the
rest of the time is heap access and ranking.

One incidental confirmation from the plans: `ts_headline` is projected in a
`Result` node *above* the sort, so it runs for the ten rows returned rather than
for every match. That is the difference between 160 ms and something far worse,
and it happens because `rank` is the sort key and `headline` is not.

### 4.2 Latency, warm cache, median of five runs

Measured through `search_documents`, forcing the `highlighted` and `result_label`
properties the template renders, and timing the paginator `COUNT` separately
because a search page pays both.

| kind | query | hits | count ms | page ms | **total ms** |
|---|---|---:|---:|---:|---:|
| worst | `surf` | 156,517 | 56.9 | 101.9 | **158.8** |
| phrase | `"surf music"` | 27,673 | 73.5 | 94.5 | **168.0** |
| common | `guitar` | 92,618 | 68.6 | 86.0 | 154.6 |
| 2-term | `surf guitar` | 41,873 | 45.8 | 89.2 | 134.9 |
| common | `reverb` | 54,065 | 45.3 | 83.7 | 129.0 |
| exclude | `reverb -fender` | 38,340 | 37.1 | 63.8 | 100.9 |
| typical | `spring reverb` | 6,050 | 2.6 | 7.5 | **10.1** |
| typical | `Los Straitjackets` | 4,297 | 1.6 | 5.9 | 7.5 |
| narrow | `FRV-1` | 2,024 | 1.2 | 2.3 | 3.5 |
| rare | `Sundazed Music` | 277 | 0.5 | 1.2 | 1.7 |
| narrow | `RE-201` | 17 | 0.3 | 0.9 | 1.3 |

`surf` is the true worst case — it matches 30% of the corpus. Nothing common is
slower; `a` and `the` are stop words and match nothing.

### 4.3 The rate-limiting deferral: the number, honestly

The design deferred rate limiting on the stated grounds that a GIN lookup over
~490k rows "should be milliseconds", despite the site's history of bots. That
holds for typical queries — **1.3–10 ms**, comfortably — but **not** for the
broadest ones, which are **~160 ms**, two orders of magnitude off "milliseconds".

Read plainly: one core saturates at roughly **6 requests/second** of `?q=surf`.

**The deferral still stands, but not for the reason given.** What is actually
carrying the load is that `/search/` is login-gated — the defence adopted after
bots were killing the site — which is what keeps an anonymous flood off this path
entirely. Speed is a secondary line, and a thinner one than the design assumed.
If the login gate is ever relaxed, rate limiting has to be reconsidered in the
same change, and this paragraph is the reason why.

---

## 5. Not fixed, and why

**Misirlou / Miserlou — the site's signature tune is split across two spellings
and neither query finds the other.**

| | documents |
|---|---:|
| match `misirlou` | 1,416 |
| match `miserlou` | 2,131 |
| match **both** | 148 |

Roughly 3,400 documents are about this one song, and either spelling reaches at
most 63% of them. The *misspelling* is the more common form on the site. Stemming
does not bridge it and neither would `'simple'`; it needs either a synonym
dictionary (`CREATE TEXT SEARCH DICTIONARY`, a config change and a full reindex)
or trigram similarity via `pg_trgm` as a fallback when a query returns little.
Both are real features, not tuning. **Deferred to Step 20** with this measurement
attached.

**Weight changes** — none proposed, none applied. Flagged per the task's
requirement that nothing touching the stored vector be changed unilaterally: a
weight change is one `UPDATE` over 516,858 rows, which task 02 measured at 3.5×
the cost of a build.

**Hyphen asymmetry** (§2.1) — `surf-rock` finding 1,328 where `surf rock` finds
14,993 is correct behavior, and the tips block is accurate as written. Whether to
spend a line of tips copy explaining that hyphens narrow is a judgement about
site voice, left to the owner rather than taken here.

---

## 6. Acceptance criteria

| # | criterion | result |
|---|---|---|
| 1 | ranking assessed on real queries | 34-query set, §3; systematic problem identified |
| 2 | cross-type surfacing verified | **failure documented with recommendation**, §3.2–3.4 |
| 3 | hyphenation settled | §2.1 — conclusive; tips block verified correct already |
| 4 | text config decided on evidence | §2.2 — `'english'`, no reindex |
| 5 | GIN index actually used | §4.1 — confirmed in every plan |
| 6 | latency measured | §4.2; deferral re-justified honestly in §4.3 |
| 7 | findings recorded | this file; stored vector untouched |
