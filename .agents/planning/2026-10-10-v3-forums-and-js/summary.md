# Summary: the V3 forums, the post box, and the site's JavaScript

PDD run 2026-10-10. GitHub #9, #16, #17, #18.

## Artifacts

| File | Holds |
|---|---|
| `rough-idea.md` | the starting idea, Brian's background on the V3 effort, and early corrections |
| `idea-honing.md` | Q1–Q13 with answers, and corrections from research |
| `research/research-plan.md` | the eight research topics and their status |
| `research/v3-dev-forums.md` | what `v3-dev` finished: 2 pages done, the topic page mostly, 16 templates not started |
| `research/upload-timing.md` | image processing measured at 0.06–0.46 s; tall, narrow images never resized (#32) |
| `research/playwright.md` | Playwright under `docker_test`: cost, and the async override |
| `research/fragments-and-flatpages.md` | the shared fragments are forum-index-only; flatpages serve nothing (#33) |
| `research/upload-error-message.md` | rejected uploads show no reason (`msg` vs `error_msg`) |
| `research/foundation-upgrade.md` | Foundation 6.9.0 measured, and not adopted |
| `research/jquery3.md` | jQuery 3.7.1 + one-line Foundation patch + jQuery UI 1.13.3 match 2.2.4 |
| `design/detailed-design.md` | the design, standalone |
| `implementation/plan.md` | 12 steps with a checklist, branches and demos |
| `STATUS.md` | what each task did and measured, from step 1 on |

## The design in brief

- **The post box is rewritten as plain ES modules,** with no jQuery and no
  build step. One fetch wrapper (`core/http.js`) turns every error into a
  readable sentence. A small `ManifestStaticFilesStorage` subclass cache-busts
  module imports.
- **It gains smileys** (a modal inserting at the cursor, with whitespace
  padding), **multi-image upload** (up to 10, one request per image, per-file
  results), and **a video button shown only on the forums**, which attaches,
  not inserts.
- **jQuery 3.7.1 and jQuery UI 1.13.3 are self-hosted.** Foundation stays
  (6.3.1's Sass, 6.2.0's JavaScript), with one line of the JavaScript patched.
- **The forums move to V3 in three releases,** starting from `v3-dev`'s
  templates, with a screenshot review before the rest is built.
- **The shoutbox and `base.html` are retired,** and with them Blueprint,
  jQuery 1.11, markItUp, and the `V3_DESIGN` flag.
- **A small set of Playwright tests** guards the faults research showed are
  possible. Each is mutation-checked.

## Next steps

1. **Commit the planning folder on `main`** (Brian reviews first).
2. **Run `/agent-sops:code-task-generator` on step 1,** then
   `/agent-sops:code-assist` on its task, on a branch cut from `main`.
3. **Brian, outside the plan:**
   - switch leopard's clone to `main`
   - delete `modernize` afterwards

## Areas that may need refinement

- **R11 (the toolbar fit at 360 px)** is settled by measurement in step 6, not
  yet known.
- **Step 6's review may change the look,** and with it the templates that
  steps 7–10 build.
- **Not measured:** leopard's image processing speed and S3 PUT time. Not
  exercised under jQuery 3 beyond page load: the menus, the Orbit banner and
  Cycle. Step 3's manual checks cover them.
- **jQuery UI** stays, maintenance-only upstream. Replacing its datepicker
  and autocomplete is outside this project, and is what remains of #18
  together with jQuery itself.
- **Related issues filed during planning:** #32 (resize), #33 (flatpages).
