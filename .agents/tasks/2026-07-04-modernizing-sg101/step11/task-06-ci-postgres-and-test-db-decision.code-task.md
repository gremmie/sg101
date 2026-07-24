# Task: Add Postgres to CI and Decide the Test-Database Policy

## Description
Bring continuous integration onto PostgreSQL and settle the deliberately deferred
question of which database the test suite runs against from here on. Then close
out Step 11: make Postgres the default for the Compose stack, update the
documentation, and record the step's outcome in the planning artifacts.

## Background
CI currently builds the Docker image and runs the suite with
`sg101.settings.docker_test`, which uses **sqlite** plus Redis over TCP. It
triggers on push and pull request to `modernize` and uploads a coverage
artifact. The suite is 567 tests, 5 skipped, at 84% coverage, and takes roughly
**5 seconds** on sqlite.

**The decision this task owns.** `implementation/plan.md` proposes keeping sqlite
for fast local runs and adding a Postgres job in CI. That was written before the
project owner asked to defer the call until there was real data. Task 01 measured
the suite's runtime on Postgres; **use that measurement, not the plan's default.**

The considerations, so the decision is made on merit:

- Sqlite cannot exercise Postgres-specific behavior at all. Step 12 builds
  Postgres full-text search — `SearchVectorField`, GIN indexes, `SearchQuery`,
  `SearchRank` — **none of which exist on sqlite**. Those tests must run on
  Postgres regardless of what is decided here.
- Task 04 established that schema drift between build paths is a real risk in
  this codebase. Sqlite tests cannot detect it.
- The design (§"testing strategy") anticipates running on Postgres via a CI
  service container once migrated, so PG-specific behavior is covered.
- Against that: a 5-second suite is a genuinely valuable local feedback loop, and
  the project's cadence is solo weekend bursts where iteration speed matters.

A split policy (sqlite locally, Postgres in CI) is legitimate, but it means
PG-only breakage reaches CI rather than the developer's terminal, and it leaves
Step 12's tests unable to run locally at all. Weigh that against the measured
runtime difference and make an explicit, recorded choice.

## Reference Documentation
**Required:**
- Design: `.agents/planning/2026-07-04-modernizing-sg101/design/detailed-design.md`
  (§testing strategy, §CI)

**Additional References (if relevant to this task):**
- `.agents/planning/2026-07-04-modernizing-sg101/research/search-stack.md`
  (what Step 12 will need from the test database)
- Task 01's completion notes (the measured Postgres suite runtime)

**Note:** You MUST read the detailed design document before beginning
implementation. Read additional references as needed for context.

## Technical Requirements
1. Add PostgreSQL to the CI workflow so the suite runs against the real engine.
   Follow the existing approach of using the same Docker image as local dev for
   parity, rather than diverging into a GitHub-hosted service container if that
   would break the parity the workflow comments call out.
2. Make the test-database decision explicitly, using task 01's measurement.
   Record the numbers and the reasoning in the planning artifacts — a future
   reader should be able to see what the runtime actually was and why the choice
   followed from it.
3. Implement whichever policy is chosen, including the settings modules needed to
   support it, and make sure the chosen local workflow is documented.
4. Keep coverage measurement and artifact upload working.
5. Make Postgres the default database for the Compose stack now that the
   conversion is proven. Decide whether the MySQL `db` service stays available
   for fallback through the remaining rungs, or is removed — the R17 fallback
   loses value once Postgres is verified, but Step 12 depends on Postgres
   permanently, so removal is defensible. Record the choice.
6. Update `DOCKER.md`: how to run against Postgres, how to load and convert a
   snapshot (linking task 03's procedure), and how to run the suite under the
   chosen policy.
7. Update the planning artifacts to close the step: tick Step 11 in
   `implementation/plan.md`'s checklist **and** write the execution record in
   `STATUS.md`. Both files — plan.md has previously drifted behind STATUS.md when
   only one was updated.
8. Carry forward anything Step 11 deliberately left undone, with its destination
   step named: the `elsewhere` seeding and `network_id`→FK rework, triage-app
   pruning, and any drift task 04 recorded but did not resolve.

## Dependencies
- Tasks 01–05 complete and verified
- Task 01's runtime measurement

## Implementation Approach
1. Revisit task 01's measurement and make the test-database call.
2. Update the CI workflow for Postgres and confirm it is green on a real push.
3. Implement the chosen local policy and its settings modules.
4. Switch the Compose default to Postgres and decide the MySQL service's fate.
5. Update `DOCKER.md`.
6. Write the step's completion into both planning files, including deferred
   items.

## Acceptance Criteria

1. **CI Runs on Postgres and Is Green**
   - Given a push to `modernize`
   - When CI runs
   - Then the suite executes against PostgreSQL and passes, with coverage still
     measured and the artifact still uploaded

2. **Test-Database Decision Made and Justified**
   - Given task 01's measured runtimes
   - When the decision is recorded
   - Then it states the policy, the measured numbers behind it, and how Step 12's
     Postgres-only test requirements are satisfied under it

3. **Chosen Policy Works Locally**
   - Given a developer following `DOCKER.md`
   - When they run the suite as documented
   - Then it works first time under the chosen policy

4. **Compose Defaults to Postgres**
   - Given a fresh `docker compose up`
   - When the stack starts
   - Then the application runs against Postgres by default, and the MySQL
     service's retention or removal is a recorded decision

5. **Documentation Current**
   - Given `DOCKER.md`
   - When read by someone returning to the project
   - Then it accurately describes running on Postgres, snapshot conversion, and
     the test workflow, with nothing left describing MySQL as the default

6. **Both Planning Files Updated**
   - Given Step 11 is complete
   - When `implementation/plan.md` and `STATUS.md` are inspected
   - Then the checklist entry is ticked with a summary, the execution record is
     written, and the two do not contradict each other

7. **Deferred Work Has a Named Destination**
   - Given the items Step 11 chose not to do
   - When the planning artifacts are read
   - Then each is listed with the step that will handle it, so nothing is
     silently dropped

## Metadata
- **Complexity**: Medium
- **Labels**: CI, Testing, PostgreSQL, Docker, Documentation, Planning, Step 11
- **Required Skills**: GitHub Actions, Docker Compose, Django test settings,
  technical writing
