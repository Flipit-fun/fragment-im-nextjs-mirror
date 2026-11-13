#!/usr/bin/env python3
"""Site-wide text editing for the local fragment.im mirror.

Framer renders copy into BOTH the static HTML and a JS module, then
hydrates. Editing only the HTML flashes and reverts, so every edit has to
touch both. This does that in one shot.

    python3 edit.py --find "One designer." --replace "Mirrored locally."
    python3 edit.py --find "One designer." --replace "X"   --dry-run
    python3 edit.py --where "One designer."       # just locate the string

Only .html and .mjs under ./mirror are touched. Use --dry-run first.
"""
import argparse
import io
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
EXTS = {".html", ".mjs"}


def targets():
    for dirpath, _d, files in os.walk(ROOT):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in EXTS:
                yield os.path.join(dirpath, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", "-f")
    ap.add_argument("--replace", "-r")
    ap.add_argument("--where", "-w", help="locate a string, change nothing")
    ap.add_argument("--dry-run", "-n", action="store_true")
    a = ap.parse_args()

    needle = a.where or a.find
    if not needle:
        ap.error("pass --find/--replace, or --where")
    if a.where is None and a.replace is None:
        ap.error("--find requires --replace")

    hits, edited, total = [], 0, 0
    for path in targets():
        try:
            text = io.open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        n = text.count(needle)
        if not n:
            continue
        rel = os.path.relpath(path, ROOT)
        hits.append((rel, n))
        total += n
        if a.where or a.dry_run:
            continue
        io.open(path, "w", encoding="utf-8").write(
            text.replace(needle, a.replace))
        edited += 1

    if not hits:
        print(f"no match for {needle!r}")
        return 1
    for rel, n in sorted(hits):
        kind = "html" if rel.endswith(".html") else " mjs"
        print(f"  [{kind}] {n}x  {rel}")
    verb = "would change" if (a.dry_run or a.where) else "changed"
    print(f"\n{verb} {total} occurrence(s) in {len(hits)} file(s)"
          + ("" if a.where or a.dry_run else f"; wrote {edited}"))
    if not hits[0][0].endswith(".mjs") and len(hits) == 1:
        print("NOTE: matched HTML only - hydration will revert this edit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
