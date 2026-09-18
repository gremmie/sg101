# Task: Make the Stylesheet Buildable Again

## Description
Reconstruct the front-end CSS toolchain so `sg101/scss/` can actually produce
`sg101/static/css/v3/main.min.css`, and reconcile the two rules that were
hand-appended to the built artifact while no build was possible.

**Generated 2026-09-17**, later than tasks 01-09. `plan.md` has carried the Sass
toolchain under Step 20 since 2026-08-13 — Brian's call to place it here — but the
2026-09-12 task generation pass produced nine files and none of them covered it.
Nothing about the work moved; only the task file was missing.

## Background
**The v3 design's stylesheet cannot currently be rebuilt, and that was discovered
the hard way:** a one-rule CSS change had to be hand-appended to the *minified
build artifact* because no rebuild was possible.

**The pipeline, as committed.** `sg101/scss/main.scss` imports Foundation and
Motion UI, then the site's own `_sg101.scss`; `sg101/gulpfile.js` runs it through
`gulp-sass` → `autoprefixer` → `cssnano` → `rename('.min')` and writes
`sg101/static/css/v3/main.min.css`, **which is committed** and updated in the same
commits as the SCSS (`a3d54a8` is an example of both moving together).

**Three independent things stop it running**, all observable rather than
suspected, and all re-verified 2026-09-17:

1. **`gulp-sass` ^2.1.1 wraps `node-sass`**, which needs native bindings built per
   Node version. Node here is **v26.5.0**; node-sass stopped shipping bindings
   many majors ago.
2. **`gulpfile.js` is gulp 3 syntax** — `gulp.task('default', ['sass'], …)`, the
   array-of-dependencies form, which gulp 4 removed. Note also that `gulp` itself
   is *not* in `package.json`'s dependencies; only five `gulp-*` plugins are.
3. **Dependencies come from bower**, not npm: `sassPaths` points at
   `bower_components/foundation-sites/scss` and `bower_components/motion-ui/src`,
   and `sg101/bower.json` pins `foundation-sites ~6.3.0` and
   `motion-ui ~1.2.2`. Bower is sunset. **Neither `node_modules` nor
   `bower_components` is present in the tree.**

**The modern shape is clear and the migration is not large:** drop bower for npm
(`foundation-sites` and `motion-ui` both publish there), drop `node-sass` for
**dart-sass** (the `sass` package, the reference implementation now, needing no
native build), and consider dropping gulp altogether — this is one `sass`
invocation plus a minifier, which an npm script can express directly. The
autoprefixer target is `['last 2 versions', 'ie >= 9']`, written in 2016; **IE 9
can go.**

### The outstanding debt to reconcile — two rules, not one

Each was appended to `main.min.css` by hand at the position a rebuild would place
it, matching its order in `_sg101.scss`. Verified present and last-in-file
2026-09-17, in `_sg101.scss` order (`.friends-logos` 227 → `.logout-form` 237 →
`.cf-turnstile` 254):

| Rule | Added | Sits after |
|---|---|---|
| `.menu>li>form.logout-form{…}` | `39aceca4`, 2026-08-13, the logout fix | `.friends-logos` |
| `.cf-turnstile{margin-bottom:1rem}` | 2026-08-30, Step 17 task 04's page cleanup | the logout rules, last in the file |

**So a correct rebuild should produce essentially the same file.** Diff the
rebuild against the committed artifact **before** replacing it: bytes that differ
*elsewhere* mean the toolchain reconstruction changed the output — a different
Sass implementation, a newer autoprefixer target, a different minifier — which is
worth seeing rather than absorbing silently.

### The decision this task inherits — DECIDED 2026-09-17 in task 02

**Built CSS stays a committed artifact, and CI verifies it is reproducible.**
Brian's call. The production image stays free of Node, deploys stay one step, and
`main.min.css` stays diffable in review — while the drift that would otherwise
argue for a deploy-time build becomes a failing CI run instead.

**That makes a CI check this task's to deliver**, not an optional extra: after
the rebuild works, CI runs the build and fails if the committed file differs.

