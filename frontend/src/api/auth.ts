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
