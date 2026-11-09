import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardFooter } from '../../components/ui/card'
import { Field } from '../../components/ui/field'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { NativeSelect } from '../../components/ui/native-select'
import { ApiError } from '../../lib/http'
import { checkIn, listAppointments, listDoctors } from './api'
import { AppointmentTable } from './AppointmentTable'
import { STATUS_LABEL } from './labels'
import { QueueNumberCard } from './QueueNumberCard'
import type { Appointment, AppointmentStatus } from './types'
import { WalkInPanel } from './WalkInPanel'

const STATUSES = Object.keys(STATUS_LABEL) as AppointmentStatus[]

function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Không thực hiện được. Vui lòng thử lại.'
}

/** MH-TD-01 Tiếp đón (SCR-001). */
export function ReceptionPage() {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [q, setQ] = useState('')
  const [doctorId, setDoctorId] = useState('')
  const [status, setStatus] = useState('')
  const [walkInOpen, setWalkInOpen] = useState(false)
  const [arrived, setArrived] = useState<Appointment | null>(null)

  const filters = {
    q: q || undefined,
    doctor_id: doctorId ? Number(doctorId) : undefined,
    status: (status || undefined) as AppointmentStatus | undefined,
  }
  const appointments = useQuery({
    queryKey: ['appointments', filters],
    queryFn: () => listAppointments(filters),
  })
  const doctors = useQuery({ queryKey: ['doctors'], queryFn: listDoctors })
  const confirm = useMutation({
    mutationFn: (appointment: Appointment) => checkIn(appointment.id),
    onSuccess: (appointment) => {
      setArrived(appointment)
      void queryClient.invalidateQueries({ queryKey: ['appointments'] })
    },
    onError: () => {
      // Trạng thái hoặc khung giờ có thể đã đổi: tải lại danh sách.
      void queryClient.invalidateQueries({ queryKey: ['appointments'] })
    },
  })

  const clear = () => {
    setText('')
    setQ('')
    setDoctorId('')
    setStatus('')
  }

  return (
    <main className="ds-kit-content">
      <header className="ds-kit-page-header">
        <div className="flex flex-col gap-1">
          <ol className="ds-kit-breadcrumb" aria-label="Đường dẫn">
            <li>Trang chủ</li>
            <li>Quản lý</li>
            <li aria-current="page">Tiếp đón</li>
          </ol>
          <h1 className="ds-text-title">Tiếp đón</h1>
        </div>
        <div className="ds-kit-page-actions">
          <Button
            onClick={() => {
              setWalkInOpen(true)
              setArrived(null)
            }}
          >
            Khách vãng lai
          </Button>
        </div>
      </header>

      <Card asChild>
        <form
          role="search"
          aria-label="Tìm lịch hẹn hôm nay"
          onSubmit={(event) => {
            event.preventDefault()
            setQ(text.trim())
          }}
        >
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field>
              <Label htmlFor="rc-q">
                Mã lịch hẹn, số điện thoại hoặc họ tên
              </Label>
              <Input
                id="rc-q"
                type="search"
                maxLength={100}
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </Field>
            <Field>
              <Label htmlFor="rc-doctor">Bác sĩ</Label>
              <NativeSelect
                id="rc-doctor"
                value={doctorId}
                onChange={(event) => setDoctorId(event.target.value)}
              >
                <option value="">Tất cả</option>
                {doctors.data?.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.full_name}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field>
              <Label htmlFor="rc-status">Trạng thái</Label>
              <NativeSelect
                id="rc-status"
                value={status}
                onChange={(event) => setStatus(event.target.value)}
              >
                <option value="">Tất cả</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {STATUS_LABEL[s]}
                  </option>
                ))}
              </NativeSelect>
            </Field>
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={clear}>
              Xóa điều kiện
            </Button>
            <Button type="submit">Tìm</Button>
          </CardFooter>
        </form>
      </Card>

      {confirm.isError && (
        <Alert variant="destructive" role="alert">
          <AlertTitle>Không xác nhận đến được</AlertTitle>
          <AlertDescription>{errorMessage(confirm.error)}</AlertDescription>
        </Alert>
      )}

      {arrived && (
        <QueueNumberCard
          appointment={arrived}
          onClose={() => setArrived(null)}
        />
      )}

      {walkInOpen && (
        <WalkInPanel
          onCancel={() => setWalkInOpen(false)}
          onCreated={(appointment) => {
            setWalkInOpen(false)
            setArrived(appointment)
          }}
        />
      )}

      {appointments.isError && (
        <Alert variant="destructive" role="alert">
          <AlertTitle>Không tải được danh sách lịch hẹn</AlertTitle>
          <AlertDescription>
            {errorMessage(appointments.error)}
          </AlertDescription>
        </Alert>
      )}
      {appointments.isPending && <p role="status">Đang tải danh sách…</p>}
      {appointments.data && (
        <AppointmentTable
          appointments={appointments.data}
          checkingInId={
            confirm.isPending ? (confirm.variables?.id ?? null) : null
          }
          onCheckIn={(appointment) => {
            confirm.reset()
            confirm.mutate(appointment)
          }}
        />
      )}
    </main>
  )
}
