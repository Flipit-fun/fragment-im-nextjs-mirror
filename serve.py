#!/usr/bin/env python3
"""Dev server for the local fragment.im mirror.

    python3 serve.py [port]       # default 8080

Serves ./mirror with clean-URL routing so /work/bsr resolves to
mirror/work/bsr/index.html, and sends no-cache headers so edits show
up on reload.
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirror")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        # Clean URLs: /about -> /about/index.html
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if not os.path.splitext(path)[1]:
            fs = self.translate_path(path)
            cand = os.path.join(fs, "index.html")
            if os.path.isfile(cand):
                self.path = path.rstrip("/") + "/index.html"
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        msg = fmt % args
        if " 404 " in msg or " 500 " in msg:
            sys.stderr.write(f"  404> {msg}\n")


if __name__ == "__main__":
    print(f"serving {ROOT}\n  http://localhost:{PORT}/\n(ctrl-c to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
