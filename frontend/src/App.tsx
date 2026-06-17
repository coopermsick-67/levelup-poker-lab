import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Onboarding from './pages/Onboarding'
import PlayLab from './pages/PlayLab/PlayLab'
import DrillLab from './pages/DrillLab/DrillLab'
import ReviewLab from './pages/ReviewLab/ReviewLab'
import Profile from './pages/Profile/Profile'
import { hasSession } from './api/auth'

/** Redirect to onboarding if not logged in and not in guest mode. */
function RequireAuth({ children }: { children: JSX.Element }) {
  if (!hasSession()) {
    return <Navigate to="/" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route element={<Layout />}>
          <Route path="/play" element={<RequireAuth><PlayLab /></RequireAuth>} />
          <Route path="/drills" element={<RequireAuth><DrillLab /></RequireAuth>} />
          <Route path="/review" element={<RequireAuth><ReviewLab /></RequireAuth>} />
          <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
