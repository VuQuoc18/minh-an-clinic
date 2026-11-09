import { ApiError, apiRequest, buildQuery, TOKEN_KEY } from './http'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

afterEach(() => {
  vi.unstubAllGlobals()
  sessionStorage.clear()
})

describe('buildQuery', () => {
  it('bỏ giá trị rỗng, null và undefined', () => {
    expect(buildQuery({ a: 'x', b: '', c: undefined, d: null, e: 0 })).toBe(
      '?a=x&e=0',
    )
  })

  it('trả chuỗi rỗng khi không có tham số', () => {
    expect(buildQuery()).toBe('')
    expect(buildQuery({ a: undefined })).toBe('')
  })

  it('mã hóa ký tự đặc biệt', () => {
    expect(buildQuery({ q: 'Nguyễn An' })).toBe('?q=Nguy%E1%BB%85n+An')
  })
})

describe('apiRequest', () => {
  it('gọi qua /api, gắn token và trả JSON', async () => {
    sessionStorage.setItem(TOKEN_KEY, 'tok-1')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([{ id: 1 }]))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiRequest('GET', '/reception/doctors', {
      params: { a: 1 },
    })

    expect(result).toEqual([{ id: 1 }])
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/reception/doctors?a=1')
    expect(init.headers.Authorization).toBe('Bearer tok-1')
  })

  it('không gắn Authorization khi chưa có token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({}))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('GET', '/x')

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined()
  })

  it('gửi body JSON kèm Content-Type', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({}))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('POST', '/x', { body: { slot_id: 3 } })

    const init = fetchMock.mock.calls[0][1]
    expect(init.method).toBe('POST')
    expect(init.headers['Content-Type']).toBe('application/json')
    expect(init.body).toBe('{"slot_id":3}')
  })

  it('đổi lỗi nghiệp vụ của máy chủ thành ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            detail: {
              code: 'SLOT_TAKEN',
              message: 'Khung giờ vừa có người đặt.',
            },
          },
          409,
        ),
      ),
    )

    await expect(apiRequest('POST', '/x')).rejects.toMatchObject({
      status: 409,
      code: 'SLOT_TAKEN',
      message: 'Khung giờ vừa có người đặt.',
    })
  })

  it('dùng thông báo chung khi phản hồi lỗi không phải JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('boom', { status: 500 })),
    )

    const error = await apiRequest('GET', '/x').catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 500, code: 'UNKNOWN' })
  })

  it('dùng thông báo chung khi lỗi 422 của FastAPI có detail dạng mảng', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ detail: [{ msg: 'field required' }] }, 422),
        ),
    )

    await expect(apiRequest('GET', '/x')).rejects.toMatchObject({
      status: 422,
      code: 'UNKNOWN',
    })
  })

  it('báo NETWORK_ERROR khi không kết nối được', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('failed')))

    await expect(apiRequest('GET', '/x')).rejects.toMatchObject({
      status: 0,
      code: 'NETWORK_ERROR',
    })
  })
})
