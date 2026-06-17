import { api } from './client'
import type { AnswerResponse, DrillSessionResponse, SessionResults } from '../types/drill'

export async function createDrillSession(
  drillType: string,
  count: number,
): Promise<DrillSessionResponse> {
  return api('/drills/session', {
    method: 'POST',
    body: JSON.stringify({ drill_type: drillType, count }),
  })
}

export async function submitDrillAnswer(
  sessionId: number,
  drillId: string,
  answer: string,
): Promise<AnswerResponse> {
  return api('/drills/answer', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      drill_id: drillId,
      answer,
    }),
  })
}

export async function getDrillResults(sessionId: number): Promise<SessionResults> {
  return api(`/drills/session/${sessionId}/results`)
}
