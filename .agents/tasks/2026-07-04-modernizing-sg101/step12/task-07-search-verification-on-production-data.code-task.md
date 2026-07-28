# Task: Verify Search Quality and Performance Against Production Data

## Description
With the index populated and the UI working, verify the things a green test suite
cannot tell you: whether results are actually *good*, whether queries are fast at
490k rows, and whether two assumptions carried through the design hold against
real content.

Step 11 task 05 is the precedent for this task existing at all. That verification
found four defects invisible to row counts, column diffs and the entire test
suite. Search has the same property — a suite can prove a query returns rows, not
that the right rows come back first.

## Background
Four things are checked, in order of how likely they are to change something:

**1. Relevance quality across types.** Blended ranking is the design's biggest
bet. `normalization=Value(1)` plus `setweight` A/B/C is a reasoned starting point,
not a measured one. The corpus is 94% forum posts, so the risk is that weblinks,
downloads and podcast items rarely surface even when they are the best answer.
Normalization is a *query-time* argument — revising it is a one-line change. The
weights are baked into the stored vector, so changing those means a full reindex
via task 02. Tune normalization freely; change weights only with evidence.

**2. Is the `FRV-1` limitation actually gone?** The old tips block apologises that
the Xapian indexer stripped punctuation, so `FRV-1` found nothing and users were
told to search `FRV 1` instead. Postgres's parser emits both the whole hyphenated
token *and* its parts, so this limitation may simply not exist any more. Confirm
against real data — and if it is gone, say so in the tips rather than carrying
forward an apology for a problem that was fixed by the engine change. Task 04
deliberately left that claim in the template pending this check.

**3. `'english'` versus `'simple'`.** The design assumes the `'english'` text
search configuration, which stems. But band and song names are a large share of
what members search for on this site, and not all of them are English words.
Stemming can help (`reverbs` → `reverb`) or hurt (mangling a band name into
something that matches unrelated content). `'simple'` — no stemming — is the
alternative. Decide on evidence from real queries, and note that changing this is
*not* free: it changes how vectors are built, so it means a full reindex.

**4. Query performance.** A GIN index lookup over ~490k rows should be
milliseconds, and that assumption is load-bearing — it is the stated reason rate
limiting was deferred in the design despite the site's history of bots hammering
search. If common queries are not fast, that deferral needs revisiting.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§4 "Corpus, measured", §6 "Carried into implementation")
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q8 score scaling, Q10 abuse defence)
- `.agents/tasks/2026-07-04-modernizing-sg101/step11/task-05-data-integrity-verification.code-task.md`
  — the precedent for this kind of verification pass

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Assemble a **query set representative of real use** — surf-guitar vocabulary,
   band names, member handles, gear terms, hyphenated model numbers, misspellings.
   Draw on the site's actual content rather than inventing terms.
2. For each query, record what comes back and judge whether the top results are
   the right ones. Ranking quality is a judgement call — record the judgement and
   the reasoning, not just the output.
3. Explicitly test **cross-type comparability**: queries where the best answer is
   a weblink, a download or a podcast item competing against thousands of forum
   posts. This is the case normalization exists to handle.
4. Determine whether hyphenated tokens (`FRV-1`) now work. Update the tips block
   in `search.html` to match reality either way.
5. Compare `'english'` and `'simple'` on the representative query set. Recommend
   one, with evidence. If the recommendation is `'simple'`, state the reindex cost
   explicitly and treat the change as a decision for the owner, not an
   implementation detail to apply silently.
6. Measure query latency against the full index — typical and worst case, with
   `EXPLAIN ANALYZE` for anything slow. Confirm the GIN index is actually used;
   a sequential scan over 490k rows would be a silent performance failure that
   returns entirely correct results.
7. Record findings in the planning directory. Anything that changes the stored
   vector must be flagged rather than applied unilaterally.

## Dependencies
- Tasks 01–05 complete, with the full backfill from task 02 loaded
- The converted production snapshot from Step 11

## Implementation Approach
1. Build the query set and capture baseline results and timings.
2. Work through hyphenation and the stemming comparison — both are concrete
   yes/no checks, unlike ranking quality.
3. Assess ranking, focusing on the cross-type cases.
4. Tune `normalization` if warranted and re-measure; propose weight changes only
   with evidence, since they cost a full reindex.
5. Write up findings, update the tips block, and list anything deferred.

## Acceptance Criteria

1. **Ranking Assessed on Real Queries**
   - Given a representative query set run against the full index
   - When results are reviewed
   - Then each query has a recorded judgement of whether the top results are
     right, and any systematic problem is identified

2. **Cross-Type Surfacing Verified**
   - Given queries whose best answer is a weblink, download or podcast item
   - When they are run against an index that is 94% forum posts
   - Then those results surface, or the failure is documented with a
     recommendation

3. **Hyphenation Question Settled**
   - Given a search for `FRV-1` and similar hyphenated terms
   - When run against real content
   - Then whether they match is determined conclusively and the tips block
     reflects the actual behavior

4. **Text Search Configuration Decided on Evidence**
   - Given `'english'` and `'simple'` compared over the query set
   - When the comparison is complete
   - Then one is recommended with supporting evidence, and the reindex cost is
     stated if a change is proposed

5. **Index Is Actually Used**
   - Given a representative query
   - When `EXPLAIN ANALYZE` is run
   - Then the GIN index is used rather than a sequential scan

6. **Latency Measured**
   - Given the full ~490k-row index
   - When typical and worst-case queries run
   - Then latencies are recorded, and if they undermine the assumption behind
     deferring rate limiting, that is called out explicitly

7. **Findings Recorded**
   - Given the verification pass
   - When it completes
   - Then findings live in the planning directory, and no change to the stored
     vector has been applied without being flagged for a decision

## Metadata
- **Complexity**: Medium
- **Labels**: Search, PostgreSQL, Verification, Performance, Relevance Tuning,
  Step 12
- **Required Skills**: PostgreSQL full-text search internals and `EXPLAIN
  ANALYZE`, relevance evaluation, familiarity with the site's subject matter
