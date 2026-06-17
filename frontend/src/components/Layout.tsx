import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { isGuest, exitGuestMode } from '../api/auth'

const nav = [
  { to: '/play', label: 'Play' },
  { to: '/drills', label: 'Drills' },
  { to: '/review', label: 'Review' },
  { to: '/profile', label: 'Profile' },
]

export default function Layout() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const guest = isGuest()

  const handleSignOut = () => {
    exitGuestMode()
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/')
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Desktop nav */}
      <nav className="bg-gray-800 border-b border-gray-700 px-4 py-3 hidden md:flex gap-6 items-center">
        <span className="font-bold text-gold text-lg mr-4">🃏 LevelUp Poker Lab</span>
        {nav.map((n) => (
          <Link
            key={n.to}
            to={n.to}
            className={`text-sm font-medium ${pathname === n.to ? 'text-gold' : 'text-gray-400 hover:text-white'}`}
          >
            {n.label}
          </Link>
        ))}
        <div className="ml-auto flex items-center gap-3">
          {guest && (
            <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full border border-gray-600">
              Guest
            </span>
          )}
          <button
            onClick={handleSignOut}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            {guest ? 'Exit Guest' : 'Sign Out'}
          </button>
        </div>
      </nav>

      {/* Mobile header */}
      <div className="md:hidden bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <span className="font-bold text-gold text-lg">🃏 LevelUp Poker Lab</span>
        <div className="flex items-center gap-2">
          {guest && (
            <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded-full border border-gray-600">
              Guest
            </span>
          )}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="text-gray-400 hover:text-white p-1"
            aria-label="Toggle menu"
          >
            {mobileOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden bg-gray-800 border-b border-gray-700 px-4 pb-3 flex flex-col gap-1">
          {nav.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              onClick={() => setMobileOpen(false)}
              className={`text-sm font-medium py-2 px-3 rounded-md ${
                pathname === n.to
                  ? 'text-gold bg-gray-700'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              {n.label}
            </Link>
          ))}
          <button
            onClick={() => { handleSignOut(); setMobileOpen(false) }}
            className="text-sm font-medium py-2 px-3 rounded-md text-gray-500 hover:text-gray-300 text-left"
          >
            {guest ? 'Exit Guest' : 'Sign Out'}
          </button>
        </div>
      )}

      <main className="flex-1 p-2 md:p-4">
        <Outlet />
      </main>
    </div>
  )
}
