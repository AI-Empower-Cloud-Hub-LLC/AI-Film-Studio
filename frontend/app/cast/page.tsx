'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { UserGroupIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, CastData } from '../../lib/api'

export default function CastPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [cast, setCast] = useState<CastData | null>(null)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadCast = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setCast(detail.cast || null)
    } catch {
      setCast(null)
    }
  }

  const roleColor = (role: string) => {
    switch (role) {
      case 'lead': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
      case 'supporting': return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      case 'extra': return 'bg-gray-500/10 text-gray-400 border-gray-500/20'
      default: return 'bg-purple-500/10 text-purple-400 border-purple-500/20'
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-1">Cast</h1>
            <p className="text-gray-400">Character descriptions, casting suggestions, and budget estimates</p>
          </div>

          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadCast(p.id)}
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
              <UserGroupIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view cast information</p>
            </div>
          ) : !cast ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No cast data available for this project yet.</p>
            </div>
          ) : (
            <div>
              {/* Casting Sheet Summary */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                {[
                  { label: 'Total', value: cast.casting_sheet.total_characters, color: 'text-white' },
                  { label: 'Leads', value: cast.casting_sheet.leads, color: 'text-yellow-400' },
                  { label: 'Supporting', value: cast.casting_sheet.supporting, color: 'text-blue-400' },
                  { label: 'Extras', value: cast.casting_sheet.extras, color: 'text-gray-400' },
                  { label: 'Budget', value: cast.casting_sheet.estimated_total_budget, color: 'text-green-400' },
                ].map((stat) => (
                  <div key={stat.label} className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4 text-center">
                    <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Character Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                {cast.characters.map((ch, i) => (
                  <motion.div
                    key={ch.character_name}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.06 }}
                    className="bg-gray-800/40 border border-gray-700/50 rounded-xl overflow-hidden"
                  >
                    <div className="h-32 bg-gradient-to-br from-purple-900/40 to-gray-800 flex items-center justify-center">
                      <div className="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center text-2xl font-bold text-purple-400">
                        {ch.character_name.charAt(0)}
                      </div>
                    </div>

                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-bold text-white">{ch.character_name}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full border ${roleColor(ch.role_type)}`}>
                          {ch.role_type}
                        </span>
                      </div>

                      <p className="text-sm text-gray-300 mb-3">{ch.description}</p>

                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Physical</span>
                          <span className="text-gray-300 text-right ml-2">{ch.physical_description}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Budget</span>
                          <span className="text-green-400">{ch.estimated_salary_range}</span>
                        </div>
                      </div>

                      {ch.suggested_actors.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-700/50">
                          <span className="text-xs text-gray-500">Suggested: </span>
                          <span className="text-xs text-gray-400">{ch.suggested_actors.join(', ')}</span>
                        </div>
                      )}

                      {ch.personality_traits.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {ch.personality_traits.map((t) => (
                            <span key={t} className="text-xs bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">
                              {t}
                            </span>
                          ))}
                        </div>
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
