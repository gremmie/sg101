# Task: Show Per-Type Result Counts on the Search Page

## Description
After a search, show how many matches each of the eight types holds — `Forum
Posts (51,543)`, `News Stories (243)` — next to the checkbox that selects it, so
a member can see where their answer actually lives before narrowing.

This is new behavior, not restoration. The Xapian search never had it. It is
proposed because measurement during task 04 showed the search page asks members
to make a choice they have no evidence for.

## Background
**The problem is a distribution nobody can see.** A search for `reverb` over the
real index returns 54,065 documents:

| Type | Hits |
|---|---|
| Forum Posts | 51,543 |
| Forum Topics | 2,006 |
| News Stories | 243 |
| User Profiles | 156 |
| Downloads | 64 |
| Links | 39 |
| Podcasts | 14 |

95% of that is forum posts, so an all-types search buries the 243 news stories
and the 39 links completely. The site owner's instinct during task 04 review was
exactly right — searching everything is rarely what a member wants — and the
checkboxes now start unchecked partly for that reason.

But unchecked boxes do not solve it. A member cannot know in advance which type
holds their answer; that is what the counts are for. Pre-filtering asks for a
guess, and post-search facets replace the guess with evidence. This is why
faceted search generally narrows *after* the query rather than before it.

**It is cheap here, and that is not an accident.** Because the index is one
table with a `content_type` column rather than a vector per model, the counts are
a `GROUP BY` over a query already being run.

**But only if the counts replace the pagination count rather than joining it.**
The facet query and the paginator's `COUNT(*)` scan the same matched set for the
same money, so adding one alongside the other costs 23–40% more per search. The
facet counts, though, *sum* to the total — summing them across the selected
types equals what `.count()` returns, verified including the two-type case that
spans the `forums.Post`/`ygroup.Post` split. So the paginator can be handed a
count derived from the facets, and the page still issues two queries rather than
three. Measured on the full 516,858-document index:

| Query | Hits | Now (count + page) | Facets replacing count | Delta |
|---|---|---|---|---|
| `reverb` | 54,065 | 0.129s | 0.130s | +0.9% |
| `-fender` | 470,846 | 0.191s | 0.196s | +2.7% |

Adding the facet query *without* removing the count instead costs +36% and +40%
on those same two searches.

**The one real design decision** is which match set the counts describe. They
must be computed over the query with the *type filter removed* — otherwise
selecting `News Stories` collapses every other type's count to zero, and the
member loses the very information they came for. So the counts always answer
"how many would I get if I checked this box", independent of what is checked
now. That is standard faceting behavior and it is the only version that helps.

That has a consequence for `search/query.py`: `search_documents()` currently
applies the type filter inside the one queryset it returns. Producing counts
means separating the matched set from the type filter, so the same tsquery can
be spent twice — once filtered and ordered for the result page, once grouped for
the counts.

**Two traps, both found by prototyping this against real data, and both of which
produce plausible-looking wrong numbers rather than an error:**

*Clear the ordering before aggregating.* `search_documents()` returns a queryset
ordered by `-rank, -date`. Calling `.values(...).annotate(Count(...))` on it
without clearing that ordering first puts the ordering columns into the `GROUP
BY`, so every row becomes its own group and **every count comes back as 1**. An
explicit `.order_by()` on the aggregate queryset is what prevents it.

*Group on `content_type_id`, not the model name.* `forums.Post` and
`ygroup.Post` are both named `post`, so grouping by `content_type__model` merges
them: the pair reported 51,543 together where the true split is 47,004 forum
posts and 4,539 archive posts. This is the same collision that made task 04 give
each document an explicit `result_label`.

With both handled, the counts agree exactly with a per-type filtered search
across all eight types — verified on the live index.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `search/query.py` — the read path this extends
- `search/forms.py` — where the checkbox choices come from
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md`
  (Q1–Q2, the ordering and single-box decisions this builds on)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Split `search/query.py` so the matched set (tsquery, no type filter) can be
   reused: one path filters and orders it for the result page, another groups it
   by `content_type` for the counts.
2. Return counts for all eight types, including zeros, keyed by content type so
   the form can pair each with its checkbox — never by model name, which
   collides. Registry order throughout, as elsewhere.
3. Compute counts over the type-unfiltered match set, so a count never changes
   because of what is currently checked.
4. Render the count beside each checkbox label, only after a search has run.
   The landing page shows labels alone.
5. Do not run the counts query when the form is invalid or unbound.
6. Derive the paginator's total from the facet counts rather than letting it
   issue its own `COUNT(*)`, so a search still costs two queries. Summing the
   facets over the selected types is that total.
7. Leave ranking, the login gate and query logging untouched. Pagination changes
   only in where its total comes from — page size, page links and the
   out-of-range 404 all stay as they are.

## Dependencies
- Task 04 (the view, form and query module this extends)
- A populated index to test against

## Implementation Approach
1. Restructure `search_documents()` first, with the existing tests green, before
   adding anything new — the split is the whole change and everything else is
   presentation.
2. Add the counts query and confirm against real data that the numbers match
   what a type-filtered search actually returns for each type.
3. Wire the counts into the form's rendered choices, then the template.
4. Re-measure on the real index once wired up, and confirm a search still issues
   two queries rather than three — `assertNumQueries` or the debug toolbar's SQL
   panel will show it directly.

## Acceptance Criteria

1. **Counts Match Reality**
   - Given a query matching several types
   - When the counts render
   - Then each equals the hit count that same query returns with only that type
     checked — asserted per type, since both known failure modes (an uncleared
     ordering, a name collision) yield numbers that look reasonable in isolation

2. **Counts Are Independent of the Current Selection**
   - Given a search narrowed to one type
   - When the counts render
   - Then the other types still show their full counts, not zero

3. **Zero Is Shown, Not Hidden**
   - Given a query no document of some type matches
   - When the counts render
   - Then that type shows zero rather than disappearing

4. **The Landing Page Is Unchanged**
   - Given no search has run
   - When the page renders
   - Then labels carry no counts and no counts query is issued

5. **Nothing Else Moves**
   - Given the change
   - When a search runs
   - Then ranking, ordering, pagination, the login gate and the logged line are
     as they were

6. **A Search Costs No More Queries Than Before**
   - Given a search that returns results
   - When the page renders
   - Then it issues the same number of queries it did without the counts, the
     paginator's total having come from the facets rather than its own `COUNT(*)`

7. **The Displayed Hit Count Still Matches the Selection**
   - Given a search narrowed to some types
   - When the page renders
   - Then the headline hit count is the total for those types only, not for all
     eight

8. **Suite Green**
   - Given the change
   - When the suite runs on PostgreSQL
   - Then it is green, with the counts covered

## Metadata
- **Complexity**: Medium
- **Labels**: Search, PostgreSQL, Faceting, Views, Templates, Step 12
- **Required Skills**: Django ORM aggregation, `django.contrib.postgres` search
