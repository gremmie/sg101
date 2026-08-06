# Task: Bump Markdown, Rewrite the Custom Extensions, and Stop Rebuilding the Parser Per Call

## Description
Move `Markdown` off the 2.6.11 pin — which requires rewriting both of the
project's custom extensions against Markdown 3.x's changed extension API — then
address the two things that live in the same code and are worth fixing while
someone is in there: the `MARKDOWN` logger's asymmetry between settings modules,
and `core/markup.py` constructing a fresh parser on every single call.

## Background
**The plan under-scoped this one, and the under-scoping is the finding.** Step
13 frames the Markdown bump as the occasion for revisiting the logger. Checking
the code on 2026-08-03 shows the bump itself is the larger piece: **both custom
extensions use the pre-3.0 extension API and cannot load on Markdown 3.x.**

`core/mdexts/deleted.py`:
```python
def extendMarkdown(self, md, md_globals):          # md_globals dropped in 3.0
    del_tag = markdown.inlinepatterns.SimpleTagPattern(DEL_RE, 'del')
    md.inlinePatterns.add('del', del_tag, '>not_strong')   # Registry.add() gone
```

`core/mdexts/urlize.py`:
```python
def extendMarkdown(self, md, md_globals):          # same signature change
    md.inlinePatterns['autolink'] = UrlizePattern(URLIZE_RE, md)  # item assignment
...
el = markdown.util.etree.Element("a")              # markdown.util.etree removed
```

Four distinct API changes across two small files:
1. `extendMarkdown(self, md, md_globals)` → `extendMarkdown(self, md)`
2. `md.inlinePatterns.add(name, obj, placement)` → `Registry.register(obj, name,
   priority)` — a **numeric priority** replaces the `'>not_strong'` relative
   placement, so the ordering must be re-derived rather than transliterated
3. `md.inlinePatterns['autolink'] = ...` — registry item assignment
4. `markdown.util.etree` → `xml.etree.ElementTree` directly

Verify each against the changelog for the version actually chosen; the details
differ across the 3.0 → 3.4 span and this list is a starting inventory, not a
patch. Note also that `SimpleTagPattern` was superseded by an inline-processor
class with a different `handleMatch` contract.

**These two extensions are user-visible markup.** `DelExtension` implements
`---struck text---` and `UrlizeExtension` replaces autolinking site-wide. Both
run on every rendered post. A silently mis-registered pattern will not raise —
it will just stop striking text or stop linking URLs, across 444,000 forum
posts.

### The MARKDOWN logger

`sg101/settings/local.py:118` and `sg101/settings/production.py:147` both
configure a `MARKDOWN` logger at `WARNING`, `propagate: False`, file handler.
The entry dates from 2014 (`bdc8901`), when Markdown logged at INFO every time
it loaded an extension. **Upstream fixed that** — 2.6.11 has no `.info()` calls
left and those messages are `debug()` now — so the original reason is gone.

**It is not dead config, though.** `local.py` sets the root logger to DEBUG and
`docker.py` inherits it, so removing the entry there puts **four records into
`sg101.log` for every render**. In `production.py`, where root is INFO, it does
nothing at all. Keep it in local; treat the production copy as symmetry rather
than function, and say so in a comment. The logger name is still `MARKDOWN` as
of 3.10.3, so no bump silently disconnects it.

### The per-call parser construction

Those four records per render are the symptom of something worth fixing on its
own. `core/markup.py`'s module-level `markdown()` helper builds a fresh
`Markdown` wrapper per call, whose `__init__` constructs a new
`markdown.Markdown` with three extensions — re-importing and re-registering them
every time. `SiteMarkup` and `site_markup()` do the same. The cost scales with
traffic instead of being paid once at startup.

**Caching is the obvious move, and the trap is stated up front:** a `Markdown`
instance carries per-conversion state — `reset()` exists for exactly this
reason — so a cached instance must be reset between conversions or made
thread-local rather than shared naively. Sharing one across threads without
that is a correctness bug that shows up as content from one request leaking
into another's output, under load, intermittently.

