'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { SwatchIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, MoodBoardData } from '../../lib/api'

export default function MoodBoardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [moodBoard, setMoodBoard] = useState<MoodBoardData | null>(null)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadMoodBoard = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setMoodBoard(detail.mood_board || null)
    } catch {
      setMoodBoard(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Mood Board</h1>
            <p className="text-gray-400">Visual style reference, color palettes, and mood images</p>
          </div>

          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadMoodBoard(p.id)}
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
              <SwatchIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view its mood board</p>
            </div>
          ) : !moodBoard ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No mood board data available for this project yet.</p>
            </div>
          ) : (
            <div>
              {/* Style Guide */}
              {moodBoard.style_guide && (
                <div className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 shadow-sm dark:shadow-none rounded-xl p-6 mb-8">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Style Guide</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">Color Palette</h3>
                      <div className="flex gap-2 mb-4">
                        {moodBoard.style_guide.primary_colors?.map((color, i) => (
                          <div key={i} className="flex flex-col items-center gap-1">
                            <div
                              className="w-12 h-12 rounded-lg border border-gray-600"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-xs text-gray-500 font-mono">{color}</span>
                          </div>
                        ))}
                        {moodBoard.style_guide.accent_colors?.map((color, i) => (
                          <div key={`accent-${i}`} className="flex flex-col items-center gap-1">
                            <div
                              className="w-12 h-12 rounded-lg border border-gray-600 ring-2 ring-offset-1 ring-offset-gray-900 ring-purple-500/30"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-xs text-gray-500 font-mono">{color}</span>
                          </div>
                        ))}
                      </div>

                      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">Typography</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{moodBoard.style_guide.typography_style}</p>

                      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">Lighting</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300">{moodBoard.style_guide.lighting_approach}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">Textures</h3>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {moodBoard.style_guide.texture_keywords?.map((kw, i) => (
                          <span key={i} className="px-2 py-1 bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-300 text-xs rounded">
                            {kw}
                          </span>
                        ))}
                      </div>

                      <h3 className="text-sm font-semibold text-gray-400 uppercase mb-2">Composition Rules</h3>
                      <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                        {moodBoard.style_guide.composition_rules?.map((rule, i) => (
                          <li key={i} className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                            {rule}
                          </li>
                        ))}
                      </ul>

                      <h3 className="text-sm font-semibold text-gray-400 uppercase mt-4 mb-2">Reference Films</h3>
                      <div className="flex flex-wrap gap-2">
                        {moodBoard.style_guide.reference_films?.map((film, i) => (
                          <span key={i} className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-full">
                            {film}
                          </span>
                        ))}
                      </div>

                      <h3 className="text-sm font-semibold text-gray-400 uppercase mt-4 mb-2">Overall Tone</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300">{moodBoard.style_guide.overall_tone}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Mood Images Grid */}
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Mood Images ({moodBoard.total_images})</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
                {moodBoard.mood_images.map((img, i) => (
                  <motion.div
                    key={img.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.06 }}
                    className="bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 shadow-sm dark:shadow-none rounded-xl overflow-hidden"
                  >
                    {/* Color swatch preview */}
                    <div className="h-24 flex">
                      {img.color_hex_codes?.map((hex, j) => (
                        <div
                          key={j}
                          className="flex-1"
                          style={{ backgroundColor: hex }}
                        />
                      ))}
                    </div>

                    <div className="p-4">
                      <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-1">{img.title}</h3>
                      <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full">
                        {img.category.replace('_', ' ')}
                      </span>
                      <p className="text-xs text-gray-400 mt-2 line-clamp-2">{img.description}</p>
                      {img.reference_notes && (
                        <p className="text-xs text-gray-500 mt-1 italic">{img.reference_notes}</p>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
