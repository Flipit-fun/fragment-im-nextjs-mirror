#!/usr/bin/env python3
"""Recursive, path-preserving mirror of the fragment.im Framer site."""
import html
import os
import re
import sys
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin

OUT = "/Volumes/T7/Frontends/fragment/mirror"
START_HTML = os.path.join(OUT, "index.html")

# Hosts whose assets we pull down locally.
ALLOWED = {"framerusercontent.com", "fonts.gstatic.com"}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

TEXT_EXT = {".mjs", ".js", ".json", ".css", ".map"}
ASSET_RE = re.compile(
    r"""['"(`]([^'"()`\s{},]+?\.(?:mjs|js|json|css|woff2?|ttf|otf|eot|png|jpe?g|gif|svg|webp|avif|mp4|webm|mov|ico)(?:\?[^'"()`\s{},]*)?)['")`]""",
    re.I)
ABS_RE = re.compile(r"""https?://[A-Za-z0-9._~:/?#@!$&*+;=%-]+""")

lock = threading.Lock()
seen = set()          # real URLs already queued
url_to_local = {}     # real URL -> local path relative to OUT
failures = {}


def sanitize_query(q):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", q).strip("-")


def local_for(url):
    """Map a remote URL to a path-preserving local file, relative to OUT."""
    p = urlparse(url)
    path = p.path.lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    if p.query:
        root, ext = os.path.splitext(path)
        path = f"{root}__{sanitize_query(p.query)}{ext}"
    return os.path.join(p.netloc, path)


def candidate_urls(text, base_url, is_html):
    """Yield (raw_token, real_url) pairs for assets referenced by `text`."""
    out = []
    for m in ABS_RE.finditer(text):
        raw = m.group(0).rstrip(".,;:)]}'\"")
        real = html.unescape(raw) if is_html else raw
        if urlparse(real).netloc in ALLOWED:
            out.append((raw, real))
    for m in ASSET_RE.finditer(text):
        raw = m.group(1)
        if raw.startswith(("http://", "https://", "//", "data:")):
            continue
        real = urljoin(base_url, html.unescape(raw) if is_html else raw)
        if urlparse(real).netloc in ALLOWED:
            out.append((raw, real))
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Referer": "https://www.fragment.im/",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:                      # noqa: BLE001
            if attempt == 2:
                raise
    return None


def download(url):
    """Download one URL to its local path. Returns (local_path, bytes) or None."""
    rel = local_for(url)
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        with open(dest, "rb") as f:
            return rel, f.read()
    try:
        data = fetch(url)
    except Exception as e:                          # noqa: BLE001
        with lock:
            failures[url] = repr(e)
        return None
    with open(dest, "wb") as f:
        f.write(data)
    with lock:
        url_to_local[url] = rel
    return rel, data


def html_pages():
    """Every mirrored HTML page, with the site URL it came from."""
    for dirpath, _dirs, files in os.walk(OUT):
        if "framerusercontent.com" in dirpath or "fonts.gstatic.com" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".html"):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, OUT)
                route = "/" if rel == "index.html" else \
                    "/" + os.path.dirname(rel) + "/"
                yield full, "https://www.fragment.im" + route


def crawl():
    frontier = []
    pages = list(html_pages())
    print(f"seeding from {len(pages)} html pages")
    for full, base in pages:
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        for _raw, real in candidate_urls(text, base, True):
            if real not in seen:
                seen.add(real)
                frontier.append(real)

    wave = 0
    while frontier:
        wave += 1
        print(f"[wave {wave}] {len(frontier)} urls", flush=True)
        with ThreadPoolExecutor(max_workers=12) as ex:
            results = list(ex.map(download, frontier))

        nxt = []
        for res, src_url in zip(results, frontier):
            if not res:
                continue
            rel, data = res
            if os.path.splitext(rel)[1].lower() not in TEXT_EXT:
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            for _raw, real in candidate_urls(text, src_url, False):
                if real not in seen:
                    seen.add(real)
                    nxt.append(real)
        frontier = nxt

    print(f"\ndownloaded: {len(url_to_local)} new, {len(seen)} total refs")
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for u, e in list(failures.items())[:20]:
            print("  ", u, e)


if __name__ == "__main__":
    crawl()
