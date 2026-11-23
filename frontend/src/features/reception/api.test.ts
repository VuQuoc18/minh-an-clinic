import {
  checkIn,
  createWalkIn,
  getWalkInSuggestions,
  listAppointments,
  listDoctors,
  listSpecialties,
  searchProfiles,
} from './api'

function stubFetch() {
  const fetchMock = vi
    .fn()
    .mockImplementation(() => Promise.resolve(new Response('[]')))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('reception api', () => {
  it('listAppointments gửi bộ lọc và bỏ giá trị rỗng', async () => {
    const fetchMock = stubFetch()

    await listAppointments({ q: 'An', doctor_id: 3 })

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/reception/appointments?q=An&doctor_id=3',
    )
  })

  it('listAppointments không có bộ lọc thì không có query string', async () => {
    const fetchMock = stubFetch()

    await listAppointments({})

    expect(fetchMock.mock.calls[0][0]).toBe('/api/reception/appointments')
  })

  it('checkIn gọi POST tới đúng lịch hẹn', async () => {
    const fetchMock = stubFetch()

    await checkIn(7)

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/reception/appointments/7/check-in',
    )
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
  })

  it('listSpecialties và listDoctors gọi đúng đường dẫn', async () => {
    const fetchMock = stubFetch()

    await listSpecialties()
    await listDoctors()

    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual([
      '/api/reception/specialties',
      '/api/reception/doctors',
    ])
  })

  it('getWalkInSuggestions gửi specialty_id', async () => {
    const fetchMock = stubFetch()

    await getWalkInSuggestions(4)

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/reception/walk-in/suggestions?specialty_id=4',
    )
  })

  it('searchProfiles gửi số điện thoại', async () => {
    const fetchMock = stubFetch()

    await searchProfiles('0901234567')

    expect(fetchMock.mock.calls[0][0]).toBe(
      '/api/reception/profiles?phone=0901234567',
    )
  })

  it('createWalkIn gửi thân JSON bằng POST', async () => {
    const fetchMock = stubFetch()

    await createWalkIn({ slot_id: 5, profile_id: 9 })

    expect(fetchMock.mock.calls[0][0]).toBe('/api/reception/walk-in')
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      slot_id: 5,
      profile_id: 9,
    })
  })
})
