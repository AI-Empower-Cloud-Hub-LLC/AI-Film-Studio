'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { FilmIcon, ChevronDownIcon, ChevronUpIcon, ArrowPathIcon, PlusIcon } from '@heroicons/react/24/outline'
import { api, ProjectSummary, ProjectDetail } from '@/lib/api'

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const colours: Record<string, string> = {
    completed: 'bg-green-400/10 text-green-400 border-green-400/20',
    processing: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
    pending: 'bg-gray-400/10 text-gray-400 border-gray-400/20',
    failed: 'bg-red-400/10 text-red-400 border-red-400/20',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded border ${colours[status] ?? colours.pending}`}>
      {status}
    </span>
  )
}

// ── Expanded project detail ───────────────────────────────────────────────────

function ProjectDetailPanel({ id }: { id: string }) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getProject(id)
      .then(setDetail)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="flex justify-center py-8">
      <div className="h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error) return <p className="text-red-400 text-sm py-4">{error}</p>
  if (!detail) return null

  return (
    <div className="pt-4 border-t border-gray-700 space-y-5">
      {/* Vision */}
      {detail.director_vision && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Director's Vision</p>
          <p className="text-gray-300 text-sm leading-relaxed">{detail.director_vision}</p>
        </div>
      )}

      {/* Scenes grid */}
      {detail.scenes?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Scenes</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {detail.scenes.map(scene => (
              <div key={scene.scene_number} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-purple-400">SCENE {scene.scene_number}</span>
                  <div className="flex gap-2 text-xs text-gray-500">
                    <span>{scene.shot_type}</span>
                    <span>·</span>
                    <span>{scene.mood}</span>
                    <span>·</span>
                    <span>{scene.duration}s</span>
                  </div>
                </div>
                <p className="text-gray-300 text-sm">{scene.description}</p>
                {scene.narration && (
                  <p className="text-gray-500 text-xs italic mt-2 line-clamp-2">{scene.narration}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Script excerpts */}
      {detail.script?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Script Highlights</p>
          <div className="space-y-2">
            {detail.script.slice(0, 3).map((s: any) => s.narration && (
              <div key={s.scene_number} className="flex gap-3 text-sm">
                <span className="text-purple-400 shrink-0 w-16">Scene {s.scene_number}</span>
                <p className="text-gray-400 italic line-clamp-2">{s.narration}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Project card ──────────────────────────────────────────────────────────────

function ProjectCard({ project }: { project: ProjectSummary }) {
  const [expanded, setExpanded] = useState(false)

  const date = new Date(project.created_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })

  return (
    <motion.div
      layout
      className="bg-gray-800 border border-gray-700 rounded-2xl overflow-hidden hover:border-gray-600 transition-colors"
    >
      {/* Card header — always visible */}
      <button
        className="w-full text-left p-6"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-gray-200 font-medium truncate">{project.title}</p>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
              <span className="capitalize">{project.style}</span>
              <span>·</span>
              <span>{project.duration}s</span>
              <span>·</span>
              <span>{project.scene_count} scenes</span>
              <span>·</span>
              <span>{date}</span>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <StatusBadge status={project.status} />
            {expanded
              ? <ChevronUpIcon className="h-4 w-4 text-gray-500" />
              : <ChevronDownIcon className="h-4 w-4 text-gray-500" />
            }
          </div>
        </div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden px-6 pb-6"
          >
            <ProjectDetailPanel id={project.id} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.listProjects()
      .then(setProjects)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-900/80 border-b border-gray-800 sticky top-0 z-10 backdrop-blur">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FilmIcon className="h-6 w-6 text-purple-400" />
            <h1 className="text-xl font-bold">AI Film Studio</h1>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">Home</Link>
            <Link href="/create" className="text-gray-400 hover:text-white transition-colors">Create</Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-10 max-w-4xl">
        {/* Page title */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-1">Projects</h2>
            <p className="text-gray-400">All your AI-generated film plans</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={load}
              className="p-2.5 bg-gray-800 border border-gray-700 rounded-xl text-gray-400 hover:text-white transition-colors"
              title="Refresh"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
            <Link
              href="/create"
              className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 rounded-xl text-sm font-medium transition-colors"
            >
              <PlusIcon className="h-4 w-4" />
              New Film
            </Link>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="h-8 w-8 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-6 text-center">
            <p className="text-red-400 mb-3">{error}</p>
            <button onClick={load} className="text-sm text-purple-400 hover:text-purple-300">Retry</button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && projects.length === 0 && (
          <div className="text-center py-20 text-gray-500">
            <FilmIcon className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg mb-2">No projects yet</p>
            <p className="text-sm mb-6">Create your first AI film to get started</p>
            <Link href="/create" className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-medium transition-colors">
              Create a Film
            </Link>
          </div>
        )}

        {/* Project list */}
        {!loading && !error && projects.length > 0 && (
          <motion.div className="space-y-4" initial="hidden" animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.06 } } }}>
            {projects.map(project => (
              <motion.div key={project.id}
                variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}>
                <ProjectCard project={project} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </main>
    </div>
  )
}
