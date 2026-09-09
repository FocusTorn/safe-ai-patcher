# Safe AI Patcher — Remaining Action Plan

## Current State

Completed and pushed:

- [x] Initial project scaffold
- [x] Safe patch transaction engine
- [x] Transactional `apply` command
- [x] Project detection
- [x] Git awareness
- [x] Structured change files
- [x] Diff preview
- [x] Transaction history
- [x] JSON history output
- [x] Dirty Git protection
- [x] Persistent rollback snapshots
- [x] Rollback conflict detection
- [x] Forced rollback
- [x] Rollback/history failure hardening
- [x] Apply exposes transaction ID
- [x] Transaction lookup by full ID
- [x] Snapshot cleanup (retention logic, protected targets, garbage collection)

Current test baseline: **34 tests passing**.

---

# PHASE 1 — Finish Snapshot Management (COMPLETED)

## 1. Fix `cleanup` implementation

- [x] Remove duplicate `cleanup` argparse registration
- [x] Properly import `cleanup_snapshots` in snapshot tests
- [x] Add cleanup tests inside the existing test class
- [x] Test `--keep N`
- [x] Test default retention
- [x] Test `--keep 0`
- [x] Test negative `--keep`
- [x] Test missing `.sap/transactions`
- [x] Test rollback-protected snapshots
- [x] Test malformed/unrecognized transaction directories
- [x] Test cleanup never touches unrelated `.sap` files

## 2. Decide snapshot retention semantics

- [x] Document retention policy (Keep 10 newest, preserve rollback targets)
- [x] Add cleanup command to README
- [x] Run complete test suite
- [x] Compile
- [x] `git diff --check`
- [x] One clean commit
- [x] Push

---

# PHASE 2 — Harden the Transaction Engine (COMPLETED)

## 3. Harden snapshot creation

- [x] Make snapshot creation failure-safe
- [x] Ensure partially-created snapshots cannot be mistaken for valid transactions
- [x] Clean up incomplete snapshot directories
- [x] Ensure no file changes occur if snapshot creation fails
- [x] Add failure tests

## 4. Harden snapshot validation

- [x] Validate transaction IDs
- [x] Reject malformed metadata safely
- [x] Handle missing snapshot payload files
- [x] Validate metadata paths
- [x] Validate expected hashes
- [x] Prevent symlink/path traversal abuse during restore
- [x] Test corrupted snapshot scenarios

## 5. Harden atomic writes

- [x] Review temporary-file handling
- [x] Verify permissions/modes are preserved
- [x] Verify file replacement is atomic
- [x] Verify cleanup of temporary files after failure
- [x] Add failure-path tests

---

# PHASE 3 — Better Transaction Semantics

## 6. Improve transaction records

Current history records:

```text
id
timestamp
status
paths
test_command
error
rollback_of
```

Add useful metadata where appropriate:

- [ ] project/root identifier
- [ ] number of changes
- [ ] snapshot availability
- [ ] duration
- [ ] tool/version information

Do not overcomplicate the format.

## 7. Transaction status model

Define and document:

```text
committed
rolled_back
rollback
```

- [ ] Clarify distinction between automatic rollback and manual rollback
- [ ] Make history output consistent
- [ ] Add tests for each status
- [ ] Ensure transaction relationships remain understandable

---

# PHASE 4 — CLI Safety UX

## 8. Improve `sap info`

Make it useful as the project safety overview:

```text
Project
Git status
Project type
SAP directory
Transaction count
Latest transaction
Snapshot count
```

- [ ] Implement/finish `sap info`
- [ ] Add JSON mode if useful
- [ ] Add tests

## 9. Improve `sap history`

Current:

```text
sap history
sap history --json
sap history <transaction-id>
```

Add:

- [ ] `--limit`
- [ ] clearer human-readable output
- [ ] status indicators
- [ ] optional filtering by status
- [ ] possibly `--json` for transaction lookup too

Keep the normal output compact.

## 10. Improve rollback UX

Current:

```text
sap rollback <transaction-id>
sap rollback <transaction-id> --force
```

Add:

