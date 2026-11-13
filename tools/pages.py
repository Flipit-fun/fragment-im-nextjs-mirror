#!/usr/bin/env python3
"""Fetch every route of the site into a path-preserving local tree."""
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT = "/Volumes/T7/Frontends/fragment/mirror"
SITE = "https://www.fragment.im"
IDX = os.path.join(
    OUT, "framerusercontent.com/sites/1w0f0s83UjRlQ3a3DeRhZN",
    "searchIndex-wHeikEufWEDe.json")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def local_page(route):
    r = route.strip("/")
    return os.path.join(OUT, "index.html") if not r \
        else os.path.join(OUT, r, "index.html")


def get(route):
    url = SITE + route
    dest = local_page(route)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as e:                                  # noqa: BLE001
        return route, f"FAIL {e!r}"
    with open(dest, "wb") as f:
        f.write(data)
    return route, f"{len(data):>9,} bytes -> {os.path.relpath(dest, OUT)}"


routes = sorted(json.load(open(IDX)).keys())
print(f"fetching {len(routes)} routes\n")
with ThreadPoolExecutor(max_workers=8) as ex:
    for route, msg in ex.map(get, routes):
        print(f"  {route:<22} {msg}")
