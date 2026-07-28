# Task: Restore the Forums Duplicate-Topic Quick Search

## Description
Bring back `/search/ajax/` — the duplicate-topic check on the forums' new-topic
form. The button, the JavaScript and the result template all survived Step 4;
only the view behind them is gone, and the route currently points at a
placeholder.

Fix the pre-existing markup bug in the fragment template while restoring it.

## Background
This is not a general-purpose AJAX search. It is one narrow feature: as a member
types a new topic title, `forums/static/js/forums.js:302` posts it to
`/search/ajax/` restricted to `forums.topic`, and the matches render inline so the
poster can see whether their question already exists. It is the one place on the
site where search prevents work rather than merely finding things.

**What survived Step 4 and should be reused, not rewritten:**
- `forums/static/js/forums.js` around lines 291–321 — the button handler, the
  busy icon, the results container and its hide toggle.
- `sg101/templates/search/search_ajax.html` — the fragment the view returns.

Rebuilding this as a JSON endpoint with client-side rendering was considered and
rejected: it rewrites working JavaScript for no user-visible gain.

**The JS hardcodes the path** `'/search/ajax/'` rather than reversing a route
name, so task 04's route rename does not affect it — but that also means the URL
path must not change. Worth a comment so the coupling is visible.

**The pre-existing markup bug:** in `search_ajax.html`, the closing `</fieldset>`
and `</div>` sit inside the `{% else %}` branch, so neither closes when there
*are* results — which is precisely the case a member sees when the feature is
doing its job. Fix it as part of this task.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/step12-idea-honing.md` (Q7)
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-design.md`
  (§6 "Carried into implementation")
- `git show pre-step-4-prune` — the deleted AJAX view, for reference

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Implement the view behind `/search/ajax/`, reusing the same query machinery as
   task 04 restricted to `forums.Topic`, and returning the existing fragment
   template.
2. Keep the URL path exactly `/search/ajax/` — the JavaScript hardcodes it. Rename
   only the route name, in step with task 04.
3. Apply the same login gate as the main search view. The new-topic form is
   already members-only, so this should be a no-op in practice, but the endpoint
   must not be independently reachable by anonymous clients.
4. Fix the unclosed `</fieldset>` / `</div>` in `search_ajax.html` so the markup
   is well-formed in both the results and no-results branches.
5. Handle an empty or whitespace-only title without erroring — the JS can fire on
   a partially typed field.
6. Do not modify `forums.js` beyond what is strictly required; it works.

## Dependencies
- Task 01 (the model), task 02 (a populated index), task 04 (the shared query
  logic this view reuses — factor it so both views share one implementation)

## Implementation Approach
1. Recover the deleted AJAX view from `pre-step-4-prune` to see its exact
   contract with the template.
2. Implement the view against `SearchDocument` filtered to `forums.Topic`.
3. Fix the template markup and verify both branches render well-formed HTML.
4. Exercise it in the running stack from the actual new-topic form, not just by
   curling the endpoint.

## Acceptance Criteria

1. **Duplicate Topics Are Found**
   - Given an existing forum topic and a member on the new-topic form
   - When they type a title matching it and trigger the check
   - Then the matching topic renders inline in the results fragment

2. **No Matches Renders Cleanly**
   - Given a title matching no existing topic
   - When the check runs
   - Then the no-results branch renders and the markup is well-formed

3. **Results Branch Markup Is Fixed**
   - Given a title that does match
   - When the fragment renders
   - Then `<fieldset>` and its containing `<div>` are both properly closed

4. **Only Topics Are Searched**
   - Given forum posts, news stories and profiles matching the typed title
   - When the check runs
   - Then only `forums.Topic` results are returned

5. **Anonymous Access Is Refused**
   - Given an anonymous client
   - When it requests `/search/ajax/` directly
   - Then it is refused, consistently with the main search view

6. **Empty Input Is Harmless**
   - Given an empty or whitespace-only title
   - When the check fires
   - Then the endpoint responds without error and runs no query

7. **Unit Test Coverage**
   - Given the implementation
   - When the suite runs on PostgreSQL
   - Then the endpoint has tests for matches, no matches, type restriction, the
     login gate and empty input, and the suite is green

## Metadata
- **Complexity**: Low
- **Labels**: Search, Forums, AJAX, Templates, Step 12
- **Required Skills**: Django views and templates, PostgreSQL full-text search,
  basic jQuery familiarity
