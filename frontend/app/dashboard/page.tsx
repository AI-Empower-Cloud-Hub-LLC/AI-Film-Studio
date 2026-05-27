'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  FilmIcon,
  DocumentTextIcon,
  PhotoIcon,
  VideoCameraIcon,
  MicrophoneIcon,
  PlusIcon,
  CpuChipIcon,
  SparklesIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon } from '@heroicons/react/24/solid'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import ErrorBoundary from '../components/ErrorBoundary'
import { SkeletonStat, SkeletonCard } from '../components/LoadingSkeleton'
import { projectsApi } from '../../lib/api'
import type { Project } from '../../lib/api'

const STATS_CARDS = [
  { label: 'Total Projects', icon: FilmIcon, gradient: 'from-purple-500 to-blue-500', key: 'total' },
  { label: 'Completed', icon: CheckCircleIcon, gradient: 'from-green-500 to-emerald-500', key: 'completed' },
  { label: 'In Progress', icon: ClockIcon, gradient: 'from-yellow-500 to-orange-500', key: 'processing' },
  { label: 'AI Agents', icon: CpuChipIcon, gradient: 'from-pink-500 to-rose-500', key: 'agents' },
]

const QUICK_ACTIONS = [
  { label: 'New Film', href: '/create', icon: PlusIcon, gradient: 'from-purple-600 to-blue-600' },
  { label: 'Scripts', href: '/scripts', icon: DocumentTextIcon, gradient: 'from-blue-500 to-cyan-500' },
  { label: 'Storyboards', href: '/storyboards', icon: PhotoIcon, gradient: 'from-pink-500 to-purple-500' },
  { label: 'Scenes', href: '/scenes', icon: VideoCameraIcon, gradient: 'from-orange-500 to-red-500' },
  { label: 'Voiceovers', href: '/voiceovers', icon: MicrophoneIcon, gradient: 'from-green-500 to-emerald-500' },
]

function DashboardContent() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const stats: Record<string, number> = {
    total: projects.length,
    completed: projects.filter((p) => p.status === 'completed').length,
    processing: projects.filter((p) => p.status === 'processing' || p.status === 'pending').length,
    agents: 10,
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-gray-900 to-black">
      <Sidebar />

      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">Dashboard</h1>
              <p className="text-gray-400">Welcome to your AI Film Studio</p>
            </div>
            <Link
              href="/create"
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30"
            >
              <PlusIcon className="h-5 w-5" />
              Create Film
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => <SkeletonStat key={i} />)
            ) : (
              STATS_CARDS.map((card, i) => (
                <motion.div
                  key={card.key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 bg-gradient-to-br ${card.gradient} rounded-lg`}>
                      <card.icon className="h-5 w-5 text-white" />
                    </div>
                    <span className="text-sm text-gray-400">{card.label}</span>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {stats[card.key]}
                  </p>
                </motion.div>
              ))
            )}
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {QUICK_ACTIONS.map((action) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="group bg-gray-800/40 hover:bg-gray-800/70 border border-gray-700/50 hover:border-gray-600 rounded-xl p-5 text-center transition-all"
                >
                  <div className={`mx-auto w-12 h-12 bg-gradient-to-br ${action.gradient} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                    <action.icon className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">
                    {action.label}
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* Recent Projects */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Recent Projects</h2>
              <Link href="/projects" className="text-sm text-purple-400 hover:text-purple-300">
                View all
              </Link>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-16">
                <SparklesIcon className="h-10 w-10 text-purple-400 mx-auto mb-3" />
                <p className="text-gray-400 mb-4">No projects yet. Create your first AI film!</p>
                <Link
                  href="/create"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-purple-500/30 transition-all"
                >
                  <PlusIcon className="h-5 w-5" />
                  Create Film
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {projects.slice(0, 6).map((project, i) => (
                  <motion.div
                    key={project.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}
                  >
                    <Link
                      href={`/projects/${project.id}`}
                      className="block bg-gray-800/40 hover:bg-gray-800/70 border border-gray-700/50 hover:border-gray-600 rounded-xl p-5 transition-all"
                    >
                      <h3 className="font-medium text-white truncate mb-2">{project.title}</h3>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <SparklesIcon className="h-3.5 w-3.5" /> {project.style}
                        </span>
                        <span className="flex items-center gap-1">
                          <ClockIcon className="h-3.5 w-3.5" /> {project.duration}s
                        </span>
                        <span className="flex items-center gap-1">
                          <FilmIcon className="h-3.5 w-3.5" /> {project.scene_count} scenes
                        </span>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <ErrorBoundary>
        <DashboardContent />
      </ErrorBoundary>
    </AuthGuard>
  )
}
