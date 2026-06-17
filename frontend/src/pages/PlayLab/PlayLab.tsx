import { useState, useEffect, useCallback } from 'react'
import { createTable, startHand, applyAction } from '../../api/play'
import type { TableState } from '../../types/game'
import { STREET_NAMES } from '../../types/game'
import TableView from './TableView'
import ActionBar from './ActionBar'
import CoachInsight from './CoachInsight'

export default function PlayLab() {
  const [table, setTable] = useState<TableState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [raiseAmount, setRaiseAmount] = useState(0)

  const initTable = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await createTable()
      setTable(res.table)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create table')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    initTable()
  }, [initTable])

  const handleStartHand = async () => {
    if (!table) return
    setLoading(true)
    setError('')
    try {
      const state = await startHand(table.table_id)
      setTable(state)
      const hero = state.seats.find((s) => s.is_hero)
      if (hero) {
        setRaiseAmount(Math.min(hero.stack, 30))
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start hand')
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (actionType: string, amount?: number) => {
    if (!table) return
    setLoading(true)
    setError('')
    try {
      const result = await applyAction(table.table_id, actionType, amount)
      setTable(result as TableState)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Action failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !table) {
    return <div className="text-center py-20 text-gray-400">Loading table...</div>
  }

  if (!table) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400 mb-4">{error || 'No table active'}</p>
        <button onClick={initTable} className="bg-gold text-gray-900 font-bold px-6 py-2 rounded-lg">
          Create Table
        </button>
      </div>
    )
  }

  const hero = table.seats.find((s) => s.is_hero)
  const streetName = STREET_NAMES[table.current_street] || 'Unknown'

  return (
    <div className="max-w-4xl mx-auto px-2 md:px-0">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-2 mb-4">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-gold">Play Lab</h2>
          <p className="text-xs md:text-sm text-gray-400">
            Hand #{table.hand_number} • {streetName} • Pot: {table.pot}
          </p>
        </div>
        {!table.is_hand_in_progress && (
          <button
            onClick={handleStartHand}
            disabled={loading}
            className="bg-green-600 text-white font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm md:text-base"
          >
            {loading ? 'Starting...' : 'Deal Hand'}
          </button>
        )}
      </div>

      {error && <div className="bg-red-900/50 border border-red-500 text-red-200 px-3 md:px-4 py-2 rounded mb-4 text-sm">{error}</div>}

      <TableView table={table} />

      {table.is_hand_in_progress && table.waiting_for_hero && hero && (
        <ActionBar
          table={table}
          hero={hero}
          raiseAmount={raiseAmount}
          setRaiseAmount={setRaiseAmount}
          onAction={handleAction}
          disabled={loading}
        />
      )}

      {table.hand_complete && (
        <CoachInsight table={table} hero={hero} onNextHand={handleStartHand} />
      )}
    </div>
  )
}
