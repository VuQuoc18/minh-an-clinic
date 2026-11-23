import type { AppointmentStatus, Channel } from './types'

// Trạng thái luôn là badge có chữ (design system), không chỉ dùng màu.
export const STATUS_LABEL: Record<AppointmentStatus, string> = {
  booked: 'Đã đặt',
  arrived: 'Đã đến',
  in_progress: 'Đang khám',
  completed: 'Đã khám',
  cancelled: 'Đã hủy',
  no_show: 'Vắng hẹn',
}

export const STATUS_BADGE: Record<AppointmentStatus, string> = {
  booked: 'ds-badge--info',
  arrived: 'ds-badge--success',
  in_progress: 'ds-badge--warning',
  completed: 'ds-badge--secondary',
  cancelled: 'ds-badge--destructive',
  no_show: 'ds-badge--destructive',
}

export const CHANNEL_LABEL: Record<Channel, string> = {
  online: 'Trực tuyến',
  reception: 'Lễ tân',
  walk_in: 'Vãng lai',
}
