import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

function Broken(): never {
  throw new Error('hỏng')
}

describe('ErrorBoundary', () => {
  it('hiện nội dung con khi không có lỗi', () => {
    render(
      <ErrorBoundary>
        <p>Bình thường</p>
      </ErrorBoundary>,
    )

    expect(screen.getByText('Bình thường')).toBeInTheDocument()
  })

  it('hiện thông báo và nút tải lại thay vì trang trắng khi màn hình lỗi', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    )

    expect(screen.getByText('Đã có lỗi xảy ra')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Tải lại trang' }),
    ).toBeInTheDocument()
    spy.mockRestore()
  })
})
