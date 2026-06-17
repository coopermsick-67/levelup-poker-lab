import { useState } from 'react'
import type { Drill } from '../../types/drill'
import { DRILL_MODULES } from '../../types/drill'
import { createDrillSession } from '../../api/drill'
import DrillCard from './DrillCard'
import DrillSession from './DrillSession'

type View = 'list' | 'active'

export default function DrillLab() {
  const [view, setView] = useState<View>('list')
  const [activeSession, setActiveSession] = useState<{
    sessionId: number
    drills: Drill[]
    drillType: string
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStart = async (moduleId: string) => {
    setLoading(true)
    setError('')
    try {
      const mod = DRILL_MODULES.find((m) => m.id === moduleId)
      const count = mod?.drillCount ?? 10
      const res = await createDrillSession(moduleId, count)
      setActiveSession({
        sessionId: res.session.id,
        drills: res.drills,
        drillType: res.session.drill_type,
      })
      setView('active')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start drill')
    } finally {
      setLoading(false)
    }
  }

  // --- Active session ---
  if (view === 'active' && activeSession) {
    return (
      <DrillSession
        key={activeSession.sessionId}
        sessionId={activeSession.sessionId}
        drills={activeSession.drills}
        drillType={activeSession.drillType}
      />
    )
  }

  // --- Module list ---
  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gold">Drill Lab</h2>
        <p className="text-gray-400 text-sm mt-1">
          Sharpen your decision-making with focused training drills.
        </p>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-2 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-10 text-gray-400">Preparing your drills...</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {DRILL_MODULES.map((mod) => (
          <DrillCard key={mod.id} module={mod} onStart={handleStart} />
        ))}
      </div>

      <div className="mt-8 bg-gray-800 border border-gray-700 rounded-xl p-5">
        <h3 className="text-sm font-bold text-gold mb-2">How Drills Work</h3>
        <ul className="text-sm text-gray-400 space-y-1 list-disc list-inside">
          <li>Each drill presents a poker scenario and asks for your action.</li>
          <li>Choose the best action — you'll get instant feedback.</li>
          <li>Your accuracy is tracked to measure improvement over time.</li>
          <li>Aim for 80%+ to master each module.</li>
        </ul>
      </div>
    </div>
  )
}
