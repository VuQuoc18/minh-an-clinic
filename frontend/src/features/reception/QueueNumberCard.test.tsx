import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueueNumberCard } from './QueueNumberCard'
import { makeAppointment } from './testUtils'

describe('QueueNumberCard', () => {
  it('hiện số thứ tự và thông tin lịch hẹn', () => {
    render(
      <QueueNumberCard
        appointment={makeAppointment({ status: 'arrived', queue_number: 7 })}
        onClose={vi.fn()}
      />,
    )

    expect(screen.getByTestId('queue-number')).toHaveTextContent('7')
    expect(screen.getByText(/Nguyen Van A/)).toBeInTheDocument()
    expect(screen.getByText(/09:00/)).toBeInTheDocument()
  })

  it('gọi onClose khi bấm Đóng', async () => {
    const onClose = vi.fn()
    render(
      <QueueNumberCard
        appointment={makeAppointment({ queue_number: 1 })}
        onClose={onClose}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Đóng' }))

    expect(onClose).toHaveBeenCalledOnce()
  })
})
