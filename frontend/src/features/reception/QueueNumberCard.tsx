import { Button } from '../../components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../../components/ui/card'
import { formatTime } from '../../lib/format'
import type { Appointment } from './types'

interface Props {
  appointment: Appointment
  onClose: () => void
}

/** Hiện số thứ tự to, rõ sau khi xác nhận đến (FR-TD-01, BR-TD-02). */
export function QueueNumberCard({ appointment, onClose }: Props) {
  return (
    <Card asChild>
      <section aria-labelledby="queue-title" role="status">
        <CardHeader>
          <CardTitle id="queue-title">
            Đã xác nhận đến: {appointment.patient_name}
          </CardTitle>
          <CardDescription>
            {appointment.code} · {appointment.doctor_name} ·{' '}
            {formatTime(appointment.start_time)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="ds-text-label">Số thứ tự</p>
          <p
            className="ds-text-display tabular-nums"
            data-testid="queue-number"
          >
            {appointment.queue_number}
          </p>
        </CardContent>
        <CardFooter>
          <Button variant="outline" onClick={onClose}>
            Đóng
          </Button>
        </CardFooter>
      </section>
    </Card>
  )
}
