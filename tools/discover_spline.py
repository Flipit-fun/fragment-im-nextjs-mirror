#!/usr/bin/env python3
"""Discover which Spline scene belongs in which Framer embed container.

Framer creates <spline-viewer> elements at runtime, so the static mirror
has only empty placeholders. We render the mirror (which still has the
Framer runtime), dump the resulting DOM, and record, for each viewer, the
nearest `framer-<id>-container` ancestor. tools/to_next.py then injects a
real React component into exactly that container.

Writes tools/spline_map.json. Needs the mirror served (default :8099).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spline_map.json")
PORT = sys.argv[1] if len(sys.argv) > 1 else "8099"
CHROME = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

ROUTES = ["/", "/about", "/contact", "/pl", "/pl/about", "/pl/contact",
          "/work/ewm", "/pl/work/ewm"]

VIEWER_RE = re.compile(r"<spline-viewer[^>]*>", re.I)
URL_RE = re.compile(r'url="([^"]+)"', re.I)
CONTAINER_RE = re.compile(r'framer-([A-Za-z0-9]+)-container')


def dump_dom(route):
    cmd = [CHROME, "--headless", "--no-sandbox", "--disable-gpu",
           "--window-size=1440,900", "--virtual-time-budget=25000",
           "--dump-dom", f"http://localhost:{PORT}{route}"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        return r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return ""


def main():
    result = {}
    for route in ROUTES:
        dom = dump_dom(route)
        if not dom:
            print(f"  {route:<16} DOM dump failed")
            continue
        entries = []
        for m in VIEWER_RE.finditer(dom):
            tag = m.group(0)
            um = URL_RE.search(tag)
            if not um:
                continue
            scene = um.group(1).rstrip("/").split("/")[-2] \
                if um.group(1).endswith("scene.splinecode") else None
            # nearest preceding framer-*-container
            before = dom[:m.start()]
            cms = CONTAINER_RE.findall(before)
            entries.append({
                "container": cms[-1] if cms else None,
                "scene": scene,
                "url": um.group(1),
            })
        result[route] = entries
        print(f"  {route:<16} {len(entries)} viewer(s): "
              + ", ".join(f"{e['container']}->{e['scene']}" for e in entries))

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
