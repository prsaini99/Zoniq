/*
 * next.config.ts — Next.js configuration for the Zoniq frontend.
 * Sets the output mode to "standalone" for optimized Docker/production deployments
 * that bundle only the necessary files (no node_modules).
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // Produces a self-contained build for containerized deployment
};

export default nextConfig;
