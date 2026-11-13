> ## ⚠️ Not my design work — not affiliated with Fragment Studio
>
> The design, copy, photography, client case studies and 3D scenes in this
> repository are the work of **Fragment Studio** — <https://www.fragment.im/>.
>
> This is an **unaffiliated mirror and Next.js port, built purely as a
> development exercise.** It is not endorsed by or connected to Fragment
> Studio. The fonts and Spline scenes are licensed to the original author,
> not to this repo.
>
> **Please don't redeploy it, reuse the assets, or present the design as
> your own.** Rights holder: open an issue and it comes down immediately.
> See [NOTICE.md](NOTICE.md).

# fragment.im — local mirror

A complete offline mirror of <https://www.fragment.im/> (a Framer-published
site), captured 2026-11-12. All 20 routes and every asset are local; the
mirror makes no network requests.

## Two versions

This repo now holds two things:

| | what it is | run |
|---|---|---|
| `mirror/` | byte-faithful offline copy, Framer runtime intact, animations work | `python3 serve.py` → :8080 |
| `next-app/` | the same site converted to Next.js 16, real JSX, no Framer runtime | `cd next-app && PORT=3310 npm run dev` → :3310 |

Edit `next-app/` — it is ordinary React. The mirror is kept as the
reference the conversion is generated from. See `next-app/README.md`.

## Run it

```bash
python3 serve.py          # http://localhost:8080
python3 serve.py 8099     # custom port
```

Serve over HTTP, not `file://` — assets are referenced with root-relative
paths (`/framerusercontent.com/...`) and ES modules need a real origin.
`serve.py` adds clean-URL routing (`/work/bsr` → `work/bsr/index.html`) and
no-cache headers so edits appear on reload.

## What's here

```
mirror/
  index.html                        /
  about/ contact/ work/ pp/         English routes
  pl/...                            Polish routes (same tree)
  work/{bsr,ewm,gorilla,kadenco,index}/
  framerusercontent.com/
    sites/1w0f0s83UjRlQ3a3DeRhZN/   76 ES modules + search index
    assets/                         fonts (woff2) + videos (mp4)
    images/                         471 images, incl. 4K originals
  fonts.gstatic.com/s/              Google-hosted webfonts
serve.py                            dev server
edit.py                             site-wide text editing
```

643 files, ~157 MB. 20 routes, 304 distinct asset references, all verified
resolving with zero 404s.

## Editing: read this first

Framer renders copy into **both** the static HTML and a JS module, then
hydrates on load. **Editing only the HTML does nothing** — the text flashes,
then React replaces it with the module's copy. This is verified behaviour,
not a guess.

Use `edit.py`, which patches both:

```bash
python3 edit.py --where "One designer."                    # locate first
python3 edit.py -f "One designer." -r "New text." --dry-run
python3 edit.py -f "One designer." -r "New text."          # apply
```

It warns if a string matches HTML only (i.e. the edit would revert).

Styling is a different story: CSS lives in `<style>` blocks in each HTML
file and is *not* re-applied by hydration, so CSS edits stick with an
HTML-only change (verified). Note that Framer nests opaque wrapper
elements, so overriding `body` alone often stays hidden — target the
generated `.framer-*` classes instead. The module bundles are minified
but readable.

## How it was built

Scripts in `tools/`, re-runnable in order (`python3 tools/<name>.py`):

1. `pages.py` — fetch all 20 routes (discovered from the site's search index)
2. `mirror.py` — recursively crawl assets to closure, preserving CDN paths
3. `rewrite.py` — rewrite CDN URLs to local paths (3535 replacements);
   idempotent, and only rewrites when the local file exists

Module-to-module imports are relative (`./react.B4lOa1lM.mjs`), so
preserving the CDN directory layout means they resolve locally untouched.

## Known gaps

- `images/pGiXYozQ3mE4cilNOItfe2L2fUA.svg` is left pointing at the CDN — it
  404s on the live site too, so there is nothing to mirror.
- Framer analytics (`events.framer.com`) was stripped from all 20 pages.
- Contact-form submissions have no backend; they will not send.
- Source maps (`.map`) are not served by the CDN and were not mirrored.

## Note on reuse

This is someone else's design work, mirrored for local development and
experimentation. Fine to poke at locally; don't republish it as your own.
