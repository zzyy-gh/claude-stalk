---
name: generate-html
description: "Converts a markdown summary/digest to styled HTML using category-specific templates and styles. Shared across all content categories."
version: "1.0"
forked: true
---

# Skill: Generate HTML

Convert a markdown summary or digest to styled HTML and optionally export it. Supports multiple content categories via template dispatch.

## Inputs

- `SUMMARY`: path to the markdown file (e.g., `summary.md` or `digest.md`)
- `CATEGORY`: content category — `audio` or `x` (determines which template/styles to use)
- `OUTPUT`: path to write the HTML file
- `EXPORT_DIR`: (optional) directory to copy HTML with formatted name
- `EXPORT_NAME`: (optional) filename for export

## Template Dispatch

Based on `CATEGORY`, select the appropriate template and styles:

| Category | Template | Styles |
|----------|----------|--------|
| `audio` | `.claude/skills/generate-html/assets/html-template-audio.html` | `.claude/skills/generate-html/assets/html-styles-audio.md` |
| `x` | `.claude/skills/generate-html/assets/html-template-x.html` | `.claude/skills/generate-html/assets/html-styles-x.md` |

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

### Export (optional)

If `EXPORT_DIR` is provided:
- Ensure the output directory exists (create if needed)
- Copy `OUTPUT` to `{EXPORT_DIR}/{EXPORT_NAME}`
- Report the exported file path
