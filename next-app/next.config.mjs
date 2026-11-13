/** @type {import('next').NextConfig} */
const nextConfig = {
  // Lets `NEXT_DIST_DIR=.next-build next build` run without disturbing a
  // dev server that is already using .next
  distDir: process.env.NEXT_DIST_DIR || '.next',
  productionBrowserSourceMaps: false,
};
export default nextConfig;
