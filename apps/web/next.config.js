const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // Resolve @shared/* to packages/shared/ in the monorepo root.
    // This is needed for Vercel deployments where the build root is apps/web
    // and tsconfig paths alone may not be enough for webpack to find the module.
    config.resolve.alias["@shared"] = path.resolve(__dirname, "../../packages/shared");
    return config;
  },
};

module.exports = nextConfig;
