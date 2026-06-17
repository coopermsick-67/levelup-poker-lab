import type { TableState } from '../../types/game'

const SEAT_POSITIONS = [
  'bottom-0 left-1/2 -translate-x-1/2',     // 0: bottom center (hero)
  'bottom-0 left-2 md:left-4',               // 1: bottom left
  'top-0 left-2 md:left-4',                  // 2: top left
  'top-0 left-1/2 -translate-x-1/2',         // 3: top center
  'top-0 right-2 md:right-4',                // 4: top right
  'bottom-0 right-2 md:right-4',             // 5: bottom right
]

function CardDisplay({ cards, faceDown }: { cards: string[]; faceDown?: boolean }) {
  if (faceDown || cards.length === 0) {
    return (
      <div className="flex gap-0.5">
        <div className="w-6 h-8 md:w-8 md:h-11 bg-blue-800 rounded border border-blue-600" />
        <div className="w-6 h-8 md:w-8 md:h-11 bg-blue-800 rounded border border-blue-600" />
      </div>
    )
  }
  return (
    <div className="flex gap-0.5">
      {cards.map((c, i) => (
        <div
          key={i}
          className="w-6 h-8 md:w-8 md:h-11 bg-white rounded border border-gray-300 flex items-center justify-center text-[10px] md:text-xs font-bold text-gray-900"
        >
          {c}
        </div>
      ))}
    </div>
  )
}

export default function TableView({ table }: { table: TableState }) {
  return (
    <div className="relative bg-felt-dark rounded-2xl border-4 border-yellow-900 h-64 md:h-80 mb-4 overflow-hidden">
      {/* Community cards */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1 md:gap-2">
        <div className="flex gap-1">
          {table.community_cards.length === 0 ? (
            <div className="text-gray-500 text-xs md:text-sm">No community cards yet</div>
          ) : (
            table.community_cards.map((c, i) => (
              <div
                key={i}
                className="w-8 h-10 md:w-10 md:h-14 bg-white rounded border border-gray-300 flex items-center justify-center text-xs md:text-sm font-bold text-gray-900"
              >
                {c}
              </div>
            ))
          )}
        </div>
        <div className="text-gold font-bold text-sm md:text-lg">Pot: {table.pot}</div>
      </div>

      {/* Seats */}
      {table.seats.map((seat) => {
        const pos = SEAT_POSITIONS[seat.index] || ''
        const isActive = table.active_seat_index === seat.index && table.is_hand_in_progress
        const isButton = table.button_index === seat.index
        const showCards = seat.is_hero || (table.showdown && seat.hole_cards.length > 0)

        return (
          <div
            key={seat.index}
            className={`absolute ${pos} flex flex-col items-center gap-0.5 md:gap-1 transition-all ${isActive ? 'scale-105 md:scale-110' : ''}`}
          >
            <div
              className={`px-2 md:px-3 py-1 md:py-1.5 rounded-lg text-center min-w-14 md:min-w-20 ${
                seat.status === 'folded'
                  ? 'bg-gray-800 opacity-50'
                  : isActive
                  ? 'bg-yellow-600 ring-2 ring-yellow-400'
                  : 'bg-gray-800'
              }`}
            >
              <div className="text-[10px] md:text-xs font-bold text-white truncate">{seat.display_name}</div>
              <div className="text-[10px] md:text-xs text-gray-300">{seat.stack}</div>
              {seat.current_bet > 0 && (
                <div className="text-[10px] md:text-xs text-gold">Bet: {seat.current_bet}</div>
              )}
            </div>
            {isButton && (
              <div className="w-4 h-4 md:w-6 md:h-6 bg-white rounded-full flex items-center justify-center text-[8px] md:text-xs font-bold text-gray-900">
                D
              </div>
            )}
            <CardDisplay cards={seat.hole_cards} faceDown={!showCards} />
          </div>
        )
      })}
    </div>
  )
}
