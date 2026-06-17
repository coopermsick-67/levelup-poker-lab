import { api } from './client'
import type { PokerStats, Leak, ReviewSummary, CoachReportData } from '../types/review'

export async function fetchStats(): Promise<PokerStats> {
  return api<PokerStats>('/review/stats')
}

export async function fetchLeaks(): Promise<Leak[]> {
  return api<Leak[]>('/review/leaks')
}

export async function fetchSummary(): Promise<ReviewSummary> {
  return api<ReviewSummary>('/review/summary')
}

export async function fetchCoachReport(): Promise<CoachReportData> {
  return api<CoachReportData>('/review/coach-report')
}
