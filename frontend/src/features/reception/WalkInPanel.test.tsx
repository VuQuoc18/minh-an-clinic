import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { makeAppointment, mockFetch, renderWithClient } from './testUtils'
import { WalkInPanel } from './WalkInPanel'

const SPECIALTIES = [{ id: 1, name: 'Nội' }]
const SUGGESTION = {
  slot_id: 55,
  doctor_id: 10,
  doctor_name: 'BS. Tran B',
  slot_date: '2026-11-09',
  start_time: '09:00:00',
  end_time: '09:30:00',
  is_walk_in_slot: true,
}
const PROFILE = {
  id: 9,
  full_name: 'Nguyen Van A',
  birth_date: '1990-05-01',
  gender: 'Nam',
  phone: '0901234567',
  is_primary: true,
}

afterEach(() => vi.unstubAllGlobals())

async function chooseSpecialty() {
  // Chờ danh sách chuyên khoa tải xong rồi mới chọn.
  await screen.findByRole('option', { name: 'Nội' })
  await userEvent.selectOptions(screen.getByLabelText(/Chuyên khoa/), '1')
}

async function searchPhone(phone: string) {
  await userEvent.type(screen.getByLabelText(/Số điện thoại/), phone)
  await userEvent.click(screen.getByRole('button', { name: 'Tìm hồ sơ' }))
}

