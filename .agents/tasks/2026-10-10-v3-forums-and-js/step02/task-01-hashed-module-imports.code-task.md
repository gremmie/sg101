# Task: Hashed module imports in production's static storage

## Description
Add `core.storage.ManifestStaticFilesStorage`, a subclass of Django's storage
of the same name with `support_js_module_import_aggregation = True`, and name it
in `production.py`'s `STORAGES`. Then a deploy can't leave a browser running a
new entry module against an old, cached copy of a module it imports. Prove the
rewrite with a test rather than assuming it.

## Background
The post box is being rewritten as native ES modules with no build step (R6,
Q2). An entry module imports its siblings by relative specifier, for example
`import { insertAtCursor } from './editor.js'`.

Production serves static files through Django's `ManifestStaticFilesStorage`
(`sg101/settings/production.py`, `STORAGES['staticfiles']`), with WhiteNoise.
By default that storage rewrites `url()` in CSS and `sourceMappingURL`, but
**not** `import` specifiers in JavaScript: `support_js_module_import_aggregation`
is `False` (design §3.3, checked in Django 5.2.17). The hashed entry module
would then import the *unhashed* `editor.js`. WhiteNoise serves hashed names
with a far-future cache lifetime and unhashed names with a short one, so the
two can disagree after a deploy.

Facts:
- Django's rewriter handles static `import … from '…'` and `export … from '…'`.
  The design uses no dynamic `import()`.
- `production.py`'s comment above `STORAGES` explains why both backends are
  named explicitly. Keep it accurate when the class path changes.
- `core` imports nothing else in the repo (AGENTS.md). A storage class that
  only subclasses Django's fits there.
- `core/tests/test_static.py` already checks that every literal `{% static %}`
  name in a template exists. It reads templates, not module imports, so it
  doesn't cover this.
- The test settings use the plain static storage, so the suite never runs the
  manifest storage unless a test does so explicitly.

## Reference Documentation
**Required:**
- Design: .agents/planning/2026-10-10-v3-forums-and-js/design/detailed-design.md (§3.3 Static files and ES modules)

**Additional References (if relevant to this task):**
- .agents/planning/2026-10-10-v3-forums-and-js/implementation/plan.md (Step 2)

**Note:** You MUST read the detailed design document before beginning implementation. Read additional references as needed for context.

## Technical Requirements
1. Create `core/storage.py` with `ManifestStaticFilesStorage`, subclassing
   `django.contrib.staticfiles.storage.ManifestStaticFilesStorage`, setting
   `support_js_module_import_aggregation = True`, with a docstring saying why.
2. Point `production.py`'s `STORAGES['staticfiles']['BACKEND']` at
   `core.storage.ManifestStaticFilesStorage`, and update the comment beside it.
   No other settings module changes.
3. A test, in `core/tests/`, that runs the storage's post-processing over a
   small module tree in a temporary directory: an entry module importing a
   sibling (`./a.js`) and a module one level up (`../b.js`), and one using
   `export … from`. It asserts that the hashed entry file names the hashed
   specifiers, and that the hashed names resolve to files the storage wrote.
   Use temporary `STATIC_ROOT` and `STATICFILES_DIRS` (`override_settings`, or
   construct the storage with a `location`). Don't touch the real
   `STATIC_ROOT`.
4. Follow the surrounding test code's style. Comments describe the code, never
   this plan's step numbers.

## Dependencies
- None within step 2. The modules in task 02 rely on this, so it goes first.

## Implementation Approach
1. Write the test against Django's own `ManifestStaticFilesStorage` first, and
   see it fail: the entry module keeps its unhashed specifiers.
2. Add `core/storage.py` and point the test at it. See it pass.
3. Mutation: set the flag `False` in the subclass, see the test fail, restore.
4. Change `production.py`. Confirm with a production-style `collectstatic` in
   a throwaway container that the image build still succeeds. The Dockerfile
   runs `collectstatic` under `sg101.settings.production`. There are no
   modules yet, so check that the run completes and the manifest is written.
5. Run the suite and the deprecation gate (AGENTS.md).

## Acceptance Criteria

1. **Imports are rewritten to hashed names**
   - Given a temporary tree with an entry module importing `./a.js` and `../b.js`, and re-exporting from a third module
   - When the new storage post-processes it
   - Then the hashed entry file names each import by its hashed name, and each such name exists in the storage

2. **The test fails without the flag**
   - Given the subclass with `support_js_module_import_aggregation = False`
   - When the test runs
   - Then it fails on the unhashed specifier; restore afterwards

3. **Production uses it**
   - Given `sg101.settings.production`
   - When `STORAGES['staticfiles']['BACKEND']` is read
   - Then it is `core.storage.ManifestStaticFilesStorage`, and `collectstatic` under those settings completes

4. **`core` stays self-contained**
   - Given `core/storage.py`
   - When its imports are read
   - Then it imports only Django, nothing else from the repo

5. **Suite and gate**
   - Given the change
   - When the suite runs, then the deprecation gate as its own run
   - Then both pass, with the test count up by the new tests

## Metadata
- **Complexity**: Low
- **Labels**: static files, ES modules, Django storage, production settings, cache busting
- **Required Skills**: Django staticfiles storage and post-processing, `override_settings`, mutation testing
