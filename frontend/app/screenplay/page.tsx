'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, RefinedScreenplay } from '../../lib/api'

export default function ScreenplayPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [screenplay, setScreenplay] = useState<RefinedScreenplay | null>(null)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadScreenplay = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setScreenplay(detail.refined_screenplay || null)
    } catch {
      setScreenplay(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Screenplay</h1>
            <p className="text-gray-400">Refined screenplay with camera directions and production notes</p>
          </div>

          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadScreenplay(p.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  selectedProject === p.id
                    ? 'bg-purple-500/10 border-purple-500/30 text-purple-400'
                    : 'bg-gray-100 dark:bg-gray-800/40 border-gray-200 dark:border-gray-700/50 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-gray-800/70'
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
              <DocumentTextIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view its refined screenplay</p>
            </div>
          ) : !screenplay ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No refined screenplay available for this project yet.</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <span className="px-3 py-1 bg-purple-500/10 text-purple-400 rounded-full">
                  {screenplay.total_scenes} scenes
                </span>
                <span className="px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full">
                  {screenplay.format}
                </span>
              </div>

              {screenplay.refined_scenes.map((scene, i) => (
                <motion.div
                  key={scene.scene_number}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-mono font-bold text-yellow-400">
                      {scene.slug_line}
                    </h3>
                    <span className="text-xs text-gray-500">Scene {scene.scene_number}</span>
                  </div>

                  <p className="text-gray-300 mb-4 font-mono text-sm leading-relaxed">
                    {scene.action_lines}
                  </p>

                  {scene.dialogue && scene.dialogue.length > 0 && (
                    <div className="mb-4 space-y-3">
                      {scene.dialogue.map((d, j) => (
                        <div key={j} className="text-center font-mono">
                          <div className="text-sm font-bold text-white uppercase">{d.character}</div>
                          {d.parenthetical && (
                            <div className="text-xs text-gray-500">({d.parenthetical})</div>
                          )}
                          <div className="text-sm text-gray-300">{d.line}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {scene.camera_directions && scene.camera_directions.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-xs font-semibold text-cyan-400 uppercase mb-1">Camera Directions</h4>
                      <div className="flex flex-wrap gap-2">
                        {scene.camera_directions.map((dir, j) => (
                          <span key={j} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-xs rounded">
                            {dir}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="font-mono">{scene.transitions}</span>
                    {scene.production_notes && scene.production_notes.length > 0 && (
                      <span className="text-orange-400">
                        {scene.production_notes.length} production note{scene.production_notes.length > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>

                  {scene.polished_narration && (
                    <div className="mt-3 pt-3 border-t border-gray-700/50">
                      <p className="text-sm text-gray-400 italic">&ldquo;{scene.polished_narration}&rdquo;</p>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
