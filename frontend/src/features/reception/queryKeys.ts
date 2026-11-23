import type { AppointmentFilters } from './types'

/** Khoá bộ nhớ đệm của màn hình Tiếp đón, gom một chỗ để làm mới dữ liệu cho đúng. */
export const receptionKeys = {
  all: ['reception'] as const,
  appointments: () => [...receptionKeys.all, 'appointments'] as const,
  appointmentList: (filters: AppointmentFilters) =>
    [...receptionKeys.appointments(), filters] as const,
  doctors: () => [...receptionKeys.all, 'doctors'] as const,
  specialties: () => [...receptionKeys.all, 'specialties'] as const,
  walkInSuggestions: () =>
    [...receptionKeys.all, 'walk-in-suggestions'] as const,
  walkInSuggestionsFor: (specialtyId: number | null) =>
    [...receptionKeys.walkInSuggestions(), specialtyId] as const,
  profiles: (phone: string) =>
    [...receptionKeys.all, 'profiles', phone] as const,
}