**Measure before optimizing.** The plan says so explicitly, and this project has
been bitten twice by unmeasured performance claims — Step 12 task 09 found a
single un-repeated run reporting +8.7% where medians of seven said +1.3%, and
found a psql session's cache order making one query look 25% faster purely by
running second.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md`
  (Step 13, "Revisit the MARKDOWN logger and how often Markdown is constructed")

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Bump `Markdown` past 3.0 in both `requirements.txt` and
   `requirements-docker.txt`.
2. Rewrite `core/mdexts/deleted.py` and `core/mdexts/urlize.py` against the
   target version's extension API — signature, registration, priority and
   ElementTree access.
3. **Re-derive `DelExtension`'s priority rather than transliterating
   `'>not_strong'`.** The relative-placement string has no direct numeric
   equivalent; the correct priority is the one that reproduces the current
   output.
4. Prove both extensions still produce identical HTML for the markup they
   handle — struck text and autolinked URLs — against real post content, not
   only synthetic examples.
5. Keep the `MARKDOWN` logger in `local.py`; add a comment to both copies
   explaining that it suppresses four DEBUG records per render under local's
   DEBUG root, and is inert in production where root is INFO.
6. Cache the `Markdown` instance, **and handle per-conversion state correctly**
   — `reset()` between conversions or thread-local instances. A naive shared
   instance is not acceptable.
7. Measure the caching change with repeated runs and report medians, not a
   single timing.
8. Add a test that would fail if a cached parser leaked state between
   conversions.
9. Review the rest of the 2.6.11 → target changelog for output differences.
   Rendered markup is stored-content-adjacent; a change in output changes how
   twenty years of posts display.

## Before You Begin
Take a database snapshot: `tools/pg_snapshot.sh dump <label>`. It costs 8
seconds and 128 MB, and it is what turns an accidental deletion into a restore
rather than an afternoon. Added after Step 13 task 05 deleted a forum and its
4,626 topics through a `Forum.last_post` cascade -- see DOCKER.md section 8.

**And when you delete forum content, use `tools/pgloader/smoke.py`'s
`delete_topic()` rather than writing your own.** `Forum.last_post` is a
`OneToOneField` with `on_delete=CASCADE` pointing the wrong way: deleting the
post a forum points at takes the forum, and every topic and post in it, with it.

## Dependencies
- Task 01 (Python 3.10)
- `core/html.py`'s `clean_html`, which `Markdown.convert()` calls — task 01
  changed its bleach call, so run this after that has settled
- `smiley.utils.SmilifyMarkdown`, used alongside rather than as an extension

## Implementation Approach
1. Capture a corpus of rendered output first: run a sample of real posts —
   including ones using `---del---` syntax and bare URLs — through the current
   pipeline and save the HTML. That corpus is the regression oracle for
   everything else in this task.
2. Bump Markdown and let the extensions fail to load. Read the actual error
   rather than pre-emptively rewriting.
3. Rewrite both extensions; diff new output against the saved corpus until it
   matches.
4. Do the logger comment work — small, independent, and easy to lose if left to
   the end.
5. Measure the current per-call construction cost with repeated runs.
6. Add caching with explicit state handling; measure again; write a test that
   fails against a naive shared instance.
7. Smoke: render a post with struck text, a post with a bare URL, a post with
   smileys, and a post mixing markdown and HTML through `clean_html`.

## Acceptance Criteria

1. **Markdown Past 3.0**
   - Given the updated requirements
   - When Markdown's version is read in the built image
   - Then it is past 3.0 and both custom extensions load without error

2. **Rendered Output Is Byte-Identical**
   - Given the corpus of real post content captured before the bump
   - When each item is re-rendered afterward
   - Then the HTML matches, including struck text and autolinked URLs

3. **DelExtension Priority Is Correct**
   - Given `---struck---` adjacent to other inline markup such as `**strong**`
   - When it is rendered
   - Then the result matches pre-bump output, demonstrating the numeric priority
     reproduces the old `'>not_strong'` placement rather than approximating it

4. **Autolinking Still Works**
   - Given post content containing bare URLs of the forms the existing
     `URLIZE_RE` handles
   - When rendered
   - Then each is linked exactly as before

5. **Cached Parser Does Not Leak State**
   - Given the caching change
   - When two different documents are converted in sequence through the cached
     parser, and again concurrently
   - Then neither output contains any part of the other, proven by a test that
     fails against a naively shared un-reset instance

6. **Caching Is Measured, Not Assumed**
   - Given repeated timing runs of the render path before and after
   - When medians are compared
   - Then the recorded improvement is a median of repeated runs, with the sample
     count stated

7. **Logger Config Is Explained**
   - Given `local.py` and `production.py`
   - When the `MARKDOWN` logger entries are read
   - Then each carries a comment stating what it does in that module — four
     suppressed DEBUG records per render locally, nothing in production

8. **Suite Green**
   - Given the bumped Markdown and the caching change
   - When the suite runs with `--settings=sg101.settings.docker_test`
   - Then all tests pass and `check` is clean

## Metadata
- **Complexity**: High
- **Labels**: Markdown, Extensions, Performance, Logging, Dependencies, Step 13
- **Required Skills**: python-markdown extension API (2.x and 3.x), thread
  safety and shared mutable state, performance measurement methodology
