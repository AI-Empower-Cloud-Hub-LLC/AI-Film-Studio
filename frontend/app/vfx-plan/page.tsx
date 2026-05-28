'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { SparklesIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, VFXData } from '../../lib/api'

export default function VFXPlanPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [vfxData, setVfxData] = useState<VFXData | null>(null)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadVFX = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setVfxData(detail.vfx_plan || null)
    } catch {
      setVfxData(null)
    }
  }

  const complexityColor = (c: string) => {
    switch (c) {
      case 'low': return 'bg-green-500/10 text-green-400'
      case 'medium': return 'bg-yellow-500/10 text-yellow-400'
      case 'high': return 'bg-orange-500/10 text-orange-400'
      case 'extreme': return 'bg-red-500/10 text-red-400'
      default: return 'bg-gray-500/10 text-gray-400'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">VFX Plan</h1>
            <p className="text-gray-400">Visual effects shots, techniques, complexity, and budget planning</p>
          </div>

          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadVFX(p.id)}
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
              <SparklesIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view VFX plan</p>
            </div>
          ) : !vfxData ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No VFX data available for this project yet.</p>
            </div>
          ) : (
            <div>
              {/* VFX Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Total Scenes', value: vfxData.vfx_summary.total_scenes, color: 'text-white' },
                  { label: 'VFX Scenes', value: vfxData.vfx_summary.scenes_with_vfx, color: 'text-purple-400' },
                  { label: 'High/Extreme', value: (vfxData.vfx_summary.complexity_breakdown.high || 0) + (vfxData.vfx_summary.complexity_breakdown.extreme || 0), color: 'text-orange-400' },
                  { label: 'Est. Budget', value: vfxData.vfx_summary.estimated_total_cost, color: 'text-green-400' },
                ].map((stat) => (
                  <div key={stat.label} className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4 text-center">
                    <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* VFX Shots */}
              <div className="space-y-4">
                {vfxData.vfx_shots.map((shot, i) => (
                  <motion.div
                    key={shot.scene_number}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={`bg-gray-800/40 border rounded-xl p-5 ${
                      shot.vfx_needed ? 'border-purple-500/30' : 'border-gray-700/50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-500">Scene {shot.scene_number}</span>
                        {shot.vfx_needed ? (
                          <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded-full font-medium">
                            VFX Required
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 bg-gray-500/10 text-gray-400 text-xs rounded-full">
                            No VFX
                          </span>
                        )}
                        <span className={`px-2 py-0.5 text-xs rounded-full ${complexityColor(shot.complexity)}`}>
                          {shot.complexity}
                        </span>
                      </div>
                      <span className="text-sm text-green-400 font-medium">{shot.estimated_cost}</span>
                    </div>

                    <p className="text-sm text-gray-300 mb-3">{shot.description}</p>

                    {shot.vfx_needed && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <span className="text-xs text-gray-500 uppercase">Techniques</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {shot.techniques.map((t, j) => (
                              <span key={j} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-xs rounded">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <span className="text-xs text-gray-500 uppercase">Software</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {shot.software_recommended.map((s, j) => (
                              <span key={j} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {shot.render_time_estimate && shot.vfx_needed && (
                      <div className="mt-3 text-xs text-gray-500">
                        Render time: <span className="text-gray-400">{shot.render_time_estimate}</span>
                      </div>
                    )}

                    {shot.notes && (
                      <div className="mt-2 text-xs text-gray-500 italic">{shot.notes}</div>
                    )}
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
