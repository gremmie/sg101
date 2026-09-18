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
`sg101/settings/base.py:264` sets `REDIS_UNIX_SOCKET = '/var/run/redis/redis.sock'`
and line 273 points `CELERY_BROKER_URL` at the same socket. That is jaguar's
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
4. Move the production **Celery broker** off the unix socket onto the compose
   service. **The cache half is already done** — task 01 rewrote
   `production.py`'s `CACHES['default']['LOCATION']` to `redis://host:port/2`
   and gave the module its own `REDIS_HOST`/`REDIS_PORT`. What remains is
   `CELERY_BROKER_URL`, which `production.py` does not override at all: it
   inherits `base.py:273`'s `redis+socket:///var/run/redis/redis.sock`, so
   **production is not deployable until this task lands.** Verified 2026-09-17
   by reading the setting out of the production module.
5. **Invert `base.py:264`'s default.** It defaults `REDIS_UNIX_SOCKET` to
   `/var/run/redis/redis.sock` — jaguar's path — and every container config has
   to null it explicitly (`docker.py:38`, `docker_test.py:31`, and whatever task
   01's merge leaves in their place). **The default is the dead architecture and
   the live configs are the exceptions.** Default to TCP and let anything needing
   a socket say so. `base.py:273`'s `CELERY_BROKER_URL` names the same socket and
   goes the same way.
6. **Decide `core/services.py:26`'s dead branch.** Once no configuration supplies
   a socket path, `if unix_socket_path:` is unreachable and the
   `REDIS_UNIX_SOCKET` setting is dead with it. Small, but the same prune
   instinct as Step 19 Phase B — decide it here rather than leaving a branch
   nothing can reach.
7. Leave the development configuration working.

**Added 2026-09-17.** Requirements 5 and 6 are the two socket consequences
`plan.md` records under Step 20's fourth "thing to settle" and no task file had
picked up. They are here rather than in task 01 because this task owns the socket
move; task 01 only stops `production.py` depending on it.

## Dependencies
- Task 03 — the production compose file that carries the Redis service
- The existing Celery configuration in `sg101/settings/base.py`

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

4. **Production no longer assumes a unix socket**
   - Given production settings
   - When the cache and broker URLs are read
   - Then both address the Redis service over the network and
     `/var/run/redis/redis.sock` appears nowhere in the production path

5. **The suite stays green**
   - Given the full test suite
   - When it is run
   - Then it passes

## Metadata
- **Complexity**: Medium
- **Labels**: Redis, Celery, Caching, Production Hardening
- **Required Skills**: Redis configuration, Celery brokers, Django cache backends
