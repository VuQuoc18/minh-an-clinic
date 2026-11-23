import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ReceptionPage } from './ReceptionPage'
import { makeAppointment, mockFetch, renderWithClient } from './testUtils'

const DOCTORS = [{ id: 10, full_name: 'BS. Tran B', specialty_id: 1 }]

afterEach(() => vi.unstubAllGlobals())

describe('ReceptionPage', () => {
  it('tải và hiện danh sách lịch hẹn hôm nay', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/reception/appointments', body: [makeAppointment()] },
        { match: '/reception/doctors', body: DOCTORS },
      ]),
    )

    renderWithClient(<ReceptionPage />)

    expect(await screen.findByText('LH-261109-0001')).toBeInTheDocument()
    expect(
      screen.getByRole('option', { name: 'BS. Tran B' }),
    ).toBeInTheDocument()
  })

  it('hiện lỗi khi không tải được danh sách', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        {
          match: '/reception/appointments',
          status: 403,
          body: {
            detail: { code: 'FORBIDDEN', message: 'Bạn không có quyền.' },
          },
        },
        { match: '/reception/doctors', body: DOCTORS },
      ]),
    )

    renderWithClient(<ReceptionPage />)

    expect(
      await screen.findByText('Không tải được danh sách lịch hẹn'),
    ).toBeInTheDocument()
    expect(screen.getByText('Bạn không có quyền.')).toBeInTheDocument()
  })

  it('tìm kiếm gửi từ khóa đã cắt khoảng trắng và Xóa điều kiện bỏ từ khóa', async () => {
    const fetchMock = mockFetch([
      { match: '/reception/appointments', body: [] },
      { match: '/reception/doctors', body: DOCTORS },
    ])
    vi.stubGlobal('fetch', fetchMock)
    renderWithClient(<ReceptionPage />)
    await screen.findByText('Không có lịch hẹn nào khớp điều kiện tìm.')

    await userEvent.type(
      screen.getByLabelText('Mã lịch hẹn, số điện thoại hoặc họ tên'),
      '  0901234567 ',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Tìm' }))

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some((c) =>
          String(c[0]).endsWith('/reception/appointments?q=0901234567'),
        ),
      ).toBe(true),
    )

    await userEvent.click(screen.getByRole('button', { name: 'Xóa điều kiện' }))

    expect(
      screen.getByLabelText('Mã lịch hẹn, số điện thoại hoặc họ tên'),
    ).toHaveValue('')
  })

  it('lọc theo bác sĩ và trạng thái', async () => {
    const fetchMock = mockFetch([
      { match: '/reception/appointments', body: [] },
      { match: '/reception/doctors', body: DOCTORS },
    ])
    vi.stubGlobal('fetch', fetchMock)
    renderWithClient(<ReceptionPage />)
    await screen.findByRole('option', { name: 'BS. Tran B' })

    await userEvent.selectOptions(screen.getByLabelText('Bác sĩ'), '10')
    await userEvent.selectOptions(
      screen.getByLabelText('Trạng thái'),
      'arrived',
    )

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some((c) =>
          String(c[0]).endsWith(
            '/reception/appointments?doctor_id=10&status=arrived',
          ),
        ),
      ).toBe(true),
    )
  })

  it('xác nhận đến thành công thì hiện số thứ tự', async () => {
    const arrived = makeAppointment({ status: 'arrived', queue_number: 3 })
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { method: 'POST', match: '/check-in', body: arrived },
        { match: '/reception/appointments', body: [makeAppointment()] },
        { match: '/reception/doctors', body: DOCTORS },
      ]),
    )
    renderWithClient(<ReceptionPage />)

    await userEvent.click(
      await screen.findByRole('button', { name: 'Xác nhận đến' }),
    )

    expect(await screen.findByTestId('queue-number')).toHaveTextContent('3')
  })

  it('xác nhận đến bị từ chối thì hiện lỗi của máy chủ', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        {
          method: 'POST',
          match: '/check-in',
          status: 409,
          body: {
            detail: {
              code: 'CHECK_IN_WINDOW',
              message: 'Đã quá giờ xác nhận.',
            },
          },
        },
        { match: '/reception/appointments', body: [makeAppointment()] },
        { match: '/reception/doctors', body: DOCTORS },
      ]),
    )
    renderWithClient(<ReceptionPage />)

    await userEvent.click(
      await screen.findByRole('button', { name: 'Xác nhận đến' }),
    )

    expect(
      await screen.findByText('Không xác nhận đến được'),
    ).toBeInTheDocument()
    expect(screen.getByText('Đã quá giờ xác nhận.')).toBeInTheDocument()
    expect(screen.queryByTestId('queue-number')).not.toBeInTheDocument()
  })

  it('lỗi mạng khi xác nhận đến hiện thông báo kết nối', async () => {
    const base = mockFetch([
      { match: '/reception/appointments', body: [makeAppointment()] },
      { match: '/reception/doctors', body: DOCTORS },
    ])
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string, init?: RequestInit) =>
        init?.method === 'POST'
          ? Promise.reject(new TypeError('network'))
          : base(url, init),
      ),
    )
    renderWithClient(<ReceptionPage />)

    await userEvent.click(
      await screen.findByRole('button', { name: 'Xác nhận đến' }),
    )

    expect(
      await screen.findByText('Không kết nối được máy chủ. Vui lòng thử lại.'),
    ).toBeInTheDocument()
  })

  it('mở và hủy panel Khách vãng lai', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/reception/appointments', body: [] },
        { match: '/reception/doctors', body: DOCTORS },
        { match: '/reception/specialties', body: [] },
      ]),
    )
    renderWithClient(<ReceptionPage />)

    await userEvent.click(
      screen.getByRole('button', { name: 'Khách vãng lai' }),
    )
    expect(
      screen.getByRole('heading', { name: 'Khách vãng lai', level: 2 }),
    ).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(
      screen.queryByRole('heading', { name: 'Khách vãng lai', level: 2 }),
    ).not.toBeInTheDocument()
  })
})
