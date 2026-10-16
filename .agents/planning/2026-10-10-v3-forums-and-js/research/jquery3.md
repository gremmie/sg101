# Research topic 8: jQuery 3 compatibility

Researched 2026-10-10. Question (from Q13): do Foundation 6.3.1, jQuery Form,
jQuery UI 1.11 and jQuery Cycle work on jQuery 3.x, and which of the site's
own scripts use APIs jQuery 3 removed?

**Answer: jQuery 3.7.1 works with two changes: a one-line patch to the
vendored Foundation 6.3.1 and jQuery UI raised from 1.11.0 to 1.13.3. With
both, every page probed matched jQuery 2.2.4 exactly.** Q13's premise that
"Foundation 6.3.1 declares `jquery >= 2.2.0`, which admits 3.x" was wrong in
practice. Its own code calls an API jQuery 3 removed.

**Corrected 2026-10-15:** the vendored JavaScript is Foundation **6.2.0** (hash-matched to its release); only the Sass is 6.3.1. See `STATUS.md`, step 3 task 01. Every finding here holds: the probe ran against
the file the site serves.

## Method

A headless Chromium (Playwright, in a throwaway container sharing the dev
`web` container's network) loaded eight V3 pages from the **dev server with
dev data**, logged in as Brian through a session created for the probe and
deleted afterwards. jQuery was swapped by intercepting the request for Google's
2.2.4. On each page it recorded:

- uncaught page errors
- jQuery Migrate's console warnings (where Migrate was loaded)
- one interaction, and whether its widget appeared, with the widget's position
  next to its input:
  - **post box:** click Upload, check the upload modal opens
  - **datepicker:** focus the date field
  - **autocomplete:** type "br"

Pages: home, news submit (post box), profile edit (datepicker), member search
and message compose (autocomplete), calendar add (datepicker), a download's
detail page, contact.

Script: `$SCRATCHPAD/jq3/jq3.py`; full output in `out.txt` alongside it.

## Results

| Run | Page errors | Upload modal | Datepickers | Autocomplete |
|---|---|---|---|---|
| **2.2.4** (today) | none | opens | under the input | under the input |
| **3.7.1, bare** | `url.indexOf is not a function` on **every page**; `elem.getClientRects is not a function` on the 2 autocomplete pages | **does not open** | ok | appears at the page's top-left (0, 0) |
| **3.7.1 + Migrate 3.4.1** | none (Migrate restores removed APIs and logs them) | opens | ok | ok |
| **3.7.1, Foundation patched** | `getClientRects` on the 2 autocomplete pages | opens | ok | at (0, 0) |
| **3.7.1, Foundation patched, jQuery UI 1.13.3** | **none** | **opens** | **identical to 2.2.4** | **identical to 2.2.4** |

(The 2.2.4 run's last page, `/contact/`, timed out waiting for the network to
go idle, probably Turnstile's widget. That's unrelated to jQuery. It loaded
cleanly in the other runs.)

## What breaks, and why

- **Foundation 6.3.1 calls `$(window).load(function …)`** once, in its
  triggers utility (`Foundation.IHearYou`). jQuery 3.0 removed `.load(handler)`.
  The call becomes an AJAX `.load(url)` with a function as the URL and throws.
  The throw aborts the rest of `foundation.min.js`'s initialisation, which is
  why **Reveal stops working: no post box modal opens.**
  - **Fix:** in `sg101/static/js/v3/foundation.min.js`, change
    `(window).load(function` to `(window).on("load",function`. That's one
    occurrence, and it was proved by the probe above. It's a hand edit to a
    vendored file, so it needs a comment, or a note next to the file, saying
    so.
- **jQuery UI 1.11.0's autocomplete** positions its menu with `.offset()` on
  `window`, which jQuery 3 rejects (`getClientRects`). The menu shows but sits
  at the top-left of the page.
  - **Fix:** jQuery UI 1.13.3. Datepicker and autocomplete then behave
    identically to today. The `redmond` theme CSS is also loaded from Google at
    1.11.0 (`settings/base.py`); serve the 1.13.3 theme to match.

## The other libraries

- **jQuery Form v20130916 is used only by `post_box.js` and markItUp**
  (`ajaxForm` for the hot-link and upload forms). It's loaded on more pages
  than use it. Its jQuery-3-sensitive code is `.selector`/`.context`, reached
  only for an `ajaxForm` call before DOM ready or with `delegation: true`.
  The site does neither. `parseJSON` and `isFunction` are deprecated but still
  present in 3.7.1. **Not exercised by a submit**, since that writes. **After
  the post box rewrite (Q10 step 1) nothing uses jQuery Form, and it can go.**
- **jQuery Cycle 3.0.3** (home page): no errors on any jQuery 3 run.
- **Orbit, ResponsiveMenu, Toggler** (home page navigation): no errors after
  the Foundation patch. Not interacted with beyond loading.

## The site's own code

- **`comments.js:26` `.size()`** (removed in 3.0) is reached only after
  posting a comment, which the probe didn't do. Static finding from topic 7;
  the fix is `.length`.
- **Deprecated, still working in 3.7.1** (Migrate's log): `.bind`,
  `.unbind`, `.delegate`, event shorthands (`.click()`, `.focus()`, …),
  `jQuery.trim`, `jQuery.isArray`, `jQuery.isFunction`, `jQuery.expr[':']`.
  Most come from jQuery UI 1.11, Foundation and jQuery Form, not site code.
  They matter only for jQuery 4.

## For the design

**The jQuery 3 step (Q13):**

- jQuery 3.7.1 and jQuery UI 1.13.3 (JS and the `redmond` theme), both
  served from the site
- the one-line Foundation patch
- `comments.js` `.size()` → `.length`

**No Migrate in production.** Use it in development to surface deprecations
if useful.

**A browser test for each fault found here:**

- the post box's upload modal opens
- the datepicker appears under its input
- the autocomplete menu appears under its input

Each one failed on bare jQuery 3, which is how we know they can fail.
