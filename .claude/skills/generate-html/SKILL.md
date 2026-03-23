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

- Read `SUMMARY`
- Read the appropriate template — this is the styled wrapper with a `{content}` placeholder
- Read the appropriate styles mapping
- Convert the markdown content to semantic HTML with inline styles, following the mapping in the styles file
- Insert the converted HTML into the template's `{content}` placeholder
- Save as `OUTPUT`

### Export (optional)

If `EXPORT_DIR` is provided:
- Ensure the output directory exists (create if needed)
- Copy `OUTPUT` to `{EXPORT_DIR}/{EXPORT_NAME}`
- Report the exported file path
