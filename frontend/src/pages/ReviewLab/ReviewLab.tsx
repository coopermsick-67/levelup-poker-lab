import { useEffect, useState, useCallback } from 'react'
import { fetchSummary, fetchCoachReport } from '../../api/review'
import type { PokerStats, Leak, ReviewSummary, CoachReportData, TrainingDrill } from '../../types/review'

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function severityBadge(severity: Leak['severity']) {
  const map: Record<Leak['severity'], { bg: string; text: string; label: string }> = {
    minor:    { bg: 'bg-blue-500/20',  text: 'text-blue-400',  label: 'Minor' },
    moderate: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Moderate' },
    major:    { bg: 'bg-red-500/20',   text: 'text-red-400',   label: 'Major' },
  }
  const s = map[severity]
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  )
}

function categoryBadge(category: Leak['category']) {
  const color: Record<Leak['category'], string> = {
    preflop:   'text-purple-400',
    postflop:  'text-green-400',
    positional: 'text-orange-400',
  }
  return (
    <span className={`text-xs font-medium uppercase tracking-wide ${color[category]}`}>
      {category}
    </span>
  )
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wider text-gray-400">{label}</span>
      <span className="text-2xl font-bold text-white">{value}</span>
      {hint && <span className="text-xs text-gray-500">{hint}</span>}
    </div>
  )
}

function StatCards({ stats }: { stats: PokerStats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      <StatCard label="VPIP"     value={`${stats.vpip}%`}     hint="Voluntarily put $" />
      <StatCard label="PFR"      value={`${stats.pfr}%`}      hint="Preflop raise" />
      <StatCard label="3-Bet"    value={`${stats.three_bet_pct}%`} hint="Re-raise preflop" />
      <StatCard label="Fold 3B"  value={`${stats.fold_to_3bet_pct}%`} hint="Fold to 3-bet" />
      <StatCard label="C-Bet"    value={`${stats.cbet_pct}%`}  hint="Continuation bet" />
      <StatCard label="Fold cB"  value={`${stats.fold_to_cbet_pct}%`} hint="Fold to c-bet" />
      <StatCard label="Agg Fact" value={stats.aggression_factor} hint="(bets+raises)/calls" />
      <StatCard label="WWSF"     value={`${stats.wwsf_pct}%`}  hint="Won when saw flop" />
    </div>
  )
}

function PositionTable({ stats }: { stats: PokerStats }) {
  const positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          Position Breakdown
        </h3>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 text-xs uppercase tracking-wider">
            <th className="px-4 py-2 text-left">Pos</th>
            <th className="px-4 py-2 text-right">Hands</th>
            <th className="px-4 py-2 text-right">VPIP</th>
            <th className="px-4 py-2 text-right">PFR</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((pos) => {
            const ps = stats.position_stats[pos] ?? { hands: 0, vpip: 0, pfr: 0 }
            return (
              <tr key={pos} className="border-t border-gray-700/50 hover:bg-gray-750">
                <td className="px-4 py-2 font-medium text-white">{pos}</td>
                <td className="px-4 py-2 text-right text-gray-300">{ps.hands}</td>
                <td className="px-4 py-2 text-right text-gray-300">{ps.vpip}%</td>
                <td className="px-4 py-2 text-right text-gray-300">{ps.pfr}%</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function LeakList({ leaks }: { leaks: Leak[] }) {
  if (leaks.length === 0) {
    return (
      <p className="text-gray-500 text-center py-8">
        No leaks detected yet. Play more hands to get analysis.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {leaks.map((leak, i) => (
        <div
          key={i}
          className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-2"
        >
          <div className="flex items-center gap-2 flex-wrap">
            {severityBadge(leak.severity)}
            {categoryBadge(leak.category)}
          </div>
          <p className="text-gray-300 text-sm leading-relaxed">{leak.description}</p>
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Coach Report                                                       */
/* ------------------------------------------------------------------ */

const ARCHETYPE_LABELS: Record<string, { label: string; color: string }> = {
  nit:     { label: 'Nit (Tight-Passive)',   color: 'text-blue-400' },
  tag:     { label: 'TAG (Tight-Aggressive)', color: 'text-green-400' },
  lag:     { label: 'LAG (Loose-Aggressive)',  color: 'text-yellow-400' },
  maniac:  { label: 'Maniac (Loose-Passive)',  color: 'text-red-400' },
  default: { label: 'Developing',             color: 'text-gray-400' },
  unknown: { label: 'Unknown',                color: 'text-gray-500' },
}

function CoachReportSection({ report }: { report: CoachReportData }) {
  const arch = ARCHETYPE_LABELS[report.archetype] ?? ARCHETYPE_LABELS.default

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span className="text-gold">AI Coach Report</span>
        </h2>
        <span className={`text-sm font-medium ${arch.color}`}>
          {arch.label}
        </span>
      </div>

      {/* Summary card */}
      <div className="bg-gradient-to-br from-felt/30 to-gray-800 border border-felt/50 rounded-xl p-6">
        <p className="text-gray-200 leading-relaxed text-base">{report.summary}</p>
      </div>

      {/* Strengths */}
      {report.strengths.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">
            Strengths
          </h3>
          <ul className="space-y-2">
            {report.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-green-400 mt-0.5 flex-shrink-0">&#10003;</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Training Plan */}
      {report.training_plan.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gold uppercase tracking-wider mb-4">
            Training Plan
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {report.training_plan.map((drill: TrainingDrill, i: number) => (
              <div
                key={i}
                className="bg-gray-900 border border-gray-600 rounded-lg p-4 flex flex-col gap-2"
              >
                <h4 className="font-semibold text-white text-sm">{drill.name}</h4>
                <p className="text-xs text-gray-400 leading-relaxed">{drill.description}</p>
                <p className="text-xs text-gold/80 italic">{drill.reason}</p>
                <a
                  href={drill.url}
                  className="mt-auto inline-block bg-felt text-white text-xs font-bold px-4 py-1.5 rounded-lg hover:bg-felt/80 transition-colors text-center"
                >
                  Start Drill
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function ReviewLab() {
  const [data, setData] = useState<ReviewSummary | null>(null)
  const [coachReport, setCoachReport] = useState<CoachReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [summary, coach] = await Promise.all([
        fetchSummary(),
        fetchCoachReport().catch(() => null),
      ])
      setData(summary)
      setCoachReport(coach)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load review data'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Review Lab</h1>
        <p className="text-gray-400 mt-1">
          Analyze your play, find leaks, and track improvement over time.
        </p>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-20">
          <div className="inline-block w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-4">Analyzing your hands...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Content */}
      {!loading && !error && data && (
        <>
          {/* AI Coach Report */}
          {coachReport && <CoachReportSection report={coachReport} />}

          {/* Overview */}
          <section className="space-y-4">
            <div className="flex items-baseline justify-between">
              <h2 className="text-xl font-semibold text-white">Stats Overview</h2>
              <span className="text-xs text-gray-500">
                {data.stats.total_hands} hands analyzed
              </span>
            </div>
            <StatCards stats={data.stats} />
          </section>

          {/* Position breakdown */}
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-white">By Position</h2>
            <PositionTable stats={data.stats} />
          </section>

          {/* Leaks */}
          <section className="space-y-4">
            <div className="flex items-baseline justify-between">
              <h2 className="text-xl font-semibold text-white">Detected Leaks</h2>
              <span className="text-xs text-gray-500">
                {data.leaks.length} issue{data.leaks.length !== 1 ? 's' : ''} found
              </span>
            </div>
            <LeakList leaks={data.leaks} />
          </section>
        </>
      )}
    </div>
  )
}
