'use client'

import { useEffect, useState } from 'react'
import { CheckIcon, SparklesIcon } from '@heroicons/react/24/outline'
import Sidebar from '../components/Sidebar'
import AuthGuard from '../components/AuthGuard'
import { paymentsApi, type PlanInfo, type SubscriptionInfo } from '../../lib/api'

const PLAN_COLORS: Record<string, string> = {
  free: 'from-gray-500 to-gray-600',
  starter: 'from-blue-500 to-cyan-500',
  professional: 'from-purple-500 to-pink-500',
  enterprise: 'from-orange-500 to-red-500',
}

function PricingContent() {
  const [plans, setPlans] = useState<PlanInfo[]>([])
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [upgrading, setUpgrading] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      paymentsApi.plans().then(setPlans).catch(() => {}),
      paymentsApi.subscription().then(setSubscription).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  const handleCheckout = async (planId: string) => {
    setUpgrading(planId)
    try {
      const res = await paymentsApi.checkout(planId)
      if (res.checkout_url) {
        window.location.href = res.checkout_url
      } else if (res.demo_mode) {
        alert(`Upgraded to ${res.plan} plan (demo mode — Stripe not configured)`)
        paymentsApi.subscription().then(setSubscription).catch(() => {})
      }
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Checkout failed')
    } finally {
      setUpgrading(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="px-8 py-8">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Plans & Pricing</h1>
            <p className="text-gray-500 dark:text-gray-400">Choose the perfect plan for your film production needs</p>
            {subscription && (
              <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-sm text-purple-400">
                <SparklesIcon className="h-4 w-4" />
                Current: <span className="font-semibold capitalize">{subscription.plan}</span> — {subscription.films_used}/{subscription.films_limit === -1 ? 'Unlimited' : subscription.films_limit} films used
              </div>
            )}
          </div>

          {loading ? (
            <div className="text-center py-20 text-gray-400">Loading plans...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
              {plans.map(plan => {
                const isCurrentPlan = subscription?.plan === plan.id
                const gradient = PLAN_COLORS[plan.id] || 'from-gray-500 to-gray-600'
                return (
                  <div key={plan.id} className={`relative bg-white dark:bg-gray-800/60 border rounded-xl p-6 flex flex-col ${isCurrentPlan ? 'border-purple-500 ring-2 ring-purple-500/20' : 'border-gray-200 dark:border-gray-700/50'}`}>
                    {isCurrentPlan && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-purple-500 text-white text-xs font-semibold rounded-full">Current Plan</div>
                    )}
                    <div className={`w-12 h-12 bg-gradient-to-br ${gradient} rounded-xl flex items-center justify-center mb-4`}>
                      <SparklesIcon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">{plan.name}</h3>
                    <div className="mb-4">
                      {plan.price === 0 ? (
                        <span className="text-3xl font-bold text-gray-900 dark:text-white">{plan.id === 'enterprise' ? 'Custom' : 'Free'}</span>
                      ) : (
                        <div>
                          <span className="text-3xl font-bold text-gray-900 dark:text-white">${(plan.price / 100).toFixed(0)}</span>
                          <span className="text-gray-500 dark:text-gray-400">/mo</span>
                        </div>
                      )}
                    </div>
                    <ul className="space-y-2 mb-6 flex-1">
                      {plan.features.map((f, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
                          <CheckIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                    <button
                      onClick={() => !isCurrentPlan && plan.id !== 'enterprise' && handleCheckout(plan.id)}
                      disabled={isCurrentPlan || upgrading === plan.id}
                      className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-all ${
                        isCurrentPlan ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                        : plan.id === 'enterprise' ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        : `bg-gradient-to-r ${gradient} text-white hover:shadow-lg`
                      }`}
                    >
                      {isCurrentPlan ? 'Current Plan' : plan.id === 'enterprise' ? 'Contact Sales' : upgrading === plan.id ? 'Processing...' : 'Upgrade'}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function PricingPage() {
  return <AuthGuard><PricingContent /></AuthGuard>
}
