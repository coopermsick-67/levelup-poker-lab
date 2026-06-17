import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Onboarding from './pages/Onboarding'
import PlayLab from './pages/PlayLab/PlayLab'
import DrillLab from './pages/DrillLab/DrillLab'
import ReviewLab from './pages/ReviewLab/ReviewLab'
import Profile from './pages/Profile/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route element={<Layout />}>
          <Route path="/play" element={<PlayLab />} />
          <Route path="/drills" element={<DrillLab />} />
          <Route path="/review" element={<ReviewLab />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
