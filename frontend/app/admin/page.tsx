'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  ChartBarIcon,
  UsersIcon,
  FilmIcon,
  CpuChipIcon,
  VideoCameraIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'

interface AdminStats {
  total_projects: number
  total_users: number
  total_scenes: number
  completed_projects: number
  agents_count: number
  pipeline_runs: number
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchStats = () => {
    setLoading(true)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${apiUrl}/api/v1/autonomous/admin/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchStats() }, [])

  const cards = stats ? [
    { label: 'Total Projects', value: stats.total_projects, icon: FilmIcon, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
    { label: 'Completed', value: stats.completed_projects, icon: ChartBarIcon, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
    { label: 'Total Users', value: stats.total_users, icon: UsersIcon, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
    { label: 'Total Scenes', value: stats.total_scenes, icon: VideoCameraIcon, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
    { label: 'AI Agents', value: stats.agents_count, icon: CpuChipIcon, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20' },
    { label: 'Pipeline Runs', value: stats.pipeline_runs, icon: ArrowPathIcon, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  ] : []

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />
      <div className="pl-64">
        <div className="px-8 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">Admin Dashboard</h1>
              <p className="text-gray-400">System-wide statistics and management</p>
            </div>
            <button
              onClick={fetchStats}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800/60 border border-gray-700/50 rounded-lg text-gray-300 text-sm hover:bg-gray-700/60 transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4" /> Refresh
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full mr-3" />
              Loading stats…
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {cards.map((card, i) => (
                <motion.div
                  key={card.label}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className={`border rounded-xl p-6 ${card.bg}`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <card.icon className={`h-8 w-8 ${card.color}`} />
                    <span className={`text-3xl font-bold ${card.color}`}>{card.value}</span>
                  </div>
                  <p className="text-gray-400 text-sm font-medium">{card.label}</p>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
