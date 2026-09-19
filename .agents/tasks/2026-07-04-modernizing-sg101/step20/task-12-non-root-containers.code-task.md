# Task: Run the Application Containers as an Ordinary User

## Description
Run `web`, `worker` and `beat` as an unprivileged user instead of root, and make
the host directories they write to work under that user on the VM.

**Generated 2026-09-19**, from an item task 03 recorded as open in
`STATUS.md` § Step 20 task 03, "Open, and not this task's".

## Background
The `prod` stage of the `Dockerfile` has no `USER` line, so everything in the
image runs as root. Measured in the running production stack on 2026-09-19:

| Container | Runs as |
|---|---|
| `web` (gunicorn) | `uid=0(root)` |
| `worker` (Celery) | root — Celery prints `SecurityWarning: You're running the worker with superuser privileges` at every start |
| `beat` | root (same image) |
| `proxy` (Apache) | one root parent, children as `www-data` — **the standard arrangement, and out of scope**: the parent needs root to bind 80 and 443 |

**Why it matters:** a code-execution bug in the application gets root inside the
container, and a root process is what most container escapes start from. It also
owns every file it writes on the host's bind mounts.

**Why now:** nothing in the stack depends on root yet, and nothing has been
deployed. After cutover, changing the user means changing ownership of a live
media tree.

### Where the work actually is
The `USER` line is one line. The work is the bind mounts, because a container
user and a host user are matched by **numeric UID**, not by name:

- `web` writes `./media` (uploads) and `./var/log/django`
- `worker` and `beat` write `./var/log/django`
- `collectstatic` runs at build time and writes `/static_root` inside the image,
  which only needs to be readable afterwards

Under Docker Desktop on macOS, bind-mount ownership is translated and almost
anything works — **so a local test can pass on a configuration the Linux VM will
reject.** On the VM, the host directories must be writable by the container's
UID. Decide how: a fixed UID in the image matching a host account, or the UID
passed at build or run time.

## Reference Documentation
**Required:**
- `Dockerfile` — the `prod` and `dev` stages
- `docker-compose.prod.yml` — the mounts each service has

**Additional References (if relevant to this task):**
- `cutover-runbook.md` § B4 — the media tree arrives by rsync, and its ownership
  has to come out right on the VM

## Technical Requirements
1. The `prod` image runs its processes as a non-root user.
2. `dev` either inherits that user or deliberately sets root back, with the
   reason stated. Development bind-mounts the whole checkout, which changes the
   question.
3. Decide and document how the container's UID matches the owner of `media/`
   and `var/` on the VM.
4. Add a cutover-runbook step setting ownership of `media/` and `var/` on the VM,
   placed after B4's rsync, which would otherwise undo it.
5. Celery's superuser `SecurityWarning` is gone from the worker's startup output.

## Dependencies
- Task 03 — the production stack and its mounts
- Task 11, if it lands first — the `var/log/django` it rotates must stay
  writable by the new user; `logrotate`'s `create` mode names an owner

## Implementation Approach
1. List every path each process writes, from the code and the mounts rather than
   from this file's list, which was read, not measured.
2. Add the user; rebuild; run `tools/prod_smoke.sh`, queue a task, upload an
   image through the site.
3. **Test the ownership question on Linux, not only on macOS** — a Linux
   container with a bind mount (or CI) — since Docker Desktop hides it.

## Acceptance Criteria

1. **No application process runs as root**
   - Given the production stack
   - When `id` is run in `web`, `worker` and `beat`
   - Then none reports uid 0

2. **Everything that writes still writes**
   - Given the production stack under the new user
   - When a photo is uploaded, a task runs and a log line is written
   - Then each succeeds, and the files on the host are owned by the chosen UID

3. **Celery stops warning**
   - Given the worker's startup output
   - When it is read
   - Then there is no superuser `SecurityWarning`

4. **The VM step is written down**
   - Given `cutover-runbook.md`
   - When section B is read
   - Then setting ownership of `media/` and `var/` after the rsync is an entry

## Metadata
- **Complexity**: Small–Medium
- **Labels**: Docker, Security, Production Hardening
- **Required Skills**: Dockerfile users, bind-mount ownership on Linux
