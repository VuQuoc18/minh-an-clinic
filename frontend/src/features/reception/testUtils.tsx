import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import type { Appointment } from './types'

export function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

export function makeAppointment(over: Partial<Appointment> = {}): Appointment {
  return {
    id: 1,
    code: 'LH-261109-0001',
    patient_name: 'Nguyen Van A',
    patient_phone: '0901234567',
    doctor_id: 10,
    doctor_name: 'BS. Tran B',
    specialty_name: 'Nội',
    appt_date: '2026-11-09',
    start_time: '09:00:00',
    end_time: '09:30:00',
    status: 'booked',
    channel: 'online',
    queue_number: null,
    has_failed_notification: false,
    can_check_in: true,
    check_in_block_reason: null,
    ...over,
  }
}

export interface Route {
  method?: string
  match: string | RegExp
  status?: number
  body: unknown
}

/** Fetch giả: trả phản hồi của route khớp đầu tiên, ghi lại các lời gọi. */
export function mockFetch(routes: Route[]) {
  return vi.fn((url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET'
    const route = routes.find(
      (r) =>
        (r.method ?? 'GET') === method &&
        (typeof r.match === 'string'
          ? url.includes(r.match)
          : r.match.test(url)),
    )
    if (!route) return Promise.reject(new Error(`unmocked ${method} ${url}`))
    return Promise.resolve(
      new Response(JSON.stringify(route.body), { status: route.status ?? 200 }),
    )
  })
}
