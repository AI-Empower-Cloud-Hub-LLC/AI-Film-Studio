import type { Metadata } from 'next'
import './globals.css'
import Providers from './providers'

export const metadata: Metadata = {
  title: 'AI Film Studio',
  description: 'AI-powered end-to-end video production platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans dark:bg-gray-950 bg-white transition-colors">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
