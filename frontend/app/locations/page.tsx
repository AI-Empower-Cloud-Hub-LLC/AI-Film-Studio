'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { MapPinIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import { projectsApi } from '../../lib/api'
import type { Project, LocationData } from '../../lib/api'

export default function LocationsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [locationData, setLocationData] = useState<LocationData | null>(null)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const loadLocations = async (id: string) => {
    setSelectedProject(id)
    try {
      const detail = await projectsApi.get(id)
      setLocationData(detail.locations || null)
    } catch {
      setLocationData(null)
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-1">Locations</h1>
            <p className="text-gray-400">Filming locations with geographic descriptions, budgets, and logistics</p>
          </div>

          <div className="flex gap-3 mb-6 flex-wrap">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => loadLocations(p.id)}
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
              <MapPinIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <p className="text-gray-400">Select a project to view filming locations</p>
            </div>
          ) : !locationData ? (
            <div className="text-center py-20">
              <p className="text-gray-400">No location data available for this project yet.</p>
            </div>
          ) : (
            <div>
              {/* Logistics Summary */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                {[
                  { label: 'Total Locations', value: locationData.logistics_summary.total_locations, color: 'text-white' },
                  { label: 'Interior', value: locationData.logistics_summary.interior_count, color: 'text-blue-400' },
                  { label: 'Exterior', value: locationData.logistics_summary.exterior_count, color: 'text-green-400' },
                  { label: 'Permits Needed', value: locationData.logistics_summary.permits_needed, color: 'text-orange-400' },
                  { label: 'Est. Cost/Day', value: locationData.logistics_summary.estimated_total_cost, color: 'text-yellow-400' },
                ].map((stat) => (
                  <div key={stat.label} className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4 text-center">
                    <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Location Cards */}
              <div className="space-y-5">
                {locationData.locations.map((loc, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-bold text-white">{loc.location_name}</h3>
                        <p className="text-sm text-gray-400">{loc.city_country}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">Scene {loc.scene_number}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          loc.type === 'exterior' ? 'bg-green-500/10 text-green-400' :
                          loc.type === 'interior' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-purple-500/10 text-purple-400'
                        }`}>
                          {loc.type}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm text-gray-300 mb-4">{loc.geographic_description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-xs text-gray-500 uppercase">Cost</span>
                        <p className="text-green-400 font-medium">{loc.estimated_cost}</p>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 uppercase">Permit Required</span>
                        <p className={loc.permit_required ? 'text-orange-400' : 'text-gray-400'}>
                          {loc.permit_required ? 'Yes' : 'No'}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 uppercase">Weather</span>
                        <p className="text-gray-300">{loc.weather_considerations}</p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-gray-700/50">
                      <span className="text-xs text-gray-500">Logistics: </span>
                      <span className="text-xs text-gray-400">{loc.logistics}</span>
                    </div>

                    {loc.alternatives && loc.alternatives.length > 0 && (
                      <div className="mt-2 flex gap-2 items-center">
                        <span className="text-xs text-gray-500">Alternatives:</span>
                        {loc.alternatives.map((alt, j) => (
                          <span key={j} className="px-2 py-0.5 bg-gray-700/50 text-gray-400 text-xs rounded">
                            {alt}
                          </span>
                        ))}
                      </div>
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
