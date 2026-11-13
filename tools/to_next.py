#!/usr/bin/env python3
"""Convert the static mirror into a real Next.js App Router project.

For each mirrored route this emits:
  app/<route>/page.jsx     real JSX (no Framer runtime)
  app/<route>/styles.css   that route's CSS, kept per-route because
                           Framer reuses class names with different bodies
Assets are hard-linked into public/ at the same paths the markup already
uses, so no URL rewriting is needed.
"""
import html as htmlmod
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from html2jsx import convert                                # noqa: E402

ROOT = os.path.dirname(HERE)
MIRROR = os.path.join(ROOT, "mirror")
APP = os.path.join(ROOT, "next-app", "app")
PUBLIC = os.path.join(ROOT, "next-app", "public")
ASSET_DIRS = ["framerusercontent.com", "fonts.gstatic.com"]

SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
SCRIPT_SELF = re.compile(r"<script\b[^>]*/?>", re.I)
STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.S | re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
META_RE = re.compile(r'<meta\s+([^>]*?)\s*/?>', re.I)

# --- reveal-state settling (Framer hides content until its JS runs) -------
STYLE_ATTR_RE = re.compile(r'style="([^"]*)"')
OPACITY_RE = re.compile(r'opacity:\s*0(?:\.0*1?)?\s*(?=[;"]|$)')
TRANSFORM_RE = re.compile(r'transform:\s*[^;"]*')


def settle(markup):
    """Rewrite Framer's hidden pre-animation styles to their end state."""
    n = [0]

    def repl(m):
        s = m.group(1)
        if not OPACITY_RE.search(s):
            return m.group(0)
        s = OPACITY_RE.sub("opacity:1", s)
        s = TRANSFORM_RE.sub("transform:none", s)
        s = s.replace("will-change:transform;", "").replace(
            "will-change:transform", "")
        n[0] += 1
        return f'style="{s}"'

    return STYLE_ATTR_RE.sub(repl, markup), n[0]


CSS_ENTITIES = {
    "&quot;": '"', "&#34;": '"', "&apos;": "'", "&#39;": "'",
    "&lt;": "<", "&gt;": ">", "&nbsp;": " ", "&amp;": "&",
}


def clean_css(css):
    """Undo HTML entity escaping that leaked into <style> contents.

    &amp; is done last so "&amp;quot;" collapses correctly.
    """
    for ent, char in CSS_ENTITIES.items():
        if ent != "&amp;":
            css = css.replace(ent, char)
    return css.replace("&amp;", "&")


# --- Spline 3D re-injection -----------------------------------------------
# Framer created <spline-viewer> elements at runtime, so the mirror holds
# only empty placeholders. tools/discover_spline.py recorded which scene
# belongs in which container; we drop a marker into that placeholder and
# turn it into a real React component after the JSX conversion.
SPLINE_MAP_PATH = os.path.join(HERE, "spline_map.json")
SLOT_RE = re.compile(
    r'(<div style="width:100%;height:100%;display:flex[^"]*">)(\s*)(</div>)')
SLOT_JSX_RE = re.compile(r"<div data-spline-slot='([^']+)' />")


