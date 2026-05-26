'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  PhotoIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, Scene } from '../../lib/api'

export default function StoryboardsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [frames, setFrames] = useState<Scene[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadFrames = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setFrames(detail.scenes)
    } catch {
      setFrames([])
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-1">Storyboards</h1>
            <p className="text-gray-400">Visual planning frames derived from scene breakdowns</p>
          </div>

          {/* Project selector */}
          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadFrames(p.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  selectedProject === p.id
                    ? 'bg-purple-500/10 border-purple-500/30 text-purple-400'
                    : 'bg-gray-800/40 border-gray-700/50 text-gray-400 hover:text-white hover:bg-gray-800/70'
                }`}
              >
                {p.title.slice(0, 40)}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
              Loading…
            </div>
          ) : !selectedProject ? (
            <div className="text-center py-20">
              <PhotoIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view storyboard frames</p>
            </div>
          ) : frames.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No storyboard frames for this project yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {frames.map((frame, i) => (
                <motion.div
                  key={frame.scene_number}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.06 }}
                  className="bg-gray-800/40 border border-gray-700/50 rounded-xl overflow-hidden"
                >
                  {/* Placeholder frame visual */}
                  <div className="aspect-video bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center relative">
                    <PhotoIcon className="h-12 w-12 text-gray-600" />
                    <div className="absolute top-3 left-3 px-2 py-0.5 bg-black/60 text-white text-xs font-medium rounded">
                      Frame {frame.scene_number}
                    </div>
                    <div className="absolute bottom-3 right-3 px-2 py-0.5 bg-black/60 text-gray-300 text-xs rounded">
                      {frame.shot_type}
                    </div>
                  </div>

                  <div className="p-4">
                    <p className="text-sm text-gray-300 mb-2 line-clamp-2">{frame.description}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded-full">{frame.mood}</span>
                      <span>{frame.duration}s</span>
                    </div>
                    {frame.visual_prompt && (
                      <p className="mt-2 text-xs text-gray-500 line-clamp-2 italic">
                        Prompt: {frame.visual_prompt}
                      </p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
