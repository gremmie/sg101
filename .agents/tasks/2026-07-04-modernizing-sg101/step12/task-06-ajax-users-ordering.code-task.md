# Task: Give `core.views.ajax_users` a Deterministic Order

## Description
`core.views.ajax_users` backs the username autocomplete. It returns a `LIMIT`ed
slice of matching usernames with **no `ORDER BY`**, so which ten of the matches a
user sees is undefined. Add an explicit ordering and correct the test that
currently asserts an order SQL never promised.

This is unrelated to the search index — it is folded into Step 12 because the
user autocomplete is search-adjacent and the defect was found during Step 11.

## Background
Found during Step 11 task 02 (2026-07-25) and parked here deliberately.

The view runs `.values_list('username', flat=True)[:limit]` against the matching
users. Without an `ORDER BY`, SQL makes no promise about which rows a `LIMIT`
returns — and against real data the match sets are large:

| Prefix | Matching active users |
|---|---|
| `bri` | 28 |
| `su` | 435 |
| `a` | 579 |
| `j` | 884 |

So a `LIMIT 10` picks an arbitrary ten of up to 884. If the person you want is
not among them, they never appear and the UI gives no hint that more exist.
Postgres does not improve this and can make it *less* stable than MySQL was,
since heap order shifts as rows are updated.

**The existing test is part of the defect.**
`core.tests.test_views.AjaxUsersTestCase.test_happy_path` asserts insertion
order, which no engine guarantees. It passes on sqlite and Postgres by
query-plan luck and **fails on MySQL today** — confirmed against unmodified
code, so this is pre-existing, not something Step 11 introduced.

**The fix is one line in each place.** Add `.order_by('username')` to the view and
change the test to expect alphabetical order. The sort is free at 15,227 rows,
and alphabetical is the conventional autocomplete behavior.

Weakening the test to `assertCountEqual` is the lesser alternative if the view is
to be left alone — but it leaves the arbitrary-ten behavior in place, so prefer
the ordering fix.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 12, the "FOLD IN" note recording this finding)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add `.order_by('username')` to the queryset in `core.views.ajax_users` before
   the slice is taken.
2. Update `AjaxUsersTestCase.test_happy_path` to assert alphabetical order rather
   than insertion order.
3. Check the autocomplete's other callers — `bio.SearchUsersForm`
   (`bio/forms.py:128`) wires this endpoint via `data-autocomplete-url` — and
   confirm nothing depends on the previous arbitrary ordering.
4. Do not change the limit, the matching semantics, or the response shape. This
   is an ordering fix only.

## Dependencies
- None beyond the current codebase

## Implementation Approach
1. Confirm the defect: query a common prefix twice against Postgres and observe
   that the returned slice is not guaranteed stable.
2. Add the ordering, update the test, and confirm the test now fails without the
   view change and passes with it.

## Acceptance Criteria

1. **Results Are Deterministic**
   - Given a prefix matching more users than the limit
   - When the endpoint is called repeatedly
   - Then the same usernames come back every time, in alphabetical order

2. **Test Asserts a Real Guarantee**
   - Given the updated test
   - When the view's `order_by` is reverted
   - Then the test fails — it must be sensitive to the fix rather than passing by
     query-plan luck

3. **Behavior Otherwise Unchanged**
   - Given the endpoint
   - When it is called
   - Then the limit, matching semantics and response shape are as before

4. **Suite Green**
   - Given the change
   - When the suite runs on PostgreSQL
   - Then it is green

## Metadata
- **Complexity**: Low
- **Labels**: Bug Fix, Django ORM, Autocomplete, Test Correctness, Step 12
- **Required Skills**: Django ORM, SQL ordering semantics
