import { getToken, setToken, TOKEN_KEY } from './tokenStore'

function block() {
  const blocked = () => {
    throw new DOMException('blocked', 'SecurityError')
  }
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(blocked)
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(blocked)
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(blocked)
}

afterEach(() => {
  vi.restoreAllMocks()
  setToken(null)
  sessionStorage.clear()
})

describe('tokenStore', () => {
  it('saves the token in sessionStorage and reads it back', () => {
    setToken('tok-1')
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe('tok-1')
    expect(getToken()).toBe('tok-1')
  })

  it('returns null when no token was saved', () => {
    expect(getToken()).toBeNull()
  })

  it('clears the token when set to null', () => {
    setToken('tok-1')
    setToken(null)
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(getToken()).toBeNull()
  })

  it('does not throw and keeps the token in memory when storage is blocked', () => {
    block()
    expect(() => setToken('tok-2')).not.toThrow()
    expect(getToken()).toBe('tok-2')
  })

  it('does not throw when reading blocked storage with no token', () => {
    block()
    expect(getToken()).toBeNull()
  })

  it('clears the in-memory token when storage is blocked', () => {
    block()
    setToken('tok-3')
    expect(() => setToken(null)).not.toThrow()
    expect(getToken()).toBeNull()
  })
})
