# Research topic 6: the upload error message

Researched 2026-10-10. **Confirmed: a rejected upload shows no reason.**

## The mismatch

`user_photos/views.py` `upload_ajax_v3` returns JSON with `error_msg` and
`url`. Its paths put the message in different keys:

| Path | Status | Message key |
|---|---|---|
| Not logged in | 403 | `error_msg` |
| Not AJAX or not POST | 405 | `error_msg` |
| `form.save()` raised | 500 | `error_msg` |
| **Form invalid** (not an image, too large, over the 50/day quota) | **400** | **`msg`** |
| **Uploads disabled** (`USER_PHOTOS_ENABLED` false) | **403** | **`msg`** |

`sg101/static/js/v3/post_box.js:215-216` shows
`"Error: " + ex + ' - ' + resp.error_msg`. So for the two `msg` paths the
member sees **"Error: Bad Request - "** (or "Forbidden"), with the reason
dropped. These are the two commonest rejections: a bad file and the quota.

## Measured

Dev stack, Django test `Client` logged in as the lowest-id active user,
posting `b'not an image'` as `x.jpg` with `X-Requested-With`:

```
400 {"error_msg": "", "url": "", "msg": "* Upload a valid image. The file you uploaded was either not an image or a corrupted image."}
```

**What the probe changed:** `UploadForm.clean()` runs `rate_limit_user`
even when the field is invalid, so this added 1 to that user's upload counter
in the **dev** Redis (expires within 24 h). Nothing else was written.

## The fix

Put every message in `error_msg`. That's a two-line server change and needs
no JavaScript change. It belongs with the upload rewrite (Q10 step 3), or
could go earlier as a standalone fix. The hot-link path's error reporting
was fixed separately in `0589f21c`.

Side observation: the 500 path sends `str(ex)` to the member, which could
expose internal detail from S3 or Pillow. Worth replacing with a generic
message when the view is touched.
