# Research topic 1: how long one image upload takes

Researched 2026-10-10. Question (from Q4): does one large phone photo finish
inside gunicorn's 30-second worker timeout, given that the processing runs in
the request and not in Celery?

**Answer: by a wide margin, on the parts measured.** Processing a
48-megapixel photo took under half a second on the dev stack. Two parts are
not measured: leopard's CPU speed and the two S3 PUTs.

## Where the time goes in one request

1. **The body transfer.** Not gunicorn's problem any more. Since 2026-10-10,
   a Cloudflare Configuration Rule buffers every `POST` body in full before
   forwarding it, so the worker reads the upload in one burst at LAN speed.
   It was checked live with a 1 MB body sent at 20 KB/s: no `WORKER TIMEOUT`.
   See STATUS.md, *A member's avatar upload got a 502*, and AGENTS.md.
2. **Django parses the multipart body,** `UploadForm.save()` copies it to a
   temp file and hashes it for de-duplication (`_signature`). This is linear
   in file size and cheap.
3. **`core/images/upload.py` `upload()`:** fix the orientation (a full-size
   re-encode when the EXIF says the photo is rotated), resize to fit 660×720,
   make a 120×120 thumbnail.
4. **Two S3 PUTs:** the resized image and the thumbnail.
5. **One `Photo` row saved.**

## Measured: step 3, the real code

The dev `web` container on the Mac (10 CPUs). This calls `upload()` itself
with S3 replaced by a stub that returns a URL. The images are synthetic: a
gradient plus noise per channel, so they compress roughly like a photo. Three
runs each; the spread was under 0.01 s.

| Input | File size | Processing | Output |
|---|---|---|---|
| 12 MP JPEG (4032×3024) | 6.5 MB | **0.06 s** | 17 KB |
| 12 MP JPEG, EXIF rotated 90° | 6.5 MB | **0.13 s** | 22 KB |
| 48 MP JPEG (8064×6048), rotated | 26.0 MB | **0.46 s** | 12 KB |
| 12 MP PNG | 32.5 MB | **0.38 s** | 524 KB |

The rotated cases are the realistic worst case: phones store the rotation in
EXIF, which forces the extra full-size re-encode.

## Not measured

- **leopard's speed.** It is a 4 GB Linode on shared vCPUs, slower per core
  than the Mac. It wasn't measured, because running a benchmark on the
  production host loads it. Even 10× slower puts the worst case near 5 s.
- **The two S3 PUTs.** Measuring them means writing to the production bucket.
  The objects are small, at most about 0.5 MB.
- **The member's upload time.** Covered by Cloudflare's buffering, step 1.

## For the design

- **One request per image (Q4's A) is safe.** The worst measured case is
  about 60 times inside the timeout before S3, and 10 sequential requests stay
  short. Moving processing to Celery isn't needed.
- **A batch of 10 ties up one sync worker per image in turn, not all at
  once,** because the requests are sequential. Leopard runs five workers.

## Side observation: tall, narrow images are never resized

`upload()` decides whether to resize with `if image.size > new_size`. That
compares the `(width, height)` tuples lexicographically, so it looks only at
width unless the widths are equal. An image narrower than 660 px is never
resized, however tall it is. A 600×5000 image is stored at full size. It is
rare for photos, possible for long screenshots. The intended test is
`width > 660 or height > 720`. Worth fixing when the upload code is touched.
The same check is in `_process_local_upload`.
