import type { TableState, Seat } from '../../types/game'

interface Props {
  table: TableState
  hero: Seat
  raiseAmount: number
  setRaiseAmount: (n: number) => void
  onAction: (action: string, amount?: number) => void
  disabled: boolean
}

export default function ActionBar({ table, hero, raiseAmount, setRaiseAmount, onAction, disabled }: Props) {
  const canAct = table.legal_actions
  const highestBet = Math.max(...table.seats.map((s) => s.current_bet))
  const toCall = highestBet - hero.current_bet

  return (
    <div className="bg-gray-800 rounded-xl p-3 md:p-4 border border-gray-700">
      <div className="flex gap-2 flex-wrap justify-center">
        {canAct.includes('fold') && (
          <button
            onClick={() => onAction('fold')}
            disabled={disabled}
            className="bg-red-700 text-white font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-red-800 disabled:opacity-50 text-sm md:text-base flex-1 md:flex-none"
          >
            Fold
          </button>
        )}
        {canAct.includes('check') && (
          <button
            onClick={() => onAction('check')}
            disabled={disabled}
            className="bg-blue-700 text-white font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-blue-800 disabled:opacity-50 text-sm md:text-base flex-1 md:flex-none"
          >
            Check
          </button>
        )}
        {canAct.includes('call') && (
          <button
            onClick={() => onAction('call')}
            disabled={disabled}
            className="bg-green-700 text-white font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-green-800 disabled:opacity-50 text-sm md:text-base flex-1 md:flex-none"
          >
            Call {toCall}
          </button>
        )}
        {canAct.includes('raise') && (
          <div className="flex items-center gap-2 w-full md:w-auto justify-center">
            <input
              type="range"
              min={Math.min(hero.stack, highestBet * 2 || 20)}
              max={hero.stack}
              value={Math.min(raiseAmount, hero.stack)}
              onChange={(e) => setRaiseAmount(Number(e.target.value))}
              className="w-20 md:w-24"
            />
            <button
              onClick={() => onAction('raise', Math.min(raiseAmount, hero.stack))}
              disabled={disabled}
              className="bg-gold text-gray-900 font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-gold-dark disabled:opacity-50 text-sm md:text-base"
            >
              Raise {Math.min(raiseAmount, hero.stack)}
            </button>
          </div>
        )}
        {canAct.includes('all_in') && (
          <button
            onClick={() => onAction('all_in')}
            disabled={disabled}
            className="bg-purple-700 text-white font-bold px-4 md:px-6 py-2 rounded-lg hover:bg-purple-800 disabled:opacity-50 text-sm md:text-base flex-1 md:flex-none"
          >
            All-In ({hero.stack})
          </button>
        )}
      </div>
    </div>
  )
}
