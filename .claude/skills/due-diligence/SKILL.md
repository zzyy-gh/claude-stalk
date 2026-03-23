---
name: due-diligence
description: "Due diligence review — scans a summary/digest markdown file for unverified claims and flags them with italic parentheticals. Shared across all content categories."
version: "1.0"
forked: true
---

# Skill: Due Diligence

Review a summary or digest for unverified claims and add analytical flags. Works with any content category (podcast, social media, etc.).

## Inputs

- `SUMMARY`: path to the markdown file to review (e.g., `summary.md` or `digest.md`)

## Execution

Re-read `SUMMARY` and scan **both content sections and the "What to watch" block** for issues:

### Content claims — flag specific issues

- Unverified stats or imprecise figures (e.g., "revenue doubled" with no source)
- Vague or second-hand attribution (e.g., "X allegedly said", "reportedly")
- Assertions that contradict known data or consensus
- Macro claims presented as fact without evidence
- New or emerging technology claims touted with specific capabilities that haven't been independently tested or proven (e.g., "this model can replace all junior devs" without benchmarks)
- Forward projections stated as certainties (e.g., "AI will eliminate 50% of jobs by 2028") without caveats or supporting analysis

For each genuine concern, append a brief italic parenthetical. Keep flags natural and concise — they should read as analyst judgment, not disclaimers:
_(second-hand -- no primary source cited)_
_(single-source -- not independently confirmed)_
_(this signal relies on the unverified claim above)_

### "What to watch" block — bigger-picture scrutiny

The signals synthesized here draw from the content, so also consider:

- Whether a "What to watch" signal rests on a flagged claim (if so, note the dependency)
- Consensus illusion: multiple sources repeating the same narrative may look like convergence but trace back to one unverified source
- Selection bias: the set of items may overweight one perspective — note if the "What to watch" signals only reflect one side
- Extrapolation leaps: a real data point being stretched into a broad trend without supporting evidence
- Missing context: important context absent that would materially change the picture (e.g., a major counterargument, a relevant regulatory development, or key data not mentioned)
- Conflicting narratives: sources that contradict each other — surface the tension rather than picking a side
- Systemic uncertainties: structural unknowns worth flagging that no single source can resolve (e.g., regulatory outcomes, macro shifts, unproven market assumptions)

No italic parenthetical here — just apply judgment and flag any signals that seem overhyped, under-evidenced, or one-sided with a brief note in the text. The goal is to provide a clear-eyed synthesis that highlights real insights while signaling where caution is warranted.

Do not force flags where none exist. Update `SUMMARY` in place.
