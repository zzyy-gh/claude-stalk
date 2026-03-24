#!/usr/bin/env python3
"""Markdown to styled HTML converter with inline styles.

Converts markdown to HTML with all styles inline (no CSS classes, no <style> blocks).
Category (audio or x) determines which style rules to apply.

Usage:
    python md-to-html.py --input summary.md --template template.html --category audio --output summary.html
"""

import argparse
import html
import re
import sys


# ---------------------------------------------------------------------------
# Inline formatting helpers
# ---------------------------------------------------------------------------

def _apply_inline_formatting(text, category):
    """Apply inline formatting: bold, italic, links, due-diligence flags."""
    # Due-diligence italic flags FIRST (before generic italic)
    # Pattern: _(second-hand -- no primary source cited)_ and similar
    text = re.sub(
        r'_\(([^)]+)\)_',
        r'<em style="color:#e67700; font-size:13px;">(\1)</em>',
        text,
    )

    # Links: [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" style="color:#1971c2; text-decoration:none;">\1</a>',
        text,
    )

    # Bold: **text**
    text = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong style="color:#1a1a2e;">\1</strong>',
        text,
    )

    # Italic: *text* (but not inside already-processed tags)
    text = re.sub(
        r'(?<![</"a-z])\*([^*]+?)\*(?![>"])',
        r'<em>\1</em>',
        text,
    )

    return text


def _is_timestamp_link(match_text):
    """Check if link text looks like a timestamp [HH:MM:SS]."""
    return bool(re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', match_text))


def _apply_inline_formatting_audio_list(text):
    """Apply inline formatting for audio list items, with timestamp link handling."""
    # Due-diligence flags
    text = re.sub(
        r'_\(([^)]+)\)_',
        r'<em style="color:#e67700; font-size:13px;">(\1)</em>',
        text,
    )

    # Timestamp links: [HH:MM:SS](url)
    text = re.sub(
        r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\(([^)]+)\)',
        r'<a href="\2" style="color:#364fc7; font-weight:600; font-family:Courier New, monospace; font-size:13px; text-decoration:none;">[\1]</a>',
        text,
    )

    # Regular links
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" style="color:#1971c2; text-decoration:none;">\1</a>',
        text,
    )

    # Bold
    text = re.sub(
        r'\*\*(.+?)\*\*',
        r'<strong style="color:#1a1a2e;">\1</strong>',
        text,
    )

    # Italic
    text = re.sub(
        r'(?<![</"a-z])\*([^*]+?)\*(?![>"])',
        r'<em>\1</em>',
        text,
    )

    return text


# ---------------------------------------------------------------------------
# Table parsing
# ---------------------------------------------------------------------------

def _parse_table(lines, category):
    """Parse markdown table lines into HTML."""
    result = []
    margin = '24px' if category == 'x' else '16px'
    result.append(f'<table style="width:100%; border-collapse:collapse; font-size:14px; margin-bottom:{margin};">')

    header_done = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        # Skip separator rows
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            continue

        cells = [c.strip() for c in stripped.split('|')[1:-1]]

        if not header_done:
            result.append('<tr>')
            for cell in cells:
                result.append(
                    f'<th style="background-color:#f1f3f5; text-align:left; padding:8px 12px; '
                    f'font-weight:600; color:#495057; border:1px solid #dee2e6;">{_apply_inline_formatting(cell, category)}</th>'
                )
            result.append('</tr>')
            header_done = True
        else:
            result.append('<tr>')
            for idx, cell in enumerate(cells):
                if category == 'x' and idx == 0:
                    result.append(
                        f'<td style="background-color:#f1f3f5; padding:8px 12px; font-weight:600; '
                        f'color:#495057; border:1px solid #dee2e6; width:200px;">{_apply_inline_formatting(cell, category)}</td>'
                    )
                else:
                    result.append(
                        f'<td style="padding:8px 12px; color:#495057; border:1px solid #dee2e6;">{_apply_inline_formatting(cell, category)}</td>'
                    )
            result.append('</tr>')

    result.append('</table>')
    return '\n'.join(result)


# ---------------------------------------------------------------------------
# Metadata pills (audio)
# ---------------------------------------------------------------------------

_PILL_PATTERNS = [
    (r'\*\*Source\*\*:\s*(.+?)(?:\s*\||\s*$)', 'background-color:#d0ebff; color:#1864ab;', 'Source'),
    (r'\*\*Guest\(s\)\*\*:\s*(.+?)(?:\s*\||\s*$)', 'background-color:#fff3bf; color:#e67700;', 'Guest(s)'),
    (r'\*\*Published\*\*:\s*(.+?)(?:\s*\||\s*$)', 'background-color:#e6fcf5; color:#087f5b;', 'Published'),
]


