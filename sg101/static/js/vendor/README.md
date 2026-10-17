# Vendored JavaScript libraries

Served from the site rather than a CDN, so a page doesn't depend on a third
party being up, and the files can't change underneath it. Each file is the
release's own, unmodified. To upgrade, download the new release from the same
place, replace the files, and update this list.

| File | Version | Source | SHA-256 |
|---|---|---|---|
| `jquery-3.7.1.min.js` | jQuery 3.7.1 | https://code.jquery.com/jquery-3.7.1.min.js | `fc9a93dd241f6b045cbff0481cf4e1901becd0e12fb45166a8f17f95823f0b1a` |
| `jquery-ui-1.13.3/jquery-ui.min.js` | jQuery UI 1.13.3 | https://code.jquery.com/ui/1.13.3/jquery-ui.min.js | `b30d2234d5e63896d085816e0bd385da43a50f929029ed72e657c19f80bd4a38` |
| `jquery-ui-1.13.3/jquery-ui.min.css` | jQuery UI 1.13.3, `redmond` theme | https://code.jquery.com/ui/1.13.3/themes/redmond/jquery-ui.min.css | `f6f031d45e728aafa42a5b81551533fecb96c284a4ceaed913d97e88ebd70c8a` |

The two `.js` files match the SRI hashes jQuery publishes at
https://releases.jquery.com/.

The theme's images are the thirteen the CSS refers to, each from
`https://code.jquery.com/ui/1.13.3/themes/redmond/images/<name>`. They must sit
in `images/` beside the CSS: production's static storage rewrites every `url()`
in it, and fails `collectstatic` if one names a missing file.

| `jquery-ui-1.13.3/images/` | SHA-256 |
|---|---|
| `ui-bg_glass_75_d0e5f5_1x400.png` | `3b7b06ac966e94afe050effb42c83b9202fdfef146a878b1fb9c34ad01bf854d` |
| `ui-bg_glass_85_dfeffc_1x400.png` | `5a44cb7d01e1a22856e55bf4cbca1646467570ae6574fd857d3f36d8785af357` |
| `ui-bg_glass_95_fef1ec_1x400.png` | `043b8d2c074d76836917c36fa4dc8fa02c74508459ba006bfa7b7549a7023432` |
| `ui-bg_gloss-wave_55_5c9ccc_500x100.png` | `636a380f5ee68eb4e56bfb228fe15258fde09d5e725f67e7367c1921e8303059` |
| `ui-bg_inset-hard_100_f5f8f9_1x100.png` | `fad12586e78fa99e1368259cdb335dec75bf5f5cb028a80a22c2123f95cfd424` |
| `ui-bg_inset-hard_100_fcfdfd_1x100.png` | `0cdc052d7a58f22c2763d4d163c7c2e096fdb447e35a1dc68edba4710f62d946` |
| `ui-icons_217bc0_256x240.png` | `81b28c01e5a9bd45eeec29469e22177ae8e1b7411f0a77e0dc47dd3f2722e7b4` |
| `ui-icons_2e83ff_256x240.png` | `8f0a4583731f44c62b9ec3afd84fb42eb70b8bda61a5badc96473527da3e06e8` |
| `ui-icons_469bdd_256x240.png` | `ef195daa6dfbec810a4aa5ab2dde2cd0d6fc2af6da8ac08593d74838387c9d0c` |
| `ui-icons_6da8d5_256x240.png` | `55bcf81e7d37e270fc635444c718c304537160f5bee7ddac8c09da65d19e27cd` |
| `ui-icons_cd0a0a_256x240.png` | `4511aa23e7e254ac4276c579c37350626f8905412811df9787d808a4bd901d35` |
| `ui-icons_d8e7f3_256x240.png` | `18a10fe91fd2630f38caeedf64828359bb5227453d7c6f0ec39f92dc77f3a7bd` |
| `ui-icons_f9bd01_256x240.png` | `dca09211da069687e12a52ac918901e8483af82dfea21780fead233e9c556bc1` |

