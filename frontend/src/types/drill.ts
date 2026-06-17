export interface DrillOption {
  action: string
  label: string
}

export interface Drill {
  id: string
  position?: string
  stack_depth?: number
  action_so_far?: string
  situation?: string
  board?: string[]
  options: DrillOption[]
  correct_action: string
  feedback_good: string
  feedback_ok: string
  feedback_poor: string
}


export interface DrillSessionResponse {
  session: {
    id: number
    user_id: number
    drill_type: string
    total_questions: number
    created_at: string | null
  }
  drills: Drill[]
}

export interface AnswerResponse {
  session_id: number
  drill_id: string
  user_answer: string
  user_answer_label: string
  correct_action: string
  correct: boolean
  feedback: string
  situation: string
  board: string
  attempt_id?: number
}

export interface SessionResults {
  session_id: number
  user_id: number
  drill_type: string
  total_questions: number
  answered: number
  correct: number
  accuracy: number
  created_at: string
  attempts: Array<{
    session_id: number
    user_id: number
    drill_id: string
    user_answer: string
    correct: boolean
    feedback: string
    created_at: string
  }>
}

export interface DrillModule {
  id: string
  title: string
  description: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  estimatedMinutes: number
  icon: string
  drillCount: number
}

export const DRILL_MODULES: DrillModule[] = [
  {
    id: 'preflop',
    title: 'Preflop Fundamentals',
    description: 'Master open raises, 3-bets, and position play before the flop.',
    difficulty: 'Beginner',
    estimatedMinutes: 5,
    icon: '🎯',
    drillCount: 10,
  },
  {
    id: 'postflop',
    title: 'Postflop Play',
    description: 'C-bets, barrels, value bets, and bluff-catching on wet and dry boards.',
    difficulty: 'Intermediate',
    estimatedMinutes: 8,
    icon: '🃏',
    drillCount: 10,
  },
]
