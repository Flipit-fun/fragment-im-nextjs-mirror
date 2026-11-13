'use client';

import { useEffect, useState } from 'react';

// Framer loaded Spline through an HTML embed that injected this script tag.
// With the Framer runtime gone we load the viewer ourselves - once per page,
// no matter how many scenes are on it.
const VIEWER_SRC = '/spline/spline-viewer.js';
let viewerPromise = null;

function loadViewer() {
  if (viewerPromise) return viewerPromise;
  viewerPromise = new Promise((resolve, reject) => {
    if (customElements.get('spline-viewer')) return resolve();
    if (!document.querySelector(`script[src="${VIEWER_SRC}"]`)) {
      const s = document.createElement('script');
      s.type = 'module';
      s.src = VIEWER_SRC;
      s.addEventListener('error', reject);
      document.head.appendChild(s);
    }
    // The script's load event is not enough: the viewer registers the
    // element from an async import, so wait for the definition itself.
    customElements.whenDefined('spline-viewer').then(() => resolve());
  });
  return viewerPromise;
}

/**
 * Renders one Spline scene, filling its parent.
 *
 * @param {string} scene  scene id, e.g. 'QzFYO-pwcQCbiF9t'
 */
export default function SplineViewer({ scene, eager = true }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let alive = true;
    loadViewer()
      .then(() => alive && setReady(true))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  // The custom element is only rendered once its definition exists, so React
  // never hands attributes to an unupgraded element.
  if (!ready) return <div style={{ width: '100%', height: '100%' }} />;

  return (
    <spline-viewer
      url={`/spline/scenes/${scene}.splinecode`}
      loading={eager ? 'eager' : 'lazy'}
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  );
}