```
npm run build
git diff --exit-code sg101/static/css/v3/main.min.css
```

It sharpens acceptance criterion 2 rather than replacing it: the criterion says
every difference from the baseline must be explained, and this says that once
they have been, the *steady state* is byte-identical and machine-checked.

**Note the ordering trap.** The check can only be added after the rebuild
reproduces the committed file, including the two hand-appended rules. Adding it
first turns every CI run red until the toolchain is finished.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — Step
  20's Sass section, which this file implements
- Task 02 — the committed-artifact-vs-deploy-build decision
- `39aceca4` — the logout fix, and the first hand-append

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Replace bower with npm for `foundation-sites` and `motion-ui`, pinned at
   versions whose Sass compiles against the site's own `_settings.scss` and
   `_sg101_settings.scss` — the 6.3.0-era settings files are the constraint, so a
   major Foundation bump is a decision, not an upgrade.
2. Replace `node-sass`/`gulp-sass` with **dart-sass**.
3. Decide gulp's fate explicitly: either gulp 4+ with modern task syntax, or an
   npm script running `sass` plus a minifier. **State the choice and the
   reasoning**; "one invocation plus a minifier" argues for the script.
4. Update the autoprefixer target, dropping IE 9.
5. Produce a build that a single documented command runs, and document it where
   the next person will look — `AGENTS.md` and/or `DOCKER.md`, not only in a
   commit message.
6. **Diff the rebuilt CSS against the committed `main.min.css` and account for
   every difference** before replacing it. The two hand-appended rules above must
   survive as SCSS-sourced output; differences elsewhere must be explained in the
   commit or the planning record.
7. Delete `sg101/bower.json` and the dead `gulpfile.js` only once the replacement
   builds.
8. Implement task 02's static-assets decision as it applies here — whether
   `main.min.css` stays committed, and whether Node enters the production image.

## Dependencies
- Task 02 — the static-assets decision, and `collectstatic`/WhiteNoise
- `sg101/scss/_settings.scss`, `_sg101_settings.scss`, `_sg101.scss` — the site's
  own Sass, which must keep compiling unchanged
- Node v26.5.0 as installed; npm registry access
- `sg101/static/css/v3/main.min.css` as the comparison baseline

## Implementation Approach
1. **Capture the baseline first**: copy the committed `main.min.css` somewhere
   outside the tree before any build can overwrite it. It is the only evidence of
   what the output should be.
2. Stand up npm dependencies and get *any* successful dart-sass compile, before
   worrying about minification or prefixing.
3. Add autoprefixer and the minifier, then diff against the baseline and drive
   the differences down until every remaining one is explained.
4. Decide gulp-or-npm-script on what the working build actually needs.
5. Remove bower and the gulp 3 file, and document the command.

## Acceptance Criteria

1. **One documented command rebuilds the stylesheet**
   - Given a clean checkout and Node v26
   - When the documented build command is run
   - Then `sg101/static/css/v3/main.min.css` is produced with no native-binding
     build and no bower

2. **The rebuild is accounted for against the committed artifact**
   - Given the pre-change `main.min.css` kept as a baseline
   - When the rebuilt file is diffed against it
   - Then both hand-appended rules are present as SCSS-sourced output, and every
     other difference is explained in writing rather than absorbed

3. **The site renders unchanged**
   - Given the rebuilt stylesheet in a running stack
   - When the v3 pages that exercise the two repaired rules are loaded — a logout
     form in the menu, and a page carrying the Turnstile widget
   - Then they render as they do today

4. **The dead toolchain is gone**
   - Given the tree after this task
   - When it is searched for `bower`, `node-sass` and `gulp-sass`
   - Then none of them appears in a file the build reads

5. **The static-assets decision is honored, not re-opened**
   - Given task 02's recorded decision
   - When this task's output is inspected
   - Then the committed-or-built choice matches it, and nothing here contradicts
     `collectstatic`/WhiteNoise configuration

## Metadata
- **Complexity**: Medium
- **Labels**: Front End, Sass, Build Tooling, Static Files
- **Required Skills**: Sass/dart-sass, npm tooling, CSS build pipelines
