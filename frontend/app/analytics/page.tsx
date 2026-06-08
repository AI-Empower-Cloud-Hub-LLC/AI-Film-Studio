'use client'

import { useEffect, useState } from 'react'
import {
  ChartBarIcon, UsersIcon, FilmIcon, CubeIcon,
  ArrowTrendingUpIcon, ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import { analyticsApi } from '../../lib/api'

interface OverviewData {
  total_users: number
  total_projects: number
  completed_projects: number
  total_scenes: number
  recent_7d: { projects: number; users: number }
  monthly_projects: number
  completion_rate: number
  avg_scenes_per_film: number
}

interface TrendDay {
  date: string
  films: number
  users: number
}

interface StyleData {
  style: string
  count: number
}

function AnalyticsContent() {
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [trends, setTrends] = useState<TrendDay[]>([])
  const [styles, setStyles] = useState<StyleData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsApi.overview().then(setOverview).catch(() => {}),
      analyticsApi.trends(30).then(r => setTrends(r.data)).catch(() => {}),
      analyticsApi.topStyles().then(setStyles).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  const maxFilms = Math.max(...trends.map(d => d.films), 1)

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Analytics Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400">Usage metrics and generation statistics</p>
          </div>

          {loading ? (
            <div className="text-center py-20 text-gray-400">Loading analytics...</div>
          ) : (
            <>
              {/* Overview cards */}
              {overview && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                  {[
                    { label: 'Total Users', value: overview.total_users, icon: UsersIcon, gradient: 'from-blue-500 to-cyan-500', sub: `+${overview.recent_7d.users} this week` },
                    { label: 'Total Films', value: overview.total_projects, icon: FilmIcon, gradient: 'from-purple-500 to-pink-500', sub: `${overview.monthly_projects} this month` },
                    { label: 'Completion Rate', value: `${overview.completion_rate}%`, icon: ArrowTrendingUpIcon, gradient: 'from-green-500 to-emerald-500', sub: `${overview.completed_projects} completed` },
                    { label: 'Total Scenes', value: overview.total_scenes, icon: CubeIcon, gradient: 'from-orange-500 to-red-500', sub: `~${overview.avg_scenes_per_film} per film` },
                  ].map((card, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-5">
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`p-2 bg-gradient-to-br ${card.gradient} rounded-lg`}>
                          <card.icon className="h-5 w-5 text-white" />
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">{card.label}</span>
                      </div>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{card.value}</p>
                      <p className="text-xs text-gray-400 mt-1">{card.sub}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Film creation trend chart */}
                <div className="lg:col-span-2 bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Film Creation Trend (30 days)</h3>
                  <div className="flex items-end gap-1 h-40">
                    {trends.slice(-30).map((day, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center group relative">
                        <div className="w-full bg-purple-500/80 rounded-t transition-all hover:bg-purple-400" style={{ height: `${Math.max(4, (day.films / maxFilms) * 100)}%` }} />
                        <div className="absolute -top-8 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          {day.date}: {day.films} film{day.films !== 1 ? 's' : ''}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>{trends[0]?.date}</span>
                    <span>{trends[trends.length - 1]?.date}</span>
                  </div>
                </div>

                {/* Top styles */}
                <div className="bg-white dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Film Styles</h3>
                  {styles.length === 0 ? (
                    <p className="text-gray-400 text-sm">No data yet</p>
                  ) : (
                    <div className="space-y-3">
                      {styles.slice(0, 8).map((s, i) => {
                        const maxCount = styles[0]?.count || 1
                        const colors = ['bg-purple-500', 'bg-blue-500', 'bg-pink-500', 'bg-green-500', 'bg-orange-500', 'bg-cyan-500', 'bg-red-500', 'bg-yellow-500']
                        return (
                          <div key={i}>
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-gray-700 dark:text-gray-300 capitalize">{s.style}</span>
                              <span className="text-gray-400">{s.count}</span>
                            </div>
                            <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div className={`h-full ${colors[i % colors.length]} rounded-full transition-all`} style={{ width: `${(s.count / maxCount) * 100}%` }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AnalyticsPage() {
  return <AuthGuard><AnalyticsContent /></AuthGuard>
}
