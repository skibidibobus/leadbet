/** @type {import('next').NextConfig} */
const isGitHubPages = process.env.GITHUB_PAGES === "true";

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@quantkupon/contracts"],
  ...(isGitHubPages
    ? {
        output: "export",
        basePath: "/leadbet",
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;