def _is_metadata_line(line):
    """Check if line is a metadata pill line."""
    return '**Source**:' in line and '**Published**:' in line


def _render_metadata_pills(line):
    """Render metadata pills from a line like **Source**: ... | **Guest(s)**: ... | **Published**: ..."""
    pills = []
    for pattern, style, label in _PILL_PATTERNS:
        m = re.search(pattern, line)
        if m:
            value = m.group(1).strip()
            formatted_value = _apply_inline_formatting(value, 'audio')
            pills.append(
                f'<span style="display:inline-block; padding:3px 10px; margin:0 4px 4px 0; '
                f'font-weight:500; {style}">{label}: {formatted_value}</span>'
            )
    if pills:
        return f'<div style="margin-bottom:12px; font-size:13px;">\n{"".join(pills)}\n</div>'
    return ''


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def convert_markdown(md_text, category):
    """Convert markdown text to styled HTML content (without template wrapper).

    Args:
        md_text: The markdown text to convert.
        category: Either 'audio' or 'x'.

    Returns:
        HTML string with inline styles.
    """
    lines = md_text.split('\n')
    output = []
    i = 0

    # State tracking
    in_table = False
    table_lines = []
    in_list = False
    in_card = False
    in_skipped_content = False
    in_what_block = False
    in_no_new_content = False

    def close_list():
        nonlocal in_list
        if in_list:
            output.append('</ul>')
            in_list = False

    def close_card():
        nonlocal in_card
        if in_card:
            close_list()
            output.append('</div>')
            in_card = False

    def close_table():
        nonlocal in_table, table_lines
        if in_table:
            output.append(_parse_table(table_lines, category))
            table_lines = []
            in_table = False

    def close_what_block():
        nonlocal in_what_block
        if in_what_block:
            output.append('</div>')
            in_what_block = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            if in_table:
                close_table()
            if in_list and category == 'audio':
                close_list()
            if in_what_block:
                pass  # blank lines are spacing within the block, not terminators
            i += 1
            continue

        # Table lines
        if stripped.startswith('|'):
            if not in_table:
                close_what_block()
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            i += 1
            continue
        elif in_table:
            close_table()

        # H1
        m = re.match(r'^# (.+)$', stripped)
        if m:
            close_what_block()
            close_card()
            heading_text = _apply_inline_formatting(m.group(1), category)
            output.append(
                f'<h1 style="font-size:28px; font-weight:700; margin:0 0 4px 0; '
                f'color:#1a1a2e; border-bottom:3px solid #364fc7; padding-bottom:8px;">'
                f'{heading_text}</h1>'
            )
            i += 1
            continue

        # H2
        m = re.match(r'^## (.+)$', stripped)
        if m:
            close_what_block()
            close_card()
            heading_text = _apply_inline_formatting(m.group(1), category)
            raw_heading = m.group(1).lower()
            if heading_text.lower().replace('<strong style="color:#1a1a2e;">', '').replace('</strong>', '').strip().lower() == 'skipped content':
                in_skipped_content = True
            elif 'skipped content' in raw_heading:
                in_skipped_content = True
            else:
                in_skipped_content = False
            in_no_new_content = 'no new content' in raw_heading
            output.append(
                f'<h2 style="font-size:20px; font-weight:600; margin:40px 0 16px 0; '
                f'color:#1a1a2e; text-transform:uppercase; letter-spacing:0.05em;">'
                f'{heading_text}</h2>'
            )
            i += 1
            continue

        # H3
        m = re.match(r'^### (.+)$', stripped)
        if m:
            close_what_block()
            h3_content = m.group(1)

            if category == 'audio':
                close_card()
                in_card = True
                output.append(
                    '<div style="background-color:#f8f9fa; border:1px solid #dee2e6; '
                    'padding:20px 24px; margin-bottom:20px;">'
                )
                # Check if heading is a link
                link_m = re.match(r'^\[([^\]]+)\]\(([^)]+)\)$', h3_content)
                if link_m:
                    title = html.escape(link_m.group(1))
                    url = link_m.group(2)
                    output.append(
                        f'<h3 style="font-size:17px; font-weight:600; margin:0 0 8px 0;">'
                        f'<a href="{url}" style="color:#1a1a2e; text-decoration:none; '
                        f'border-bottom:2px solid #364fc7;">{title}</a></h3>'
                    )
                else:
                    h3_text = _apply_inline_formatting(h3_content, category)
                    output.append(
                        f'<h3 style="font-size:17px; font-weight:600; margin:0 0 8px 0;">'
                        f'{h3_text}</h3>'
                    )
            elif category == 'x':
                h3_text = _apply_inline_formatting(h3_content, category)
                output.append(
                    f'<h3 style="font-size:17px; font-weight:600; margin:28px 0 8px 0; '
                    f'color:#1a1a2e; border-left:3px solid #364fc7; padding-left:12px;">'
                    f'{h3_text}</h3>'
                )

            i += 1
            continue

        # "What happened" / "What to watch" blocks
        if stripped.startswith('**What happened:**') or stripped.startswith('**What to watch:**'):
            close_what_block()
            in_what_block = True
            content = _apply_inline_formatting(stripped, category)
            output.append(
                f'<div style="background-color:#edf2ff; border-left:4px solid #364fc7; '
                f'padding:16px 20px; margin:24px 0 12px 0; font-size:15px; color:#495057; '
                f'line-height:1.7;">{content}'
            )
            # Keep in_what_block = True -- continuation paragraphs will be appended inside
            i += 1
            continue

        # Continuation paragraph inside a what block
        if in_what_block:
            content = _apply_inline_formatting(stripped, category)
            output.append(f'<p style="margin:12px 0 0 0;">{content}</p>')
            i += 1
            continue

        # Audio: metadata pills
        if category == 'audio' and _is_metadata_line(stripped):
            output.append(_render_metadata_pills(stripped))
            i += 1
            continue

        # Audio: list items
        if category == 'audio' and stripped.startswith('- '):
            if not in_list:
                in_list = True
                output.append('<ul style="list-style:none; padding:0; margin:0;">')
            item_text = stripped[2:]
            item_html = _apply_inline_formatting_audio_list(item_text)
            output.append(
                f'<li style="padding:6px 0 6px 20px; font-size:14px; color:#495057; '
                f'border-left:2px solid #dee2e6; margin-left:4px;">{item_html}</li>'
            )
            i += 1
            continue
        elif in_list:
            close_list()

        # X: skipped content boxes
        if category == 'x' and in_skipped_content:
            content = _apply_inline_formatting(stripped, category)
            output.append(
                f'<div style="background-color:#f8f9fa; border:1px solid #dee2e6; '
                f'padding:16px 20px; margin-bottom:12px; font-size:14px; color:#495057;">'
                f'{content}</div>'
            )
            i += 1
            continue

        # Audio: "No new content" -- comma-separated channel names (only in that section)
        if category == 'audio' and in_no_new_content and ',' in stripped and not stripped.startswith('*') and not stripped.startswith('#'):
            # Heuristic: line with comma-separated names, no markdown formatting
            names = [n.strip() for n in stripped.split(',')]
            if all(n and not n.startswith('[') and not n.startswith('*') for n in names):
                spans = []
                for name in names:
                    spans.append(
                        f'<span style="display:inline-block; padding:4px 11px; margin:0 4px 4px 0; '
                        f'background-color:#e9ecef; color:#495057; font-size:13px;">{html.escape(name)}</span>'
                    )
                output.append('<div>' + ''.join(spans) + '</div>')
                i += 1
                continue

        # X: body paragraphs
        if category == 'x':
            content = _apply_inline_formatting(stripped, category)
            output.append(
                f'<p style="font-size:15px; color:#495057; margin:0 0 12px 0; '
                f'line-height:1.7;">{content}</p>'
            )
            i += 1
            continue

        # Audio: regular paragraphs (fallback)
        content = _apply_inline_formatting(stripped, category)
        output.append(
            f'<p style="font-size:15px; color:#495057; margin:0 0 12px 0; '
            f'line-height:1.7;">{content}</p>'
        )
        i += 1

    # Close any open elements
    close_table()
    close_list()
    close_what_block()
    close_card()

    # Footer
    output.append(
        '<div style="margin-top:48px; padding-top:16px; border-top:1px solid #dee2e6; '
        'font-size:12px; color:#868e96; text-align:center;">Generated by Claude Stalk</div>'
    )

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='Convert markdown to styled HTML with inline styles.')
    parser.add_argument('--input', required=True, help='Input markdown file')
    parser.add_argument('--template', required=True, help='HTML template file with {content} placeholder')
    parser.add_argument('--category', required=True, choices=['audio', 'x'], help='Content category')
    parser.add_argument('--output', required=True, help='Output HTML file')

    args = parser.parse_args()

    # Read input
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            md_text = f.read()
    except (FileNotFoundError, IOError) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(2)

    # Read template
    try:
        with open(args.template, 'r', encoding='utf-8') as f:
            template = f.read()
    except (FileNotFoundError, IOError) as e:
        print(f"Error reading template file: {e}", file=sys.stderr)
        sys.exit(2)

    # Convert
    content_html = convert_markdown(md_text, args.category)

    # Apply template
    final_html = template.replace('{content}', content_html)

    # Write output
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(final_html)
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Converted {args.input} -> {args.output} (category: {args.category})")


if __name__ == '__main__':
    main()
