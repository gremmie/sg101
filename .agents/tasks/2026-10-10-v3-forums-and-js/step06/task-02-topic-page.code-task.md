# Task: Port the topic page and the post card to the V3 design

## Description
Move `/forums/topic/<id>/` onto `v3/base.html` from `v3-dev`'s
`topic.html`, with its new per-post card `display_post_v3.html` and its reply
form `new_post_form.html`. Cards alternate colour by CSS `:nth-child` instead
of `{% cycle %}`, and the post box loads as the ES module from steps 2 to 5.
The card stays as `v3-dev` left it. Completing it with everything in R14 is
step 7.

## Background
`v3-dev` built the topic page in `cafc1361`, `4071a09d` and `75592992`, and
left it work in progress. Research topic 1 lists what its card lacks: the post
anchors, the per-post tools, attachments, signatures, "Last edited", PM and
email links, the stranger highlight, and the IP link. **Those are step 7's,
not this task's.** This task brings the page up and makes it correct to look
at, for task 03's screenshots.

What changes from `v3-dev`:

- **`{% load static %}`:** `topic.html` still has `{% load static from
  staticfiles %}`, which fails to load on Django 5.2.
- **Card colours.** `v3-dev` cycles `sg101-card1`/`sg101-card2` and the
  matching divider classes into `card_class` and `card_divider_class`
  (`topic.html` lines 36 and 37). Replace these with one card class and an
  `:nth-child(odd)`/`(even)` rule on the posts in
  `#forum-topic-post-container` (design §4.4). A post appended later by quick
  reply then gets the right colour on its own. The colours are `v3-dev`'s:
  surf green and blue, at 50%.
- **Scripts.** `v3-dev` loads `jquery-ui`, `jquery.form`, `forums.js` and the
  2017 `js/v3/post_box.js`. On `main` the post box is
  `js/v3/post_box/post_box.js`, loaded with `type="module"` as on news
  submit. `forums.js` targets the old table markup and is replaced in step 7,
  so **leave it out**. Quick reply, flag and delete don't work on this
  branch until then, and that is expected (plan, step 6). Load jQuery UI only
  if something on the page still uses it.
- **The modals.** `new_post_form.html` includes
  `core/v3/post_box_modals.html`. Step 4 found a page that included it twice
  (`download_detail.html`), so check `topic.html` includes it once.
- **`quick_reply_ajax`** renders `display_post_v3.html` instead of
  `display_post.html`, as `v3-dev` did. Its context must give the card what
  it needs without the cycle variables.
- **`topic_index`** adds `'V3_DESIGN': True` and drops `page_nav`, as in task
  01.

`new_post_form.html` hard-codes a help link, `/forums/topic/18843/`. Keep it
as `v3-dev` has it, and note it for step 8, which builds the video button and
the attachment list.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§2.4 R12 and R14, §4.4, §7.2)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/research/v3-dev-forums.md (what the topic page lacks)
- .agents/planning/2026-10-10-v3-forums-and-js/research/playwright.md (the browser test setup)
- .agents/planning/2026-10-10-v3-forums-and-js/STATUS.md (step 4's doubled modals include; earlier browser-test traps)
- `core/tests/browser.py` (`BrowserTestCase`, which fails a test on any uncaught page error)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Bring over `forums/topic.html`, `forums/display_post_v3.html` and
   `forums/new_post_form.html` from `v3-dev`. Diff each against `main` first
   and keep mainline changes other than the `staticfiles` line.
2. Remove the two `{% cycle %}` lines. Use one card class, and colour the cards
   with `:nth-child` rules in `_sg101.scss`. Rebuild and commit
   `main.min.css`.
3. Load the post box as `js/v3/post_box/post_box.js` with `type="module"`.
   Don't load `forums.js`, `jquery.form`, or the 2017 `post_box.js`.
4. `topic_index` adds `V3_DESIGN` and drops `page_nav`. `quick_reply_ajax`
   renders `display_post_v3.html`.
5. `display_post.html` stays: the unconverted list and moderator pages still
   use it.
6. A browser test under `@tag('browser')`, on `BrowserTestCase`: the topic
   page loads as a member, with no page errors.

## Dependencies
- Task 01: the Sass colour variables, the navigation and jump box fragments,
  and the V3 pagination.
- Steps 2 to 5: the post box modules and modals.

## Implementation Approach
1. Diff the three templates between `v3-dev` and `main`.
2. Write the render tests and the browser test first, and watch them fail on
   today's topic page.
3. Port the templates and the views, then the card Sass. Rebuild the CSS.
4. Check the colours alternate in a browser: one topic with an odd number of
   posts, and one with an even number, at desktop and phone widths.
5. Run `make test-browser`, the full suite, then the deprecation gate, one at
   a time.
6. Mutation-check: put `forums.js` back on the page (or break the module's
   import) and confirm the browser test fails. Point the template back at
   `base.html` and confirm the render test fails. Restore, and confirm the
   files are byte-identical.

## Acceptance Criteria

1. **The topic page renders on the V3 design for each role**
   - Given a topic with posts, and an anonymous visitor, a member, and a moderator
   - When each requests `/forums/topic/<id>/`
   - Then each gets 200 from `v3/base.html`, with every post on the page in the response

2. **Cards alternate by CSS**
   - Given a topic page
   - When it is rendered
   - Then every card has the same class, the template has no `{% cycle %}`, and the stylesheet has the `:nth-child` rules

3. **The post box is the module**
   - Given a member who can reply on the last page of a topic
   - When the page is rendered
   - Then it loads `js/v3/post_box/post_box.js` as a module, includes the post box modals once, and doesn't load `forums.js`

4. **Quick reply renders the V3 card**
   - Given a member posting through `/forums/quick-reply/`
   - When the reply is accepted
   - Then the response is rendered from `display_post_v3.html`

5. **The page loads clean in a browser**
   - Given a member on a topic page in headless Chromium
   - When the page loads
   - Then no uncaught page error is reported

6. **Tests are seen to fail**
   - Given the new tests
   - When each is run against a deliberate defect it guards
   - Then it fails, and passes again once the defect is removed

## Metadata
- **Complexity**: Medium
- **Labels**: forums, templates, V3 design, Sass, ES modules, Playwright
- **Required Skills**: Django templates and views, CSS selectors, Playwright for Python
