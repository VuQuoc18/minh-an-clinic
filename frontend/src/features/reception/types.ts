export type AppointmentStatus =
  'booked' | 'arrived' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'

export type Channel = 'online' | 'reception' | 'walk_in'

export interface Appointment {
  id: number
  code: string
  patient_name: string
  patient_phone: string
  doctor_id: number
  doctor_name: string
  specialty_name: string
  appt_date: string
  start_time: string
  end_time: string
  status: AppointmentStatus
  channel: Channel
  queue_number: number | null
  has_failed_notification: boolean
  can_check_in: boolean
  check_in_block_reason: string | null
}

export interface Specialty {
  id: number
  name: string
}

export interface Doctor {
  id: number
  full_name: string
  specialty_id: number
}

export interface Suggestion {
  slot_id: number
  doctor_id: number
  doctor_name: string
  slot_date: string
  start_time: string
  end_time: string
  is_walk_in_slot: boolean
}

export interface Suggestions {
  suggestions: Suggestion[]
  message: string | null
  next_available_date: string | null
}

export interface Profile {
  id: number
  full_name: string
  birth_date: string
  gender: string
  phone: string | null
  is_primary: boolean
}

export interface NewProfile {
  full_name: string
  birth_date: string
  gender: 'Nam' | 'Nữ'
  phone: string
  email?: string
  address?: string
}

export interface WalkInBody {
  slot_id: number
  profile_id?: number
  new_profile?: NewProfile
}

export interface AppointmentFilters {
  q?: string
  doctor_id?: number
  status?: AppointmentStatus
}