describe('WalkInPanel', () => {
  it('hiện khung trống sớm nhất của bác sĩ, gắn nhãn khung vãng lai', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [SUGGESTION],
            message: null,
            next_available_date: null,
          },
        },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await chooseSpecialty()

    expect(
      await screen.findByText(/BS\. Tran B · 09:00 - 09:30 \(khung vãng lai\)/),
    ).toBeInTheDocument()
  })

  it('hết khung hôm nay thì báo hết chỗ và gợi ý ngày gần nhất', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [],
            message: 'Hết chỗ hôm nay',
            next_available_date: '2026-11-10',
          },
        },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await chooseSpecialty()

    expect(await screen.findByText('Hết chỗ hôm nay')).toBeInTheDocument()
    expect(
      screen.getByText('Ngày gần nhất còn trống: 10/11/2026.'),
    ).toBeInTheDocument()
  })

  it('hết khung và không có ngày trống trong 30 ngày thì báo rõ', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: { suggestions: [], message: null, next_available_date: null },
        },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await chooseSpecialty()

    expect(await screen.findByText('Hết chỗ hôm nay')).toBeInTheDocument()
    expect(
      screen.getByText('Chưa có ngày nào còn trống trong 30 ngày tới.'),
    ).toBeInTheDocument()
  })

  it('hiện lỗi khi không tải được khung giờ', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          status: 500,
          body: { detail: 'boom' },
        },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await chooseSpecialty()

    expect(
      await screen.findByText('Không tải được khung giờ trống'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Không thực hiện được. Vui lòng thử lại.'),
    ).toBeInTheDocument()
  })

  it('số điện thoại sai định dạng thì báo lỗi và không gọi API tìm hồ sơ', async () => {
    const fetchMock = mockFetch([{ match: '/specialties', body: SPECIALTIES }])
    vi.stubGlobal('fetch', fetchMock)
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await searchPhone('12345')

    expect(
      screen.getByText('Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.'),
    ).toBeInTheDocument()
    expect(
      fetchMock.mock.calls.some((c) => String(c[0]).includes('/profiles')),
    ).toBe(false)
  })

  it('nút tạo lịch bị khóa cho đến khi chọn đủ khung giờ và hồ sơ', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [SUGGESTION],
            message: null,
            next_available_date: null,
          },
        },
        { match: '/reception/profiles', body: [PROFILE] },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)
    const submit = screen.getByRole('button', {
      name: 'Tạo lịch và xác nhận đến',
    })
    expect(submit).toBeDisabled()

    await chooseSpecialty()
    await userEvent.click(
      await screen.findByRole('radio', { name: /BS\. Tran B/ }),
    )
    expect(submit).toBeDisabled()

    await searchPhone('0901234567')
    await userEvent.click(
      await screen.findByRole('radio', { name: /Nguyen Van A/ }),
    )

    expect(submit).toBeEnabled()
  })

  it('tạo lịch với hồ sơ có sẵn thì gửi slot_id, profile_id và gọi onCreated', async () => {
    const created = makeAppointment({
      status: 'arrived',
      channel: 'walk_in',
      queue_number: 1,
    })
    const fetchMock = mockFetch([
      { match: '/specialties', body: SPECIALTIES },
      {
        match: '/walk-in/suggestions',
        body: {
          suggestions: [SUGGESTION],
          message: null,
          next_available_date: null,
        },
      },
      { match: '/reception/profiles', body: [PROFILE] },
      { method: 'POST', match: '/reception/walk-in', body: created },
    ])
    vi.stubGlobal('fetch', fetchMock)
    const onCreated = vi.fn()
    renderWithClient(<WalkInPanel onCreated={onCreated} onCancel={vi.fn()} />)

    await chooseSpecialty()
    await userEvent.click(
      await screen.findByRole('radio', { name: /BS\. Tran B/ }),
    )
    await searchPhone('0901234567')
    await userEvent.click(
      await screen.findByRole('radio', { name: /Nguyen Van A/ }),
    )
    await userEvent.click(
      screen.getByRole('button', { name: 'Tạo lịch và xác nhận đến' }),
    )

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(created))
    const post = fetchMock.mock.calls.find((c) => c[1]?.method === 'POST')
    expect(JSON.parse(post![1]!.body as string)).toEqual({
      slot_id: 55,
      profile_id: 9,
    })
  })

  it('chưa có hồ sơ thì nhập hồ sơ mới và gửi new_profile', async () => {
    const created = makeAppointment({ status: 'arrived', queue_number: 2 })
    const fetchMock = mockFetch([
      { match: '/specialties', body: SPECIALTIES },
      {
        match: '/walk-in/suggestions',
        body: {
          suggestions: [SUGGESTION],
          message: null,
          next_available_date: null,
        },
      },
      { match: '/reception/profiles', body: [] },
      { method: 'POST', match: '/reception/walk-in', body: created },
    ])
    vi.stubGlobal('fetch', fetchMock)
    const onCreated = vi.fn()
    renderWithClient(<WalkInPanel onCreated={onCreated} onCancel={vi.fn()} />)

    await chooseSpecialty()
    await userEvent.click(
      await screen.findByRole('radio', { name: /BS\. Tran B/ }),
    )
    await searchPhone('0901234567')
    expect(
      await screen.findByText(/Chưa có hồ sơ với số điện thoại này/),
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: 'Nhập hồ sơ mới' }))

    await userEvent.type(screen.getByLabelText(/Họ tên/), 'Le Thi C')
    await userEvent.type(screen.getByLabelText(/Ngày sinh/), '1995-02-03')
    await userEvent.click(screen.getByRole('radio', { name: 'Nữ' }))
    const submit = screen.getByRole('button', {
      name: 'Tạo lịch và xác nhận đến',
    })
    await waitFor(() => expect(submit).toBeEnabled())
    await userEvent.click(submit)

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(created))
    const post = fetchMock.mock.calls.find((c) => c[1]?.method === 'POST')
    expect(JSON.parse(post![1]!.body as string)).toEqual({
      slot_id: 55,
      new_profile: {
        full_name: 'Le Thi C',
        birth_date: '1995-02-03',
        gender: 'Nữ',
        phone: '0901234567',
      },
    })
  })

  it('hồ sơ mới thiếu họ tên thì nút tạo lịch vẫn bị khóa', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [SUGGESTION],
            message: null,
            next_available_date: null,
          },
        },
        { match: '/reception/profiles', body: [] },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await chooseSpecialty()
    await userEvent.click(
      await screen.findByRole('radio', { name: /BS\. Tran B/ }),
    )
    await searchPhone('0901234567')
    await screen.findByText(/Chưa có hồ sơ/)
    await userEvent.click(screen.getByRole('radio', { name: 'Nhập hồ sơ mới' }))
    await userEvent.type(screen.getByLabelText(/Ngày sinh/), '1995-02-03')
    await userEvent.click(screen.getByRole('radio', { name: 'Nam' }))

    expect(
      screen.getByRole('button', { name: 'Tạo lịch và xác nhận đến' }),
    ).toBeDisabled()
  })

  it('máy chủ từ chối tạo lịch thì hiện lỗi và không gọi onCreated', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [SUGGESTION],
            message: null,
            next_available_date: null,
          },
        },
        { match: '/reception/profiles', body: [PROFILE] },
        {
          method: 'POST',
          match: '/reception/walk-in',
          status: 409,
          body: {
            detail: {
              code: 'SLOT_TAKEN',
              message: 'Khung giờ vừa có người đặt.',
            },
          },
        },
      ]),
    )
    const onCreated = vi.fn()
    renderWithClient(<WalkInPanel onCreated={onCreated} onCancel={vi.fn()} />)

    await chooseSpecialty()
    await userEvent.click(
      await screen.findByRole('radio', { name: /BS\. Tran B/ }),
    )
    await searchPhone('0901234567')
    await userEvent.click(
      await screen.findByRole('radio', { name: /Nguyen Van A/ }),
    )
    await userEvent.click(
      screen.getByRole('button', { name: 'Tạo lịch và xác nhận đến' }),
    )

    expect(
      await screen.findByText('Không tạo được lịch hẹn'),
    ).toBeInTheDocument()
    expect(screen.getByText('Khung giờ vừa có người đặt.')).toBeInTheDocument()
    expect(onCreated).not.toHaveBeenCalled()
  })

  it('hiện lỗi khi không tìm được hồ sơ', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        { match: '/specialties', body: SPECIALTIES },
        { match: '/reception/profiles', status: 500, body: {} },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)

    await searchPhone('0901234567')

    expect(await screen.findByText('Không tìm được hồ sơ')).toBeInTheDocument()
  })

  it('đổi chuyên khoa thì bỏ khung giờ đã chọn', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch([
        {
          match: '/specialties',
          body: [...SPECIALTIES, { id: 2, name: 'Nhi' }],
        },
        {
          match: '/walk-in/suggestions',
          body: {
            suggestions: [SUGGESTION],
            message: null,
            next_available_date: null,
          },
        },
      ]),
    )
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={vi.fn()} />)
    await screen.findByRole('option', { name: 'Nhi' })

    await chooseSpecialty()
    const radio = await screen.findByRole('radio', { name: /BS\. Tran B/ })
    await userEvent.click(radio)
    expect(radio).toBeChecked()

    await userEvent.selectOptions(screen.getByLabelText(/Chuyên khoa/), '')

    expect(
      screen.queryByRole('radio', { name: /BS\. Tran B/ }),
    ).not.toBeInTheDocument()
  })

  it('gọi onCancel khi bấm Hủy', async () => {
    vi.stubGlobal('fetch', mockFetch([{ match: '/specialties', body: [] }]))
    const onCancel = vi.fn()
    renderWithClient(<WalkInPanel onCreated={vi.fn()} onCancel={onCancel} />)

    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(onCancel).toHaveBeenCalledOnce()
  })
})
