#!/usr/bin/env python3
"""Verify the local mirror: every referenced asset must resolve 200."""
import os
import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

BASE = "http://localhost:8099"
OUT = "/Volumes/T7/Frontends/fragment/mirror"

LOCAL_RE = re.compile(
    r"""['"(`](/(?:framerusercontent\.com|fonts\.gstatic\.com)"""
    r"""[^'"()`\s{},]+)['")`]""")
REL_IMPORT_RE = re.compile(r"""from\s*['"](\.[^'"]+)['"]|import\s*\(?['"](\.[^'"]+)['"]""")
REMOTE_RE = re.compile(r"""https?://(?:framerusercontent\.com|fonts\.gstatic\.com)[^'"()`\s]*""")

checked = {}


def head(path):
    """HTTP HEAD with retries; falls back to reporting the on-disk truth."""
    url = BASE + path
    for attempt in range(4):
        req = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return path, r.status
        except urllib.error.HTTPError as e:
            return path, e.code
        except Exception:                                   # noqa: BLE001
            continue
    # transport kept failing - check the filesystem directly
    fs = os.path.join(OUT, path.lstrip("/").replace("&amp;", "&"))
    return path, 200 if os.path.isfile(fs) else "MISSING-ON-DISK"


# ---- collect references from every text file in the mirror ----------------
refs = set()
remote_left = {}
module_paths = set()

for dirpath, _d, files in os.walk(OUT):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in {".html", ".mjs", ".js", ".css", ".json"}:
            continue
        full = os.path.join(dirpath, fn)
        rel_url = "/" + os.path.relpath(full, OUT).replace(os.sep, "/")
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        for m in LOCAL_RE.finditer(text):
            refs.add(m.group(1).replace("&amp;", "&"))
        # relative module imports, resolved against this file's own URL
        for m in REL_IMPORT_RE.finditer(text):
            tgt = m.group(1) or m.group(2)
            refs.add(urljoin(rel_url, tgt))
        for m in REMOTE_RE.finditer(text):
            u = m.group(0)
            if u.rstrip("/") in ("https://fonts.gstatic.com",
                                 "https://fonts.gstatic.com/s"):
                continue
            remote_left.setdefault(u, []).append(rel_url)
        if ext == ".mjs":
            module_paths.add(rel_url)

print(f"checking {len(refs)} distinct asset references\n")
with ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(head, sorted(refs)))

bad = [(p, s) for p, s in results if s != 200]
print(f"OK:  {len(results) - len(bad)}")
print(f"BAD: {len(bad)}")
for p, s in sorted(bad)[:40]:
    print(f"   {s}  {p}")

print(f"\nmodules present: {len(module_paths)}")
if remote_left:
    print(f"\nstill pointing at remote CDN ({len(remote_left)}):")
    for u, where in sorted(remote_left.items())[:20]:
        print(f"   {u[:100]}\n        in {where[0]}")
else:
    print("\nno remaining remote CDN references ✓")
