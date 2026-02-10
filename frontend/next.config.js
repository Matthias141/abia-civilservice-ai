/** @type {import('next').NextConfig} */
const nextConfig = {
  // "standalone" is only needed for Docker deployments
  // Vercel handles this automatically
  ...(process.env.DOCKER_BUILD === "true" ? { output: "standalone" } : {}),
};

module.exports = nextConfig;