- [ ] clearer transaction summary before rollback
- [ ] distinguish "not found" from "conflict"
- [ ] show restored paths
- [ ] optionally support `--json`
- [ ] tests for every failure mode

---

# PHASE 5 — Structured AI Input

## 11. Define the AI change format

Establish a stable schema such as:

```json
{
  "changes": [
    {
      "path": "src/example.py",
      "content": "..."
    }
  ]
}
```

Then expand carefully:

- [ ] schema version
- [ ] optional change description
- [ ] optional expected old content/hash
- [ ] optional test command
- [ ] optional project metadata

Example future format:

```json
{
  "version": 1,
  "changes": [
    {
      "path": "src/example.py",
      "content": "..."
    }
  ]
}
```

- [ ] Validate schema strictly
- [ ] Reject unknown/dangerous fields where appropriate
- [ ] Add comprehensive parser tests

---

# PHASE 6 — AI Patch Safety

## 12. Add stronger preflight validation

Before touching files:

```text
parse
  ↓
validate schema
  ↓
detect project
  ↓
validate paths
  ↓
check Git state
  ↓
generate diff
  ↓
create snapshot
  ↓
apply
```

Add:

- [ ] maximum file/path limits
- [ ] maximum patch size
- [ ] binary-file policy
- [ ] symlink policy
- [ ] protected-file policy
- [ ] `.git` protection
- [ ] `.sap` protection
- [ ] optional allow/deny patterns

---

# PHASE 7 — Preview / Approval Workflow

## 13. Make preview a first-class safety step

Ideal workflow:

```text
sap diff change.json
        ↓
review
        ↓
sap apply change.json
```

Improve:

- [ ] clear summary of added/modified/deleted files
- [ ] additions/deletions count
- [ ] size changes
- [ ] dangerous-path warnings
- [ ] Git dirty warnings
- [ ] optional interactive confirmation

Potential future command:

```text
sap apply change.json --preview
```

---

# PHASE 8 — Testing / Reliability

## 14. Build a comprehensive safety test suite

Cover:

- [ ] path traversal
- [ ] absolute paths
- [ ] symlinks
- [ ] duplicate paths
- [ ] missing files
- [ ] new files
- [ ] empty files
- [ ] large files
- [ ] permission changes
- [ ] dirty Git state
- [ ] test failure
- [ ] rollback failure
- [ ] snapshot corruption
- [ ] history corruption
- [ ] interrupted transactions
- [ ] cleanup failures

Target:

```text
100+ focused tests
```

without making the implementation unnecessarily complicated.

---

# PHASE 9 — Crash Recovery

## 15. Handle interrupted transactions

This is an important safety feature before calling the engine production-ready.

Design:

```text
transaction starts
      ↓
mark pending
      ↓
snapshot created
      ↓
files modified
      ↓
transaction committed
```

If the process dies midway:

```text
sap
 ↓
detect pending transaction
 ↓
offer/recommend recovery
 ↓
restore snapshot
```

Implement:

- [ ] pending transaction state
- [ ] startup/recovery detection
- [ ] interrupted-write tests
- [ ] recovery command
- [ ] recovery history records

Potential command:

```text
sap recover
```

---

# PHASE 10 — Configuration

## 16. Add project/user configuration

Potential:

```text
.sap/config.json
```

Configuration could control:

- [ ] default test command
- [ ] snapshot retention
- [ ] protected paths
- [ ] maximum patch size
- [ ] Git behavior
- [ ] preview behavior

Keep configuration optional.

The tool should work with zero configuration.

---

# PHASE 11 — Packaging / Installation

## 17. Make `sap` properly installable

Current launcher works in the development environment.

Move toward:

```text
pip install safe-ai-patcher
```

and:

```text
sap --help
```

- [ ] package metadata
- [ ] console entry point
- [ ] version number
- [ ] install test
- [ ] clean environment test
- [ ] Termux installation test

---

# PHASE 12 — Documentation

## 18. Rewrite README around actual workflow

README should eventually show:

```text
# Safe AI Patcher

AI generates change
        ↓
sap diff
        ↓
human reviews
        ↓
sap apply
        ↓
snapshot
        ↓
atomic changes
        ↓
tests
        ↓
PASS → committed
FAIL → automatic rollback
```

