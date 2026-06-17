import type { TableState, Seat } from '../../types/game'

interface Props {
  table: TableState
  hero: Seat | undefined
  onNextHand: () => void
}

export default function CoachInsight({ table, hero, onNextHand }: Props) {
  const heroWon = table.winner?.seat_index === hero?.index || table.pot_results?.some((pr) =>
    pr.winners.some((w) => w.seat_index === hero?.index),
  )

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mt-4">
      <h3 className="font-bold text-gold mb-2">Hand Complete</h3>

      {table.winner && !table.showdown && (
        <p className="text-gray-300">
          <span className="font-bold text-white">{table.winner.display_name}</span> wins {table.winner.reason === 'all_others_folded' ? '(all others folded)' : ''}
        </p>
      )}

      {table.showdown && table.pot_results && (
        <div className="space-y-2">
          {table.pot_results.map((pr, i) => (
            <div key={i} className="text-sm">
              <span className="text-gold font-bold">{pr.winners.map((w) => w.display_name).join(', ')}</span>
              {' '}wins {pr.pot_amount} with {pr.winning_hand}
            </div>
          ))}
        </div>
      )}

      {hero && (
        <p className={`mt-2 font-bold ${heroWon ? 'text-green-400' : 'text-red-400'}`}>
          {heroWon ? '🎉 You won this hand!' : 'You lost this hand. Keep practicing!'}
        </p>
      )}

      <button
        onClick={onNextHand}
        className="mt-4 bg-green-600 text-white font-bold px-6 py-2 rounded-lg hover:bg-green-700"
      >
        Next Hand
      </button>
    </div>
  )
}
