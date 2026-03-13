---
name: scheduled-check
description: "This skill should be used when the user asks to 'scheduled-check' or 'run scheduled check'. Sends a Telegram heartbeat then runs update on ai-podcast."
version: "1.0"
---

# Skill: Scheduled Check

Sends a Telegram notification, then runs the ai-podcast update pipeline.

## Arguments

- `/scheduled-check {session-name}` — send heartbeat then update the specified session
- `/scheduled-check` — send heartbeat then update all sessions

## Steps

### 1. Send Telegram heartbeat

Run the notify script:

```bash
bash .claude/scripts/notify-telegram.sh "🔍 Scheduled check started"
```

### 2. Update

Read `.claude/skills/update/SKILL.md` and execute it, passing through the session argument if provided.
