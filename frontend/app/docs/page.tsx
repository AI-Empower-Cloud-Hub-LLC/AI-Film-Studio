'use client'

import { useState } from 'react'
import Sidebar from '../components/Sidebar'
import { BookOpenIcon, ServerIcon, RocketLaunchIcon } from '@heroicons/react/24/outline'

type Tab = 'user' | 'api' | 'deploy'

function UserGuide() {
  return (
    <div className="space-y-6 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Getting Started</h2>
        <ol className="list-decimal pl-5 space-y-2">
          <li><strong>Register</strong> an account at the login page with your email, username, and password.</li>
          <li>After logging in, you will be redirected to the <strong>Dashboard</strong>.</li>
          <li>Click <strong>Create Film</strong> to start generating your first AI film.</li>
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Creating a Film</h2>
        <ol className="list-decimal pl-5 space-y-2">
          <li>Enter a <strong>prompt</strong> describing your film concept.</li>
          <li>Select a <strong>style</strong> (cinematic, documentary, music video, animation, commercial).</li>
          <li>Set the <strong>duration</strong> in seconds (10-300).</li>
          <li>Click <strong>Generate Film</strong> and watch the 10-agent pipeline process your film.</li>
          <li>The pipeline runs through: Director &rarr; Screenwriter &rarr; Screenplay Refinement &rarr; Cinematographer + Sound Designer + Cast + Locations (parallel) &rarr; VFX Planning + Mood Board (parallel) &rarr; Editor.</li>
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Managing Projects</h2>
        <ul className="list-disc pl-5 space-y-2">
          <li>View all projects from the <strong>Projects</strong> page.</li>
          <li>Use the <strong>search bar</strong> and <strong>status filter</strong> to find specific projects.</li>
          <li>Click a project to see full details: scenes, scripts, cast, locations, VFX plan, and mood board.</li>
          <li><strong>Edit</strong> a project title inline or <strong>delete</strong> projects you no longer need.</li>
          <li><strong>Download</strong> project assets as a ZIP bundle or individual files (PDF, TXT, JSON).</li>
          <li><strong>Attach</strong> your own files (scripts, images, audio) to projects.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Pipeline Pages</h2>
        <ul className="list-disc pl-5 space-y-2">
          <li><strong>Screenplay</strong> &mdash; Refined scenes with slug lines, camera directions, and production notes.</li>
          <li><strong>Cast</strong> &mdash; Character descriptions, casting sheets, and budget estimates.</li>
          <li><strong>Locations</strong> &mdash; Filming location suggestions with logistics and budget breakdowns.</li>
          <li><strong>Mood Board</strong> &mdash; Style guides, color palettes, and reference images.</li>
          <li><strong>VFX Plan</strong> &mdash; VFX shot breakdowns with techniques and cost estimates.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Account Settings</h2>
        <ul className="list-disc pl-5 space-y-2">
          <li>Update your profile (name, username, avatar) from the <strong>Profile</strong> page.</li>
          <li>Change your password from the Profile page.</li>
          <li>Toggle between <strong>dark</strong> and <strong>light</strong> mode using the sun/moon icon in the sidebar.</li>
        </ul>
      </section>
    </div>
  )
}

