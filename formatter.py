"""
FairLens — PDF Content Formatter (Step 3)
==========================================

Ensures the report text is clean and safe for PDF rendering engines.
Strips all markdown symbols, normalizes whitespace, and structures
the text with proper line breaks and section headings.

Output: Plain text only — no markdown, no HTML, no special characters
that could break PDF renderers like FPDF, ReportLab, or WeasyPrint.
"""

import re
from typing import Optional


class PDFContentFormatter:
    """Sanitizes report text for PDF generation."""

    # Characters and patterns that must be stripped for PDF safety
    MARKDOWN_PATTERNS = [
        (r"#{1,6}\s*", ""),          # Heading markers (### etc.)
        (r"\*\*(.+?)\*\*", r"\1"),   # Bold **text**
        (r"\*(.+?)\*", r"\1"),       # Italic *text*
        (r"__(.+?)__", r"\1"),       # Bold __text__
        (r"_(.+?)_", r"\1"),         # Italic _text_
        (r"~~(.+?)~~", r"\1"),       # Strikethrough ~~text~~
        (r"`(.+?)`", r"\1"),         # Inline code `text`
        (r"```[\s\S]*?```", ""),     # Fenced code blocks
        (r"\[(.+?)\]\(.+?\)", r"\1"),  # Links [text](url)
        (r"!\[.*?\]\(.+?\)", ""),    # Images ![alt](url)
        (r"^>\s*", "", re.MULTILINE),  # Blockquotes
        (r"^[-*+]\s+", "  - ", re.MULTILINE),  # Unordered lists → clean bullet
        (r"^\d+\.\s+", "", re.MULTILINE),  # Ordered list numbers (keep content)
    ]

    def format(self, report_text: str) -> str:
        """
        Cleans the report text for PDF rendering.

        Parameters
        ----------
        report_text : str
            The raw report text from ReportGenerator.

        Returns
        -------
        str
            Clean, PDF-safe plain text with proper structure.
        """
        if not report_text:
            return ""

        cleaned = report_text

        # Apply each markdown stripping pattern
        for pattern_entry in self.MARKDOWN_PATTERNS:
            if len(pattern_entry) == 3:
                pattern, replacement, flags = pattern_entry
                cleaned = re.sub(pattern, replacement, cleaned, flags=flags)
            else:
                pattern, replacement = pattern_entry
                cleaned = re.sub(pattern, replacement, cleaned)

        # Strip all non-latin-1 characters (emoji, CJK, etc.)
        # fpdf2's built-in Helvetica only supports latin-1 (0x00-0xFF)
        cleaned = self.strip_non_latin1(cleaned)

        # Normalize excessive blank lines (max 2 consecutive)
        cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)

        # Ensure consistent line endings
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in cleaned.split("\n")]
        cleaned = "\n".join(lines)

        # Remove leading/trailing whitespace from the entire document
        cleaned = cleaned.strip()

        return cleaned

    @staticmethod
    def strip_non_latin1(text: str) -> str:
        """
        Removes all characters that cannot be encoded in latin-1.
        This includes emoji, CJK, and other Unicode blocks that
        fpdf2's built-in fonts (Helvetica, etc.) cannot render.

        Common offenders from API responses:
          - \U0001f534 (red circle emoji)
          - \U0001f7e2 (green circle emoji)
          - Various warning/check mark symbols
        """
        result = []
        for char in text:
            try:
                char.encode("latin-1")
                result.append(char)
            except UnicodeEncodeError:
                # Replace known emoji with text equivalents
                replacements = {
                    "\U0001f534": "[!]",    # Red circle
                    "\U0001f7e2": "[OK]",   # Green circle
                    "\U0001f7e1": "[~]",    # Yellow circle
                    "\u2705": "[OK]",       # Check mark
                    "\u274c": "[X]",        # Cross mark
                    "\u26a0": "[!]",        # Warning sign
                    "\u2022": "-",          # Bullet
                    "\u2013": "-",          # En dash
                    "\u2014": "-",          # Em dash
                    "\u2018": "'",          # Left single quote
                    "\u2019": "'",          # Right single quote
                    "\u201c": '"',          # Left double quote
                    "\u201d": '"',          # Right double quote
                    "\u2026": "...",        # Ellipsis
                    "\u2192": "->",         # Right arrow
                    "\u2190": "<-",         # Left arrow
                    "\u2264": "<=",         # Less than or equal
                    "\u2265": ">=",         # Greater than or equal
                }
                result.append(replacements.get(char, ""))
        return "".join(result)

    def validate(self, text: str) -> bool:
        """
        Validates that the text contains no markdown artifacts
        and no characters outside the latin-1 range.

        Returns True if the text is PDF-safe, False otherwise.
        """
        markdown_indicators = ["###", "**", "__", "~~", "```", "!["]
        for indicator in markdown_indicators:
            if indicator in text:
                return False

        # Check for non-latin-1 characters
        try:
            text.encode("latin-1")
        except UnicodeEncodeError:
            return False

        return True
