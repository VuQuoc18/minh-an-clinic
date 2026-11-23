import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppointmentTable } from './AppointmentTable'
import { makeAppointment } from './testUtils'

describe('AppointmentTable', () => {
  it('hiện thông báo khi danh sách rỗng', () => {
    render(
      <AppointmentTable
        appointments={[]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    expect(
      screen.getByText('Không có lịch hẹn nào khớp điều kiện tìm.'),
    ).toBeInTheDocument()
  })

  it('hiện thông tin lịch hẹn với giờ dạng 24 giờ và badge trạng thái', () => {
    render(
      <AppointmentTable
        appointments={[makeAppointment()]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    expect(screen.getByText('LH-261109-0001')).toBeInTheDocument()
    expect(screen.getByText('09:00 - 09:30')).toBeInTheDocument()
    expect(screen.getByText('Đã đặt')).toBeInTheDocument()
    expect(screen.getByText('Trực tuyến')).toBeInTheDocument()
  })

  it('gọi onCheckIn khi bấm Xác nhận đến', async () => {
    const onCheckIn = vi.fn()
    const appt = makeAppointment()
    render(
      <AppointmentTable
        appointments={[appt]}
        checkingInId={null}
        onCheckIn={onCheckIn}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Xác nhận đến' }))

    expect(onCheckIn).toHaveBeenCalledWith(appt)
  })

  it('khóa nút và hiện lý do khi ngoài khoảng cho phép (BR-TD-01)', () => {
    const appt = makeAppointment({
      can_check_in: false,
      check_in_block_reason: 'Chưa đến giờ xác nhận.',
    })
    render(
      <AppointmentTable
        appointments={[appt]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    const button = screen.getByRole('button', { name: 'Xác nhận đến' })
    expect(button).toBeDisabled()
    expect(button).toHaveAccessibleDescription('Chưa đến giờ xác nhận.')
  })

  it('khóa nút khi đang xác nhận đúng lịch hẹn đó', () => {
    render(
      <AppointmentTable
        appointments={[makeAppointment({ id: 3 })]}
        checkingInId={3}
        onCheckIn={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Xác nhận đến' })).toBeDisabled()
  })

  it('không hiện nút khi lịch không còn ở trạng thái Đã đặt và hiện số thứ tự', () => {
    render(
      <AppointmentTable
        appointments={[makeAppointment({ status: 'arrived', queue_number: 4 })]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    expect(
      screen.queryByRole('button', { name: 'Xác nhận đến' }),
    ).not.toBeInTheDocument()
    expect(screen.getByText('Đã đến')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('hiện cảnh báo khi tin thông báo gửi lỗi (FR-TB-02)', () => {
    render(
      <AppointmentTable
        appointments={[makeAppointment({ has_failed_notification: true })]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    expect(
      screen.getByRole('img', { name: 'Tin thông báo gửi lỗi' }),
    ).toBeInTheDocument()
  })

  it('không hiện cảnh báo khi tin gửi bình thường', () => {
    render(
      <AppointmentTable
        appointments={[makeAppointment()]}
        checkingInId={null}
        onCheckIn={vi.fn()}
      />,
    )

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
})
