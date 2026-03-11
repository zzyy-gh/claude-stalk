---
name: update
description: "This skill should be used when the user asks to 'update', 'run update', 'check all feeds', 'check all sessions', or 'update session-name'. It runs the full stalker pipeline: stalk for new content, then delegate to each session's custom skill."
version: "1.0"
---

# Skill: Update

High-level orchestrator. Iterates sessions, stalks for new content, and delegates processing to each session's custom skill.

## Arguments

- `/update` — process all sessions (all subdirectories of `sessions/` that contain `config.yaml`)
- `/update {session-name}` — process only `sessions/{session-name}/`

## Steps (per session)

1. **Read config**: Load `sessions/{name}/config.yaml`.

2. **Stalk**: Read `skills/stalk/SKILL.md` and execute it for this session.
   - This returns a list of new (unseen) items
   - If no new items: report "No new content for {name}" and skip to next session

3. **Create update directory**:
   - Generate timestamp: `YYYY-MM-DD-HHMM` from current time
   - Create `sessions/{name}/updates/{timestamp}/`

4. **Delegate to custom skill**:
   - Read `sessions/{name}/custom-skill/SKILL.md`
   - Execute it with the following context:
     - `NEW_ITEMS`: the list of new items from stalk (each has title, url, source_type, source_name, published)
     - `UPDATE_DIR`: `sessions/{name}/updates/{timestamp}/`
     - `SESSION_DIR`: `sessions/{name}/`
     - `OUTPUT_DIR`: from `config.yaml` (may be null)
   - The custom skill orchestrates the per-item pipeline (ingest, transcribe, summarize, etc.)
   - It creates `{item-slug}/` subdirectories within `UPDATE_DIR` as needed
   - It may produce cross-item outputs like `summary.md` in `UPDATE_DIR`

5. **Update seen.yaml**:
   - After the custom skill completes, check which items were successfully processed
   - Look for `{item-slug}/metadata.yaml` files in `UPDATE_DIR` with `stages.ingest.completed: true`
   - Append each successfully-processed URL to `sessions/{name}/seen.yaml`:
     ```yaml
     - url: "https://..."
       title: "Item Title"
       date_seen: "2026-03-11T14:00:00Z"
     ```
   - Items that failed or were skipped by the custom skill are NOT added to seen (will be retried next run)

6. **Report**: Print summary for this session:
   ```
   Session: {name}
   New items found: {count}
   Successfully processed: {count}
   Failed: {count}
   Update folder: sessions/{name}/updates/{timestamp}/
   ```

## Multi-session run

When running all sessions:
- Process each session sequentially
- Print a final summary across all sessions
- Report any sessions that had errors

## Loop integration

For automated polling, use:
```
/loop {frequency} /update
```
The `frequency` field in each session's config.yaml is an informational hint for how often to run.