def load_spline_map():
    try:
        with open(SPLINE_MAP_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def inject_spline(markup, entries):
    """Put a marker inside each Spline container's empty placeholder."""
    n = 0
    for e in entries:
        scene = e.get("scene")
        container = e.get("container")
        if not scene or not container:
            continue
        i = markup.find(f"framer-{container}-container")
        if i < 0:
            continue
        m = SLOT_RE.search(markup, i)
        if not m:
            continue
        marker = f'<div data-spline-slot="{scene}"/>'
        markup = markup[:m.start(2)] + marker + markup[m.end(2):]
        n += 1
    return markup, n


VIDEO_RE = re.compile(r"<video\b([^>]*)>", re.I)


def native_video(markup):
    """Make Framer's videos play without Framer's runtime.

    Framer ships <video preload="none"> and calls play() from JS. With the
    runtime gone those elements reserve layout space and paint nothing, so
    we opt into native autoplay instead (muted + playsinline, which every
    browser allows to start on its own).
    """
    n = [0]

    def repl(m):
        attrs = m.group(1)
        if "autoplay" in attrs.lower():
            return m.group(0)
        attrs = re.sub(r'preload\s*=\s*"[^"]*"', 'preload="auto"', attrs,
                       flags=re.I)
        if "preload" not in attrs.lower():
            attrs += ' preload="auto"'
        if "muted" not in attrs.lower():
            attrs += " muted"
        if "playsinline" not in attrs.lower():
            attrs += " playsinline"
        n[0] += 1
        return f"<video{attrs} autoplay>"

    return VIDEO_RE.sub(repl, markup), n[0]


def meta_of(doc):
    """Pull title/description/og into a Next metadata object."""
    out = {}
    m = TITLE_RE.search(doc)
    if m:
        out["title"] = htmlmod.unescape(m.group(1)).strip()
    og = {}
    for m in META_RE.finditer(doc):
        attrs = dict(re.findall(r'([A-Za-z:_-]+)\s*=\s*"([^"]*)"', m.group(1)))
        key = attrs.get("name") or attrs.get("property")
        val = attrs.get("content")
        if not key or val is None:
            continue
        val = htmlmod.unescape(val)
        if key == "description":
            out["description"] = val
        elif key == "og:title":
            og["title"] = val
        elif key == "og:description":
            og["description"] = val
        elif key == "og:image":
            og["images"] = [val]
    if og:
        out["openGraph"] = og
    return out


def route_of(path):
    rel = os.path.relpath(os.path.dirname(path), MIRROR)
    return "/" if rel == "." else "/" + rel.replace(os.sep, "/")


def comp_name(route):
    if route == "/":
        return "HomePage"
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", route) if p]
    return "".join(p.capitalize() for p in parts) + "Page"


def link_assets():
    """Hard-link mirrored assets into public/ (same paths, no copy cost)."""
    linked = 0
    for d in ASSET_DIRS:
        src_root = os.path.join(MIRROR, d)
        if not os.path.isdir(src_root):
            continue
        for dirpath, _dirs, files in os.walk(src_root):
            rel = os.path.relpath(dirpath, MIRROR)
            dest_dir = os.path.join(PUBLIC, rel)
            os.makedirs(dest_dir, exist_ok=True)
            for fn in files:
                src = os.path.join(dirpath, fn)
                dst = os.path.join(dest_dir, fn)
                if os.path.exists(dst):
                    continue
                try:
                    os.link(src, dst)
                except OSError:
                    shutil.copy2(src, dst)
                linked += 1
    return linked


def main():
    pages = []
    for dirpath, _dirs, files in os.walk(MIRROR):
        if any(a in dirpath for a in ASSET_DIRS):
            continue
        if "index.html" in files:
            pages.append(os.path.join(dirpath, "index.html"))
    pages.sort()

    print(f"converting {len(pages)} routes\n")
    total_settled = 0
    total_spline = 0
    spline_map = load_spline_map()
    for path in pages:
        route = route_of(path)
        doc = io.open(path, encoding="utf-8").read()

        meta = meta_of(doc)

        doc_nos = SCRIPT_RE.sub("", doc)
        doc_nos = SCRIPT_SELF.sub("", doc_nos)
        # Take CSS from the script-free document so nothing is lifted out of
        # a JS string, and undo the double-escaping Framer emits inside
        # <style> (browsers silently drop those rules; Next refuses to parse).
        css = clean_css("\n".join(STYLE_RE.findall(doc_nos)))
        body = BODY_RE.search(doc_nos)
        markup = body.group(1) if body else ""
        markup = STYLE_RE.sub("", markup)
        markup, n = settle(markup)
        markup, nv = native_video(markup)
        markup, ns = inject_spline(markup, spline_map.get(route, []))
        total_settled += n
        total_spline += ns

        jsx = convert(markup)
        jsx = SLOT_JSX_RE.sub(r"<SplineViewer scene='\1' />", jsx)
        spline_import = (
            "import SplineViewer from '@/components/SplineViewer';\n"
            if ns else "")

        out_dir = APP if route == "/" else os.path.join(APP, route.strip("/"))
        os.makedirs(out_dir, exist_ok=True)
        io.open(os.path.join(out_dir, "styles.css"), "w",
                encoding="utf-8").write(css)

        name = comp_name(route)
        src = (
            "// Generated from the fragment.im mirror by tools/to_next.py\n"
            "// Plain JSX - edit freely.\n"
            "import './styles.css';\n"
            + spline_import + "\n"
            f"export const metadata = {json.dumps(meta, indent=2)};\n\n"
            f"export default function {name}() {{\n"
            "  return (\n"
            "    <>\n"
            f"{jsx}"
            "    </>\n"
            "  );\n"
            "}\n"
        )
        io.open(os.path.join(out_dir, "page.jsx"), "w",
                encoding="utf-8").write(src)
        print(f"  {route:<22} jsx {len(src):>8,}  css {len(css):>8,}"
              f"  settled {n}  video {nv}  spline {ns}")

    print(f"\nsettled {total_settled} reveal-state styles, "
          f"injected {total_spline} Spline scenes")
    print(f"linking assets into public/ ...")
    print(f"  {link_assets()} files linked")


if __name__ == "__main__":
    main()
