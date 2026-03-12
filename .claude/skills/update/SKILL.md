---
name: update
description: "This skill should be used when the user asks to 'update', 'run update', 'check all feeds', 'check all sessions', or 'update session-name'. It loops enabled sessions and runs each session's process."
version: "3.0"
---

# Skill: Update

Minimal orchestrator. Loops enabled sessions, runs each session's process.

## Arguments

- `/update` — process all sessions (all subdirectories of `sessions/` that contain `config.yaml`)
- `/update {session-name}` — process only `sessions/{session-name}/`

## Steps

1. **Determine sessions**: List all `sessions/*/config.yaml` (or just the one specified).

2. **For each session**:

   a. **Read config**: Load `sessions/{name}/config.yaml`. If `enabled: false`, skip this session.

   b. **Run process**: Read `sessions/{name}/process/SKILL.md` and execute it with:
      - `SESSION_DIR`: `sessions/{name}/`

   c. **Report**: Print whatever the process reported (new items found, or "no new content").

3. **Final summary** (multi-session only): Print results across all sessions.

## Loop integration

For automated polling, use:
```
/loop {frequency} /update
```
The `frequency` field in each session's config.yaml is an informational hint for how often to run.