Document:

- [ ] installation
- [ ] supported platforms
- [ ] `sap diff`
- [ ] `sap apply`
- [ ] `sap history`
- [ ] `sap rollback`
- [ ] `sap cleanup`
- [ ] `sap info`
- [ ] recovery
- [ ] change-file format
- [ ] safety guarantees
- [ ] limitations
- [ ] examples

---

# PHASE 13 — CLI Polish

## 19. Consistent command behavior

Standardize:

```text
exit 0 = success
exit 1 = expected/user error
non-zero unexpected = internal failure
```

- [ ] consistent error prefix
- [ ] consistent stderr usage
- [ ] consistent JSON output
- [ ] useful `--help`
- [ ] useful top-level help
- [ ] version command

Potential:

```text
sap --version
```

---

# PHASE 14 — AI Integration Boundary

## 20. Design the AI-facing API without coupling to a provider

The core should accept structured changes regardless of where they came from:

```text
AI
 ↓
structured change JSON
 ↓
SAP validator
 ↓
SAP transaction engine
```

Do NOT tightly couple the project to:

- OpenAI
- Claude
- Gemini
- any specific agent
- any specific editor

Instead provide a stable machine-readable interface.

- [ ] documented JSON schema
- [ ] stdin support
- [ ] JSON stdout mode
- [ ] machine-readable errors
- [ ] transaction ID output
- [ ] predictable exit codes

Potential future usage:

```bash
agent | sap apply -
```

---

# PHASE 15 — Android / Acode Integration

Only start this after the CLI core is stable.

## 21. Android frontend architecture

Target:

```text
Acode
  ↓
Acode plugin
  ↓
SAP CLI/API
  ↓
Termux
  ↓
Safe AI Patcher
```

Potential UI:

```text
┌─────────────────────────┐
│ Safe AI Patcher         │
├─────────────────────────┤
│ Project                 │
│                         │
│ Changes: 3              │
│ +42  -17                │
│                         │
│ [ Preview ]             │
│ [ Apply Safely ]        │
│                         │
│ Last transaction        │
│ 8f3a91c2...             │
│                         │
│ [ History ] [ Rollback ]│
└─────────────────────────┘
```

- [ ] define IPC boundary
- [ ] define CLI/API protocol
- [ ] build minimal Acode integration
- [ ] show diff
- [ ] apply
- [ ] display transaction ID
- [ ] history viewer
- [ ] rollback UI

---

# PHASE 16 — Release v0.1

## 22. v0.1 Definition of Done

Before calling v0.1 complete:

- [ ] Safe structured changes
- [ ] Path validation
- [ ] Git awareness
- [ ] Dirty-file protection
- [ ] Atomic writes
- [ ] Persistent snapshots
- [ ] Automatic rollback
- [ ] Manual rollback
- [ ] Transaction history
- [ ] Transaction lookup
- [ ] Snapshot cleanup
- [ ] Crash-safe transaction state
- [ ] Comprehensive tests
- [ ] CLI installation
- [ ] README documentation
- [ ] Clean Git repository
- [ ] Release tag

Target:

```text
v0.1.0
```

---

# Development Rule

Continue using:

```text
EDIT
  ↓
BUILD WHOLE STAGE
  ↓
TEST
  ↓
INSPECT
  ↓
ONE CLEAN COMMIT
  ↓
PUSH
  ↓
NEXT STAGE
```

Do NOT create a commit for every tiny edit.

Each stage should leave the repository:

```text
tests passing
compile clean
git diff --check clean
working tree clean
pushed to origin
```

---

# Immediate Next Actions

1. Fix the duplicate `cleanup` parser registration.
2. Fix the cleanup tests so they actually execute.
3. Add the remaining cleanup edge-case tests.
4. Run the complete suite.
5. Inspect the implementation.
6. Commit/push the completed snapshot-cleanup stage.
7. Move to **transaction/snapshot failure hardening**.
8. Then crash recovery.
9. Then CLI/API polish.
10. Then packaging.
11. Then Android/Acode integration.

**Priority:** Keep the transaction engine rock-solid before adding UI features.