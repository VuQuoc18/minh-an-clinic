import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { getPatientToken, setPatientToken } from './patientSession'
import {
  CREATE_PROFILE_PATH,
  LOGIN_PATH,
  MY_APPOINTMENTS_PATH,
  SET_PASSWORD_PATH,
} from './routes'

function Where({ name }: { name: string }) {
  const location = useLocation()
  return (
    <p data-testid="where">
      {name} {JSON.stringify(location.state)}
    </p>
  )
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[LOGIN_PATH]}>
        <Routes>
          <Route path={LOGIN_PATH} element={<LoginPage />} />
          <Route path={SET_PASSWORD_PATH} element={<Where name="set" />} />
          <Route
            path={CREATE_PROFILE_PATH}
            element={<Where name="profile" />}
          />
          <Route path={MY_APPOINTMENTS_PATH} element={<Where name="mine" />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function stubLogin(status: number, body: unknown) {
  const fetchMock = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify(body), { status })),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const OK = {
  ket_qua: 'THANH_CONG',
  so_dien_thoai: '0912345678',
  token: 'tok-1',
  het_han_luc: '2026-12-24T09:00:00+07:00',
  can_tao_ho_so: false,
}

async function fill(phone: string, password: string) {
  const phoneInput = screen.getByLabelText(/Số điện thoại/)
  if (phone) await userEvent.type(phoneInput, phone)
  if (password)
    await userEvent.type(screen.getByLabelText(/^Mật khẩu/), password)
}

const submitButton = () => screen.getByRole('button', { name: 'Đăng nhập' })

beforeEach(() => {
  sessionStorage.clear()
  setPatientToken(null)
})
afterEach(() => vi.unstubAllGlobals())

describe('LoginPage', () => {
  it('khóa nút Đăng nhập khi còn trống', () => {
    renderPage()

    expect(submitButton()).toBeDisabled()
  })

  it('khóa nút và báo lỗi dưới ô khi số điện thoại sai định dạng', async () => {
    renderPage()

    await fill('12345', 'abc')

    expect(submitButton()).toBeDisabled()
    expect(
      screen.getByText('Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/Số điện thoại/)).toHaveAttribute(
      'aria-invalid',
      'true',
    )
  })

  it('khóa nút khi mật khẩu trống dù số điện thoại đúng', async () => {
    renderPage()

    await fill('0912345678', '')

    expect(submitButton()).toBeDisabled()
    expect(screen.queryByText(/10 chữ số/)).not.toBeInTheDocument()
  })

  it('mở nút khi số điện thoại đúng và có mật khẩu', async () => {
    renderPage()

    await fill('0912345678', 'a')

    expect(submitButton()).toBeEnabled()
  })

  it('nút hiện/ẩn đổi kiểu ô mật khẩu', async () => {
    renderPage()
    const input = screen.getByLabelText(/^Mật khẩu/)
    expect(input).toHaveAttribute('type', 'password')

    await userEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }))
    expect(input).toHaveAttribute('type', 'text')

    await userEvent.click(screen.getByRole('button', { name: 'Ẩn mật khẩu' }))
    expect(input).toHaveAttribute('type', 'password')
  })

  it('đã có hồ sơ thì vào Lịch hẹn của tôi và lưu token', async () => {
    const fetchMock = stubLogin(200, OK)
    renderPage()
    await fill('0912345678', 'matkhau123')

    await userEvent.click(submitButton())

    expect(await screen.findByTestId('where')).toHaveTextContent('mine')
    expect(getPatientToken()).toBe('tok-1')
    const init = (fetchMock.mock.calls[0] as unknown[])[1] as RequestInit
    expect(JSON.parse(init.body as string)).toEqual({
      so_dien_thoai: '0912345678',
      mat_khau: 'matkhau123',
    })
  })

  it('chưa có hồ sơ chính chủ thì sang form hồ sơ kèm số điện thoại', async () => {
    stubLogin(200, { ...OK, can_tao_ho_so: true })
    renderPage()
    await fill('0912345678', 'a')

    await userEvent.click(submitButton())

    const where = await screen.findByTestId('where')
    expect(where).toHaveTextContent('profile')
    expect(where).toHaveTextContent('0912345678')
    expect(getPatientToken()).toBe('tok-1')
  })

  it('chưa có mật khẩu thì sang MH-TK-05 kèm số điện thoại, không lưu token', async () => {
    stubLogin(200, {
      ket_qua: 'CHUA_CO_MAT_KHAU',
      so_dien_thoai: '0912345678',
      token: null,
      het_han_luc: null,
      can_tao_ho_so: false,
    })
    renderPage()
    await fill('0912345678', 'a')

    await userEvent.click(submitButton())

    const where = await screen.findByTestId('where')
    expect(where).toHaveTextContent('set')
    expect(where).toHaveTextContent('0912345678')
    expect(getPatientToken()).toBeNull()
  })

  it('sai thông tin thì hiện thông báo kèm số lần còn lại và ở lại màn hình', async () => {
    stubLogin(401, {
      detail: {
        code: 'SAI_THONG_TIN',
        message: 'Số điện thoại hoặc mật khẩu không đúng. Còn 4 lần thử.',
        so_lan_con_lai: 4,
      },
    })
    renderPage()
    await fill('0912345678', 'sai')

    await userEvent.click(submitButton())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Số điện thoại hoặc mật khẩu không đúng. Còn 4 lần thử.',
    )
    expect(screen.queryByTestId('where')).not.toBeInTheDocument()
    expect(getPatientToken()).toBeNull()
  })

  it('bị khóa thì hiện thời điểm được thử lại', async () => {
    stubLogin(429, {
      detail: {
        code: 'BI_KHOA',
        message:
          'Số điện thoại bị khóa đăng nhập. Thử lại sau 09:15 ngày 24/11/2026.',
        thu_lai_luc: '2026-11-24T09:15:00+07:00',
      },
    })
    renderPage()
    await fill('0912345678', 'sai')

    await userEvent.click(submitButton())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Thử lại sau 09:15 ngày 24/11/2026.',
    )
  })

  it('mất kết nối thì hiện thông báo lỗi và cho thử lại', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    renderPage()
    await fill('0912345678', 'a')

    await userEvent.click(submitButton())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Không kết nối được máy chủ',
    )
    await waitFor(() => expect(submitButton()).toBeEnabled())
  })

  it('lỗi không rõ nguồn thì dùng thông báo chung', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response('oops', { status: 500 }))),
    )
    renderPage()
    await fill('0912345678', 'a')

    await userEvent.click(submitButton())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Không thực hiện được. Vui lòng thử lại.',
    )
  })

  it('bấm nút hiện/ẩn mật khẩu không gửi form đăng nhập', async () => {
    const fetchMock = stubLogin(200, OK)
    renderPage()
    await fill('0912345678', 'matkhau1')

    await userEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }))
    await userEvent.click(screen.getByRole('button', { name: 'Ẩn mật khẩu' }))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Hiện mật khẩu' })).toHaveAttribute(
      'type',
      'button',
    )
  })

  it('bấm Enter trong ô mật khẩu khi nút bị khóa thì không gửi yêu cầu', async () => {
    const fetchMock = stubLogin(200, OK)
    renderPage()
    await fill('12345', 'abc{Enter}')

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('Quên mật khẩu mở MH-TK-05', async () => {
    renderPage()

    await userEvent.click(screen.getByRole('link', { name: 'Quên mật khẩu' }))

    expect(await screen.findByTestId('where')).toHaveTextContent('set')
  })
})
