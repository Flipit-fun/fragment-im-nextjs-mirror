#!/usr/bin/env python3
"""Rewrite remote CDN URLs in the mirror to local root-relative paths.

Idempotent: only rewrites a URL when the corresponding local file exists.
"""
import html
import os
import re
import sys

OUT = "/Volumes/T7/Frontends/fragment/mirror"
ALLOWED = ("framerusercontent.com", "fonts.gstatic.com")
TEXT_EXT = {".html", ".mjs", ".js", ".json", ".css"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror import local_for                                # noqa: E402

URL_RE = re.compile(
    r"""https?://(?:framerusercontent\.com|fonts\.gstatic\.com)"""
    r"""[A-Za-z0-9._~:/?#@!$&*+;=%-]*""")

# Third-party calls that should not phone home from a local mirror.
ANALYTICS = re.compile(
    r"""<script[^>]*src=["']https://events\.framer\.com/script\?[^"']*["'][^>]*>"""
    r"""\s*</script>""", re.I)

stats = {"files": 0, "urls": 0, "analytics": 0, "unmapped": set()}


def rewrite_text(text, is_html):
    tokens = set()
    for m in URL_RE.finditer(text):
        tokens.add(m.group(0).rstrip(".,;:)]}'\""))

    # Longest first so a bare URL never clobbers its query-string sibling.
    repl = 0
    for raw in sorted(tokens, key=len, reverse=True):
        real = html.unescape(raw) if is_html else raw
        rel = local_for(real)
        if not os.path.exists(os.path.join(OUT, rel)):
            stats["unmapped"].add(real)
            continue
        local = "/" + rel.replace(os.sep, "/")
        if raw in text:
            text = text.replace(raw, local)
            repl += 1
    stats["urls"] += repl

    if is_html:
        text, n = ANALYTICS.subn(
            "<!-- analytics removed for local mirror -->", text)
        stats["analytics"] += n
    return text


for dirpath, _dirs, files in os.walk(OUT):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in TEXT_EXT:
            continue
        full = os.path.join(dirpath, fn)
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            orig = f.read()
        new = rewrite_text(orig, ext == ".html")
        if new != orig:
            with open(full, "w", encoding="utf-8") as f:
                f.write(new)
            stats["files"] += 1

print(f"rewrote {stats['files']} files, {stats['urls']} url replacements, "
      f"{stats['analytics']} analytics tags removed")
if stats["unmapped"]:
    print(f"\nleft remote ({len(stats['unmapped'])}, no local copy):")
    for u in sorted(stats["unmapped"]):
        print("  ", u[:120])
