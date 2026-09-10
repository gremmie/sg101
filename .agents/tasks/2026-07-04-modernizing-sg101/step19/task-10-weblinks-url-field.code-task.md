# Task: `AddLinkForm.url` Becomes a `URLField`

## Description
Change `weblinks/forms.py`'s `AddLinkForm.url` from a `forms.CharField` to a
`forms.URLField`, so a member who types `example.com` gets it normalized instead
of rejected, and cover the three input shapes with tests.

**This is a usability fix, not a security fix.** Nothing is unsafe today. The
task is small on purpose; its risk is entirely in a side effect the obvious
reading misses.

## Background

### What the field looks like now
`weblinks/forms.py:11`:

```python
url = forms.CharField(widget = forms.TextInput(attrs = {'size': 52}))
```

`AddLinkForm` is a `ModelForm` over `PendingLink`, which inherits
`weblinks.models.LinkBase.url` — `models.URLField(db_index=True)`
(`weblinks/models.py:38`).

### The obvious reading of this is wrong, and it was measured before scheduling
**The `CharField` is not skipping URL validation.** `ModelForm._post_clean` runs
the *model* field's validators for any field the form carries, so
`javascript:alert(1)` and plain gibberish are already rejected today. Nothing is
unsafe here and this task does not close a hole.

**The difference is confined to scheme-less input, and it runs the wrong way
round.** Typing `example.com` is currently **rejected** — "Enter a valid URL.",
which does not tell a member what to fix — where a form `URLField` normalizes it
and accepts it.

**⚠️ Corrected 2026-09-09 during execution: the scheme is `https`, not `http`.**
`sg101/settings/base.py:75` sets `FORMS_URLFIELD_ASSUME_HTTPS = True`, so a bare
domain normalizes to `https://example.com`. The setting is deliberate —
`tools/deprecation_gate.sh` carries an ignore for its own deprecation warning and
says so. Every `http://` below was written without accounting for it.

### The side effect that makes this worth a test rather than a one-liner
`AddLinkForm` has a `clean_url` that rejects duplicates:

```python
def clean_url(self):
   new_url = self.cleaned_data['url']
   try:
      Link.objects.get(url__iexact = new_url)
   except Link.DoesNotExist:
      return new_url
   raise forms.ValidationError('That link already exists in our database.')
```

Field cleaning runs **before** `clean_<field>`, so after this change the value
`clean_url` compares is the *normalized* one. **The duplicate check therefore
changes behaviour too**, and in the useful direction: `example.com` currently
never reaches the check at all (it fails validation first), and afterwards it
arrives as `http://example.com` and matches an existing `http://example.com`.

That is an improvement, but it is a behaviour change in a method this task does
not edit, which is exactly the kind that ships unnoticed. **It needs its own
test.** Note also what normalization does *not* fix: a trailing slash still makes
`http://example.com/` a different string from `http://example.com`, so the
duplicate check remains exact-match-after-normalization. Do not widen it here.

**⚠️ The improvement is smaller than this paragraph claims.** Because the assumed
scheme is `https` and 475 of 571 stored links are `http://`, a bare domain will
*not* collide with the stored form of most of them. It is not a regression —
`example.com` never reached `clean_url` at all before — but the duplicate check
still only works for input carrying a scheme, plus the 94 rows already on https.

### House style in this file
`weblinks/forms.py` is one of the legacy 3-space-indented files and uses spaces
around `=` in keyword arguments. **Match the surrounding code**; this task is not
the place to normalize it, and the whole-repo formatter was taken out of scope on
2026-09-08.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Additional References:**
- `.agents/planning/2026-07-04-modernizing-sg101/implementation/plan.md` — the
  `[Phase D]` weblinks block, which carries the measurement above and its
  Step 14 provenance
- `CODEASSIST.md`, `AGENTS.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements

1. **`AddLinkForm.url` becomes a `forms.URLField`**, keeping the existing widget
   and its `size` attribute so the rendered form is unchanged.

2. **Confirm the premise before relying on it.** Verify in the running code that
   a `CharField` here already rejects `javascript:alert(1)` and gibberish via
   `_post_clean`. If it does not, that is a finding that changes this task's
   character from usability to security — stop and report it.

3. **`clean_url` is not edited**, but its changed input is covered by a test. Do
   not widen the duplicate check to handle trailing slashes or case beyond the
   existing `__iexact`.

4. **The rendered field does not regress.** `URLField` renders
   `<input type="url">` by default; the explicit `forms.TextInput` widget keeps
   it a text input. Decide deliberately whether to keep `TextInput` — keeping it
   is the no-visible-change option and is what this task assumes.

5. **Tests cover scheme-less, schemed and invalid input**, per the plan's Phase D
   Tests line, plus the duplicate-check interaction.

6. **Each test is mutation-verified** by reverting the field to `CharField` and
   observing the intended failures.

7. **No shipped comment mentions the step or phase number.** Per `CODEASSIST.md`,
   comments describe the code, not the plan.

## Dependencies
- `weblinks/models.py`'s `LinkBase.url` staying a `models.URLField`
- `weblinks/views.py:84` constructs `AddLinkForm(request.POST)` — the view is
  unchanged by this task
- Task 09 covers the `weblinks` receivers; running that first means this lands on
  an app whose signal wiring is finally under test. Not a hard ordering
  constraint.

## Implementation Approach
1. Confirm current behaviour by exercising the form directly: gibberish,
   `javascript:` scheme, `example.com`, `http://example.com`.
2. Change the field.
3. Add form tests for the three input shapes and the duplicate interaction.
4. Revert the field to `CharField` and confirm the new tests fail; restore.
5. Render the add-link page and confirm the widget is unchanged.
6. Run the suite and the deprecation gate.

## Acceptance Criteria

1. **Scheme-less input is accepted and normalized**
   - Given the add-link form
   - When `example.com` is submitted with an otherwise valid payload
   - Then the form is valid and `cleaned_data['url']` is `https://example.com`
     (**corrected 2026-09-09** — `FORMS_URLFIELD_ASSUME_HTTPS`)

2. **Schemed input is unchanged**
   - Given the add-link form
   - When `http://example.com/page` is submitted
   - Then the form is valid and the value passes through untouched

3. **Invalid input is still rejected**
   - Given the add-link form
   - When gibberish and a `javascript:` URL are submitted
   - Then the form is invalid with an error on `url` in both cases

4. **The duplicate check sees the normalized value**
   - Given an existing `Link` with url `https://example.com` (**corrected
     2026-09-09** — as written, with `http://`, this criterion fails: the
     normalized value is `https://` and `url__iexact` does not bridge the two)
   - When `example.com` is submitted
   - Then the form is invalid with "That link already exists in our database." —
     which it is not today, because the value never reaches `clean_url`
   - And the `http://` case is pinned by its own test as a known boundary

5. **The tests are real — mutation-verified**
   - Given the new tests
   - When `url` is reverted to `forms.CharField`
   - Then criteria 1 and 4's tests **fail**, observed rather than assumed, while
     criterion 3's still pass — the invalid cases were always covered by
     `_post_clean` and are not what this change buys

6. **The page looks the same**
   - Given the add-link page rendered before and after
   - When the two are compared
   - Then the `url` input is unchanged, including its `size` attribute

7. **The suite and the gate are green**
   - Given `manage.py test --noinput --settings=sg101.settings.docker_test` and,
     separately, the deprecation gate
   - When both are run in the container
   - Then both pass

## Metadata
- **Complexity**: Low
- **Labels**: weblinks, forms, validation, usability, Step 19 Phase D
- **Required Skills**: Django forms and ModelForm cleaning order, form testing
