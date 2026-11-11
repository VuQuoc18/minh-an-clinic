import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { ReceptionPage } from './features/reception/ReceptionPage'

function HomePage() {
  return (
    <main>
      <h1>Phòng khám Minh An</h1>
      <p>
        <Link to="/quan-tri/tiep-don">Quản lý: Tiếp đón</Link>
      </p>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/quan-tri"
        element={<Navigate to="/quan-tri/tiep-don" replace />}
      />
      <Route path="/quan-tri/tiep-don" element={<ReceptionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
