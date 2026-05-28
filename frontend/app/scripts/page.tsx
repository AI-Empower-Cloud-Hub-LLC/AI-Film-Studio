'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  DocumentTextIcon,
  SparklesIcon,
  FilmIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import ErrorBoundary from '../components/ErrorBoundary'
import { projectsApi } from '../../lib/api'
import type { Project, ProjectDetail } from '../../lib/api'

function ScriptsContent() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selected, setSelected] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadScript = async (id: string) => {
    try {
      const detail = await projectsApi.get(id)
      setSelected(detail)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Scripts</h1>
            <p className="text-gray-400">AI-generated screenplays from your film projects</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
              Loading scripts…
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-20">
              <DocumentTextIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400 mb-4">No scripts yet. Create a film to generate one.</p>
              <Link
                href="/create"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-purple-500/30 transition-all"
              >
                Create Film
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Project List */}
              <div className="space-y-3">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Projects</h2>
                {projects.map((p, i) => (
                  <motion.button
                    key={p.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => loadScript(p.id)}
                    className={`w-full text-left p-4 rounded-xl border transition-all ${
                      selected?.id === p.id
                        ? 'bg-purple-500/10 border-purple-500/30'
                        : 'bg-gray-800/40 border-gray-700/50 hover:bg-gray-800/70'
                    }`}
                  >
                    <h3 className="text-sm font-medium text-white truncate">{p.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <SparklesIcon className="h-3 w-3" /> {p.style}
                      </span>
                      <span className="flex items-center gap-1">
                        <FilmIcon className="h-3 w-3" /> {p.scene_count} scenes
                      </span>
                    </div>
                  </motion.button>
                ))}
              </div>

              {/* Script Viewer */}
              <div className="lg:col-span-2">
                {selected ? (
                  <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6">
                    <h2 className="text-xl font-bold text-white mb-4">{selected.title}</h2>
                    {selected.director_vision && (
                      <div className="mb-6 p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg">
                        <h3 className="text-sm font-semibold text-purple-400 mb-2">Director&apos;s Vision</h3>
                        <p className="text-gray-300 text-sm leading-relaxed">{selected.director_vision}</p>
                      </div>
                    )}
                    <div className="space-y-4">
                      {(selected.script.length > 0 ? selected.script : selected.scenes).map((scene) => (
                        <div key={scene.scene_number} className="p-4 bg-gray-700/30 rounded-lg border border-gray-600/30">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs font-medium rounded-full">
                              Scene {scene.scene_number}
                            </span>
                            <span className="text-xs text-gray-500">{scene.shot_type} | {scene.mood} | {scene.duration}s</span>
                          </div>
                          <p className="text-sm text-gray-300 mb-2">{scene.description}</p>
                          {scene.narration && (
                            <p className="text-sm text-gray-400 italic border-l-2 border-purple-500/50 pl-3">
                              {scene.narration}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                    <DocumentTextIcon className="h-10 w-10 mb-3" />
                    <p>Select a project to view its script</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ScriptsPage() {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <ScriptsContent />
      </ErrorBoundary>
    </AuthGuard>
  )
}