To check them all: `shasum -a 256 -c` against the hashes above.

## Hand edits to vendored files elsewhere

### `../v3/foundation.min.js`

Foundation 6.2.0's `dist/foundation.min.js` (SHA-256
`a34cbbdb75973d8660d0153c6c5580a19c62934bd7c74a045f5c53eb79453813` as
released), with the changes below. The stylesheet is built from Foundation
6.3.1's Sass; the JavaScript was never upgraded with it.

- **`(window).load(function` → `(window).on("load",function`**, the only
  occurrence. jQuery 3 removed `.load(handler)`, so the original call is taken
  as an AJAX `.load(url)`, throws, and stops the rest of Foundation's
  initialisation: no Reveal modal opens.
- **Reveal no longer sets `aria-hidden`** on `<body>` or on the overlay
  holding the open modal, and no longer leaves `<body>` with
  `aria-hidden="false"` on close. Three edits, in `_makeOverlay`, `open` and
  `close`'s `finishUp`:
  - `.attr({tabindex:-1,"aria-hidden":!0})` → `.attr({tabindex:-1})`
  - `t("body").addClass("is-reveal-open").attr("aria-hidden",…)` →
    `t("body").addClass("is-reveal-open")`
  - `t("body").attr({"aria-hidden":!1,tabindex:""})` →
    `t("body").attr({tabindex:""})`

  Both settings hid the open modal itself: it sits inside the overlay, which
  is inside `<body>`. ARIA forbids `aria-hidden` on `<body>` and tells
  browsers to ignore it there, and Chrome also refuses it on an ancestor of
  the focused element, logging an error and a warning for each modal.
  Foundation 6.3.0 made the same removal upstream. Reveal still keeps Tab
  inside an open modal.
- **Closing a Reveal modal puts focus back on the link that opened it**,
  Foundation 6.5.0's fix. Two edits:
  - `open` first records `this.$activeAnchor`: the focused element if it is
    one of the modal's opening links, otherwise all of them.
  - `close` ends with `this.$activeAnchor.focus()`.

  6.2.0 returned focus only when a modal was closed from the keyboard. Closed
  with the mouse, focus stayed on the button inside the modal, which `close`
  then marks `aria-hidden="true"`: Chrome blocks that with a warning, and
  focus falls to `<body>`. Recording the link used matters where several post
  boxes share one set of modals, as on the profile edit page; 6.4.0's
  `this.$anchor.focus()` would land on the last of them.
- **The keyboard handlers no longer move focus after closing**, finishing
  that fix as Foundation 6.4.0 did. 6.2.0's three keyboard handlers each
  focused `this.$anchor` (every opening link, ending on the last) after
  `close` had already focused the one used:
  - Escape, on the window and on the modal (two identical occurrences):
    `close:function(){e.options.closeOnEsc&&(e.close(),e.$anchor.focus())}` →
    `close:function(){e.options.closeOnEsc&&e.close()}`
  - Enter on a `[data-close]` button: the
    `?setTimeout(function(){e.$anchor.focus()},1):` branch → `||`.

  6.4.0 deleted the modal's whole keydown handler, since 6.3.0's shared
  `Keyboard.trapFocus` had replaced it. 6.2.0 has no `trapFocus`, and the same
  handler keeps Tab inside an open modal, so only the focus moves are gone.
- **A `[data-toggle]` with no value no longer throws**, Foundation 6.3.0's
  fix. The click handler `function(){r(t(this),"toggle")}` →
  `function(){var e=t(this).data("toggle");e?r(t(this),"toggle"):t(this).trigger("toggle.zf.trigger")}`,
  the same shape as the `[data-close]` handler beside it. It built the
  selector `"#" + ""`: jQuery 2 read `#` as an empty ID lookup, jQuery 3 hands
  it to its selector engine, which raises `Syntax error, unrecognized
  expression: #`. 6.2.0's docs show the responsive menu's icon that way.
