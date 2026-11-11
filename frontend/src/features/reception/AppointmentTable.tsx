import { Badge } from '../../components/ui/badge'
import { Button } from '../../components/ui/button'
import { FieldHint } from '../../components/ui/field'
import {
  Table,
  TableBody,
  TableCell,
  TableCellActions,
  TableCellNum,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table'
import { formatTime } from '../../lib/format'
import { CHANNEL_LABEL, STATUS_BADGE, STATUS_LABEL } from './labels'
import type { Appointment } from './types'

interface Props {
  appointments: Appointment[]
  checkingInId: number | null
  onCheckIn: (appointment: Appointment) => void
}

export function AppointmentTable({
  appointments,
  checkingInId,
  onCheckIn,
}: Props) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Mã lịch hẹn</TableHead>
          <TableHead>Bệnh nhân</TableHead>
          <TableHead>Số điện thoại</TableHead>
          <TableHead>Bác sĩ</TableHead>
          <TableHead>Giờ khám</TableHead>
          <TableHead>Kênh</TableHead>
          <TableHead>Trạng thái</TableHead>
          <TableHead className="ds-table-num">Số thứ tự</TableHead>
          <TableHead>
            <span className="sr-only">Thao tác</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {appointments.length === 0 ? (
          <TableRow>
            <TableCell colSpan={9} className="ds-table-empty">
              Không có lịch hẹn nào khớp điều kiện tìm.
            </TableCell>
          </TableRow>
        ) : (
          appointments.map((appt) => (
            <AppointmentRow
              key={appt.id}
              appt={appt}
              busy={checkingInId === appt.id}
              onCheckIn={onCheckIn}
            />
          ))
        )}
      </TableBody>
    </Table>
  )
}

interface RowProps {
  appt: Appointment
  busy: boolean
  onCheckIn: (appointment: Appointment) => void
}

function AppointmentRow({ appt, busy, onCheckIn }: RowProps) {
  const showCheckIn = appt.status === 'booked'
  const reasonId = `reason-${appt.id}`
  return (
    <TableRow>
      <TableCell className="ds-text-mono">{appt.code}</TableCell>
      <TableCell>
        {appt.patient_name}
        {appt.has_failed_notification && (
          <Badge
            variant="warning"
            title="Tin thông báo gửi lỗi"
            role="img"
            aria-label="Tin thông báo gửi lỗi"
          >
            ⚠ Tin lỗi
          </Badge>
        )}
      </TableCell>
      <TableCell className="tabular-nums">{appt.patient_phone}</TableCell>
      <TableCell>{appt.doctor_name}</TableCell>
      <TableCell className="tabular-nums">
        {formatTime(appt.start_time)} - {formatTime(appt.end_time)}
      </TableCell>
      <TableCell>{CHANNEL_LABEL[appt.channel]}</TableCell>
      <TableCell>
        <Badge className={STATUS_BADGE[appt.status]}>
          {STATUS_LABEL[appt.status]}
        </Badge>
      </TableCell>
      <TableCellNum>{appt.queue_number ?? ''}</TableCellNum>
      <TableCellActions>
        {showCheckIn && (
          <>
            <Button
              size="sm"
              disabled={!appt.can_check_in || busy}
              aria-describedby={
                appt.check_in_block_reason ? reasonId : undefined
              }
              onClick={() => onCheckIn(appt)}
            >
              Xác nhận đến
            </Button>
            {!appt.can_check_in && appt.check_in_block_reason && (
              <FieldHint id={reasonId}>{appt.check_in_block_reason}</FieldHint>
            )}
          </>
        )}
      </TableCellActions>
    </TableRow>
  )
}
