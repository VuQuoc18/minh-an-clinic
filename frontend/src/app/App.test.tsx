import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

function renderAt(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App', () => {
  it('hiển thị tiêu đề phòng khám ở trang mặc định', () => {
    renderAt('/')

    expect(
      screen.getByRole('heading', { name: 'Phòng khám Minh An' }),
    ).toBeInTheDocument()
  })

  it('trang chủ có liên kết tới màn hình Tiếp đón', () => {
    renderAt('/')

    expect(
      screen.getByRole('link', { name: 'Quản lý: Tiếp đón' }),
    ).toHaveAttribute('href', '/quan-tri/tiep-don')
  })

  it('chuyển /quan-tri sang màn hình Tiếp đón', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {})),
    )

    renderAt('/quan-tri')

    expect(
      await screen.findByRole('heading', { name: 'Tiếp đón' }),
    ).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('đường dẫn không tồn tại quay về trang chủ', () => {
    renderAt('/khong-co')

    expect(
      screen.getByRole('heading', { name: 'Phòng khám Minh An' }),
    ).toBeInTheDocument()
  })

  it('mở màn hình Tiếp đón ở /quan-tri/tiep-don', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {})),
    )

    renderAt('/quan-tri/tiep-don')

    expect(
      await screen.findByRole('heading', { name: 'Tiếp đón' }),
    ).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('mở màn hình Đăng nhập bệnh nhân ở /dang-nhap', async () => {
    renderAt('/dang-nhap')

    expect(
      await screen.findByRole('heading', { name: 'Đăng nhập' }),
    ).toBeInTheDocument()
  })
})
