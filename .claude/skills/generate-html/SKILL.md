---
name: generate-html
description: "Converts a markdown summary/digest to styled HTML using category-specific templates and styles. Shared across all content categories."
version: "1.0"
forked: true
---

# Skill: Generate HTML

Convert a markdown summary or digest to styled HTML. Supports multiple content categories via template dispatch. Export is handled by the calling agent, not this skill.

## Inputs

- `SUMMARY`: path to the markdown file (e.g., `summary.md` or `digest.md`)
- `CATEGORY`: content category — `audio`, `x`, or `webpage` (determines which template/styles to use)
- `OUTPUT`: path to write the HTML file

## Template Dispatch

Based on `CATEGORY`, select the appropriate template and styles:

| Category | Template | Styles |
|----------|----------|--------|
| `audio` | `.claude/skills/generate-html/assets/html-template-audio.html` | `.claude/skills/generate-html/assets/html-styles-audio.md` |
| `x` | `.claude/skills/generate-html/assets/html-template-x.html` | `.claude/skills/generate-html/assets/html-styles-x.md` |
| `webpage` | `.claude/skills/generate-html/assets/html-template-webpage.html` | `.claude/skills/generate-html/assets/html-styles-webpage.md` |

Future categories just add new template + styles files — no skill logic changes needed.

## Execution

### Generate HTML

Run the converter script:
```bash
python scripts/md-to-html.py \
  --input "{SUMMARY}" \
  --template ".claude/skills/generate-html/assets/html-template-{CATEGORY}.html" \
  --category "{CATEGORY}" \
  --output "{OUTPUT}"
```

The script handles markdown-to-HTML conversion with all inline styles per the styles reference files. The styles `.md` files in `assets/` serve as documentation for the conversion rules hardcoded in the script.
