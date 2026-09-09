# Safe AI Patcher

**Safe AI Patcher** (`sap`) is a project-agnostic tool for safely applying AI-generated code changes.

The goal is to replace fragile copy/paste workflows with a controlled change pipeline:

    receive change
        ↓
    validate
        ↓
    backup
        ↓
    preview diff
        ↓
    apply atomically
        ↓
    validate
        ↓
    test
        ↓
    PASS → keep
    FAIL → rollback

## Status

Early development — v0.1 scaffold.

## Planned Features

- Project detection
- Git awareness
- Safe file changes
- Atomic writes
- Automatic backups
- Diff previews
- Validation
- Project-specific tests
- Automatic rollback
- Transaction history
- AI-friendly change input
- CLI first
- Android frontend later

## Repository

The project is intentionally independent of any particular programming language, project, repository, AI provider, or development environment.

## License

TBD

### Snapshot Cleanup

Remove old transaction snapshots while preserving history-protected rollback targets:

```bash
sap cleanup --keep 10
```
