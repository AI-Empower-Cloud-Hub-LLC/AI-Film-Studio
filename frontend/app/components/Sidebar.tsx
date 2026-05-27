'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FilmIcon,
  HomeIcon,
  DocumentTextIcon,
  PhotoIcon,
  VideoCameraIcon,
  MicrophoneIcon,
  PlusCircleIcon,
  CpuChipIcon,
  ArrowRightStartOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  PencilSquareIcon,
  UserGroupIcon,
  MapPinIcon,
  SwatchIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { useAuthStore } from '../../lib/auth-store'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: HomeIcon },
  { href: '/projects', label: 'Projects', icon: FilmIcon },
  { href: '/create', label: 'Create Film', icon: PlusCircleIcon },
  { href: '/scripts', label: 'Scripts', icon: DocumentTextIcon },
  { href: '/screenplay', label: 'Screenplay', icon: PencilSquareIcon },
  { href: '/cast', label: 'Cast', icon: UserGroupIcon },
  { href: '/locations', label: 'Locations', icon: MapPinIcon },
  { href: '/storyboards', label: 'Storyboards', icon: PhotoIcon },
  { href: '/mood-board', label: 'Mood Board', icon: SwatchIcon },
  { href: '/vfx-plan', label: 'VFX Plan', icon: SparklesIcon },
  { href: '/scenes', label: 'Scenes', icon: VideoCameraIcon },
  { href: '/voiceovers', label: 'Voiceovers', icon: MicrophoneIcon },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  return (
    <>
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-800/60">
        <Link href="/" className="flex items-center gap-2 group" onClick={onNavigate}>
          <div className="relative">
            <FilmIcon className="h-7 w-7 text-purple-400 group-hover:text-purple-300 transition-colors" />
            <div className="absolute inset-0 blur-lg bg-purple-400/40 group-hover:bg-purple-300/40 transition-all" />
          </div>
          <span className="text-lg font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            AI Film Studio
          </span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                  ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Agent Status */}
      <div className="px-4 py-3 border-t border-gray-800/60">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
          <CpuChipIcon className="h-4 w-4" />
          <span>10 AI Agents Active</span>
        </div>
      </div>

      {/* User section */}
      {user && (
        <div className="px-4 py-3 border-t border-gray-800/60">
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.full_name || user.username}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-gray-500 hover:text-red-400 rounded-lg transition-colors"
              title="Sign out"
            >
              <ArrowRightStartOnRectangleIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </>
  )
}

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-30 p-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white lg:hidden"
        aria-label="Open menu"
      >
        <Bars3Icon className="h-6 w-6" />
      </button>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 bg-gray-900 border-r border-gray-800/60 flex-col z-20">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 w-64 bg-gray-900 border-r border-gray-800/60 flex flex-col z-50">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-4 p-1 text-gray-400 hover:text-white"
              aria-label="Close menu"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}
    </>
  )
}
