export interface Seat {
  index: number
  display_name: string
  stack: number
  status: string
  current_bet: number
  total_hand_bet: number
  is_hero: boolean
  is_bot: boolean
  hole_cards: string[]
}

export interface TableState {
  table_id: string
  seats: Seat[]
  community_cards: string[]
  pot: number
  button_index: number
  current_street: number
  active_seat_index: number
  hand_number: number
  is_hand_in_progress: boolean
  hero_seat_index: number
  legal_actions: string[]
  waiting_for_hero: boolean
  hand_complete: boolean
  winner: { seat_index: number; display_name: string; reason: string } | null
  showdown: boolean
  pot_results: Array<{
    pot_amount: number
    winners: Array<{ seat_index: number; display_name: string }>
    winning_hand: string
  }>
}

export const STREET_NAMES = ['Preflop', 'Flop', 'Turn', 'River', 'Showdown']
