import type { NextConfig } from "next";

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiBaseUrl}/api/v1/:path*`,
      },
      {
        source: "/health",
        destination: `${apiBaseUrl}/health`,
      },
      {
        source: "/health/:path*",
        destination: `${apiBaseUrl}/health/:path*`,
      },
    ];
  },
};

export default nextConfig;
