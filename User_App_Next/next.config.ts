import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */

  // Explicitly acknowledge using both Turbopack and webpack
  turbopack: {},

  // Suppress source map warnings from dependencies (for webpack fallback)
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.ignoreWarnings = [
        /Failed to parse source map/,
        /Critical dependency: the request of a dependency is an expression/
      ]
    }
    return config
  }
};

export default nextConfig;
