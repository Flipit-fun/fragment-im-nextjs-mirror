// Root layout for the converted fragment.im site.
// Per-route CSS is imported by each page, because Framer reuses the same
// generated class names with different rule bodies across pages.

export const metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3310'
  ),
  title: 'Fragment Studio',
  description:
    'Independent multidisciplinary designer creating visual identities, ' +
    'websites and digital product experiences.',
};

export const viewport = { width: 'device-width' };

export default function RootLayout({ children }) {
  // `fragment-loader-complete` is the site's own hook: its CSS hides the
  // "Loading Page" overlay when that class is on <html>. Framer's JS used
  // to set it, so without the runtime the overlay would otherwise sit
  // there until its 5s pure-CSS fallback kicked in.
  return (
    <html lang="en" className="fragment-loader-complete">
      <body>{children}</body>
    </html>
  );
}
