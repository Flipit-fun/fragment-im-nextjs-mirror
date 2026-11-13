# fragment-next

The fragment.im site converted from the static Framer mirror into a real
Next.js 16 App Router project. **No Framer runtime** — every page is plain
React you can edit.

## Run

```bash
npm install
PORT=3310 npm run dev        # http://localhost:3310
```

The dev/build scripts set `--max-old-space-size=8192`. This is required,
not cosmetic: 5.3 MB of generated JSX across 20 routes crashes the dev
server with a V8 heap OOM at Node's default limit.

Port 3310 is the default used here because 3000 and 3001 were already
taken on this machine. Any free port works: `PORT=4000 npm run dev`.

```bash
npm run build && PORT=3310 npm start   # production
```

## Layout

```
app/
  layout.jsx            <html>/<body>, shared metadata
  page.jsx              /            + styles.css
  about/ contact/ pp/   English routes
  work/{bsr,ewm,gorilla,kadenco,index}/
  pl/...                Polish routes (same shape)
public/
  framerusercontent.com/   images, fonts, video (hard-linked from ../mirror)
  fonts.gstatic.com/
```

Each route is a folder with two files:

- `page.jsx` — the markup as ordinary JSX, plus a `metadata` export
- `styles.css` — that route's CSS

**CSS is per-route on purpose.** Framer reuses the same generated class
names with *different* rule bodies across pages (333 selectors conflict,
e.g. `html { font-size }`), so merging them into one global sheet would
break pages. Each page imports only its own.

## Editing

Edit `page.jsx` directly — it is real JSX, so the dual HTML+module problem
of the raw mirror is gone. Change the hero:

```bash
# app/page.jsx
<h1 ...>One designer.</h1>   →   <h1 ...>Your text.</h1>
```

Fast Refresh picks it up. Class names are Framer-generated
(`.framer-p6ag5x`), so to restyle something, find that class in the
route's `styles.css`.

## What the conversion does

`../tools/to_next.py` regenerates every page from `../mirror`:

1. **Strips all Framer JavaScript.**
2. **Settles reveal states.** Framer ships content hidden
   (`opacity:0` + a translate/scale offset) and animates it in from JS.
   With the runtime gone the page renders *completely blank*, so 2553
   style attributes are rewritten to their settled end state. Only style
   attributes that actually contain `opacity:0` are touched, so layout
   transforms such as `translate(-50%,-50%)` survive.
3. **Makes video native.** Framer ships `<video preload="none">` and calls
   `play()` from JS; those elements otherwise reserve space and paint
   nothing. They become `autoplay muted playsinline preload="auto"`.
4. **Re-injects the Spline 3D scenes.** The hero "fragments", and the 3D
   on About / Contact / EWM, are Spline WebGL scenes that Framer created
   at runtime — the static mirror holds only empty placeholders, and
   `mirror/` itself streams them from `spline.design`.
   `tools/discover_spline.py` renders the mirror, reads the live DOM and
   records which scene belongs in which Framer container; the generator
   then injects `<SplineViewer>` into exactly that placeholder. All 14
   scenes and the viewer runtime are served locally from `public/spline/`.
5. **Converts HTML to JSX** (`../tools/html2jsx.py`) — `class` →
   `className`, style strings → style objects, SVG/HTML attribute
   casing, `value`/`checked` → `defaultValue`/`defaultChecked`.
6. **Un-escapes CSS entities.** Framer emits `&quot;` inside `<style>`;
   browsers silently drop those rules, Next refuses to parse them.
7. **Hard-links assets** into `public/` — no duplicated disk space.

Re-run after changing the mirror:

```bash
python3 ../tools/to_next.py      # overwrites every page.jsx
python3 ../tools/verify_next.py 3310
```

Note that `to_next.py` **overwrites** `page.jsx`, so it will discard hand
edits. Once you start editing, treat the generator as a one-time import.

## Spline 3D

```
public/spline/spline-viewer.js      viewer runtime (2.0.183)
public/spline/scenes/<id>.splinecode  14 scenes
components/SplineViewer.jsx         loads the runtime once, renders a scene
```

The runtime is pinned to **2.0.183**, not the 2.0.93 the site references:
the scenes Spline serves today are file format 134, which 2.0.93 cannot
read ("Update @splinetool/runtime to the latest version"). The viewer may
still fetch optional chunks (draco, physics) from `cdn.spline.design` for
scenes that use those features.

Scenes are keyed by id in `tools/spline_map.json`. To re-discover the
mapping after the upstream site changes, serve the mirror and run
`python3 ../tools/discover_spline.py 8099`.

## Verified

`tools/verify_next.py`: 20/20 routes 200, 600 distinct assets, 0 broken,
clean browser console. Rendering was compared against the original mirror
screenshot-by-screenshot.

## Differences from the live site

Removing the Framer runtime is a real trade-off:

- **Scroll and entrance animations are gone.** Content renders in its
  final state instead of animating in. The Spline scenes themselves do
  animate (they are real WebGL), but scroll-driven camera moves that
  Framer orchestrated are not wired up.
- Interactive Framer components (nav hover effects, the custom select
  widget) are static.
- Client-side route transitions are plain full-page loads; links are
  ordinary `<a>` tags, not `next/link`.
- The contact form has no backend and will not submit.
- Videos loop muted on autoplay rather than being JS-orchestrated.

Layout, typography, colour, imagery and copy match the original.
