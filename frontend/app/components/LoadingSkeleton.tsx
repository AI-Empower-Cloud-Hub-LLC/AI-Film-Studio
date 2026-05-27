'use client'

export function SkeletonCard() {
  return (
    <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-5 animate-pulse">
      <div className="h-4 bg-gray-700 rounded w-3/4 mb-3" />
      <div className="h-3 bg-gray-700 rounded w-1/2 mb-2" />
      <div className="h-3 bg-gray-700 rounded w-1/3" />
    </div>
  )
}

export function SkeletonStat() {
  return (
    <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-5 animate-pulse">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 bg-gray-700 rounded-lg" />
        <div className="h-3 bg-gray-700 rounded w-20" />
      </div>
      <div className="h-6 bg-gray-700 rounded w-12" />
    </div>
  )
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-700 rounded-lg flex-shrink-0" />
            <div className="flex-1">
              <div className="h-4 bg-gray-700 rounded w-2/3 mb-2" />
              <div className="h-3 bg-gray-700 rounded w-1/3" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
