import { lazy, Suspense } from 'react'
import { Link, Navigate, Route, Routes } from 'react-router-dom'

// Mỗi màn hình tải riêng khi cần, để trang đầu nhẹ hơn khi có thêm phân hệ.
const ReceptionPage = lazy(() =>
  import('@/features/reception/ReceptionPage').then((m) => ({
    default: m.ReceptionPage,
  })),
)

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

function PageLoading() {
  return (
    <p role="status" className="ds-kit-content">
      Đang tải…
    </p>
  )
}

export default function App() {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/quan-tri"
          element={<Navigate to="/quan-tri/tiep-don" replace />}
        />
        <Route path="/quan-tri/tiep-don" element={<ReceptionPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
