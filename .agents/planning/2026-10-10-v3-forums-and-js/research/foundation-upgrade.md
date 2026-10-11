# Research topic 7: Foundation 6.3.1 → 6.9.0

Researched 2026-10-10. Question (from Q12): what does moving from 6.3.1 to
6.9.0 cost, what breaks, and does it belong in this project?

**Method.** A scratch copy of `sg101/scss/` and `package.json` with
`foundation-sites` 6.9.0 and `motion-ui` 2.0.8 (Foundation's peer dependency
is `motion-ui: latest`), built with the repo's own command (`sass` 1.105.1).
Both builds were compiled unminified, then compared by CSS class and by
declarations per selector. Class usage was checked by grepping every `.html`,
`.js` and `.py` file in the repo (excluding `node_modules`, TinyMCE,
`archive/`, `.agents/` and the vendored Foundation bundle). No browser
rendering yet.

## What the site uses

- **Sass:** `main.scss` includes nearly every Foundation component, using the
  **flex grid** (`foundation-flex-grid`) for `row`/`columns`. The float grid
  is commented out, and the XY grid introduced in 6.4 isn't used.
- **The site's customisations are all in `_sg101_settings.scss`** (31 lines:
  the green/red palette, anchor colour, pagination and table colours).
  **`_settings.scss` is byte-for-byte Foundation 6.3.1's stock settings file**
  (trailing whitespace aside; `diff` against
  `node_modules/foundation-sites/scss/settings/_settings.scss` is empty).
- **JavaScript plugins** (from `data-*` attributes in templates):
  - **Reveal**: 8 modals, mostly the post box's
  - **Toggler** (`data-toggle`): 2
  - **ResponsiveToggle** and **ResponsiveMenu**: the main navigation in
    `v3/base.html`, drilldown on small screens and a dropdown on medium and up
  - **Orbit**: the banner carousel on small screens

  `sg101.js` calls `$(document).foundation()` once.

## Sass build on 6.9.0

**It compiles, with the 6.3.1 settings file unchanged.** Only warnings:

- Dart Sass deprecations (`@import`, global `darken()`, `/` division) from the
  site's own `main.scss`, `_settings.scss` and `_sg101_settings.scss`. The
  current build already hides Foundation's with `--quiet-deps`. They become
  errors only in Dart Sass 2.0/3.0, and `package.json` pins `sass ^1.80`.
- `$offcanvas-size` and `$offcanvas-vertical-size` are deprecated in favour of
  maps. Taking 6.9.0's own `_settings.scss` fixes both.

**What changes in the CSS:**

| | 6.3.1 | 6.9.0 |
|---|---|---|
| Unminified size | 105 KB | 137 KB |
| Distinct classes | 472 | 522 |
| Classes removed | — | 2: `menu-bordered`, `menu-hover`, **neither used anywhere in the repo** |
| Selectors (per media query) | 1,298 | 1,894 |
| Selectors whose declarations changed | — | 142 |
| Selectors no longer present in the same media context | — | 141 |

The changed and moved rules cluster in **menus (41), buttons (36), the
`position-*` off-canvas classes (24), dropdowns (14), tables (13)**, then
inputs, visibility classes and progress bars. **No class the site uses
disappears, but menus, buttons, dropdowns and tables will look different
somewhere.** How different needs a side-by-side screenshot pass, which is
not yet done.

## JavaScript on 6.9.0

- **jQuery ≥ 3.6 required** (peer dependency). The site loads 2.2.4.
- **Packaging allows no build step (Q2):** `dist/js/foundation.min.js`
  (197 KB, all plugins, against 104 KB for today's 6.3.1 bundle), or the
  individual UMD files in `dist/js/plugins/`. Core, the five plugins the
  site uses, and their ten utilities come to **123 KB** as separate
  `<script>` tags.
- **jQuery 3 breaks some of the site's own code.** `.size()` was removed in
  jQuery 3.0:
  - `comments/static/js/comments.js:26` numbers a newly posted comment with
    `.size()`. It is loaded on four V3 pages (contests, downloads, polls, photo
    of the day), so **posting a comment there would throw** after the
    upgrade.
  - `shoutbox.js` uses it too, but is being removed (Q5).
  - Deprecated in jQuery 3 but still present, so no breakage:
    `jQuery.trim` (`sg101.js`), and `.bind`/`.delegate` (`rating.js`,
    `shoutbox.js`).
- **Third-party jQuery plugins still loaded on V3 pages**, none checked
  against jQuery 3 yet:
  - jQuery Form, v20130916, on at least 8 pages
  - jQuery UI 1.11.0, on 4 pages
  - jQuery Cycle 3.0.3, on the home page

  Counts are a floor: they come from templates that extend `v3/base.html`
  directly, plus `messages/compose.html`, found by hand. Templates extending
  an intermediate base (such as `messages/messages_base.html`) weren't all
  swept.

## A correction to Q5: jQuery UI is not only on old-design pages

Q5 assumed retiring `base.html` removes jQuery UI. **It does not.** At least
four V3 pages load it from `script_tags`:

| Page | Uses |
|---|---|
| `bio/edit_profile.html` | `datepicker` (birthday, `bio.js`) |
| `gcalendar/event.html` | `datepicker` (start and end dates, `gcalendar.js`) |
| `bio/member_search.html` | `autocomplete` (`v3/autocomplete.js`) |
| `messages/compose.html` (V3, via `messages/messages_base.html`) | `autocomplete` for the recipient (`v3/autocomplete.js`) |
Under Q1, jQuery UI goes only when these are rewritten. Native
`<input type="date">` and a small `fetch`-based autocomplete are the obvious
replacements. That's new scope, for Brian to place.

## Assessment

- **Smaller than feared.** The settings file is stock, so the upgrade is: take
  6.9.0's `_settings.scss`, keep `_sg101_settings.scss`, rebuild, and swap the
  JS bundle.
- **The real work is checking it in a browser.** About a fifth of the rules
  changed, in the components most visible on every page: the navigation menu,
  buttons and tables.
- **jQuery 3 comes with it**, which:
  - fixes the security advisories on 2.2.4 (research topic 2 folds in here)
  - breaks `comments.js` until `.size()` becomes `.length`
  - needs jQuery Form, jQuery UI 1.11 and Cycle checked, and probably jQuery
    UI raised to 1.12 or later or replaced
- **Placement options:**
  - **(a) A step before the forum work.** The new forum pages would be built
    and reviewed against the CSS they will ship with. Otherwise the Q6
    screenshot review happens twice.
  - **(b) Its own project after this one.** That keeps this project's scope
    as decided. The forums would be built on 6.3.1 and then re-checked after
    the upgrade.
  - Not decided. Brian's call.

## Sources

- npm registry, `npm view foundation-sites`, read 2026-10-10.
- Scratch builds:
  `$SCRATCHPAD/f69/out-631.css` and `out-old-settings.css` (6.9.0), produced
  as described under Method.
