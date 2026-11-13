#!/usr/bin/env python3
"""Verify the Next.js app: every route 200s and every asset it references
resolves. Usage: python3 tools/verify_next.py [port]
"""
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PORT = sys.argv[1] if len(sys.argv) > 1 else "3310"
BASE = f"http://localhost:{PORT}"

ROUTES = ["/", "/about", "/contact", "/work", "/work/bsr", "/work/ewm",
          "/work/gorilla", "/work/index", "/work/kadenco", "/pp",
          "/pl", "/pl/about", "/pl/contact", "/pl/pp", "/pl/work",
          "/pl/work/bsr", "/pl/work/ewm", "/pl/work/gorilla",
          "/pl/work/index", "/pl/work/kadenco"]

ASSET_RE = re.compile(r'(?:src|href)="(/(?:framerusercontent\.com|'
                      r'fonts\.gstatic\.com|_next)[^"]*)"')
SRCSET_RE = re.compile(r'srcSet="([^"]*)"', re.I)


def get(url, method="GET"):
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "verify"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read() if method == "GET" else b""
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception:                                   # noqa: BLE001
            continue
    return "CONN-FAIL", b""


def main():
    assets = set()
    bad_routes = []
    print(f"checking {len(ROUTES)} routes on {BASE}\n")
    for r in ROUTES:
        status, body = get(BASE + r)
        html = body.decode("utf-8", "replace")
        if status != 200:
            bad_routes.append((r, status))
            print(f"  {r:<22} {status}  <-- FAIL")
            continue
        n = 0
        for m in ASSET_RE.finditer(html):
            assets.add(m.group(1).replace("&amp;", "&"))
            n += 1
        for m in SRCSET_RE.finditer(html):
            for cand in m.group(1).split(","):
                u = cand.strip().split(" ")[0]
                if u.startswith("/"):
                    assets.add(u.replace("&amp;", "&"))
                    n += 1
        print(f"  {r:<22} 200   {len(html):>8,} bytes, {n:>4} asset refs")

    print(f"\nchecking {len(assets)} distinct assets ...")
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda u: (u, get(BASE + u, "HEAD")[0]),
                              sorted(assets)))
    bad = [(u, s) for u, s in results if s != 200]
    print(f"  OK  {len(results) - len(bad)}")
    print(f"  BAD {len(bad)}")
    for u, s in bad[:25]:
        print(f"     {s}  {u[:95]}")

    print()
    if not bad_routes and not bad:
        print("ALL GREEN: 20/20 routes, 0 broken assets")
        return 0
    print(f"routes failed: {len(bad_routes)}, assets broken: {len(bad)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
