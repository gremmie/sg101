# Task: Bound Redis Memory and Set an Eviction Policy That Cannot Eat the Broker

## Description
Give Redis a memory ceiling and an eviction policy that evicts only cache entries,
and move the connection configuration off the unix-socket path that belongs to the
old host.

## Background
**Carried in 2026-08-05 and unresolved since.** One Redis now serves three things:
the cache (db 2), the Celery broker (db 1) and the site's kept state (db 0). The
eviction policy is server-wide, so `allkeys-lru` would evict broker messages and
kept keys as readily as cache entries. `volatile-lru` evicts only keys that carry
a TTL, which is the cache and nothing else.

Unbounded, Redis grows until the VM's memory runs out, and the failure lands on
whichever service allocates next rather than on the cache that caused it.

**A second problem this task should fix while it is here.**
`sg101/settings/base.py:274` sets `REDIS_UNIX_SOCKET = '/var/run/redis/redis.sock'`
and line 283 points `CELERY_BROKER_URL` at the same socket. That is jaguar's
shape: a Redis process on the same machine. The compose stack reaches Redis as a
network service, so the socket assumption has to come out of the production path.

**Also worth knowing when reasoning about failure:** the Redis cache backend fails
hard where the memcached backend it replaced failed soft.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Set an explicit `maxmemory` on the production Redis service, derived from the
   VM's memory and documented.
2. Set `maxmemory-policy volatile-lru`.
3. Confirm the three logical databases and their roles, and confirm that broker
   and kept-state keys carry no TTL — the property the policy depends on.
4. ~~Move the production **Celery broker** off the unix socket onto the compose
   service.~~ **Moved to task 03, 2026-09-18** — see *Amendment record*. Task 03
   cannot serve a page without it, so it is done there as a `production.py`
   override; this task inherits a production module that already reaches Redis
   over TCP for all three databases.
5. **Invert `base.py:274`'s default.** It defaults `REDIS_UNIX_SOCKET` to
   `/var/run/redis/redis.sock` — jaguar's path — and every container config has
   to null it explicitly (`dev.py:29`, `docker_test.py:31`, and `production.py`
   since task 03, `60c54324`). **The default is the dead architecture and
   the live configs are the exceptions.** Default to TCP and let anything needing
   a socket say so. `base.py:283`'s `CELERY_BROKER_URL` names the same socket and
   goes the same way.
6. **Decide `core/services.py:26`'s dead branch.** Once no configuration supplies
   a socket path, `if unix_socket_path:` is unreachable and the
   `REDIS_UNIX_SOCKET` setting is dead with it. Small, but the same prune
   instinct as Step 19 Phase B — decide it here rather than leaving a branch
   nothing can reach.
7. Leave the development configuration working.
8. **Choose the Redis version.** Added 2026-09-19 from task 03: both compose files
   run `redis:6`, kept there by task 03 only for parity with development. Check
   the 6.x line's support status and the current stable release from Redis's own
   documentation rather than from memory, and move both files together if it
   moves. The eviction behaviour this task tests belongs to the version chosen.

**Added 2026-09-17.** Requirements 5 and 6 are the two socket consequences
`plan.md` records under Step 20's fourth "thing to settle" and no task file had
picked up. They are here rather than in task 01 because this task owns the socket
move; task 01 only stops `production.py` depending on it.

## Dependencies
- Task 03 — the production compose file that carries the Redis service, and the
  `production.py` override that moved all three databases off the socket
- The existing Celery configuration in `sg101/settings/base.py`

**The order is 03 then 05**, decided 2026-09-18. Task 03 ships a `redis` service
with no `maxmemory` and no policy — Redis's own defaults — and this task adds
both to that service. Task 03 does not list this task
as a dependency.

## Implementation Approach
1. Enumerate what actually writes to each database, from the code rather than
   from memory.
2. Verify that kept state and broker messages are written without expiry; if any
   carry a TTL, the policy choice has to be revisited before it is applied.
3. Apply the ceiling and policy in the compose service, not in a host config file
   that will not travel.
4. Exercise it: fill the cache past the ceiling and confirm what survives.

## Acceptance Criteria

1. **The ceiling and policy are in effect**
   - Given the production Redis service
   - When `CONFIG GET maxmemory` and `CONFIG GET maxmemory-policy` are read
   - Then both return the intended values

2. **Eviction takes cache entries and nothing else**
   - Given a Redis filled past `maxmemory` with cache entries, queued broker
     messages and kept state
   - When eviction runs
   - Then cache keys are evicted and the broker messages and kept state remain

3. **Kept state and broker messages carry no TTL**
   - Given the keys written to db 0 and db 1
   - When their TTLs are inspected
   - Then none is set, which is what makes `volatile-lru` safe

4. **No configuration assumes a unix socket by default**
   - Given `base.py` after the default is inverted
   - When the socket setting and broker URL are read from every settings module
   - Then all address Redis over TCP, and the explicit nulls task 03 and the
     container modules added are gone because nothing needs them (task 03 owns
     the production half of this; this criterion is the default's)

5. **The suite stays green**
   - Given the full test suite
   - When it is run
   - Then it passes

## Metadata
- **Complexity**: Medium
- **Labels**: Redis, Celery, Caching, Production Hardening
- **Required Skills**: Redis configuration, Celery brokers, Django cache backends

## Amendment record — 2026-09-18

1. **Tasks 03 and 05 each listed the other as a dependency.** Brian's call: 03
   first. This file keeps its dependency on 03; task 03's on this one is removed.
2. **Requirement 4 moved to task 03, and it was narrower than the defect.** It
   said production's only remaining socket dependency was `CELERY_BROKER_URL`.
   Read out of the settings 2026-09-18: `production.py` also leaves
   `REDIS_UNIX_SOCKET` inherited from `base.py:274`, and `core/services.py`
   uses the socket whenever that setting is truthy. So **db 0 — who's-online and
   the forums' latest-post lists — also points at jaguar's socket in production**,
   not only the broker. `dev.py:29` and `docker_test.py:31` null it; production
   never did. Task 03 cannot pass its own acceptance criterion 1 with either half
   broken, so the override goes there: null `REDIS_UNIX_SOCKET` and set the broker
   URL in `production.py`, the same shape `dev.py` already uses.
3. **Line references corrected**: `base.py:264`/`:273` are now `:274`/`:283`,
   moved by task 01 and 02's edits, and `docker.py:38` no longer exists — task
   01 merged it into `dev.py`, which nulls the socket at line 29.
4. **Acceptance criterion 4 rewritten** to the default inversion, since its
   production half is now task 03's.

## Amendment record — 2026-09-19

1. **Requirement 8 added: choose the Redis version.** Task 03 kept `redis:6` in
   the production stack only for parity with development and recorded it as
   open; this task owns the Redis service, so the choice belongs here.
2. **Requirement 5's `production.py` reference made current** — task 03 landed
   in `60c54324` with the explicit null in place.
