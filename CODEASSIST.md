# CODEASSIST.md

Project-specific overlay for the `agent-sops:code-assist` SOP. The SOP reads this
at its setup step and applies what is here throughout.

**Scope:** only things that are true of *running the SOP in this repo*. Codebase
facts — the test commands, the traps, the architecture — live in
[`AGENTS.md`](AGENTS.md) and [`.agents/summary/`](.agents/summary/index.md).
Do not restate them here; a second home for a claim is how the two drift apart.

## Parameters — already settled

Ask only if something about the task makes one of these wrong. Do not
re-litigate them each run, and state the inferred values rather than asking.

| Parameter | Value |
|---|---|
| `mode` | **interactive** |
| `documentation_dir` | the **session scratchpad**, never `.agents/scratchpad/` |
| `repo_root` | the repository root |
| `project_name` | inferred from the task path (`2026-07-04-modernizing-sg101`) |

**Why interactive.** Chosen for Step 16 task 09 over auto, and it earned its
keep: the design was redirected twice at the planning checkpoint and both
changes improved the result. The checkpoints are the value, not overhead.

**Why not `.agents/scratchpad/`.** That directory has never existed in this repo.
The SOP's `context.md` / `plan.md` / `progress.md` are working notes; a tracked
copy would be a second set of process artifacts sitting beside `STATUS.md`,
which is the duplication the Step 12 planning note blames for real drift.

## Overrides to the SOP

**Do not commit at the end.** The SOP's commit step conflicts with how this
project works: finish, report, and **leave the work unstaged**. Brian reviews
before anything is staged, committed, or pushed.

**"Commit and push" authorizes one commit, not a policy.** Explicit approval in
previous turns does not carry forward to the next piece of work. Ask again.

**Mutation verification is required, not optional.** A passing test proves
nothing until it has been watched to fail. Prefer writing the test first; where
that did not happen, run a mutation battery and record it — introduce a
deliberate defect per test, confirm the expected test fails, restore, and verify
the restored file is byte-identical and the suite green. Step 17 task 01 is a
worked example: eight mutations, all caught, recorded in `STATUS.md`.

**A mutation that does not reproduce the fault proves nothing either.** Check
that the mutation actually exercises the behaviour the test claims to cover.

## Where the record goes

**`STATUS.md` gets the durable write-up** — the one in the task's own project,
`.agents/planning/<project_name>/STATUS.md`: the modernization's for its
tasks, `2026-10-10-v3-forums-and-js/STATUS.md` for the V3 forums. A commit message is
not a substitute; the commit is found only by someone who already knows to look
for it.

Two rules that file is kept under, both earned:

1. **One claim, one home.** A decision lives in exactly one place and everything
   else points at it.
2. **A section is about one task, and it gets closed.** A running journal wants
   a log file, not a status heading.

Record what was *measured*, not just what was concluded, and keep the caveat
attached to the number rather than dropping it once the number is useful.

## Before starting

**Search `.agents/` before concluding something is undocumented or new.**
Planning, research and task files hold a great deal of this codebase's apparent
mystery, usually with the measurement attached. This has caught repeated
"discoveries" that were already recorded with the answer.

**Read the task file's *Background* section, not just its requirements.** Task
files in `.agents/tasks/` carry the reasoning and the known defects; several
name things deliberately left unverified, which are instructions to measure
rather than to assume.

## While writing code

**No step numbers in shipped code.** Comments describe the code, not the
modernization plan's step numbers or statistics. `STATUS.md` owns that
vocabulary; a comment saying "added in Step 16 task 02" is stale the moment the
plan is renumbered and meaningless to anyone reading the file on its own.

**Match the surrounding code** — its comment density, naming and idiom — rather
than importing conventions from elsewhere.

## Verifying

The suite and the deprecation gate are **two separate runs**; both must pass
before reporting completion. Commands are in [`AGENTS.md`](AGENTS.md).

**Browser-test anything touching deferred work or a rendered page.** The suite
cannot see it: `CELERY_TASK_ALWAYS_EAGER` hides worker faults by construction,
and tests assert state rather than what a person would see. Ten minutes in a
browser during Step 16 task 05 found six defects against 946 green tests.
