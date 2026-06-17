import { api } from './client'
import type { TableState } from '../types/game'

export async function createTable(): Promise<{ table_id: string; table: TableState }> {
  return api('/play/tables', { method: 'POST' })
}

export async function startHand(tableId: string): Promise<TableState> {
  return api(`/play/tables/${tableId}/start`, { method: 'POST' })
}

export async function applyAction(
  tableId: string,
  actionType: string,
  amount?: number,
): Promise<TableState & { waiting_for_hero?: boolean; hand_complete?: boolean }> {
  return api(`/play/tables/${tableId}/action`, {
    method: 'POST',
    body: JSON.stringify({ action_type: actionType, amount }),
  })
}

export async function getTable(tableId: string): Promise<TableState> {
  return api(`/play/tables/${tableId}`)
}
