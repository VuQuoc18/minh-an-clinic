import { loginPatient } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('auth api', () => {
  it('loginPatient gửi POST kèm số điện thoại và mật khẩu', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ ket_qua: 'THANH_CONG' })),
      )
    vi.stubGlobal('fetch', fetchMock)

    const result = await loginPatient({
      so_dien_thoai: '0912345678',
      mat_khau: 'abc',
    })

    expect(result.ket_qua).toBe('THANH_CONG')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/auth/patient/login')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({
      so_dien_thoai: '0912345678',
      mat_khau: 'abc',
    })
  })
})
