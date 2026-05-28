'use client'

import Link from 'next/link'
import { FilmIcon, SparklesIcon } from '@heroicons/react/24/outline'

interface Props {
  title: string
  description: string
}

export default function ComingSoon({ title, description }: Props) {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black flex flex-col">
      <header className="border-b border-gray-200 dark:border-gray-800/60 backdrop-blur-sm bg-white/80 dark:bg-gray-900/80">
        <div className="container mx-auto px-4 py-4 flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2 group">
            <FilmIcon className="h-6 w-6 text-purple-400 group-hover:text-purple-300 transition-colors" />
            <span className="font-bold text-gray-900 dark:text-white">AI Film Studio</span>
          </Link>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
        <div className="mb-6 p-4 bg-purple-500/10 rounded-2xl border border-purple-500/20">
          <SparklesIcon className="h-10 w-10 text-purple-400" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">{title}</h1>
        <p className="text-gray-400 max-w-md mb-8">{description}</p>
        <div className="flex gap-3">
          <Link
            href="/projects"
            className="px-5 py-2.5 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 text-gray-900 dark:text-white text-sm font-medium rounded-lg transition-colors"
          >
            View Projects
          </Link>
          <Link
            href="/create"
            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-sm font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30"
          >
            Create a Film
          </Link>
        </div>
      </div>
    </main>
  )
}
