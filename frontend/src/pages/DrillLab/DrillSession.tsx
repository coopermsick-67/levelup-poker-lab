import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import type { AnswerResponse, Drill, SessionResults } from '../../types/drill'
import { submitDrillAnswer, getDrillResults } from '../../api/drill'
import DrillFeedback from './DrillFeedback'

interface Props {
  sessionId: number
  drills: Drill[]
  drillType: string
}

export default function DrillSession({ sessionId, drills, drillType }: Props) {
  const navigate = useNavigate()
  const [index, setIndex] = useState(0)
  const [result, setResult] = useState<AnswerResponse | null>(null)
  const [results, setResults] = useState<SessionResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const current = drills[index]
  const total = drills.length
  const progress = Math.round((index / total) * 100)

  const fetchResults = useCallback(async () => {
    try {
      const r = await getDrillResults(sessionId)
      setResults(r)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load results')
    }
  }, [sessionId])

  useEffect(() => {
    if (index >= total) {
      fetchResults()
    }
  }, [index, total, fetchResults])

  const handleAnswer = async (action: string) => {
    if (!current || loading) return
    setLoading(true)
    setError('')
    try {
      const res = await submitDrillAnswer(sessionId, current.id, action)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to submit answer')
    } finally {
      setLoading(false)
    }
  }

  const handleNext = () => {
    setResult(null)
    setError('')
    setIndex((i) => i + 1)
  }

  // --- Results screen ---
  if (results || index >= total) {
    const r = results ?? {
      session_id: sessionId,
      correct: 0,
      answered: index,
      total_questions: total,
      accuracy: 0,
      drill_type: drillType,
    }
    const pct = r.answered > 0 ? Math.round((r.correct / r.answered) * 100) : 0
    const grade =
      pct >= 80 ? 'Excellent' : pct >= 60 ? 'Good' : pct >= 40 ? 'Needs Work' : 'Keep Studying'
    const gradeColor =
      pct >= 80
        ? 'text-green-400'
        : pct >= 60
          ? 'text-yellow-400'
          : pct >= 40
            ? 'text-orange-400'
            : 'text-red-400'

    return (
      <div className="max-w-lg mx-auto">
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 text-center">
          <h2 className="text-2xl font-bold text-gold mb-2">Session Complete</h2>
          <p className={`text-4xl font-black ${gradeColor} my-4`}>{pct}%</p>
          <p className="text-gray-400">
            {r.correct} / {r.answered} correct
          </p>
          <p className={`text-lg font-bold mt-2 ${gradeColor}`}>{grade}</p>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => navigate('/drills')}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition-colors"
            >
              Back to Drills
            </button>
            <button
              onClick={() => navigate('/play')}
              className="flex-1 bg-felt hover:bg-felt-dark text-white font-bold py-3 rounded-lg transition-colors"
            >
              Play a Hand
            </button>
          </div>
        </div>
      </div>
    )
  }

  // --- Active drill screen ---
  const situation = current.situation ?? current.action_so_far ?? ''
  const board = current.board ?? []
  const isPreflop = drillType === 'preflop'

  return (
    <div className="max-w-lg mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gold capitalize">{drillType} Drill</h2>
          <p className="text-xs text-gray-500">
            {index + 1} of {total}
          </p>
        </div>
        <button
          onClick={() => navigate('/drills')}
          className="text-sm text-gray-500 hover:text-white"
        >
          ✕ Quit
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-700 rounded-full h-2 mb-6">
        <div
          className="bg-gold h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Scenario card */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
        {/* Position badge */}
        {isPreflop && current.position && (
          <div className="flex items-center gap-2 mb-3">
            <span className="bg-felt text-white text-xs font-bold px-2 py-1 rounded">
              {current.position}
            </span>
            {current.stack_depth && (
              <span className="bg-gray-700 text-gray-300 text-xs font-bold px-2 py-1 rounded">
                {current.stack_depth}bb
              </span>
            )}
          </div>
        )}

        {/* Board (postflop) */}
        {!isPreflop && board.length > 0 && (
          <div className="flex gap-1 mb-4 justify-center">
            {board.map((card, i) => (
              <span
                key={i}
                className="inline-block bg-white text-gray-900 font-bold text-sm px-2 py-1 rounded border border-gray-300 min-w-[2rem] text-center"
              >
                {card}
              </span>
            ))}
          </div>
        )}

        {/* Situation text */}
        <p className="text-gray-200 leading-relaxed mb-5">{situation}</p>

        {/* Error */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-3 py-2 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Answer buttons */}
        {!result && (
          <div className="flex flex-col gap-2">
            {current.options.map((opt) => (
              <button
                key={opt.action + opt.label}
                onClick={() => handleAnswer(opt.action)}
                disabled={loading}
                className="w-full bg-gray-700 hover:bg-felt border border-gray-600 hover:border-gold text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 text-left"
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Feedback */}
        {result && (
          <DrillFeedback
            result={result}
            onNext={handleNext}
            isLast={index === total - 1}
          />
        )}
      </div>
    </div>
  )
}
