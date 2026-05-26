/** @type {import('next').NextConfig} */
const isGithubPages = process.env.GITHUB_PAGES === 'true'

const nextConfig = {
  ...(isGithubPages
    ? {
        output: 'export',
        basePath: '/AI-Film-Studio',
        images: { unoptimized: true },
        trailingSlash: true,
      }
    : {
        images: { unoptimized: true },
      }),
}

module.exports = nextConfig