function ApiDocs() {
  const endpoints = [
    { method: 'POST', path: '/api/v1/auth/register', desc: 'Register a new user account' },
    { method: 'POST', path: '/api/v1/auth/login', desc: 'Log in and receive JWT tokens' },
    { method: 'POST', path: '/api/v1/auth/refresh', desc: 'Refresh access token' },
    { method: 'GET', path: '/api/v1/auth/me', desc: 'Get current user profile' },
    { method: 'PUT', path: '/api/v1/auth/me', desc: 'Update user profile (name, username, avatar)' },
    { method: 'POST', path: '/api/v1/auth/change-password', desc: 'Change password' },
    { method: 'POST', path: '/api/v1/auth/forgot-password', desc: 'Send password reset email' },
    { method: 'POST', path: '/api/v1/auth/reset-password', desc: 'Reset password with token' },
    { method: 'POST', path: '/api/v1/autonomous/create-film', desc: 'Create a new film (runs 10-agent pipeline)' },
    { method: 'GET', path: '/api/v1/autonomous/projects', desc: 'List projects (paginated, search, filter)' },
    { method: 'GET', path: '/api/v1/autonomous/projects/:id', desc: 'Get project details with all data' },
    { method: 'PATCH', path: '/api/v1/autonomous/projects/:id', desc: 'Update project title/style/duration' },
    { method: 'DELETE', path: '/api/v1/autonomous/projects/:id', desc: 'Delete project and all related data' },
    { method: 'GET', path: '/api/v1/autonomous/agent-status', desc: 'Get status of all 10 AI agents' },
    { method: 'GET', path: '/api/v1/autonomous/graph', desc: 'Get LangGraph pipeline topology' },
    { method: 'GET', path: '/api/v1/autonomous/pipeline-history', desc: 'Get pipeline run history' },
    { method: 'GET', path: '/api/v1/autonomous/admin/stats', desc: 'Admin dashboard statistics (admin only)' },
    { method: 'POST', path: '/api/v1/attachments/:project_id', desc: 'Upload file attachment' },
    { method: 'GET', path: '/api/v1/attachments/:project_id', desc: 'List attachments (paginated)' },
    { method: 'GET', path: '/api/v1/attachments/:project_id/:id/download', desc: 'Download attachment' },
    { method: 'DELETE', path: '/api/v1/attachments/:project_id/:id', desc: 'Delete attachment' },
    { method: 'GET', path: '/api/v1/exports/zip/:project_id', desc: 'Download all assets as ZIP' },
    { method: 'GET', path: '/api/v1/exports/pdf/:project_id', desc: 'Download script as PDF' },
    { method: 'GET', path: '/api/v1/exports/screenplay/:project_id', desc: 'Download screenplay as TXT' },
  ]

  const methodColors: Record<string, string> = {
    GET: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    POST: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    PUT: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    PATCH: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    DELETE: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  }

  return (
    <div className="space-y-4 text-sm">
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        FastAPI auto-generates interactive Swagger docs at <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-purple-600 dark:text-purple-400">/docs</code> and ReDoc at <code className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-purple-600 dark:text-purple-400">/redoc</code> (disabled in production).
      </p>

      <div className="space-y-2">
        {endpoints.map((ep, i) => (
          <div key={i} className="flex items-center gap-3 bg-white dark:bg-gray-800/40 border border-gray-200 dark:border-gray-700/50 rounded-lg px-4 py-2.5">
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${methodColors[ep.method]}`}>{ep.method}</span>
            <code className="text-xs text-gray-800 dark:text-gray-200 font-mono flex-1 truncate">{ep.path}</code>
            <span className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">{ep.desc}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function DeployGuide() {
  return (
    <div className="space-y-6 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Prerequisites</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>Docker and Docker Compose installed</li>
          <li>Node.js 18+ (for frontend development)</li>
          <li>Python 3.11+ (for backend development)</li>
          <li>PostgreSQL 16 (production) or SQLite (development)</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Quick Start (Development)</h2>
        <div className="bg-gray-900 dark:bg-gray-800 rounded-lg p-4 font-mono text-xs text-green-400 space-y-1 overflow-x-auto">
          <p># Clone the repository</p>
          <p>git clone https://github.com/AI-Cloud-Tech-Inc/AI-Film-Studio.git</p>
          <p>cd AI-Film-Studio</p>
          <p>&nbsp;</p>
          <p># Backend setup</p>
          <p>cd backend</p>
          <p>python -m venv venv && source venv/bin/activate</p>
          <p>pip install -r requirements.txt</p>
          <p>cp .env.example .env</p>
          <p>uvicorn main:app --reload --port 8000</p>
          <p>&nbsp;</p>
          <p># Frontend setup (new terminal)</p>
          <p>cd frontend</p>
          <p>npm install && npm run dev</p>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Docker Compose (Production)</h2>
        <div className="bg-gray-900 dark:bg-gray-800 rounded-lg p-4 font-mono text-xs text-green-400 space-y-1 overflow-x-auto">
          <p># Copy and configure environment variables</p>
          <p>cp .env.example .env</p>
          <p># Edit .env with production values (SECRET_KEY, DATABASE_URL, API keys)</p>
          <p>&nbsp;</p>
          <p># Build and start all services</p>
          <p>docker-compose up -d --build</p>
          <p>&nbsp;</p>
          <p># Services: nginx(:80), backend(:8000), frontend(:3000), postgres(:5432)</p>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Environment Variables</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 pr-4 text-gray-900 dark:text-white">Variable</th>
                <th className="text-left py-2 pr-4 text-gray-900 dark:text-white">Description</th>
                <th className="text-left py-2 text-gray-900 dark:text-white">Required</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">SECRET_KEY</td><td className="py-1.5 pr-4">JWT signing secret</td><td className="py-1.5">Yes</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">DATABASE_URL</td><td className="py-1.5 pr-4">PostgreSQL connection string</td><td className="py-1.5">Production</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">ANTHROPIC_API_KEY</td><td className="py-1.5 pr-4">Claude API key</td><td className="py-1.5">Optional</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">GOOGLE_AI_API_KEY</td><td className="py-1.5 pr-4">Google Gemini API key</td><td className="py-1.5">Optional</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">ELEVENLABS_API_KEY</td><td className="py-1.5 pr-4">ElevenLabs TTS key</td><td className="py-1.5">Optional</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">RUNWAY_API_KEY</td><td className="py-1.5 pr-4">Runway Gen-4 video key</td><td className="py-1.5">Optional</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">CORS_ORIGINS</td><td className="py-1.5 pr-4">Allowed CORS origins</td><td className="py-1.5">Production</td></tr>
              <tr><td className="py-1.5 pr-4 font-mono text-purple-600 dark:text-purple-400">SENTRY_DSN</td><td className="py-1.5 pr-4">Sentry error monitoring</td><td className="py-1.5">Optional</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">GCP Deployment</h2>
        <ol className="list-decimal pl-5 space-y-2">
          <li>Create a GCP project and enable Cloud Run, Cloud SQL, and Artifact Registry APIs.</li>
          <li>Set up Cloud SQL (PostgreSQL 16) and note the connection string.</li>
          <li>Push Docker images to Artifact Registry.</li>
          <li>Deploy backend and frontend as Cloud Run services.</li>
          <li>Configure Cloud Run environment variables with production secrets.</li>
          <li>Set up a load balancer with SSL certificate for your domain.</li>
        </ol>
      </section>
    </div>
  )
}

export default function DocsPage() {
  const [tab, setTab] = useState<Tab>('user')

  const tabs: { key: Tab; label: string; icon: typeof BookOpenIcon }[] = [
    { key: 'user', label: 'User Guide', icon: BookOpenIcon },
    { key: 'api', label: 'API Reference', icon: ServerIcon },
    { key: 'deploy', label: 'Deployment', icon: RocketLaunchIcon },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="max-w-4xl mx-auto px-4 sm:px-8 py-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-6">Documentation</h1>

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 mb-8">
            {tabs.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
                  tab === t.key
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                <t.icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            ))}
          </div>

          {tab === 'user' && <UserGuide />}
          {tab === 'api' && <ApiDocs />}
          {tab === 'deploy' && <DeployGuide />}
        </div>
      </div>
    </div>
  )
}
