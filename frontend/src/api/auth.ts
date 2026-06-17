import { api } from './client'

export async function register(displayName: string, username: string, password: string) {
  return api<{ access_token: string; user: { id: number; display_name: string; username: string; level: number; xp: number; streak: number; skill_rating: number } }>(
    '/auth/register',
    { method: 'POST', body: JSON.stringify({ display_name: displayName, username, password }) },
  )
}

export async function login(username: string, password: string) {
  return api<{ access_token: string; user: { id: number; display_name: string; username: string; level: number; xp: number; streak: number; skill_rating: number } }>(
    '/auth/login',
    { method: 'POST', body: JSON.stringify({ username, password }) },
  )
}

export function isLoggedIn(): boolean {
  return !!localStorage.getItem('access_token')
}

export function isGuest(): boolean {
  return localStorage.getItem('guest_mode') === '1'
}

/** Enter guest mode — clears any auth tokens, sets guest flag. */
export function enterGuestMode(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  localStorage.setItem('guest_mode', '1')
}

/** Exit guest mode — clears guest flag. */
export function exitGuestMode(): void {
  localStorage.removeItem('guest_mode')
}

/** Whether the current session is usable (logged in OR guest). */
export function hasSession(): boolean {
  return isLoggedIn() || isGuest()
}
