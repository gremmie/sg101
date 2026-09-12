# Task: The Two Index Decisions Deferred Out of Step 12

## Description
Add the member-autocomplete index Step 12 measured and deferred, and decide the
spelling-variant question it left open.

## Background
Step 12 closed with two items explicitly deferred to Step 20, each with its
measurement already attached:

- **A `UPPER(username)` functional index for the member autocomplete**, measured
  at **2.7 ms → 0.48 ms**. The measurement exists; only the index does not.
- **The Misirlou/Miserlou spelling split**, which needs either a synonym
  dictionary or `pg_trgm`, and which was deferred because it is a design choice
  rather than an omission.

**The autocomplete index carries a caveat recorded with it**: the plan notes it
should be revisited with real traffic and dropped if the autocomplete turns out to
be rare. A 2.2 ms saving on an operation nobody performs is not worth an index to
maintain. So this task decides on evidence, and dropping it is an acceptable
outcome.

**The spelling question is a genuine fork.** A synonym dictionary is exact,
cheap at query time, and requires knowing the variants in advance. `pg_trgm` is
general, catches variants nobody enumerated, and costs more per query and an
index. Surf music has a long tail of transliterated titles, which argues one way;
the site's search volume is modest, which argues the other.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md` — the
  Step 12 search design these two items were deferred out of
- `.agents/planning/2026-07-04-modernizing-sg101/STATUS.md` — *Deferred out of
  Step 12, each with its measurement attached*

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Measure how often the member autocomplete is actually used, from the query
   logging that already exists, before adding its index.
2. If the usage justifies it, add the `UPPER(username)` functional index as a
   Django migration, and re-measure to confirm the improvement holds on production
   data volumes.
3. If it does not, record the decision not to add it, with the usage figure that
   settled it.
4. Decide the spelling-variant approach — synonym dictionary or `pg_trgm` — and
   record the reasoning, not only the choice.
5. Implement the chosen approach, with tests covering the Misirlou/Miserlou case
   that prompted it.

## Dependencies
- The existing search query logging, one `INFO` line per search
- A production-sized database for any timing measurement to mean anything

## Implementation Approach
1. Read the query logs for autocomplete usage; this decides whether requirement 2
   or 3 applies.
2. Add the index as a migration if it is warranted, and re-time against a
   production-sized dataset rather than a fixture.
3. Prototype both spelling approaches against the real corpus, on the actual
   failing query, before choosing.
4. Implement the chosen approach with tests that fail without it.

## Acceptance Criteria

1. **The autocomplete decision rests on usage**
   - Given the search query logs
   - When autocomplete usage is counted
   - Then the figure is recorded, and the decision to add or skip the index cites
     it

2. **The index, if added, is a migration and measurably helps**
   - Given the index is warranted
   - When it is applied to a production-sized database and the query re-timed
   - Then the improvement is recorded, and the index arrives via a Django
     migration rather than by hand

3. **The spelling approach is chosen with reasons**
   - Given both approaches prototyped against the real corpus
   - When one is selected
   - Then the reasoning is recorded, including what the rejected one would have
     cost

4. **The case that prompted it works**
   - Given the chosen implementation
   - When a search for one spelling is run
   - Then results for the other spelling are returned, covered by a test that
     fails without the change

5. **The suite stays green**
   - Given the full test suite
   - When it is run
   - Then it passes

## Metadata
- **Complexity**: Medium
- **Labels**: PostgreSQL, Full-Text Search, Indexing, Measurement
- **Required Skills**: PostgreSQL indexing, Django migrations, text search configuration
