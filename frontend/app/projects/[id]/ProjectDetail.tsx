'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeftIcon,
  ClockIcon,
  SparklesIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  TrashIcon,
  FolderArrowDownIcon,
  FilmIcon,
  UserGroupIcon,
  MapPinIcon,
  PaintBrushIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline'
import { exportsApi, projectsApi } from '../../../lib/api'
import type { ProjectDetail as ProjectDetailType } from '../../../lib/api'

export default function ProjectDetail() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string
  const [project, setProject] = useState<ProjectDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'scenes' | 'scripts'>('scenes')
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    projectsApi.get(id)
      .then((data) => { setProject(data); setEditTitle(data.title) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = async () => {
    if (!project) return
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    await fetch(`${apiUrl}/api/v1/autonomous/projects/${project.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: editTitle }),
    })
    setProject({ ...project, title: editTitle })
    setEditing(false)
  }

  const handleDelete = async () => {
    if (!project) return
    setDeleting(true)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    await fetch(`${apiUrl}/api/v1/autonomous/projects/${project.id}`, { method: 'DELETE' })
    router.push('/projects')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-purple-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">Project not found</p>
          <Link href="/projects" className="text-purple-400 hover:text-purple-300">Back to Projects</Link>
        </div>
      </div>
    )
  }

  const statusColor: Record<string, string> = {
    completed: 'bg-green-500/10 text-green-400 border-green-500/30',
    processing: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    pending: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    failed: 'bg-red-500/10 text-red-400 border-red-500/30',
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/projects" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
            <ArrowLeftIcon className="h-5 w-5" />
          </Link>
          <div className="flex-1">
            {editing ? (
              <div className="flex items-center gap-2">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="text-2xl font-bold text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1"
                />
                <button onClick={handleSave} className="px-3 py-1 bg-purple-600 text-white text-sm rounded-lg">Save</button>
                <button onClick={() => setEditing(false)} className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm rounded-lg">Cancel</button>
              </div>
            ) : (
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{project.title}</h1>
            )}
            <div className="flex items-center gap-3 mt-1">
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${statusColor[project.status] || 'bg-gray-500/10 text-gray-400 border-gray-500/30'}`}>
                {project.status}
              </span>
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <SparklesIcon className="h-3.5 w-3.5" /> {project.style}
              </span>
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <ClockIcon className="h-3.5 w-3.5" /> {project.duration}s
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1 px-3 py-2 bg-gray-100 dark:bg-gray-700/50 border border-gray-300 dark:border-gray-600/50 rounded-lg text-gray-600 dark:text-gray-300 text-xs font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              <PencilIcon className="h-4 w-4" /> Edit
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-1 px-3 py-2 bg-red-600/20 border border-red-500/30 rounded-lg text-red-400 text-xs font-medium hover:bg-red-600/30 transition-colors disabled:opacity-50"
            >
              <TrashIcon className="h-4 w-4" /> {deleting ? 'Deleting...' : 'Delete'}
            </button>
            <a
              href={exportsApi.zipUrl(project.id)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-xs font-medium transition-colors"
            >
              <FolderArrowDownIcon className="h-4 w-4" /> Download All
            </a>
          </div>
        </div>

        {/* Video Preview Player */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 rounded-xl overflow-hidden shadow-sm dark:shadow-none"
        >
          <div className="aspect-video bg-black flex items-center justify-center relative">
            <div className="text-center">
              <VideoCameraIcon className="h-12 w-12 text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">Video preview will appear here when generated</p>
              <p className="text-gray-600 text-xs mt-1">{project.scenes.length} scenes &middot; {project.duration}s</p>
            </div>
          </div>
        </motion.div>

        {/* Downloads */}
        {project.status === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8 bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6 shadow-sm dark:shadow-none"
          >
            <div className="flex items-center gap-2 mb-4">
              <ArrowDownTrayIcon className="h-5 w-5 text-purple-500" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Downloads</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              <a
                href={exportsApi.zipUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-500/30 rounded-xl hover:bg-purple-100 dark:hover:bg-purple-500/20 transition-colors group"
              >
                <FolderArrowDownIcon className="h-8 w-8 text-purple-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-purple-700 dark:text-purple-300">All Assets (ZIP)</span>
              </a>
              <a
                href={exportsApi.pdfUrl(project.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-2 p-4 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-xl hover:bg-red-100 dark:hover:bg-red-500/20 transition-colors group"
              >
                <DocumentTextIcon className="h-8 w-8 text-red-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-red-700 dark:text-red-300">Script (PDF)</span>
              </a>
              <a
                href={exportsApi.screenplayUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/30 rounded-xl hover:bg-blue-100 dark:hover:bg-blue-500/20 transition-colors group"
              >
                <FilmIcon className="h-8 w-8 text-blue-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">Screenplay</span>
              </a>
              <a
                href={exportsApi.castUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/30 rounded-xl hover:bg-green-100 dark:hover:bg-green-500/20 transition-colors group"
              >
                <UserGroupIcon className="h-8 w-8 text-green-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">Cast Sheet</span>
              </a>
              <a
                href={exportsApi.locationsUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 rounded-xl hover:bg-amber-100 dark:hover:bg-amber-500/20 transition-colors group"
              >
                <MapPinIcon className="h-8 w-8 text-amber-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-amber-700 dark:text-amber-300">Locations</span>
              </a>
              <a
                href={exportsApi.vfxUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-cyan-50 dark:bg-cyan-500/10 border border-cyan-200 dark:border-cyan-500/30 rounded-xl hover:bg-cyan-100 dark:hover:bg-cyan-500/20 transition-colors group"
              >
                <CpuChipIcon className="h-8 w-8 text-cyan-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-cyan-700 dark:text-cyan-300">VFX Plan</span>
              </a>
              <a
                href={exportsApi.moodBoardUrl(project.id)}
                className="flex flex-col items-center gap-2 p-4 bg-pink-50 dark:bg-pink-500/10 border border-pink-200 dark:border-pink-500/30 rounded-xl hover:bg-pink-100 dark:hover:bg-pink-500/20 transition-colors group"
              >
                <PaintBrushIcon className="h-8 w-8 text-pink-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-pink-700 dark:text-pink-300">Mood Board</span>
              </a>
              <a
                href={exportsApi.jsonUrl(project.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-2 p-4 bg-gray-50 dark:bg-gray-500/10 border border-gray-200 dark:border-gray-500/30 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-500/20 transition-colors group"
              >
                <ArrowDownTrayIcon className="h-8 w-8 text-gray-500 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Raw Data (JSON)</span>
              </a>
            </div>
          </motion.div>
        )}

        {/* Director Vision */}
        {project.director_vision && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-purple-500/5 border border-purple-500/20 rounded-xl"
          >
            <h2 className="text-sm font-semibold text-purple-400 mb-2">Director&apos;s Vision</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{project.director_vision}</p>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800/60 p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('scenes')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'scenes' ? 'bg-purple-500/20 text-purple-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <VideoCameraIcon className="h-4 w-4" /> Scenes ({project.scenes.length})
          </button>
          <button
            onClick={() => setActiveTab('scripts')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'scripts' ? 'bg-purple-500/20 text-purple-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <DocumentTextIcon className="h-4 w-4" /> Scripts ({project.script.length})
          </button>
        </div>

        {/* Content */}
        {activeTab === 'scenes' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {project.scenes.map((scene, i) => (
              <motion.div
                key={scene.scene_number}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 rounded-xl p-5 shadow-sm dark:shadow-none"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">Scene {scene.scene_number}</span>
                  <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs rounded-full">{scene.duration}s</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{scene.description}</p>
                <div className="flex gap-2">
                  <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-full">{scene.shot_type}</span>
                  <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full">{scene.mood}</span>
                </div>
                {scene.visual_prompt && (
                  <p className="mt-3 text-xs text-gray-500 italic border-l-2 border-gray-300 dark:border-gray-700 pl-3">{scene.visual_prompt}</p>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {project.script.map((script, i) => (
              <motion.div
                key={script.scene_number}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 rounded-xl p-5 shadow-sm dark:shadow-none"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs font-medium rounded-full">
                    Scene {script.scene_number}
                  </span>
                </div>
                {script.narration && (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 italic border-l-2 border-purple-500/50 pl-3">
                    {script.narration}
                  </p>
                )}
                {script.dialogue && script.dialogue.length > 0 && (
                  <div className="space-y-2">
                    {script.dialogue.map((d, di) => (
                      <div key={di} className="pl-4">
                        <span className="text-xs font-semibold text-blue-400 uppercase">{d.character}</span>
                        <p className="text-sm text-gray-600 dark:text-gray-300">{d.line}</p>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
