import { apiRequest } from '../../lib/http'
import type {
  Appointment,
  AppointmentFilters,
  Doctor,
  Profile,
  Specialty,
  Suggestions,
  WalkInBody,
} from './types'

export const listAppointments = (filters: AppointmentFilters) =>
  apiRequest<Appointment[]>('GET', '/reception/appointments', {
    params: { ...filters },
  })

export const checkIn = (appointmentId: number) =>
  apiRequest<Appointment>(
    'POST',
    `/reception/appointments/${appointmentId}/check-in`,
  )

export const listSpecialties = () =>
  apiRequest<Specialty[]>('GET', '/reception/specialties')

export const listDoctors = () =>
  apiRequest<Doctor[]>('GET', '/reception/doctors')

export const getWalkInSuggestions = (specialtyId: number) =>
  apiRequest<Suggestions>('GET', '/reception/walk-in/suggestions', {
    params: { specialty_id: specialtyId },
  })

export const searchProfiles = (phone: string) =>
  apiRequest<Profile[]>('GET', '/reception/profiles', { params: { phone } })

export const createWalkIn = (body: WalkInBody) =>
  apiRequest<Appointment>('POST', '/reception/walk-in', { body })
