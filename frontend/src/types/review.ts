export interface PositionStats {
  hands: number
  vpip: number
  pfr: number
}

export interface PokerStats {
  total_hands: number
  total_decisions: number
  vpip: number
  pfr: number
  three_bet_pct: number
  fold_to_3bet_pct: number
  cbet_pct: number
  fold_to_cbet_pct: number
  aggression_factor: number
  wwsf_pct: number
  position_stats: Record<string, PositionStats>
}

export interface Leak {
  description: string
  severity: 'minor' | 'moderate' | 'major'
  category: 'preflop' | 'postflop' | 'positional'
}

export interface ReviewSummary {
  stats: PokerStats
  leaks: Leak[]
}

export interface TrainingDrill {
  name: string
  description: string
  url: string
  reason: string
}

export interface CoachReportData {
  summary: string
  archetype: string
  leaks: Leak[]
  strengths: string[]
  training_plan: TrainingDrill[]
  stats_snapshot: {
    total_hands: number
    vpip: number
    pfr: number
    three_bet_pct: number
    cbet_pct: number
    aggression_factor: number
    wwsf_pct: number
  }
}
