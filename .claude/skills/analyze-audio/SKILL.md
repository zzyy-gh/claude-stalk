---
name: analyze-audio
description: "Extract candidate key moments from a transcript into candidates.yaml. Called by podcast and adhoc agents."
version: "1.0"
forked: true
---

# Skill: Analyze Audio

Read a transcript and extract candidate key moments for the summary pipeline.

## Inputs

- `TRANSCRIPT`: path to `02-generated-transcript.md`
- `OUTPUT`: path to write `candidates.yaml`

## Execution

- Read the full transcript (`TRANSCRIPT`), chunking if needed to cover the entire file
- Extracts candidate key moments spread across the full runtime — roughly **one per 10 minutes** as a guide — each with:
  - `[HH:MM:SS]` timestamp from the transcript
  - One-sentence description of the insight/claim
  - One-sentence note on why it matters for a VC/AI audience
  - Any notable stats, figures, or claims worth flagging
- Determines relevance (relevant vs skipped) for the item
- Identifies speaker(s) with role (exclude demo props, mascots, audience members)
- Writes candidates to `OUTPUT`

Multiple items can run in parallel when called from a batch context.
