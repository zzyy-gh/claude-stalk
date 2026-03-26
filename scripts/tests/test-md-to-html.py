#!/usr/bin/env python3
"""Tests for md-to-html.py converter."""

import importlib.util
import os
import sys
import tempfile
import unittest

# Import the module (filename has a hyphen so we use importlib)
spec = importlib.util.spec_from_file_location(
    "md_to_html",
    os.path.join(os.path.dirname(__file__), "..", "md-to-html.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
convert_markdown = mod.convert_markdown


class TestHeaders(unittest.TestCase):
    """Test header conversion for h1, h2, h3."""

    def test_h1(self):
        result = convert_markdown("# Main Title", "audio")
        self.assertIn('<h1 style="font-size:28px;', result)
        self.assertIn('border-bottom:3px solid #364fc7', result)
        self.assertIn('Main Title', result)

    def test_h2(self):
        result = convert_markdown("## Section Heading", "audio")
        self.assertIn('<h2 style="font-size:20px;', result)
        self.assertIn('text-transform:uppercase', result)
        self.assertIn('Section Heading', result)

    def test_h3_audio(self):
        result = convert_markdown("### Episode Title", "audio")
        self.assertIn('<h3 style="font-size:17px;', result)
        self.assertIn('Episode Title', result)
        # Audio h3 should trigger a card wrapper
        self.assertIn('background-color:#f8f9fa', result)

    def test_h3_audio_link(self):
        result = convert_markdown("### [My Episode](https://example.com)", "audio")
        self.assertIn('<h3 style="font-size:17px;', result)
        self.assertIn('href="https://example.com"', result)
        self.assertIn('border-bottom:2px solid #364fc7', result)
        self.assertIn('My Episode', result)

    def test_h3_x(self):
        result = convert_markdown("### Topic", "x")
        self.assertIn('<h3 style="font-size:17px;', result)
        self.assertIn('border-left:3px solid #364fc7', result)
        self.assertIn('padding-left:12px', result)


class TestInlineFormatting(unittest.TestCase):
    """Test inline formatting: bold, italic, links."""

    def test_bold(self):
        result = convert_markdown("Some **bold text** here", "x")
        self.assertIn('<strong style="color:#1a1a2e;">bold text</strong>', result)

    def test_italic(self):
        result = convert_markdown("Some *italic text* here", "x")
        self.assertIn('<em>italic text</em>', result)

    def test_link(self):
        result = convert_markdown("Check [this link](https://example.com) out", "x")
        self.assertIn('href="https://example.com"', result)
        self.assertIn('style="color:#1971c2; text-decoration:none;"', result)
        self.assertIn('this link</a>', result)


class TestDueDiligenceFlags(unittest.TestCase):
    """Test due-diligence italic flag styling."""

    def test_due_diligence_flag(self):
        md = "Some claim _(second-hand -- no primary source cited)_"
        result = convert_markdown(md, "x")
        self.assertIn('color:#e67700', result)
        self.assertIn('font-size:13px', result)
        self.assertIn('second-hand -- no primary source cited', result)

    def test_due_diligence_in_audio(self):
        md = "### Test\n- Key point _(unverified)_"
        result = convert_markdown(md, "audio")
        self.assertIn('color:#e67700', result)
        self.assertIn('unverified', result)


class TestTables(unittest.TestCase):
    """Test table conversion."""

    def test_basic_table(self):
        md = (
            "| Name | Value |\n"
            "|------|-------|\n"
            "| Alpha | 100 |\n"
            "| Beta | 200 |"
        )
        result = convert_markdown(md, "audio")
        self.assertIn('<table style="width:100%; border-collapse:collapse;', result)
        self.assertIn('<th style="background-color:#f1f3f5;', result)
        self.assertIn('<td style="padding:8px 12px;', result)
        self.assertIn('Name', result)
        self.assertIn('Alpha', result)
        self.assertIn('200', result)
        # Separator row should not appear as a row
        self.assertNotIn('---', result)


class TestWhatBlocks(unittest.TestCase):
    """Test 'What happened' / 'What to watch' callout divs."""

    def test_what_happened(self):
        md = "**What happened:** Something important occurred."
        result = convert_markdown(md, "audio")
        self.assertIn('background-color:#edf2ff', result)
        self.assertIn('border-left:4px solid #364fc7', result)
        self.assertIn('Something important occurred', result)

    def test_what_to_watch(self):
        md = "**What to watch:** Keep an eye on this trend."
        result = convert_markdown(md, "x")
        self.assertIn('background-color:#edf2ff', result)
        self.assertIn('Keep an eye on this trend', result)


class TestAudioMetadataPills(unittest.TestCase):
    """Test audio metadata pill rendering."""

    def test_metadata_pills(self):
        md = "**Source**: TechPod | **Guest(s)**: Jane Doe | **Published**: 2026-03-20"
        result = convert_markdown(md, "audio")
        self.assertIn('background-color:#d0ebff', result)
        self.assertIn('Source: TechPod', result)
        self.assertIn('background-color:#fff3bf', result)
        self.assertIn('Guest(s): Jane Doe', result)
        self.assertIn('background-color:#e6fcf5', result)
        self.assertIn('Published: 2026-03-20', result)

    def test_metadata_not_rendered_for_x(self):
        md = "**Source**: TechPod | **Guest(s)**: Jane Doe | **Published**: 2026-03-20"
        result = convert_markdown(md, "x")
        # For x category it should be a paragraph, not pills
        self.assertNotIn('background-color:#d0ebff', result)


class TestAudioItemCards(unittest.TestCase):
    """Test audio item card wrapping."""

    def test_card_wrapping(self):
        md = "### [Episode Title](https://example.com)\n**Source**: Pod | **Guest(s)**: Bob | **Published**: 2026-01-01\n- First key point\n- Second key point"
        result = convert_markdown(md, "audio")
        # Card div
        self.assertIn('background-color:#f8f9fa; border:1px solid #dee2e6; padding:20px 24px', result)
        # List items
        self.assertIn('<ul style="list-style:none;', result)
        self.assertIn('<li style="padding:6px 0 6px 20px;', result)
        self.assertIn('First key point', result)
        # Closing card div
        card_open_count = result.count('background-color:#f8f9fa; border:1px solid #dee2e6; padding:20px 24px')
        self.assertEqual(card_open_count, 1)

    def test_timestamp_link_in_list(self):
        md = "### Test\n- [01:23:45](https://yt.com/t=5025) Discussion about AI"
        result = convert_markdown(md, "audio")
        self.assertIn('font-family:Courier New, monospace', result)
        self.assertIn('[01:23:45]', result)
        self.assertIn('color:#364fc7', result)


class TestXBodyParagraphs(unittest.TestCase):
    """Test X-category body paragraph styling."""

    def test_paragraph(self):
        md = "This is a regular paragraph about some news."
        result = convert_markdown(md, "x")
        self.assertIn('<p style="font-size:15px; color:#495057;', result)
        self.assertIn('line-height:1.7', result)

    def test_multiple_paragraphs(self):
        md = "First paragraph.\n\nSecond paragraph."
        result = convert_markdown(md, "x")
        self.assertEqual(result.count('<p style="font-size:15px;'), 2)


class TestXSkippedContent(unittest.TestCase):
    """Test X skipped content boxes."""

    def test_skipped_content(self):
        md = "## Skipped Content\nThis was not relevant.\nAnother skipped item."
        result = convert_markdown(md, "x")
        self.assertIn('background-color:#f8f9fa; border:1px solid #dee2e6; padding:16px 20px', result)
        self.assertIn('This was not relevant', result)
        self.assertIn('Another skipped item', result)

    def test_skipped_content_not_in_audio(self):
        md = "## Skipped Content\nSome text here."
        result = convert_markdown(md, "audio")
        # Audio should not apply skipped-content box styling
        self.assertNotIn('padding:16px 20px; margin-bottom:12px; font-size:14px', result)


class TestFooter(unittest.TestCase):
    """Test footer is always appended."""

    def test_footer_present(self):
        result = convert_markdown("# Title", "audio")
        self.assertIn('Generated by Claude Stalk', result)
        self.assertIn('border-top:1px solid #dee2e6', result)

    def test_footer_in_x(self):
        result = convert_markdown("Some text.", "x")
        self.assertIn('Generated by Claude Stalk', result)


class TestEndToEnd(unittest.TestCase):
    """Full end-to-end test: markdown input -> HTML output with template."""

    def test_full_pipeline(self):
        template = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<title>VC/AI Briefing</title>\n</head>\n'
            '<body style="margin:0; padding:32px 16px; font-family:Arial, Helvetica, sans-serif;">\n'
            '<div style="max-width:740px; margin:0 auto;">\n'
            '{content}\n'
            '</div>\n</body>\n</html>'
        )

        md = (
            "# VC/AI Daily Briefing\n\n"
            "## Key Stories\n\n"
            "### [AI Startup Raises $50M](https://example.com/story)\n"
            "**Source**: TechCrunch | **Guest(s)**: CEO | **Published**: 2026-03-23\n"
            "- [00:05:12](https://yt.com/t=312) Funding details and valuation\n"
            "- [00:12:30](https://yt.com/t=750) Market strategy discussion\n\n"
            "**What happened:** A major AI startup closed a Series B round.\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| Valuation | $200M |\n"
            "| Revenue | $10M ARR |\n\n"
            "## No New Content\n\n"
            "Channel A, Channel B, Channel C"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(md)
            md_path = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(template)
            tpl_path = f.name
        out_path = md_path.replace('.md', '-out.html')

        try:
            # Use the main function via subprocess-like invocation
            sys.argv = ['md-to-html.py', '--input', md_path, '--template', tpl_path,
                         '--category', 'audio', '--output', out_path]
            mod.main()

            with open(out_path, 'r', encoding='utf-8') as f:
                html_output = f.read()

            # Template wrapper present
            self.assertIn('<!DOCTYPE html>', html_output)
            self.assertIn('max-width:740px', html_output)

            # H1
            self.assertIn('<h1 style="font-size:28px;', html_output)
            self.assertIn('VC/AI Daily Briefing', html_output)

            # H2
            self.assertIn('<h2 style="font-size:20px;', html_output)

            # H3 with link in card
            self.assertIn('AI Startup Raises $50M', html_output)
            self.assertIn('border-bottom:2px solid #364fc7', html_output)

            # Metadata pills
            self.assertIn('Source: TechCrunch', html_output)
            self.assertIn('background-color:#d0ebff', html_output)

            # Timestamp links
            self.assertIn('[00:05:12]', html_output)
            self.assertIn('font-family:Courier New, monospace', html_output)

            # What happened block
            self.assertIn('background-color:#edf2ff', html_output)

            # Table
            self.assertIn('<table style="width:100%;', html_output)
            self.assertIn('Valuation', html_output)

            # No new content spans
            self.assertIn('Channel A', html_output)
            self.assertIn('background-color:#e9ecef', html_output)

            # Footer
            self.assertIn('Generated by Claude Stalk', html_output)

        finally:
            for p in [md_path, tpl_path, out_path]:
                if os.path.exists(p):
                    os.unlink(p)


class TestWebpageCategory(unittest.TestCase):
    """Test webpage-specific conversion."""

    def test_h3_card_wrapper(self):
        md = "### [Article Title](https://example.com/post)"
        result = convert_markdown(md, "webpage")
        self.assertIn('background-color:#f8f9fa', result)
        self.assertIn('border:1px solid #dee2e6', result)
        self.assertIn('Article Title', result)
        self.assertIn('href="https://example.com/post"', result)

    def test_source_only_metadata_pill(self):
        md = '**Source**: [Anthropic Blog](https://blog.anthropic.com)'
        result = convert_markdown(md, "webpage")
        self.assertIn('background-color:#d0ebff', result)
        self.assertIn('Source:', result)
        self.assertIn('Anthropic Blog', result)
        # Should NOT have a Published pill
        self.assertNotIn('Published:', result)

    def test_source_with_guest_pill(self):
        md = '**Source**: [OpenAI Blog](https://openai.com) | **Guest(s)**: Sam Altman, CEO'
        result = convert_markdown(md, "webpage")
        self.assertIn('background-color:#d0ebff', result)
        self.assertIn('background-color:#fff3bf', result)
        self.assertIn('Guest(s):', result)
        self.assertIn('Sam Altman, CEO', result)

    def test_body_paragraph_inside_card(self):
        md = (
            "### [Title](https://example.com)\n"
            "**Source**: [Blog](https://blog.com)\n\n"
            "This is a summary paragraph inside the card."
        )
        result = convert_markdown(md, "webpage")
        # Card wrapper
        self.assertIn('background-color:#f8f9fa', result)
        # Paragraph inside card
        self.assertIn('<p style="font-size:15px;', result)
        self.assertIn('summary paragraph inside the card', result)

    def test_body_paragraph_outside_card(self):
        md = "This is a standalone paragraph not inside any card."
        result = convert_markdown(md, "webpage")
        self.assertIn('<p style="font-size:15px;', result)
        self.assertIn('standalone paragraph', result)

    def test_paywall_flag(self):
        md = "Summary text. _(paywalled -- summary based on publicly available portion)_"
        result = convert_markdown(md, "webpage")
        self.assertIn('color:#e67700', result)
        self.assertIn('paywalled', result)

    def test_no_timestamp_links(self):
        md = (
            "### [Article](https://example.com)\n"
            "**Source**: [Blog](https://blog.com)\n\n"
            "No timestamps in webpage summaries."
        )
        result = convert_markdown(md, "webpage")
        self.assertNotIn('font-family:Courier New', result)

    def test_what_happened_block(self):
        md = "**What happened:** AI models got better this week."
        result = convert_markdown(md, "webpage")
        self.assertIn('background-color:#edf2ff', result)
        self.assertIn('AI models got better', result)

    def test_skipped_table(self):
        md = (
            "## Skipped\n\n"
            "| Title | Source | Reason |\n"
            "|-------|--------|--------|\n"
            "| [Post](https://x.com) | [Blog](https://b.com) | Not relevant |\n"
        )
        result = convert_markdown(md, "webpage")
        self.assertIn('<table', result)
        self.assertIn('Not relevant', result)

    def test_source_only_not_detected_as_audio_metadata(self):
        """Source-only line should NOT be detected when category is audio."""
        md = '**Source**: [Blog](https://blog.com)'
        result = convert_markdown(md, "audio")
        # Audio requires both Source AND Published, so this falls through to paragraph
        self.assertNotIn('background-color:#d0ebff', result)


if __name__ == '__main__':
    unittest.main()
