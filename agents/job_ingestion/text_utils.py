"""Minimal HTML-to-text helper for job description content. Greenhouse/Lever
descriptions use basic markup (p/div/li/br/headings) — a full HTML parser
dependency isn't needed for that.
"""

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def strip_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Unescape first: some job boards double-encode markup (e.g. "&lt;h2&gt;"),
    # so tags only become literal "<...>" after this step and must be stripped
    # afterward, not before.
    text = html.unescape(raw_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|h[1-6])\s*>", "\n", text)
    text = _TAG_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()
